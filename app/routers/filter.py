"""Filter API endpoints"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import pandas as pd
import io
import json
from typing import Dict, Any

from app.models.schemas import (
    FilterRequest,
    FilterMetadataResponse,
    FilteredDonorsResponse,
    TimeseriesRequest,
    TimeseriesResponse,
    TraitsResponse,
    DownloadRequest,
)
from app.models.enums import TimeseriesType
from app.services.filter_service import filter_service
from app.services.data_loader import data_loader

router = APIRouter(prefix="/api/filter", tags=["Filter"])


@router.get("/metadata", response_model=FilterMetadataResponse)
async def get_filter_metadata():
    """
    Get available filter options and ranges.
    
    Returns categorical options (for dropdown/multi-select) and 
    numerical ranges (for slider/input) for all filterable fields.
    """
    try:
        metadata = filter_service.get_filter_metadata()
        return FilterMetadataResponse(**metadata)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/donors", response_model=FilteredDonorsResponse)
async def filter_donors(filter_request: FilterRequest):
    """
    Filter donors based on metadata criteria.
    
    Returns list of donor RRIDs and their metadata matching the filter criteria.
    """
    try:
        filtered_df = filter_service.apply_filters(filter_request)
        
        # Get donor metadata columns
        donor_cols = [col for col in data_loader.donor_df.columns 
                      if col in filtered_df.columns]
        
        return FilteredDonorsResponse(
            donor_count=len(filtered_df),
            donor_rrids=filtered_df['RRID'].tolist(),
            donor_metadata=filtered_df[donor_cols].to_dict(orient='records')
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/timeseries", response_model=TimeseriesResponse)
async def get_timeseries(request: TimeseriesRequest):
    """
    Get time-series data for filtered donors.
    
    Returns IEQ-normalized (or content-normalized) time-series data
    for insulin or glucagon secretion.
    """
    try:
        result = filter_service.get_timeseries_for_filter(
            request.filter_criteria,
            request.timeseries_type.value
        )
        return TimeseriesResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/traits", response_model=TraitsResponse)
async def get_traits(filter_request: FilterRequest):
    """
    Get trait data for filtered donors.
    
    Returns derived traits (AUC, SI, II, etc.) for filtered donors.
    """
    try:
        traits_df = filter_service.get_filtered_traits(filter_request)
        
        trait_names = [c for c in traits_df.columns if c != 'RRID']
        
        return TraitsResponse(
            donor_count=len(traits_df),
            trait_names=trait_names,
            data=traits_df.to_dict(orient='records')
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/download")
async def download_data(request: DownloadRequest):
    """
    Download filtered data as CSV or JSON.
    
    Allows downloading metadata, traits, and time-series data
    for filtered donors.
    """
    try:
        filtered_df = filter_service.apply_filters(request.filter_criteria)
        donor_rrids = filtered_df['RRID'].tolist()
        
        if request.format.lower() == 'json':
            return await _download_json(request, filtered_df, donor_rrids)
        else:
            return await _download_csv(request, filtered_df, donor_rrids)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def _download_json(
    request: DownloadRequest, 
    filtered_df: pd.DataFrame, 
    donor_rrids: list
) -> Dict[str, Any]:
    """Create JSON download response"""
    result = {}
    
    if request.include_metadata:
        donor_cols = [col for col in data_loader.donor_df.columns 
                      if col in filtered_df.columns]
        result['metadata'] = filtered_df[donor_cols].to_dict(orient='records')
    
    if request.include_traits:
        trait_cols = ['RRID'] + data_loader.get_trait_columns()
        available_cols = [c for c in trait_cols if c in filtered_df.columns]
        result['traits'] = filtered_df[available_cols].to_dict(orient='records')
    
    if request.include_timeseries:
        result['timeseries'] = {}
        for ts_type in request.timeseries_types:
            ts_df = data_loader.get_timeseries_for_donors(donor_rrids, ts_type.value)
            result['timeseries'][ts_type.value] = {
                'time_points': ts_df['time'].tolist(),
                'data': {col: ts_df[col].tolist() 
                        for col in ts_df.columns if col != 'time'}
            }
    
    return result


async def _download_csv(
    request: DownloadRequest, 
    filtered_df: pd.DataFrame, 
    donor_rrids: list
) -> StreamingResponse:
    """Create CSV download response (ZIP with multiple files)"""
    import zipfile
    
    # Create in-memory ZIP file
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        if request.include_metadata:
            donor_cols = [col for col in data_loader.donor_df.columns 
                          if col in filtered_df.columns]
            metadata_csv = filtered_df[donor_cols].to_csv(index=False)
            zip_file.writestr('donor_metadata.csv', metadata_csv)
        
        if request.include_traits:
            trait_cols = ['RRID'] + data_loader.get_trait_columns()
            available_cols = [c for c in trait_cols if c in filtered_df.columns]
            traits_csv = filtered_df[available_cols].to_csv(index=False)
            zip_file.writestr('traits.csv', traits_csv)
        
        if request.include_timeseries:
            for ts_type in request.timeseries_types:
                ts_df = data_loader.get_timeseries_for_donors(donor_rrids, ts_type.value)
                ts_csv = ts_df.to_csv(index=False)
                zip_file.writestr(f'timeseries_{ts_type.value}.csv', ts_csv)
    
    zip_buffer.seek(0)
    
    return StreamingResponse(
        zip_buffer,
        media_type='application/zip',
        headers={'Content-Disposition': 'attachment; filename=pankbase_data.zip'}
    )


@router.get("/timeseries-types")
async def get_timeseries_types():
    """Get available time-series data types"""
    return {
        "types": [
            {
                "value": TimeseriesType.INS_IEQ.value,
                "label": "Insulin (IEQ normalized)",
                "unit": "ng/100 IEQ/min"
            },
            {
                "value": TimeseriesType.INS_CONTENT.value,
                "label": "Insulin (Content normalized)",
                "unit": "% of total content"
            },
            {
                "value": TimeseriesType.GCG_IEQ.value,
                "label": "Glucagon (IEQ normalized)",
                "unit": "pg/100 IEQ/min"
            },
            {
                "value": TimeseriesType.GCG_CONTENT.value,
                "label": "Glucagon (Content normalized)",
                "unit": "% of total content"
            }
        ]
    }
