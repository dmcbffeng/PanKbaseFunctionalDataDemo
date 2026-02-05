"""Data loader service for loading and caching PanKbase data"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Optional, List
from functools import lru_cache


class DataLoader:
    """Singleton service to load and cache all PanKbase data"""
    
    _instance: Optional['DataLoader'] = None
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if DataLoader._initialized:
            return
        
        from app.config import settings
        self.settings = settings
        
        # DataFrames
        self._donor_df: Optional[pd.DataFrame] = None
        self._biosample_df: Optional[pd.DataFrame] = None
        self._traits_df: Optional[pd.DataFrame] = None
        self._timeseries: Dict[str, pd.DataFrame] = {}
        self._merged_df: Optional[pd.DataFrame] = None
        
        DataLoader._initialized = True
    
    def load_all(self) -> None:
        """Load all data files into memory"""
        self._load_donor_metadata()
        self._load_biosample_metadata()
        self._load_traits()
        self._load_timeseries()
        self._create_merged_dataframe()
    
    def _load_donor_metadata(self) -> None:
        """Load donor metadata from TSV file"""
        path = self.settings.donor_metadata_path
        if not path.exists():
            raise FileNotFoundError(f"Donor metadata file not found: {path}")
        
        self._donor_df = pd.read_csv(path, sep='\t', dtype=str)
        
        # Clean up column names
        self._donor_df.columns = self._donor_df.columns.str.strip()
        
        # Convert numeric columns
        numeric_cols = [
            'Age (years)', 'BMI', 'C-Peptide (ng/ml)', 'Diabetes Duration (years)',
            'HbA1C (percentage)', 'AAB GADA value (unit/ml)', 'AAB IA2 value (unit/ml)',
            'AAB IAA value (unit/ml)', 'AAB ZNT8 value (unit/ml)', 'Number AAB',
            'Hospital Stay (hours)'
        ]
        for col in numeric_cols:
            if col in self._donor_df.columns:
                self._donor_df[col] = pd.to_numeric(
                    self._donor_df[col].replace('-', np.nan), errors='coerce'
                )
        
        # Convert boolean columns
        bool_cols = [
            'AAB GADA POSITIVE', 'AAB IA2 POSITIVE', 'AAB IAA POSITIVE',
            'AAB ZNT8 POSITIVE', 'Multi AAB', 'Only AAB GADA', 'Only AAB IA2',
            'Only AAB IAA', 'Only AAB ZNT8', 'Family History of Diabetes'
        ]
        for col in bool_cols:
            if col in self._donor_df.columns:
                self._donor_df[col] = self._donor_df[col].map({
                    'TRUE': True, 'FALSE': False, 'true': True, 'false': False,
                    '-': None, '': None
                })
        
        # Replace '-' with NaN for all string columns
        self._donor_df = self._donor_df.replace('-', np.nan)
        self._donor_df = self._donor_df.replace('', np.nan)
        
        print(f"Loaded {len(self._donor_df)} donor records")
    
    def _load_biosample_metadata(self) -> None:
        """Load biosample metadata from TSV file"""
        path = self.settings.biosample_metadata_path
        if not path.exists():
            raise FileNotFoundError(f"Biosample metadata file not found: {path}")
        
        self._biosample_df = pd.read_csv(path, sep='\t', dtype=str)
        
        # Clean up column names
        self._biosample_df.columns = self._biosample_df.columns.str.strip()
        
        # Convert numeric columns
        numeric_cols = [
            'Cold Ischaemia Time (hours)', 'Warm Ischaemia Duration / Down Time (hours)',
            'Digest Time (hours)', 'IEQ/Pancreas Weight (grams)', 'Islet Yield (IEQ)',
            'Percentage Trapped (percentage)', 'Pre-Shipment Culture Time (hours)',
            'Prep Viability (percentage)', 'Purity (Percentage)'
        ]
        for col in numeric_cols:
            if col in self._biosample_df.columns:
                self._biosample_df[col] = pd.to_numeric(
                    self._biosample_df[col].replace('-', np.nan), errors='coerce'
                )
        
        # Convert boolean columns
        bool_cols = ['Islet Function Available', 'Islet Histology', 'Islet Morphology']
        for col in bool_cols:
            if col in self._biosample_df.columns:
                self._biosample_df[col] = self._biosample_df[col].map({
                    'TRUE': True, 'FALSE': False, 'true': True, 'false': False,
                    '-': None, '': None
                })
        
        # Replace '-' with NaN
        self._biosample_df = self._biosample_df.replace('-', np.nan)
        self._biosample_df = self._biosample_df.replace('', np.nan)
        
        print(f"Loaded {len(self._biosample_df)} biosample records")
    
    def _load_traits(self) -> None:
        """Load HIPP traits data from CSV file"""
        path = self.settings.traits_path
        if not path.exists():
            raise FileNotFoundError(f"Traits file not found: {path}")
        
        self._traits_df = pd.read_csv(path)
        
        # Rename 'Donor ID' to 'RRID' for consistency
        if 'Donor ID' in self._traits_df.columns:
            self._traits_df = self._traits_df.rename(columns={'Donor ID': 'RRID'})
        
        # All columns except RRID and HPAP ID are numeric traits
        trait_cols = [c for c in self._traits_df.columns if c not in ['RRID', 'HPAP ID']]
        for col in trait_cols:
            self._traits_df[col] = pd.to_numeric(self._traits_df[col], errors='coerce')
        
        print(f"Loaded {len(self._traits_df)} trait records with {len(trait_cols)} traits")
    
    def _load_timeseries(self) -> None:
        """Load all time-series data files"""
        for name, path in self.settings.timeseries_paths.items():
            if not path.exists():
                print(f"Warning: Time-series file not found: {path}")
                continue
            
            df = pd.read_csv(path)
            
            # First column is index, second is 'time', rest are donor RRIDs
            # Drop the unnamed index column if present
            if df.columns[0] == '' or df.columns[0].startswith('Unnamed'):
                df = df.drop(df.columns[0], axis=1)
            
            # Ensure 'time' column exists
            if 'time' not in df.columns:
                # If first column is numeric, assume it's time
                if df.columns[0] != 'time':
                    df = df.rename(columns={df.columns[0]: 'time'})
            
            self._timeseries[name] = df
            
            # Count donor columns (all columns except 'time')
            donor_cols = [c for c in df.columns if c != 'time']
            print(f"Loaded time-series '{name}' with {len(df)} time points and {len(donor_cols)} donors")
    
    def _create_merged_dataframe(self) -> None:
        """Create a merged dataframe joining donor metadata with traits"""
        if self._donor_df is None or self._traits_df is None:
            return
        
        # Merge donor metadata with traits on RRID
        self._merged_df = self._donor_df.merge(
            self._traits_df,
            on='RRID',
            how='inner'  # Only keep donors with functional data
        )
        
        # Optionally merge with biosample data
        if self._biosample_df is not None:
            # Aggregate biosample data by donor (take first biosample per donor)
            biosample_by_donor = self._biosample_df.groupby('Donors').first().reset_index()
            biosample_by_donor = biosample_by_donor.rename(columns={'Donors': 'Accession'})
            
            # Add biosample columns with prefix to avoid conflicts
            biosample_cols = [c for c in biosample_by_donor.columns if c != 'Accession']
            rename_map = {c: f'biosample_{c}' for c in biosample_cols}
            biosample_by_donor = biosample_by_donor.rename(columns=rename_map)
            
            self._merged_df = self._merged_df.merge(
                biosample_by_donor,
                on='Accession',
                how='left'
            )
        
        print(f"Created merged dataframe with {len(self._merged_df)} records")
    
    @property
    def donor_df(self) -> pd.DataFrame:
        """Get donor metadata DataFrame"""
        if self._donor_df is None:
            self._load_donor_metadata()
        return self._donor_df
    
    @property
    def biosample_df(self) -> pd.DataFrame:
        """Get biosample metadata DataFrame"""
        if self._biosample_df is None:
            self._load_biosample_metadata()
        return self._biosample_df
    
    @property
    def traits_df(self) -> pd.DataFrame:
        """Get traits DataFrame"""
        if self._traits_df is None:
            self._load_traits()
        return self._traits_df
    
    @property
    def timeseries(self) -> Dict[str, pd.DataFrame]:
        """Get time-series data dictionary"""
        if not self._timeseries:
            self._load_timeseries()
        return self._timeseries
    
    @property
    def merged_df(self) -> pd.DataFrame:
        """Get merged donor + traits DataFrame"""
        if self._merged_df is None:
            self._create_merged_dataframe()
        return self._merged_df
    
    def get_timeseries_for_donors(
        self, 
        donor_rrids: List[str], 
        timeseries_type: str = 'ins_ieq'
    ) -> pd.DataFrame:
        """Get time-series data for specific donors
        
        Args:
            donor_rrids: List of donor RRIDs (e.g., ['RRID:SAMN08769199'])
            timeseries_type: Type of time-series data ('ins_ieq', 'ins_content', 'gcg_ieq', 'gcg_content')
        
        Returns:
            DataFrame with 'time' column and one column per donor
        """
        if timeseries_type not in self.timeseries:
            raise ValueError(f"Unknown timeseries type: {timeseries_type}")
        
        ts_df = self.timeseries[timeseries_type]
        
        # Filter columns to requested donors
        available_donors = [d for d in donor_rrids if d in ts_df.columns]
        
        if not available_donors:
            return pd.DataFrame({'time': ts_df['time']})
        
        return ts_df[['time'] + available_donors]
    
    def get_categorical_options(self, column: str) -> List[str]:
        """Get unique values for a categorical column"""
        if column in self.merged_df.columns:
            values = self.merged_df[column].dropna().unique().tolist()
            return sorted([str(v) for v in values])
        return []
    
    def get_numerical_range(self, column: str) -> tuple:
        """Get min and max values for a numerical column"""
        if column in self.merged_df.columns:
            col = self.merged_df[column]
            return (float(col.min()), float(col.max()))
        return (0.0, 0.0)
    
    def get_trait_columns(self) -> List[str]:
        """Get list of trait column names"""
        if self._traits_df is None:
            return []
        return [c for c in self._traits_df.columns if c not in ['RRID', 'HPAP ID']]
    
    def get_donor_metadata_columns(self) -> Dict[str, str]:
        """Get donor metadata columns with their types (categorical/numerical)"""
        if self._donor_df is None:
            return {}
        
        result = {}
        for col in self._donor_df.columns:
            if col in ['Accession', 'Center Donor ID', 'RRID']:
                continue  # Skip ID columns
            
            if self._donor_df[col].dtype in ['float64', 'int64']:
                result[col] = 'numerical'
            else:
                result[col] = 'categorical'
        
        return result
    
    def reload(self) -> None:
        """Reload all data from files"""
        self._donor_df = None
        self._biosample_df = None
        self._traits_df = None
        self._timeseries = {}
        self._merged_df = None
        self.load_all()


# Global instance
data_loader = DataLoader()
