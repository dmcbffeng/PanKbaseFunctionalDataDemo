# PanKbase Functional Data API

A Python FastAPI backend for the PanKbase functional perifusion data portal, supporting data filtering, trait analysis, and integration with external data sources.

## Features

1. **Data Filtering**: Filter donors by metadata (categorical and numerical) and retrieve time-series data and derived traits
2. **Association Analysis**: Analyze associations between traits and variables of interest with support for control variables
3. **External Integration**: API for integrating external data sources (e.g., gene expression) with functional data

## Project Structure

```
PanKbase_API/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI entry point
│   ├── config.py               # Configuration settings
│   ├── models/
│   │   ├── schemas.py          # Pydantic request/response models
│   │   └── enums.py            # Categorical field enums
│   ├── services/
│   │   ├── data_loader.py      # Load and cache data
│   │   ├── filter_service.py   # Filter logic
│   │   └── analysis_service.py # Statistical analysis
│   ├── routers/
│   │   ├── filter.py           # /api/filter endpoints
│   │   ├── analysis.py         # /api/analysis endpoints
│   │   └── integration.py      # /api/integration endpoints
│   └── utils/
│       └── statistics.py       # Statistical helpers
├── data/                       # Data folder (donor, biosample, functional data)
├── test_app.py                 # Streamlit test application
├── requirements.txt            # Python dependencies
└── README.md
```

## Installation

1. Create a virtual environment (Only need to do this once):
```bash
python -m venv venv 
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the API

Start the FastAPI server:

```bash
source venv/bin/activate
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

- **API Documentation (Swagger UI)**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## Testing with Streamlit

A Streamlit test application is provided for interactive testing (Please run this in another command line window):

```bash
source venv/bin/activate
# Make sure the API server is running first in the first command line window
streamlit run test_app.py
```

**This website takes ~1 min to load everything. Please wait patiently.**

This provides a UI for:
- Data exploration with filters
- Time-series visualization
- Association analysis
- Integration testing

## API Endpoints

### Filter Endpoints (`/api/filter`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/filter/metadata` | GET | Get available filter options and ranges |
| `/api/filter/donors` | POST | Filter donors by metadata criteria |
| `/api/filter/timeseries` | POST | Get time-series data for filtered donors |
| `/api/filter/traits` | POST | Get trait data for filtered donors |
| `/api/filter/download` | POST | Download filtered data as CSV/JSON |

### Analysis Endpoints (`/api/analysis`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/analysis/variables` | GET | Get available variables for analysis |
| `/api/analysis/association` | POST | Run association analysis |
| `/api/analysis/methods` | GET | Get available analysis methods |
| `/api/analysis/traits` | GET | Get list of available traits |

### Integration Endpoints (`/api/integration`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/integration/sources` | GET | List registered external data sources |
| `/api/integration/sources/register` | POST | Register external data source |
| `/api/integration/analyze` | POST | Run analysis with external data |
| `/api/integration/donors` | GET | Get donors available for integration |
| `/api/integration/validate` | POST | Validate external data format |

## Example Usage

### Filter Donors

```python
import requests

response = requests.post(
    "http://localhost:8000/api/filter/donors",
    json={
        "gender": ["male", "female"],
        "collections": ["HPAP"],
        "diabetes_status": ["control without diabetes", "type 1 diabetes"],
        "age_range": {"min_value": 18, "max_value": 65}
    }
)
donors = response.json()
print(f"Found {donors['donor_count']} donors")
```

### Get Time-Series Data

```python
response = requests.post(
    "http://localhost:8000/api/filter/timeseries",
    json={
        "filter_criteria": {"collections": ["HPAP"]},
        "timeseries_type": "ins_ieq"
    }
)
data = response.json()
# data['time_points'] - list of time points in minutes
# data['data'] - dict mapping donor RRID to values
```

### Run Association Analysis

```python
response = requests.post(
    "http://localhost:8000/api/analysis/association",
    json={
        "filter_criteria": {},
        "variables_of_interest": ["Age (years)", "BMI"],
        "control_variables": ["Gender"],
        "traits": ["INS-IEQ Basal Secretion", "INS-IEQ G 16.7 AUC"],
        "analysis_method": "linear_regression"
    }
)
results = response.json()
# results['results'] - list of association results with coefficients, p-values, etc.
```

### Integration with External Data

```python
response = requests.post(
    "http://localhost:8000/api/integration/analyze",
    json={
        "filter_criteria": {"collections": ["HPAP"]},
        "external_data": {
            "RRID:SAMN08769199": {"GCK_expression": 5.2, "INS_expression": 8.1},
            "RRID:SAMN08769198": {"GCK_expression": 4.8, "INS_expression": 7.5}
        },
        "variables_of_interest": ["GCK_expression", "INS_expression"],
        "control_variables": ["Age (years)", "Gender"],
        "analysis_method": "linear_regression"
    }
)
```

## Data Sources

The API uses data from:
- **Donor Metadata**: `data/donor_metadata/pankbase_human_donor.txt`
- **Biosample Metadata**: `data/biosample_metadata/biosamples.2_2025-11-06.txt`
- **Functional Traits**: `data/functional_data/HIPP_all_traits.csv`
- **Time-Series Data**: `data/functional_data/HIPP_*.csv`

## Configuration

Configuration is managed through environment variables (prefix: `PANKBASE_`):

- `PANKBASE_HOST`: API host (default: `0.0.0.0`)
- `PANKBASE_PORT`: API port (default: `8000`)
- `PANKBASE_DEBUG`: Debug mode (default: `True`)

## Development

### Adding New Filters

1. Add the filter field to `FilterRequest` in `app/models/schemas.py`
2. Add the column mapping in `FilterService._apply_*_filters()` in `app/services/filter_service.py`
3. Update the metadata response in `FilterService.get_filter_metadata()`

### Adding New Analysis Methods

1. Add the method to `AnalysisMethod` enum in `app/models/enums.py`
2. Implement the analysis in `AnalysisService._analyze_association()` in `app/services/analysis_service.py`
3. Add documentation in `app/routers/analysis.py`

## License

[Add license information]
