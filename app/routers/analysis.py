"""Analysis API endpoints"""
from fastapi import APIRouter, HTTPException
from typing import List

from app.models.schemas import (
    AssociationRequest,
    AssociationResponse,
    VariablesResponse,
    VariableInfo,
)
from app.models.enums import AnalysisMethod
from app.services.analysis_service import analysis_service

router = APIRouter(prefix="/api/analysis", tags=["Analysis"])


@router.get("/variables", response_model=VariablesResponse)
async def get_available_variables():
    """
    Get available variables for association analysis.
    
    Returns lists of donor metadata, biosample metadata, and trait variables
    that can be used in association analyses.
    """
    try:
        variables = analysis_service.get_available_variables()
        return VariablesResponse(**variables)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/association", response_model=AssociationResponse)
async def run_association_analysis(request: AssociationRequest):
    """
    Run association analysis between traits and variables of interest.
    
    Analyzes the association between functional traits and selected variables,
    optionally controlling for confounding variables. Supports multiple
    statistical methods including linear regression, correlation, and ANOVA.
    
    **Example use cases:**
    - Test association between age and insulin secretion traits
    - Compare trait values between diabetes status groups
    - Analyze BMI effects while controlling for age and sex
    """
    try:
        if not request.variables_of_interest:
            raise HTTPException(
                status_code=400, 
                detail="At least one variable of interest is required"
            )
        
        results, filter_summary = analysis_service.run_association_analysis(request)
        
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


@router.get("/methods")
async def get_analysis_methods():
    """
    Get available statistical analysis methods.
    
    Returns information about each supported analysis method
    and when to use them.
    """
    return {
        "methods": [
            {
                "value": AnalysisMethod.LINEAR_REGRESSION.value,
                "label": "Linear Regression",
                "description": "OLS regression for continuous outcomes. Supports control variables.",
                "use_when": "Variable of interest and outcome are continuous, or testing multiple predictors"
            },
            {
                "value": AnalysisMethod.CORRELATION.value,
                "label": "Pearson Correlation",
                "description": "Pearson correlation coefficient between two continuous variables.",
                "use_when": "Simple bivariate relationship between two continuous variables"
            },
            {
                "value": AnalysisMethod.ANOVA.value,
                "label": "One-way ANOVA",
                "description": "Compare means across categorical groups (parametric).",
                "use_when": "Variable of interest is categorical with 2+ groups, outcome is continuous and normally distributed"
            },
            {
                "value": AnalysisMethod.KRUSKAL_WALLIS.value,
                "label": "Kruskal-Wallis H-test",
                "description": "Non-parametric alternative to ANOVA.",
                "use_when": "Variable of interest is categorical, outcome may not be normally distributed"
            }
        ]
    }


@router.get("/traits")
async def get_available_traits():
    """
    Get list of available trait variables for analysis.
    
    Returns all functional traits that can be used as outcomes
    in association analyses.
    """
    try:
        variables = analysis_service.get_available_variables()
        traits = variables.get('trait_variables', [])
        
        # Group traits by category
        ins_ieq = [t for t in traits if 'INS-IEQ' in t.name]
        ins_content = [t for t in traits if 'INS-content' in t.name]
        gcg_ieq = [t for t in traits if 'GCG-IEQ' in t.name]
        gcg_content = [t for t in traits if 'GCG-content' in t.name]
        
        return {
            "categories": [
                {
                    "name": "Insulin (IEQ normalized)",
                    "description": "Insulin secretion traits normalized to islet equivalents",
                    "traits": [{"name": t.name, "range": t.range} for t in ins_ieq]
                },
                {
                    "name": "Insulin (Content normalized)",
                    "description": "Insulin secretion traits as percentage of total content",
                    "traits": [{"name": t.name, "range": t.range} for t in ins_content]
                },
                {
                    "name": "Glucagon (IEQ normalized)",
                    "description": "Glucagon secretion traits normalized to islet equivalents",
                    "traits": [{"name": t.name, "range": t.range} for t in gcg_ieq]
                },
                {
                    "name": "Glucagon (Content normalized)",
                    "description": "Glucagon secretion traits as percentage of total content",
                    "traits": [{"name": t.name, "range": t.range} for t in gcg_content]
                }
            ],
            "total_traits": len(traits)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
