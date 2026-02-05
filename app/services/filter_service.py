"""Filter service for applying filters to donor data"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from app.models.schemas import FilterRequest, RangeFilter
from app.services.data_loader import data_loader


class FilterService:
    """Service for filtering donor data based on metadata criteria"""
    
    def __init__(self):
        self.data_loader = data_loader
    
    def apply_filters(self, filter_request: FilterRequest) -> pd.DataFrame:
        """
        Apply filter criteria to the merged donor+traits dataframe.
        
        Args:
            filter_request: Filter criteria
            
        Returns:
            Filtered DataFrame
        """
        df = self.data_loader.merged_df.copy()
        
        # Apply categorical filters
        df = self._apply_categorical_filters(df, filter_request)
        
        # Apply numerical range filters
        df = self._apply_numerical_filters(df, filter_request)
        
        # Apply boolean filters
        df = self._apply_boolean_filters(df, filter_request)
        
        return df
    
    def _apply_categorical_filters(
        self, df: pd.DataFrame, filter_request: FilterRequest
    ) -> pd.DataFrame:
        """Apply categorical (multi-select) filters"""
        
        # Mapping of filter fields to DataFrame columns
        categorical_mappings = {
            'gender': 'Gender',
            'collections': 'Collections',
            'diabetes_status': 'Description of diabetes status',
            'ethnicities': 'Ethnicities',
            'cause_of_death': 'Cause of Death',
            'donation_type': 'Donation Type',
            'isolation_center': 'biosample_Isolation_center',
        }
        
        for filter_field, df_column in categorical_mappings.items():
            filter_values = getattr(filter_request, filter_field, None)
            
            if filter_values and df_column in df.columns:
                # Convert filter values to lowercase for case-insensitive matching
                filter_values_lower = [str(v).lower().strip() for v in filter_values]
                
                # Create a mask for matching values (handle NaN safely)
                def match_value(val):
                    if pd.isna(val):
                        return False
                    return str(val).lower().strip() in filter_values_lower
                
                mask = df[df_column].apply(match_value)
                df = df[mask]
        
        return df
    
    def _apply_numerical_filters(
        self, df: pd.DataFrame, filter_request: FilterRequest
    ) -> pd.DataFrame:
        """Apply numerical range filters"""
        
        # Mapping of filter fields to DataFrame columns
        numerical_mappings = {
            'age_range': 'Age (years)',
            'bmi_range': 'BMI',
            'hba1c_range': 'HbA1C (percentage)',
            'diabetes_duration_range': 'Diabetes Duration (years)',
            'c_peptide_range': 'C-Peptide (ng/ml)',
            'purity_range': 'biosample_Purity (Percentage)',
            'viability_range': 'biosample_Prep Viability (percentage)',
            'islet_yield_range': 'biosample_Islet Yield (IEQ)',
        }
        
        for filter_field, df_column in numerical_mappings.items():
            range_filter: Optional[RangeFilter] = getattr(filter_request, filter_field, None)
            
            if range_filter and df_column in df.columns:
                if range_filter.min_value is not None:
                    df = df[df[df_column] >= range_filter.min_value]
                if range_filter.max_value is not None:
                    df = df[df[df_column] <= range_filter.max_value]
        
        return df
    
    def _apply_boolean_filters(
        self, df: pd.DataFrame, filter_request: FilterRequest
    ) -> pd.DataFrame:
        """Apply boolean filters"""
        
        # Mapping of filter fields to DataFrame columns
        boolean_mappings = {
            'aab_gada_positive': 'AAB GADA POSITIVE',
            'aab_ia2_positive': 'AAB IA2 POSITIVE',
            'aab_iaa_positive': 'AAB IAA POSITIVE',
            'aab_znt8_positive': 'AAB ZNT8 POSITIVE',
            'multi_aab': 'Multi AAB',
        }
        
        for filter_field, df_column in boolean_mappings.items():
            filter_value = getattr(filter_request, filter_field, None)
            
            if filter_value is not None and df_column in df.columns:
                df = df[df[df_column] == filter_value]
        
        return df
    
    def get_filtered_donor_rrids(self, filter_request: FilterRequest) -> List[str]:
        """Get list of donor RRIDs matching filter criteria"""
        filtered_df = self.apply_filters(filter_request)
        return filtered_df['RRID'].tolist()
    
    def get_filtered_donor_metadata(
        self, filter_request: FilterRequest
    ) -> List[Dict[str, Any]]:
        """Get donor metadata for filtered donors"""
        filtered_df = self.apply_filters(filter_request)
        
        # Select donor metadata columns only (exclude traits and biosample)
        donor_cols = [col for col in self.data_loader.donor_df.columns 
                      if col in filtered_df.columns]
        
        return filtered_df[donor_cols].to_dict(orient='records')
    
    def get_filtered_traits(self, filter_request: FilterRequest) -> pd.DataFrame:
        """Get trait data for filtered donors"""
        filtered_df = self.apply_filters(filter_request)
        
        # Get trait columns
        trait_cols = ['RRID'] + self.data_loader.get_trait_columns()
        available_cols = [c for c in trait_cols if c in filtered_df.columns]
        
        return filtered_df[available_cols]
    
    def get_filter_metadata(self) -> Dict[str, Any]:
        """Get available filter options and ranges"""
        df = self.data_loader.merged_df
        
        # Categorical options
        categorical_filters = {}
        categorical_columns = {
            'Gender': 'gender',
            'Collections': 'collections', 
            'Description of diabetes status': 'diabetes_status',
            'Ethnicities': 'ethnicities',
            'Cause of Death': 'cause_of_death',
            'Donation Type': 'donation_type',
            'biosample_Isolation_center': 'isolation_center',
        }
        
        for df_col, filter_name in categorical_columns.items():
            if df_col in df.columns:
                values = df[df_col].dropna().unique().tolist()
                categorical_filters[filter_name] = sorted([str(v) for v in values if v])
        
        # Numerical ranges
        numerical_filters = {}
        numerical_columns = {
            'Age (years)': 'age_range',
            'BMI': 'bmi_range',
            'HbA1C (percentage)': 'hba1c_range',
            'Diabetes Duration (years)': 'diabetes_duration_range',
            'C-Peptide (ng/ml)': 'c_peptide_range',
            'biosample_Purity (Percentage)': 'purity_range',
            'biosample_Prep Viability (percentage)': 'viability_range',
            'biosample_Islet Yield (IEQ)': 'islet_yield_range',
        }
        
        for df_col, filter_name in numerical_columns.items():
            if df_col in df.columns:
                col_data = pd.to_numeric(df[df_col], errors='coerce')
                if not col_data.isna().all():
                    numerical_filters[filter_name] = {
                        'min': float(col_data.min()),
                        'max': float(col_data.max())
                    }
        
        return {
            'categorical_filters': categorical_filters,
            'numerical_filters': numerical_filters,
            'total_donors': len(self.data_loader.donor_df),
            'donors_with_functional_data': len(self.data_loader.merged_df)
        }
    
    def get_timeseries_for_filter(
        self, 
        filter_request: FilterRequest, 
        timeseries_type: str = 'ins_ieq'
    ) -> Dict[str, Any]:
        """Get time-series data for filtered donors"""
        donor_rrids = self.get_filtered_donor_rrids(filter_request)
        
        ts_df = self.data_loader.get_timeseries_for_donors(donor_rrids, timeseries_type)
        
        # Convert to response format
        time_points = ts_df['time'].tolist()
        
        data = {}
        for col in ts_df.columns:
            if col != 'time':
                # Convert NaN to None for JSON serialization
                values = ts_df[col].tolist()
                data[col] = [None if pd.isna(v) else v for v in values]
        
        return {
            'donor_count': len(data),
            'timeseries_type': timeseries_type,
            'time_points': time_points,
            'data': data
        }


# Global instance
filter_service = FilterService()
