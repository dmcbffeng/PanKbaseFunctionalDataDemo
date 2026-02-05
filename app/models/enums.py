"""Enums for categorical fields"""
from enum import Enum


class DiabetesStatus(str, Enum):
    """Diabetes status categories"""
    CONTROL = "control without diabetes"
    T1D = "type 1 diabetes"
    T2D = "type 2 diabetes"
    PREDIABETES = "prediabetes"
    GESTATIONAL = "gestational diabetes"
    OTHER = "other diabetes"


class Gender(str, Enum):
    """Gender categories"""
    MALE = "male"
    FEMALE = "female"


class Collection(str, Enum):
    """Data collection/center categories"""
    HPAP = "HPAP"
    NPOD = "nPOD"
    IIDP = "IIDP"
    ADI = "ADI"
    PANCREATLAS = "Pancreatlas"


class TimeseriesType(str, Enum):
    """Types of time-series data"""
    INS_IEQ = "ins_ieq"
    INS_CONTENT = "ins_content"
    GCG_IEQ = "gcg_ieq"
    GCG_CONTENT = "gcg_content"


class AnalysisMethod(str, Enum):
    """Statistical analysis methods"""
    LINEAR_REGRESSION = "linear_regression"
    LOGISTIC_REGRESSION = "logistic_regression"
    CORRELATION = "correlation"
    ANOVA = "anova"
    KRUSKAL_WALLIS = "kruskal_wallis"


class VariableType(str, Enum):
    """Types of variables"""
    CATEGORICAL = "categorical"
    NUMERICAL = "numerical"
    BOOLEAN = "boolean"
