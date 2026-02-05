"""Configuration settings for the PanKbase API"""
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # API settings
    api_title: str = "PanKbase Functional Data API"
    api_description: str = "API for querying and analyzing human pancreas perifusion data"
    api_version: str = "1.0.0"
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    
    # Data paths
    base_path: Path = Path(__file__).parent.parent / "data"
    
    @property
    def donor_metadata_path(self) -> Path:
        return self.base_path / "donor_metadata" / "pankbase_human_donor.txt"
    
    @property
    def biosample_metadata_path(self) -> Path:
        return self.base_path / "biosample_metadata" / "biosamples.2_2025-11-06.txt"
    
    @property
    def traits_path(self) -> Path:
        return self.base_path / "functional_data" / "HIPP_all_traits.csv"
    
    @property
    def timeseries_paths(self) -> dict:
        return {
            "ins_ieq": self.base_path / "functional_data" / "HIPP_ins_ieq.csv",
            "ins_content": self.base_path / "functional_data" / "HIPP_ins_content.csv",
            "gcg_ieq": self.base_path / "functional_data" / "HIPP_gcg_ieq.csv",
            "gcg_content": self.base_path / "functional_data" / "HIPP_gcg_content.csv",
        }
    
    class Config:
        env_prefix = "PANKBASE_"


settings = Settings()
