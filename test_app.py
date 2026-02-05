"""
Streamlit test application for PanKbase Functional Data API

Run with: streamlit run test_app.py

This app provides a UI for testing the API endpoints locally.
"""
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any, List
import json

# API base URL
API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="PanKbase Functional Data Portal",
    page_icon="🧬",
    layout="wide"
)

st.title("🧬 PanKbase Functional Data Portal")
st.markdown("Test interface for the functional perifusion data API")


def check_api_health():
    """Check if API is running"""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


# Check API status
api_healthy = check_api_health()
if not api_healthy:
    st.error("⚠️ API is not running. Please start the API server first:")
    st.code("uvicorn app.main:app --reload", language="bash")
    st.stop()

st.success("✅ API is running")

# Sidebar for navigation
page = st.sidebar.selectbox(
    "Select Page",
    ["Data Explorer", "Time-Series Visualization", "Association Analysis", "Integration Testing"]
)


# ============================================================================
# Helper Functions
# ============================================================================

@st.cache_data(ttl=60)
def get_filter_metadata():
    """Fetch filter metadata from API"""
    response = requests.get(f"{API_URL}/api/filter/metadata")
    if response.status_code == 200:
        return response.json()
    return None


@st.cache_data(ttl=60)
def get_analysis_variables():
    """Fetch available analysis variables"""
    response = requests.get(f"{API_URL}/api/analysis/variables")
    if response.status_code == 200:
        return response.json()
    return None


def build_filter_request(filters: Dict[str, Any]) -> Dict[str, Any]:
    """Build filter request from UI inputs"""
    request = {}
    
    for key, value in filters.items():
        if value is None:
            continue
        if isinstance(value, list) and len(value) == 0:
            continue
        if isinstance(value, dict):
            if value.get('min_value') is None and value.get('max_value') is None:
                continue
        request[key] = value
    
    return request


# ============================================================================
# Page: Data Explorer
# ============================================================================

if page == "Data Explorer":
    st.header("📊 Data Explorer")
    st.markdown("Filter and explore donor data")
    
    # Get filter metadata
    metadata = get_filter_metadata()
    
    if not metadata:
        st.error("Failed to load filter metadata")
        st.stop()
    
    # Display statistics
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Donors", metadata['total_donors'])
    with col2:
        st.metric("Donors with Functional Data", metadata['donors_with_functional_data'])
    
    # Filter controls
    st.subheader("Filters")
    
    filters = {}
    
    # Categorical filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if 'gender' in metadata['categorical_filters']:
            filters['gender'] = st.multiselect(
                "Gender",
                metadata['categorical_filters']['gender']
            )
        
        if 'collections' in metadata['categorical_filters']:
            filters['collections'] = st.multiselect(
                "Collection Center",
                metadata['categorical_filters']['collections']
            )
    
    with col2:
        if 'diabetes_status' in metadata['categorical_filters']:
            filters['diabetes_status'] = st.multiselect(
                "Diabetes Status",
                metadata['categorical_filters']['diabetes_status']
            )
        
        if 'ethnicities' in metadata['categorical_filters']:
            filters['ethnicities'] = st.multiselect(
                "Ethnicity",
                metadata['categorical_filters']['ethnicities'][:20]  # Limit options
            )
    
    with col3:
        if 'cause_of_death' in metadata['categorical_filters']:
            filters['cause_of_death'] = st.multiselect(
                "Cause of Death",
                metadata['categorical_filters']['cause_of_death'][:20]
            )
    
    # Numerical filters
    st.subheader("Numerical Filters")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if 'age_range' in metadata['numerical_filters']:
            age_range = metadata['numerical_filters']['age_range']
            age_min, age_max = st.slider(
                "Age Range (years)",
                min_value=int(age_range['min']),
                max_value=int(age_range['max']),
                value=(int(age_range['min']), int(age_range['max']))
            )
            if age_min != age_range['min'] or age_max != age_range['max']:
                filters['age_range'] = {'min_value': age_min, 'max_value': age_max}
    
    with col2:
        if 'bmi_range' in metadata['numerical_filters']:
            bmi_range = metadata['numerical_filters']['bmi_range']
            bmi_min, bmi_max = st.slider(
                "BMI Range",
                min_value=float(bmi_range['min']),
                max_value=float(bmi_range['max']),
                value=(float(bmi_range['min']), float(bmi_range['max']))
            )
            if bmi_min != bmi_range['min'] or bmi_max != bmi_range['max']:
                filters['bmi_range'] = {'min_value': bmi_min, 'max_value': bmi_max}
    
    with col3:
        if 'hba1c_range' in metadata['numerical_filters']:
            hba1c_range = metadata['numerical_filters']['hba1c_range']
            hba1c_min, hba1c_max = st.slider(
                "HbA1c Range (%)",
                min_value=float(hba1c_range['min']),
                max_value=float(hba1c_range['max']),
                value=(float(hba1c_range['min']), float(hba1c_range['max']))
            )
            if hba1c_min != hba1c_range['min'] or hba1c_max != hba1c_range['max']:
                filters['hba1c_range'] = {'min_value': hba1c_min, 'max_value': hba1c_max}
    
    # Apply filters button
    if st.button("Apply Filters", type="primary"):
        filter_request = build_filter_request(filters)
        
        with st.spinner("Fetching filtered data..."):
            response = requests.post(
                f"{API_URL}/api/filter/donors",
                json=filter_request
            )
        
        if response.status_code == 200:
            data = response.json()
            st.success(f"Found {data['donor_count']} donors matching criteria")
            
            # Display donor metadata
            if data['donor_metadata']:
                df = pd.DataFrame(data['donor_metadata'])
                st.dataframe(df, use_container_width=True)
                
                # Download button
                csv = df.to_csv(index=False)
                st.download_button(
                    "Download CSV",
                    csv,
                    "filtered_donors.csv",
                    "text/csv"
                )
        else:
            st.error(f"Error: {response.text}")


# ============================================================================
# Page: Time-Series Visualization
# ============================================================================

elif page == "Time-Series Visualization":
    st.header("📈 Time-Series Visualization")
    st.markdown("Visualize perifusion time-series data")
    
    # Get filter metadata
    metadata = get_filter_metadata()
    
    if not metadata:
        st.error("Failed to load filter metadata")
        st.stop()
    
    # Simplified filter controls
    col1, col2 = st.columns(2)
    
    filters = {}
    
    with col1:
        if 'diabetes_status' in metadata['categorical_filters']:
            filters['diabetes_status'] = st.multiselect(
                "Diabetes Status",
                metadata['categorical_filters']['diabetes_status'],
                default=[]
            )
        
        timeseries_type = st.selectbox(
            "Time-Series Type",
            ["ins_ieq", "ins_content", "gcg_ieq", "gcg_content"],
            format_func=lambda x: {
                "ins_ieq": "Insulin (IEQ normalized)",
                "ins_content": "Insulin (Content normalized)",
                "gcg_ieq": "Glucagon (IEQ normalized)",
                "gcg_content": "Glucagon (Content normalized)"
            }[x]
        )
    
    with col2:
        if 'collections' in metadata['categorical_filters']:
            filters['collections'] = st.multiselect(
                "Collection Center",
                metadata['categorical_filters']['collections'],
                default=[]
            )
        
        max_donors = st.slider("Max donors to display", 1, 50, 10)
    
    # Fetch time-series data
    if st.button("Load Time-Series", type="primary"):
        filter_request = build_filter_request(filters)
        
        with st.spinner("Fetching time-series data..."):
            response = requests.post(
                f"{API_URL}/api/filter/timeseries",
                json={
                    "filter_criteria": filter_request,
                    "timeseries_type": timeseries_type
                }
            )
        
        if response.status_code == 200:
            data = response.json()
            st.success(f"Loaded data for {data['donor_count']} donors")
            
            if data['data']:
                # Create plotly figure
                fig = go.Figure()
                
                donors = list(data['data'].keys())[:max_donors]
                
                for donor in donors:
                    fig.add_trace(go.Scatter(
                        x=data['time_points'],
                        y=data['data'][donor],
                        mode='lines',
                        name=donor[-8:],  # Shortened ID
                        opacity=0.7
                    ))
                
                fig.update_layout(
                    title=f"Time-Series: {timeseries_type}",
                    xaxis_title="Time (minutes)",
                    yaxis_title="Secretion Rate",
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Calculate and plot average
                st.subheader("Average Response")
                
                df = pd.DataFrame(data['data'])
                df['time'] = data['time_points']
                
                avg_values = df.drop('time', axis=1).mean(axis=1)
                std_values = df.drop('time', axis=1).std(axis=1)
                
                fig_avg = go.Figure()
                fig_avg.add_trace(go.Scatter(
                    x=data['time_points'],
                    y=avg_values,
                    mode='lines',
                    name='Mean',
                    line=dict(color='blue', width=2)
                ))
                fig_avg.add_trace(go.Scatter(
                    x=data['time_points'] + data['time_points'][::-1],
                    y=list(avg_values + std_values) + list(avg_values - std_values)[::-1],
                    fill='toself',
                    fillcolor='rgba(0, 0, 255, 0.2)',
                    line=dict(color='rgba(255,255,255,0)'),
                    name='±1 SD'
                ))
                
                fig_avg.update_layout(
                    title="Average Response ± SD",
                    xaxis_title="Time (minutes)",
                    yaxis_title="Secretion Rate"
                )
                
                st.plotly_chart(fig_avg, use_container_width=True)
        else:
            st.error(f"Error: {response.text}")


# ============================================================================
# Page: Association Analysis
# ============================================================================

elif page == "Association Analysis":
    st.header("🔬 Association Analysis")
    st.markdown("Analyze associations between traits and metadata variables")
    
    # Get available variables
    variables = get_analysis_variables()
    
    if not variables:
        st.error("Failed to load analysis variables")
        st.stop()
    
    # Extract variable names by category
    donor_vars = [v['name'] for v in variables['donor_variables']]
    trait_vars = [v['name'] for v in variables['trait_variables']]
    
    # Analysis settings
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Variables of Interest")
        selected_vars = st.multiselect(
            "Select metadata variables",
            donor_vars,
            default=['Age (years)', 'BMI'] if 'Age (years)' in donor_vars else donor_vars[:2]
        )
        
        control_vars = st.multiselect(
            "Control variables",
            [v for v in donor_vars if v not in selected_vars],
            default=[]
        )
    
    with col2:
        st.subheader("Traits to Analyze")
        
        # Group traits
        ins_ieq_traits = [t for t in trait_vars if 'INS-IEQ' in t]
        
        trait_options = st.radio(
            "Select traits",
            ["All traits", "INS-IEQ traits only", "Custom selection"]
        )
        
        if trait_options == "Custom selection":
            selected_traits = st.multiselect(
                "Select specific traits",
                trait_vars,
                default=ins_ieq_traits[:3]
            )
        elif trait_options == "INS-IEQ traits only":
            selected_traits = ins_ieq_traits
        else:
            selected_traits = None  # All traits
    
    analysis_method = st.selectbox(
        "Analysis Method",
        ["linear_regression", "correlation", "anova"],
        format_func=lambda x: {
            "linear_regression": "Linear Regression",
            "correlation": "Pearson Correlation",
            "anova": "One-way ANOVA"
        }[x]
    )
    
    # Run analysis
    if st.button("Run Analysis", type="primary"):
        if not selected_vars:
            st.warning("Please select at least one variable of interest")
            st.stop()
        
        request = {
            "filter_criteria": {},
            "variables_of_interest": selected_vars,
            "control_variables": control_vars,
            "traits": selected_traits,
            "analysis_method": analysis_method
        }
        
        with st.spinner("Running analysis..."):
            response = requests.post(
                f"{API_URL}/api/analysis/association",
                json=request
            )
        
        if response.status_code == 200:
            data = response.json()
            
            st.success(f"Analysis complete! {len(data['results'])} associations tested")
            st.metric("Total Samples", data['n_total_samples'])
            
            if data['results']:
                # Convert to DataFrame
                results_df = pd.DataFrame(data['results'])
                
                # Display results table
                st.subheader("Results")
                st.dataframe(
                    results_df[['trait', 'variable', 'coefficient', 'p_value', 'r_squared', 'n_samples']],
                    use_container_width=True
                )
                
                # Significance threshold
                significance_level = st.slider("Significance threshold (p-value)", 0.001, 0.1, 0.05)
                
                significant_results = results_df[results_df['p_value'] < significance_level]
                
                if len(significant_results) > 0:
                    st.subheader(f"Significant Results (p < {significance_level})")
                    
                    # Heatmap of p-values
                    pivot = results_df.pivot(index='trait', columns='variable', values='p_value')
                    
                    fig = px.imshow(
                        -np.log10(pivot.values),
                        x=pivot.columns,
                        y=pivot.index,
                        labels=dict(color="-log10(p-value)"),
                        aspect="auto"
                    )
                    fig.update_layout(title="Association Significance (-log10 p-value)")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No significant associations found at the selected threshold")
                
                # Download results
                csv = results_df.to_csv(index=False)
                st.download_button(
                    "Download Results CSV",
                    csv,
                    "association_results.csv",
                    "text/csv"
                )
        else:
            st.error(f"Error: {response.text}")


# ============================================================================
# Page: Integration Testing
# ============================================================================

elif page == "Integration Testing":
    st.header("🔗 Integration Testing")
    st.markdown("Test external data integration API")
    
    st.info("""
    This page demonstrates how external data (e.g., gene expression) can be 
    integrated with the functional data for joint analysis.
    """)
    
    # Get donors for integration
    response = requests.get(f"{API_URL}/api/integration/donors")
    if response.status_code == 200:
        donor_data = response.json()
        st.metric("Available Donors for Integration", donor_data['count'])
    
    st.subheader("Test External Data Integration")
    
    # Sample external data input
    st.markdown("### Sample External Data (JSON format)")
    
    # Get some real donor RRIDs
    sample_rrids = donor_data['donor_rrids'][:5] if response.status_code == 200 else []
    
    default_data = {}
    for i, rrid in enumerate(sample_rrids[:3]):
        default_data[rrid] = {
            "GCK_expression": round(5.0 + i * 0.5, 2),
            "INS_expression": round(8.0 + i * 0.3, 2),
            "PDX1_expression": round(3.0 + i * 0.2, 2)
        }
    
    external_data_str = st.text_area(
        "External Data (JSON)",
        value=json.dumps(default_data, indent=2),
        height=200
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        external_vars = st.multiselect(
            "Variables to Analyze",
            ["GCK_expression", "INS_expression", "PDX1_expression"],
            default=["GCK_expression"]
        )
    
    with col2:
        control_vars = st.multiselect(
            "Control Variables (from metadata)",
            ["Age (years)", "Gender", "BMI"],
            default=[]
        )
    
    # Validate data
    if st.button("Validate External Data"):
        try:
            external_data = json.loads(external_data_str)
            
            response = requests.post(
                f"{API_URL}/api/integration/validate",
                json=external_data
            )
            
            if response.status_code == 200:
                validation = response.json()
                
                if validation['valid']:
                    st.success("✅ External data is valid!")
                else:
                    st.warning("⚠️ External data has issues")
                
                st.json(validation['statistics'])
                
                if validation.get('unmatched_rrids'):
                    st.warning(f"Unmatched RRIDs: {validation['unmatched_rrids']}")
        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON: {e}")
    
    # Run integration analysis
    if st.button("Run Integration Analysis", type="primary"):
        try:
            external_data = json.loads(external_data_str)
            
            request = {
                "filter_criteria": {},
                "external_data": external_data,
                "variables_of_interest": external_vars,
                "control_variables": control_vars,
                "analysis_method": "linear_regression"
            }
            
            with st.spinner("Running integration analysis..."):
                response = requests.post(
                    f"{API_URL}/api/integration/analyze",
                    json=request
                )
            
            if response.status_code == 200:
                data = response.json()
                
                st.success(f"Analysis complete! {len(data['results'])} associations tested")
                st.metric("Samples with External Data", data['n_total_samples'])
                
                if data['results']:
                    results_df = pd.DataFrame(data['results'])
                    st.dataframe(results_df, use_container_width=True)
                else:
                    st.info("No results - check that external data matches available donors")
            else:
                st.error(f"Error: {response.text}")
        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON: {e}")


# Import numpy for the association analysis page
import numpy as np
