"""Integration API endpoints for external data sources"""
from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any, Optional
import httpx

from app.models.schemas import (
    ExternalDataRequest,
    ExternalDataSource,
    ExternalSourcesResponse,
    AssociationResponse,
)
from app.services.analysis_service import analysis_service
from app.services.filter_service import filter_service

router = APIRouter(prefix="/api/integration", tags=["Integration"])

# In-memory storage for registered external data sources
# In production, this would be stored in a database
_registered_sources: Dict[str, ExternalDataSource] = {}


@router.get("/sources", response_model=ExternalSourcesResponse)
async def list_external_sources():
    """
    List all registered external data sources.
    
    Returns information about external data sources that have been
    registered for integration with the functional data analysis.
    """
    return ExternalSourcesResponse(sources=list(_registered_sources.values()))


@router.post("/sources/register")
async def register_external_source(source: ExternalDataSource):
    """
    Register a new external data source.
    
    Registers an external data source (e.g., gene expression portal)
    that can be used in integrated analyses. The source must provide
    data keyed by donor RRID.
    
    **Example:**
    ```json
    {
        "name": "gene_expression",
        "api_url": "https://expression-api.example.com/data",
        "description": "Bulk RNA-seq gene expression data",
        "id_field": "RRID",
        "available_variables": ["INS", "GCK", "PDX1", "NKX6.1"]
    }
    ```
    """
    _registered_sources[source.name] = source
    return {"message": f"Source '{source.name}' registered successfully"}


@router.delete("/sources/{source_name}")
async def unregister_external_source(source_name: str):
    """
    Unregister an external data source.
    """
    if source_name not in _registered_sources:
        raise HTTPException(status_code=404, detail=f"Source '{source_name}' not found")
    
    del _registered_sources[source_name]
    return {"message": f"Source '{source_name}' unregistered successfully"}


@router.post("/analyze", response_model=AssociationResponse)
async def analyze_with_external_data(request: ExternalDataRequest):
    """
    Run association analysis with external data.
    
    Analyzes associations between functional traits and variables from
    external data sources (e.g., gene expression levels). This enables
    integration with other data portals in the PanKbase ecosystem.
    
    **Two modes of providing external data:**
    
    1. **Direct data submission** - Include external data directly in the request:
    ```json
    {
        "external_data": {
            "RRID:SAMN08769199": {"GCK_expression": 5.2, "INS_expression": 8.1},
            "RRID:SAMN08769198": {"GCK_expression": 4.8, "INS_expression": 7.5}
        },
        "variables_of_interest": ["GCK_expression", "INS_expression"]
    }
    ```
    
    2. **Registered source** - Use a pre-registered external data source:
    ```json
    {
        "external_source_name": "gene_expression",
        "variables_of_interest": ["INS", "GCK"]
    }
    ```
    
    **Note:** When using a registered source, the API will attempt to fetch
    data for the filtered donors from the source's API endpoint.
    """
    try:
        # Validate request
        if not request.external_data and not request.external_source_name:
            raise HTTPException(
                status_code=400,
                detail="Either external_data or external_source_name must be provided"
            )
        
        if not request.variables_of_interest:
            raise HTTPException(
                status_code=400,
                detail="At least one variable of interest is required"
            )
        
        # If using registered source, fetch data
        if request.external_source_name and not request.external_data:
            request.external_data = await _fetch_from_external_source(
                request.external_source_name,
                request.filter_criteria,
                request.variables_of_interest
            )
        
        # Run analysis
        results, filter_summary = analysis_service.run_external_data_analysis(request)
        
        return AssociationResponse(
            results=results,
            filter_summary=filter_summary,
            control_variables=request.control_variables,
            n_total_samples=filter_summary.get('n_samples', 0)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def _fetch_from_external_source(
    source_name: str,
    filter_criteria,
    variables: List[str]
) -> Dict[str, Dict[str, float]]:
    """
    Fetch data from a registered external source.
    
    This is a placeholder implementation that shows how external
    data would be fetched. In production, this would make actual
    HTTP requests to the external API.
    """
    if source_name not in _registered_sources:
        raise HTTPException(
            status_code=404,
            detail=f"External source '{source_name}' not registered"
        )
    
    source = _registered_sources[source_name]
    
    # Get filtered donor RRIDs
    donor_rrids = filter_service.get_filtered_donor_rrids(filter_criteria)
    
    if not source.api_url:
        raise HTTPException(
            status_code=400,
            detail=f"Source '{source_name}' has no API URL configured"
        )
    
    # In production, this would make an HTTP request to the external API
    # Example implementation:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                source.api_url,
                json={
                    "donor_ids": donor_rrids,
                    "variables": variables,
                    "id_field": source.id_field
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=502,
                    detail=f"External API returned status {response.status_code}"
                )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to connect to external source: {str(e)}"
        )


@router.get("/donors")
async def get_donors_for_integration():
    """
    Get list of donor RRIDs available for integration.
    
    Returns all donor RRIDs that have functional data and can be
    used for integration with external data sources.
    """
    try:
        from app.services.data_loader import data_loader
        
        rrids = data_loader.merged_df['RRID'].tolist()
        
        return {
            "count": len(rrids),
            "donor_rrids": rrids
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate")
async def validate_external_data(data: Dict[str, Dict[str, Any]]):
    """
    Validate external data format before analysis.
    
    Checks that the provided external data:
    - Has valid donor RRIDs
    - Has matching donors in the functional data
    - Has consistent variable names
    
    Returns validation results and statistics.
    """
    try:
        from app.services.data_loader import data_loader
        
        available_rrids = set(data_loader.merged_df['RRID'].tolist())
        provided_rrids = set(data.keys())
        
        matching_rrids = available_rrids & provided_rrids
        unmatched_rrids = provided_rrids - available_rrids
        
        # Get unique variables across all donors
        all_variables = set()
        for donor_data in data.values():
            all_variables.update(donor_data.keys())
        
        # Check for consistency
        inconsistent_donors = []
        for donor_id, donor_data in data.items():
            if set(donor_data.keys()) != all_variables:
                inconsistent_donors.append(donor_id)
        
        return {
            "valid": len(unmatched_rrids) == 0 and len(inconsistent_donors) == 0,
            "statistics": {
                "total_provided": len(provided_rrids),
                "matching_donors": len(matching_rrids),
                "unmatched_donors": len(unmatched_rrids),
                "variables": list(all_variables),
                "inconsistent_donors": len(inconsistent_donors)
            },
            "unmatched_rrids": list(unmatched_rrids)[:20],  # Limit to first 20
            "inconsistent_rrids": inconsistent_donors[:20]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Webhook/Callback Support for Async Integration
# ============================================================================

@router.post("/webhook/register")
async def register_webhook(
    source_name: str,
    webhook_url: str,
    events: List[str] = ["analysis_complete"]
):
    """
    Register a webhook for async notifications.
    
    This is a placeholder for future async integration support.
    When long-running analyses complete, the registered webhook
    would be called with the results.
    """
    # Placeholder implementation
    return {
        "message": "Webhook registration is not yet implemented",
        "note": "This endpoint is reserved for future async integration support"
    }
