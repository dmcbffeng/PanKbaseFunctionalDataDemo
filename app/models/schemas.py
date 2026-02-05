"""Pydantic schemas for API requests and responses"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Tuple
from .enums import TimeseriesType, AnalysisMethod, VariableType


# ============================================================================
# Filter Schemas
# ============================================================================

class RangeFilter(BaseModel):
    """Range filter for numerical values"""
    min_value: Optional[float] = Field(None, description="Minimum value (inclusive)")
    max_value: Optional[float] = Field(None, description="Maximum value (inclusive)")


class FilterRequest(BaseModel):
    """Request schema for filtering donors"""
    
    # Donor metadata filters - Categorical (multi-select)
    gender: Optional[List[str]] = Field(None, description="Filter by gender (e.g., ['male', 'female'])")
    collections: Optional[List[str]] = Field(None, description="Filter by collection center (e.g., ['HPAP', 'IIDP'])")
    diabetes_status: Optional[List[str]] = Field(None, description="Filter by diabetes status description")
    ethnicities: Optional[List[str]] = Field(None, description="Filter by ethnicity")
    cause_of_death: Optional[List[str]] = Field(None, description="Filter by cause of death")
    donation_type: Optional[List[str]] = Field(None, description="Filter by donation type")
    
    # Donor metadata filters - Numerical (range)
    age_range: Optional[RangeFilter] = Field(None, description="Filter by age range in years")
    bmi_range: Optional[RangeFilter] = Field(None, description="Filter by BMI range")
    hba1c_range: Optional[RangeFilter] = Field(None, description="Filter by HbA1c percentage range")
    diabetes_duration_range: Optional[RangeFilter] = Field(None, description="Filter by diabetes duration in years")
    c_peptide_range: Optional[RangeFilter] = Field(None, description="Filter by C-Peptide (ng/ml) range")
    
    # Autoantibody filters
    aab_gada_positive: Optional[bool] = Field(None, description="Filter by GADA positivity")
    aab_ia2_positive: Optional[bool] = Field(None, description="Filter by IA2 positivity")
    aab_iaa_positive: Optional[bool] = Field(None, description="Filter by IAA positivity")
    aab_znt8_positive: Optional[bool] = Field(None, description="Filter by ZNT8 positivity")
    multi_aab: Optional[bool] = Field(None, description="Filter by multiple autoantibody positivity")
    
    # Biosample filters - Categorical
    isolation_center: Optional[List[str]] = Field(None, description="Filter by isolation center")
    
    # Biosample filters - Numerical
    purity_range: Optional[RangeFilter] = Field(None, description="Filter by purity percentage range")
    viability_range: Optional[RangeFilter] = Field(None, description="Filter by prep viability percentage range")
    islet_yield_range: Optional[RangeFilter] = Field(None, description="Filter by islet yield (IEQ) range")

    class Config:
        json_schema_extra = {
            "example": {
                "gender": ["male", "female"],
                "collections": ["HPAP"],
                "diabetes_status": ["control without diabetes", "type 1 diabetes"],
                "age_range": {"min_value": 18, "max_value": 65},
                "bmi_range": {"min_value": 18.5, "max_value": 30}
            }
        }


class TimeseriesRequest(BaseModel):
    """Request schema for getting time-series data"""
    filter_criteria: FilterRequest = Field(..., description="Filter criteria to select donors")
    timeseries_type: TimeseriesType = Field(
        TimeseriesType.INS_IEQ, 
        description="Type of time-series data"
    )


class DownloadRequest(BaseModel):
    """Request schema for downloading data"""
    filter_criteria: FilterRequest = Field(..., description="Filter criteria to select donors")
    include_timeseries: bool = Field(True, description="Include time-series data in download")
    include_traits: bool = Field(True, description="Include trait data in download")
    include_metadata: bool = Field(True, description="Include donor metadata in download")
    timeseries_types: List[TimeseriesType] = Field(
        default=[TimeseriesType.INS_IEQ],
        description="Types of time-series data to include"
    )
    format: str = Field("csv", description="Download format (csv or json)")


# ============================================================================
# Response Schemas
# ============================================================================

class FilterMetadataResponse(BaseModel):
    """Response schema for filter metadata (available options)"""
    categorical_filters: Dict[str, List[str]] = Field(
        ..., description="Available options for categorical filters"
    )
    numerical_filters: Dict[str, Dict[str, float]] = Field(
        ..., description="Min/max ranges for numerical filters"
    )
    total_donors: int = Field(..., description="Total number of donors in database")
    donors_with_functional_data: int = Field(
        ..., description="Number of donors with functional data"
    )


class FilteredDonorsResponse(BaseModel):
    """Response schema for filtered donors"""
    donor_count: int = Field(..., description="Number of donors matching filter criteria")
    donor_rrids: List[str] = Field(..., description="List of donor RRIDs")
    donor_metadata: List[Dict[str, Any]] = Field(
        ..., description="Metadata for filtered donors"
    )


class TimeseriesResponse(BaseModel):
    """Response schema for time-series data"""
    donor_count: int = Field(..., description="Number of donors with time-series data")
    timeseries_type: str = Field(..., description="Type of time-series data")
    time_points: List[float] = Field(..., description="Time points in minutes")
    data: Dict[str, List[Optional[float]]] = Field(
        ..., description="Time-series data per donor (RRID -> values)"
    )


class TraitsResponse(BaseModel):
    """Response schema for trait data"""
    donor_count: int = Field(..., description="Number of donors with trait data")
    trait_names: List[str] = Field(..., description="List of trait column names")
    data: List[Dict[str, Any]] = Field(
        ..., description="Trait data per donor"
    )


# ============================================================================
# Analysis Schemas
# ============================================================================

class AssociationRequest(BaseModel):
    """Request schema for association analysis"""
    filter_criteria: FilterRequest = Field(
        default_factory=FilterRequest,
        description="Filter criteria to select donors for analysis"
    )
    variables_of_interest: List[str] = Field(
        ..., description="Variables to analyze for association with traits"
    )
    control_variables: List[str] = Field(
        default=[], description="Variables to control for in analysis"
    )
    traits: Optional[List[str]] = Field(
        None, description="Specific traits to analyze (None = all traits)"
    )
    analysis_method: AnalysisMethod = Field(
        AnalysisMethod.LINEAR_REGRESSION,
        description="Statistical method to use"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "filter_criteria": {},
                "variables_of_interest": ["Age (years)", "BMI"],
                "control_variables": ["Gender"],
                "traits": ["INS-IEQ Basal Secretion", "INS-IEQ G 16.7 AUC"],
                "analysis_method": "linear_regression"
            }
        }


class VariableInfo(BaseModel):
    """Information about an available variable"""
    name: str = Field(..., description="Variable name")
    type: VariableType = Field(..., description="Variable type")
    source: str = Field(..., description="Source of variable (donor, biosample, trait)")
    description: Optional[str] = Field(None, description="Variable description")
    unique_values: Optional[List[str]] = Field(
        None, description="Unique values for categorical variables"
    )
    range: Optional[Dict[str, float]] = Field(
        None, description="Min/max range for numerical variables"
    )


class VariablesResponse(BaseModel):
    """Response schema for available analysis variables"""
    donor_variables: List[VariableInfo] = Field(
        ..., description="Variables from donor metadata"
    )
    biosample_variables: List[VariableInfo] = Field(
        ..., description="Variables from biosample metadata"
    )
    trait_variables: List[VariableInfo] = Field(
        ..., description="Trait variables"
    )


class AssociationResult(BaseModel):
    """Single association result"""
    trait: str = Field(..., description="Trait name")
    variable: str = Field(..., description="Variable of interest")
    coefficient: Optional[float] = Field(None, description="Regression coefficient or correlation")
    std_error: Optional[float] = Field(None, description="Standard error")
    p_value: Optional[float] = Field(None, description="P-value")
    ci_lower: Optional[float] = Field(None, description="95% CI lower bound")
    ci_upper: Optional[float] = Field(None, description="95% CI upper bound")
    r_squared: Optional[float] = Field(None, description="R-squared (for regression)")
    n_samples: int = Field(..., description="Number of samples in analysis")
    method: str = Field(..., description="Analysis method used")


class AssociationResponse(BaseModel):
    """Response schema for association analysis"""
    results: List[AssociationResult] = Field(
        ..., description="Association results"
    )
    filter_summary: Dict[str, Any] = Field(
        ..., description="Summary of applied filters"
    )
    control_variables: List[str] = Field(
        ..., description="Control variables used"
    )
    n_total_samples: int = Field(
        ..., description="Total samples after filtering"
    )


# ============================================================================
# Integration Schemas
# ============================================================================

class ExternalDataSource(BaseModel):
    """Schema for registering external data sources"""
    name: str = Field(..., description="Name of the external data source")
    api_url: Optional[str] = Field(None, description="API URL for fetching data")
    description: Optional[str] = Field(None, description="Description of the data source")
    id_field: str = Field("RRID", description="Field name for donor identification")
    available_variables: List[str] = Field(
        ..., description="List of available variable names"
    )


class ExternalDataRequest(BaseModel):
    """Request schema for analysis with external data"""
    filter_criteria: FilterRequest = Field(
        default_factory=FilterRequest,
        description="Filter criteria to select donors"
    )
    external_data: Optional[Dict[str, Dict[str, float]]] = Field(
        None, description="External data: {donor_id: {variable_name: value}}"
    )
    external_source_name: Optional[str] = Field(
        None, description="Name of registered external data source"
    )
    variables_of_interest: List[str] = Field(
        ..., description="Variables from external data to analyze"
    )
    control_variables: List[str] = Field(
        default=[], description="Variables to control for"
    )
    traits: Optional[List[str]] = Field(
        None, description="Specific traits to analyze"
    )
    analysis_method: AnalysisMethod = Field(
        AnalysisMethod.LINEAR_REGRESSION,
        description="Statistical method to use"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "filter_criteria": {"collections": ["HPAP"]},
                "external_data": {
                    "RRID:SAMN08769199": {"GCK_expression": 5.2, "INS_expression": 8.1},
                    "RRID:SAMN08769198": {"GCK_expression": 4.8, "INS_expression": 7.5}
                },
                "variables_of_interest": ["GCK_expression", "INS_expression"],
                "control_variables": ["Age (years)", "Gender"],
                "analysis_method": "linear_regression"
            }
        }


class ExternalSourcesResponse(BaseModel):
    """Response schema for listing registered external data sources"""
    sources: List[ExternalDataSource] = Field(
        ..., description="List of registered external data sources"
    )


# ============================================================================
# Error Schemas
# ============================================================================

class ErrorResponse(BaseModel):
    """Error response schema"""
    detail: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")
