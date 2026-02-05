"""Analysis service for statistical analysis of trait associations"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from scipy import stats
import statsmodels.api as sm
from statsmodels.formula.api import ols

from app.models.schemas import (
    FilterRequest, 
    AssociationRequest, 
    AssociationResult,
    VariableInfo,
    ExternalDataRequest,
)
from app.models.enums import AnalysisMethod, VariableType
from app.services.filter_service import filter_service
from app.services.data_loader import data_loader


class AnalysisService:
    """Service for statistical analysis of trait-variable associations"""
    
    def __init__(self):
        self.data_loader = data_loader
        self.filter_service = filter_service
    
    def get_available_variables(self) -> Dict[str, List[VariableInfo]]:
        """Get all available variables for analysis"""
        donor_vars = self._get_donor_variables()
        biosample_vars = self._get_biosample_variables()
        trait_vars = self._get_trait_variables()
        
        return {
            'donor_variables': donor_vars,
            'biosample_variables': biosample_vars,
            'trait_variables': trait_vars
        }
    
    def _get_donor_variables(self) -> List[VariableInfo]:
        """Get variable info for donor metadata"""
        df = self.data_loader.donor_df
        variables = []
        
        # Skip ID columns
        skip_cols = ['Accession', 'Center Donor ID', 'RRID']
        
        for col in df.columns:
            if col in skip_cols:
                continue
            
            var_type = self._infer_variable_type(df[col])
            var_info = VariableInfo(
                name=col,
                type=var_type,
                source='donor',
                description=None
            )
            
            if var_type == VariableType.CATEGORICAL:
                values = df[col].dropna().unique().tolist()
                var_info.unique_values = sorted([str(v) for v in values if v])[:50]
            elif var_type == VariableType.NUMERICAL:
                col_numeric = pd.to_numeric(df[col], errors='coerce')
                var_info.range = {
                    'min': float(col_numeric.min()) if not col_numeric.isna().all() else None,
                    'max': float(col_numeric.max()) if not col_numeric.isna().all() else None
                }
            
            variables.append(var_info)
        
        return variables
    
    def _get_biosample_variables(self) -> List[VariableInfo]:
        """Get variable info for biosample metadata"""
        df = self.data_loader.biosample_df
        variables = []
        
        # Skip ID columns
        skip_cols = ['Accession', 'Donors']
        
        for col in df.columns:
            if col in skip_cols:
                continue
            
            var_type = self._infer_variable_type(df[col])
            var_info = VariableInfo(
                name=f"biosample_{col}",
                type=var_type,
                source='biosample',
                description=None
            )
            
            if var_type == VariableType.CATEGORICAL:
                values = df[col].dropna().unique().tolist()
                var_info.unique_values = sorted([str(v) for v in values if v])[:50]
            elif var_type == VariableType.NUMERICAL:
                col_numeric = pd.to_numeric(df[col], errors='coerce')
                var_info.range = {
                    'min': float(col_numeric.min()) if not col_numeric.isna().all() else None,
                    'max': float(col_numeric.max()) if not col_numeric.isna().all() else None
                }
            
            variables.append(var_info)
        
        return variables
    
    def _get_trait_variables(self) -> List[VariableInfo]:
        """Get variable info for traits"""
        trait_cols = self.data_loader.get_trait_columns()
        df = self.data_loader.traits_df
        variables = []
        
        for col in trait_cols:
            col_data = pd.to_numeric(df[col], errors='coerce')
            var_info = VariableInfo(
                name=col,
                type=VariableType.NUMERICAL,
                source='trait',
                description=self._get_trait_description(col),
                range={
                    'min': float(col_data.min()) if not col_data.isna().all() else None,
                    'max': float(col_data.max()) if not col_data.isna().all() else None
                }
            )
            variables.append(var_info)
        
        return variables
    
    def _get_trait_description(self, trait_name: str) -> str:
        """Get description for a trait based on its name"""
        descriptions = {
            'Basal Secretion': 'Average secretion rate during baseline period',
            'AUC': 'Area under the curve during stimulation',
            'SI': 'Stimulation index (fold change from basal)',
            'II': 'Inhibition index',
            'phase 1': 'First phase secretion response',
            'phase 2': 'Second phase secretion response',
        }
        
        for key, desc in descriptions.items():
            if key in trait_name:
                return desc
        return ''
    
    def _infer_variable_type(self, series: pd.Series) -> VariableType:
        """Infer the variable type from a pandas Series"""
        if series.dtype == bool or set(series.dropna().unique()).issubset({True, False}):
            return VariableType.BOOLEAN
        
        # Try to convert to numeric
        numeric = pd.to_numeric(series, errors='coerce')
        non_null_count = series.dropna().shape[0]
        numeric_count = numeric.dropna().shape[0]
        
        # If most values are numeric, treat as numerical
        if non_null_count > 0 and numeric_count / non_null_count > 0.8:
            return VariableType.NUMERICAL
        
        return VariableType.CATEGORICAL
    
    def run_association_analysis(
        self, request: AssociationRequest
    ) -> Tuple[List[AssociationResult], Dict[str, Any]]:
        """
        Run association analysis between traits and variables of interest.
        
        Args:
            request: Association analysis request
            
        Returns:
            Tuple of (results list, filter summary dict)
        """
        # Apply filters to get analysis dataset
        filtered_df = self.filter_service.apply_filters(request.filter_criteria)
        
        if len(filtered_df) == 0:
            return [], {'n_samples': 0, 'message': 'No samples match filter criteria'}
        
        # Determine which traits to analyze
        trait_cols = request.traits or self.data_loader.get_trait_columns()
        available_traits = [t for t in trait_cols if t in filtered_df.columns]
        
        results = []
        
        for variable in request.variables_of_interest:
            if variable not in filtered_df.columns:
                continue
            
            for trait in available_traits:
                result = self._analyze_association(
                    df=filtered_df,
                    trait=trait,
                    variable=variable,
                    control_variables=request.control_variables,
                    method=request.analysis_method
                )
                if result:
                    results.append(result)
        
        filter_summary = {
            'n_samples': len(filtered_df),
            'traits_analyzed': len(available_traits),
            'variables_analyzed': len(request.variables_of_interest)
        }
        
        return results, filter_summary
    
    def _analyze_association(
        self,
        df: pd.DataFrame,
        trait: str,
        variable: str,
        control_variables: List[str],
        method: AnalysisMethod
    ) -> Optional[AssociationResult]:
        """Run single association analysis"""
        
        # Prepare data
        analysis_cols = [trait, variable] + control_variables
        available_cols = [c for c in analysis_cols if c in df.columns]
        
        if trait not in df.columns or variable not in df.columns:
            return None
        
        analysis_df = df[available_cols].dropna()
        
        if len(analysis_df) < 10:  # Minimum sample size
            return None
        
        var_type = self._infer_variable_type(df[variable])
        
        try:
            if method == AnalysisMethod.LINEAR_REGRESSION:
                return self._linear_regression(
                    analysis_df, trait, variable, control_variables, var_type
                )
            elif method == AnalysisMethod.CORRELATION:
                return self._correlation(analysis_df, trait, variable)
            elif method == AnalysisMethod.ANOVA:
                return self._anova(analysis_df, trait, variable)
            elif method == AnalysisMethod.KRUSKAL_WALLIS:
                return self._kruskal_wallis(analysis_df, trait, variable)
            else:
                return self._linear_regression(
                    analysis_df, trait, variable, control_variables, var_type
                )
        except Exception as e:
            print(f"Error in analysis {trait} ~ {variable}: {e}")
            return None
    
    def _linear_regression(
        self,
        df: pd.DataFrame,
        trait: str,
        variable: str,
        control_variables: List[str],
        var_type: VariableType
    ) -> Optional[AssociationResult]:
        """Run linear regression analysis"""
        
        # Prepare outcome
        y = pd.to_numeric(df[trait], errors='coerce')
        
        # Prepare predictors
        X_cols = [variable] + [c for c in control_variables if c in df.columns]
        X = df[X_cols].copy()
        
        # Handle categorical variables
        for col in X.columns:
            col_type = self._infer_variable_type(df[col])
            if col_type == VariableType.CATEGORICAL:
                X = pd.get_dummies(X, columns=[col], drop_first=True)
            else:
                X[col] = pd.to_numeric(X[col], errors='coerce')
        
        # Drop rows with NaN
        valid_mask = ~(X.isna().any(axis=1) | y.isna())
        X = X[valid_mask]
        y = y[valid_mask]
        
        if len(y) < 10:
            return None
        
        # Add constant
        X = sm.add_constant(X)
        
        # Fit model
        model = sm.OLS(y, X).fit()
        
        # Get coefficient for main variable (first non-constant column)
        var_cols = [c for c in model.params.index if variable in c and c != 'const']
        if not var_cols:
            return None
        
        main_var = var_cols[0]
        
        return AssociationResult(
            trait=trait,
            variable=variable,
            coefficient=float(model.params[main_var]),
            std_error=float(model.bse[main_var]),
            p_value=float(model.pvalues[main_var]),
            ci_lower=float(model.conf_int().loc[main_var, 0]),
            ci_upper=float(model.conf_int().loc[main_var, 1]),
            r_squared=float(model.rsquared),
            n_samples=int(model.nobs),
            method='linear_regression'
        )
    
    def _correlation(
        self,
        df: pd.DataFrame,
        trait: str,
        variable: str
    ) -> Optional[AssociationResult]:
        """Run Pearson correlation analysis"""
        
        x = pd.to_numeric(df[variable], errors='coerce')
        y = pd.to_numeric(df[trait], errors='coerce')
        
        valid_mask = ~(x.isna() | y.isna())
        x = x[valid_mask]
        y = y[valid_mask]
        
        if len(x) < 10:
            return None
        
        r, p_value = stats.pearsonr(x, y)
        
        # Calculate confidence interval using Fisher transformation
        n = len(x)
        z = np.arctanh(r)
        se = 1 / np.sqrt(n - 3)
        ci_lower = np.tanh(z - 1.96 * se)
        ci_upper = np.tanh(z + 1.96 * se)
        
        return AssociationResult(
            trait=trait,
            variable=variable,
            coefficient=float(r),
            std_error=float(se),
            p_value=float(p_value),
            ci_lower=float(ci_lower),
            ci_upper=float(ci_upper),
            r_squared=float(r ** 2),
            n_samples=int(n),
            method='correlation'
        )
    
    def _anova(
        self,
        df: pd.DataFrame,
        trait: str,
        variable: str
    ) -> Optional[AssociationResult]:
        """Run one-way ANOVA"""
        
        y = pd.to_numeric(df[trait], errors='coerce')
        groups = df[variable].astype(str)
        
        # Group data
        group_data = []
        for group_name in groups.unique():
            if pd.isna(group_name) or group_name == 'nan':
                continue
            group_values = y[groups == group_name].dropna()
            if len(group_values) >= 2:
                group_data.append(group_values)
        
        if len(group_data) < 2:
            return None
        
        f_stat, p_value = stats.f_oneway(*group_data)
        
        # Calculate eta-squared
        total_n = sum(len(g) for g in group_data)
        
        return AssociationResult(
            trait=trait,
            variable=variable,
            coefficient=float(f_stat),
            std_error=None,
            p_value=float(p_value),
            ci_lower=None,
            ci_upper=None,
            r_squared=None,
            n_samples=int(total_n),
            method='anova'
        )
    
    def _kruskal_wallis(
        self,
        df: pd.DataFrame,
        trait: str,
        variable: str
    ) -> Optional[AssociationResult]:
        """Run Kruskal-Wallis H-test (non-parametric alternative to ANOVA)"""
        
        y = pd.to_numeric(df[trait], errors='coerce')
        groups = df[variable].astype(str)
        
        # Group data
        group_data = []
        for group_name in groups.unique():
            if pd.isna(group_name) or group_name == 'nan':
                continue
            group_values = y[groups == group_name].dropna()
            if len(group_values) >= 2:
                group_data.append(group_values)
        
        if len(group_data) < 2:
            return None
        
        h_stat, p_value = stats.kruskal(*group_data)
        total_n = sum(len(g) for g in group_data)
        
        return AssociationResult(
            trait=trait,
            variable=variable,
            coefficient=float(h_stat),
            std_error=None,
            p_value=float(p_value),
            ci_lower=None,
            ci_upper=None,
            r_squared=None,
            n_samples=int(total_n),
            method='kruskal_wallis'
        )
    
    def run_external_data_analysis(
        self, request: ExternalDataRequest
    ) -> Tuple[List[AssociationResult], Dict[str, Any]]:
        """
        Run association analysis with external data (e.g., gene expression).
        
        Args:
            request: External data analysis request
            
        Returns:
            Tuple of (results list, filter summary dict)
        """
        # Apply filters to get analysis dataset
        filtered_df = self.filter_service.apply_filters(request.filter_criteria)
        
        if len(filtered_df) == 0:
            return [], {'n_samples': 0, 'message': 'No samples match filter criteria'}
        
        # Add external data to dataframe
        if request.external_data:
            external_df = pd.DataFrame.from_dict(
                request.external_data, orient='index'
            )
            external_df.index.name = 'RRID'
            external_df = external_df.reset_index()
            
            # Merge with filtered data
            analysis_df = filtered_df.merge(external_df, on='RRID', how='inner')
        else:
            return [], {'n_samples': 0, 'message': 'No external data provided'}
        
        if len(analysis_df) == 0:
            return [], {'n_samples': 0, 'message': 'No matching samples with external data'}
        
        # Determine which traits to analyze
        trait_cols = request.traits or self.data_loader.get_trait_columns()
        available_traits = [t for t in trait_cols if t in analysis_df.columns]
        
        results = []
        
        for variable in request.variables_of_interest:
            if variable not in analysis_df.columns:
                continue
            
            for trait in available_traits:
                result = self._analyze_association(
                    df=analysis_df,
                    trait=trait,
                    variable=variable,
                    control_variables=request.control_variables,
                    method=request.analysis_method
                )
                if result:
                    results.append(result)
        
        filter_summary = {
            'n_samples': len(analysis_df),
            'traits_analyzed': len(available_traits),
            'variables_analyzed': len(request.variables_of_interest),
            'external_variables': list(request.external_data.keys()) if request.external_data else []
        }
        
        return results, filter_summary


# Global instance
analysis_service = AnalysisService()
