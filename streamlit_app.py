import streamlit as st
import requests
import json
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="DN Log Analyser",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        background-color: #000000;
        color: #FFFFFF;
        padding: 1rem !important;
    }
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
    }
    [data-testid="stSidebar"] {
        background-color: #000000;
    }
    .stMarkdown, p, span, div {
        color: #FFFFFF !important;
    }
    h1 {
        color: #FFFFFF !important;
        font-size: 1.8rem !important;
        margin-bottom: 0.5rem !important;
    }
    h2, h3, h4, h5, h6 {
        color: #FFFFFF !important;
        font-size: 1rem !important;
        margin: 0.5rem 0 !important;
    }
    [data-testid="stFileUploader"] {
        background-color: #1a1a1a;
        border: 1px solid #333333;
        border-radius: 6px;
        padding: 0.75rem;
    }
    .stSelectbox {
        background-color: #1a1a1a;
    }
    .stSelectbox > div > div {
        background-color: #1a1a1a;
        color: #FFFFFF;
        border: 1px solid #333333;
    }
    .stButton > button {
        background-color: #2563EB;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 6px;
        font-weight: 600;
    }
    .stButton > button:hover {
        background-color: #1d4ed8;
    }
    .stCheckbox {
        background-color: #1a1a1a;
        padding: 0.75rem;
        border-radius: 6px;
        border: 1px solid #333333;
        margin: 0.25rem 0;
    }
    .stCheckbox > label {
        color: #FFFFFF !important;
        font-weight: 500;
    }
    .stRadio > div {
        background-color: #1a1a1a;
        padding: 0.5rem;
        border-radius: 6px;
        border: 1px solid #333333;
    }
    .stRadio label {
        color: #FFFFFF !important;
    }
    .streamlit-expanderHeader {
        background-color: #1a1a1a !important;
        border: 1px solid #333333 !important;
    }
    .element-container {
        margin-bottom: 0.5rem !important;
    }
    .caption {
        color: #9CA3AF !important;
        font-size: 0.75rem !important;
    }
    .info-path {
        background-color: #0a0a0a;
        padding: 0.5rem;
        border-radius: 4px;
        border: 1px solid #333333;
        font-family: monospace;
        color: #9CA3AF !important;
        margin: 0.5rem 0;
        font-size: 0.8rem !important;
    }
    </style>
""", unsafe_allow_html=True)

# API Configuration
API_BASE_URL = "http://localhost:8000/api/v1"

# Initialize session state
if 'zip_processed' not in st.session_state:
    st.session_state.zip_processed = False
if 'file_types_loaded' not in st.session_state:
    st.session_state.file_types_loaded = False
if 'available_types' not in st.session_state:
    st.session_state.available_types = []
if 'selected_file_types' not in st.session_state:
    st.session_state.selected_file_types = []

# ============================================
# FUNCTION IMPLEMENTATIONS
# ============================================

def render_transaction_stats():
    """Render Transaction Type Statistics functionality"""
    
    if st.button("📈 Generate Statistics", use_container_width=True):
        with st.spinner("Analyzing transactions..."):
            try:
                response = requests.get(f"{API_BASE_URL}/analyze-customer-journals")
                
                if response.status_code == 200:
                    analysis_data = response.json()
                    st.session_state['transaction_analysis'] = analysis_data
                    
                    # Display statistics
                    st.success("✅ Analysis complete!")
                    
                    # Summary metrics
                    st.markdown("#### 📊 Overview")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Transactions", analysis_data['total_transactions'])
                    with col2:
                        st.metric("Successful", analysis_data['successful'])
                    with col3:
                        st.metric("Unsuccessful", analysis_data['unsuccessful'])
                    with col4:
                        st.metric("Unknown", analysis_data['unknown'])
                    
                    st.markdown("---")
                    
                    # Transaction type breakdown - ENHANCED VERSION
                    st.markdown("#### 📋 Transaction Type Breakdown")
                    
                    transactions_df = pd.DataFrame(analysis_data['transactions'])
                    
                    # Calculate comprehensive statistics for each transaction type
                    type_stats_list = []
                    
                    for txn_type in transactions_df['Transaction Type'].unique():
                        # Filter transactions for this type
                        type_df = transactions_df[transactions_df['Transaction Type'] == txn_type]
                        
                        # Count by state
                        total_count = len(type_df)
                        successful_count = len(type_df[type_df['End State'] == 'Successful'])
                        unsuccessful_count = len(type_df[type_df['End State'] == 'Unsuccessful'])
                        unknown_count = len(type_df[type_df['End State'] == 'Unknown'])
                        
                        # Calculate success rate
                        success_rate = (successful_count / total_count * 100) if total_count > 0 else 0
                        
                        # Parse duration strings to seconds
                        durations = []
                        for duration_str in type_df['Duration']:
                            if isinstance(duration_str, str) and duration_str != 'N/A':
                                try:
                                    # Remove 's' suffix and convert to float
                                    duration_sec = float(duration_str.replace('s', ''))
                                    durations.append(duration_sec)
                                except ValueError:
                                    continue
                        
                        # Calculate duration statistics
                        if durations:
                            min_duration = min(durations)
                            max_duration = max(durations)
                            avg_duration = sum(durations) / len(durations)
                        else:
                            min_duration = None
                            max_duration = None
                            avg_duration = None
                        
                        # Add to results
                        type_stats_list.append({
                            'Transaction Type': txn_type,
                            'Total Count': total_count,
                            'Successful': successful_count,
                            'Unsuccessful': unsuccessful_count,
                            'Unknown': unknown_count,
                            'Min Duration (s)': f"{min_duration:.2f}" if min_duration is not None else 'N/A',
                            'Max Duration (s)': f"{max_duration:.2f}" if max_duration is not None else 'N/A',
                            'Avg Duration (s)': f"{avg_duration:.2f}" if avg_duration is not None else 'N/A',
                            'Success Rate (%)': f"{success_rate:.2f}"
                        })
                    
                    # Create DataFrame from results
                    type_stats = pd.DataFrame(type_stats_list)
                    
                    # Sort by total count descending
                    type_stats = type_stats.sort_values('Total Count', ascending=False)
                    
                    # Reset index to start from 1
                    type_stats.index = range(1, len(type_stats) + 1)
                    
                    # Display the enhanced table
                    st.dataframe(type_stats, use_container_width=True)
                    
                    # ============================================
                    # SUMMARY INSIGHTS
                    # ============================================
                    
                    # Filter out rows with N/A durations for insights
                    valid_duration_stats = type_stats[type_stats['Avg Duration (s)'] != 'N/A'].copy()
                    
                    if not valid_duration_stats.empty:
                        # Convert duration strings back to floats for comparison
                        valid_duration_stats['Avg Duration Float'] = valid_duration_stats['Avg Duration (s)'].astype(float)
                        
                        # Find fastest and slowest
                        fastest_idx = valid_duration_stats['Avg Duration Float'].idxmin()
                        slowest_idx = valid_duration_stats['Avg Duration Float'].idxmax()
                        
                        fastest_txn = valid_duration_stats.loc[fastest_idx, 'Transaction Type']
                        fastest_time = valid_duration_stats.loc[fastest_idx, 'Avg Duration (s)']
                        
                        slowest_txn = valid_duration_stats.loc[slowest_idx, 'Transaction Type']
                        slowest_time = valid_duration_stats.loc[slowest_idx, 'Avg Duration (s)']
                    else:
                        fastest_txn = "N/A"
                        fastest_time = "N/A"
                        slowest_txn = "N/A"
                        slowest_time = "N/A"
                    
                    # Calculate overall success rate
                    total_all = type_stats['Total Count'].sum()
                    successful_all = type_stats['Successful'].sum()
                    overall_success_rate = (successful_all / total_all * 100) if total_all > 0 else 0
                    
                    # Display insights in columns
                    insight_col1, insight_col2, insight_col3 = st.columns(3)
                    
                    with insight_col1:
                        st.metric(
                            label="⚡ Fastest Avg Transaction",
                            value=fastest_txn,
                            delta=f"{fastest_time}s" if fastest_time != "N/A" else None,
                            delta_color="normal"
                        )
                    
                    with insight_col2:
                        st.metric(
                            label="🐌 Slowest Avg Transaction",
                            value=slowest_txn,
                            delta=f"{slowest_time}s" if slowest_time != "N/A" else None,
                            delta_color="inverse"
                        )
                    
                    with insight_col3:
                        # Color code the success rate
                        if overall_success_rate >= 95:
                            success_color = "normal"
                        elif overall_success_rate >= 80:
                            success_color = "off"
                        else:
                            success_color = "inverse"
                        
                        st.metric(
                            label="✅ Overall Success Rate",
                            value=f"{overall_success_rate:.2f}%",
                            delta=f"{successful_all}/{total_all}",
                            delta_color=success_color
                        )
                    

                    # Add download button for CSV export
                    csv = type_stats.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Statistics as CSV",
                        data=csv,
                        file_name="transaction_statistics.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                    
                else:
                    st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
            
            except Exception as e:
                st.error(f"Error: {str(e)}")


def render_individual_transaction_analysis():
    """Render Individual Transaction Analysis functionality"""
    st.markdown("#### 🔍 Individual Transaction Analysis")
    
    # First, get transactions if not already loaded
    if 'transaction_analysis' not in st.session_state:
        if st.button("📥 Load Transactions", use_container_width=True):
            with st.spinner("Loading transactions..."):
                try:
                    response = requests.get(f"{API_BASE_URL}/analyze-customer-journals")
                    
                    if response.status_code == 200:
                        analysis_data = response.json()
                        st.session_state['transaction_analysis'] = analysis_data
                        st.success("✅ Transactions loaded!")
                        st.rerun()
                    else:
                        st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
                
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    else:
        # Show transaction selector
        analysis_data = st.session_state['transaction_analysis']
        transactions_df = pd.DataFrame(analysis_data['transactions'])
        
        st.markdown("**Select a transaction to analyze:**")
        
        # Create transaction selector
        transaction_options = [
            f"{row['Transaction ID']} - {row['Transaction Type']} ({row['End State']})"
            for _, row in transactions_df.iterrows()
        ]
        
        selected_txn_option = st.selectbox(
            "Transaction:",
            options=["-- Select a transaction --"] + transaction_options,
            key="selected_transaction"
        )
        
        if selected_txn_option != "-- Select a transaction --":
            # Extract transaction ID
            selected_txn_id = selected_txn_option.split(" - ")[0]
            
            # Find transaction data
            txn_data = transactions_df[transactions_df['Transaction ID'] == selected_txn_id].iloc[0]
            
            st.markdown("---")
            st.markdown(f"### 📝 Transaction: {selected_txn_id}")
            
            # Display details in columns
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**Type:** {txn_data['Transaction Type']}")
                st.write(f"**State:** {txn_data['End State']}")
            with col2:
                st.write(f"**Start Time:** {txn_data['Start Time']}")
                st.write(f"**End Time:** {txn_data['End Time']}")
            with col3:
                st.write(f"**Duration:** {txn_data['Duration']}")
                st.write(f"**Source:** {txn_data['Source_File']}")
            
            st.markdown("---")
            st.markdown("**Full Transaction Log:**")
            st.code(txn_data['Transaction Log'], language='log')


# ============================================
# MAIN UI STARTS HERE
# ============================================

# Header
st.title("📦 DN Log Analyser")

# Step 1: File Upload
uploaded_file = st.file_uploader("Select ZIP File", type=['zip'])

# Process uploaded file
if uploaded_file is not None and not st.session_state.zip_processed:
    with st.spinner("Processing ZIP file..."):
        try:
            # Prepare the file for upload
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/zip")}
            
            # Make API request
            response = requests.post(f"{API_BASE_URL}/process-zip", files=files)
            
            if response.status_code == 200:
                result = response.json()
                st.session_state.zip_processed = True
                st.session_state.processing_result = result
                
            else:
                error_detail = response.json().get('detail', 'Unknown error')
                st.error(f"Error: {error_detail}")
                
        except requests.exceptions.ConnectionError:
            st.error("❌ Connection Error: FastAPI server not running")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# Step 2: Show Functionality Selection (only if ZIP is processed)
if st.session_state.zip_processed:
    st.markdown("---")
    st.markdown("# 🎯 Select Analysis Function")
    
    # Define all available functionalities
    functionalities = {
        "transaction_stats": {
            "name": "📊 Transaction Type Statistics",
            "description": "View statistics for different transaction types",
            "status": "ready",
            "requires": ["customer_journals"]
        },
        "individual_transaction": {
            "name": "🔍 Individual Transaction Analysis",
            "description": "Analyze a specific transaction in detail",
            "status": "ready",
            "requires": ["customer_journals"]
        },
        "ui_flow_individual": {
            "name": "🖥️ UI Flow of Individual Transaction",
            "description": "Visualize UI flow for a specific transaction",
            "status": "construction",
            "requires": ["customer_journals", "ui_journals"]
        },
        "llm_feedback": {
            "name": "💬 LLM Response Feedback",
            "description": "Provide feedback on LLM analysis results",
            "status": "construction",
            "requires": ["customer_journals"]
        },
        "consolidated_flow": {
            "name": "🌐 Consolidated Transaction UI Flow and Analysis",
            "description": "View consolidated flow across multiple transactions",
            "status": "construction",
            "requires": ["customer_journals", "ui_journals"]
        },
        "transaction_comparison": {
            "name": "⚖️ Transaction Comparison Analysis",
            "description": "Compare two transactions side by side",
            "status": "construction",
            "requires": ["customer_journals", "ui_journals"]
        },
        "registry_single": {
            "name": "📝 Single View of Registry Files",
            "description": "View and analyze a single registry file",
            "status": "construction",
            "requires": ["registry_files"]
        },
        "registry_compare": {
            "name": "🔄 Compare Two Registry Files",
            "description": "Compare differences between two registry files",
            "status": "construction",
            "requires": ["registry_files"]
        }
    }
    
    # Get available file types from the processed result
    if 'processing_result' in st.session_state:
        available_file_types = []
        for category, data in st.session_state.processing_result['categories'].items():
            if data['count'] > 0:
                available_file_types.append(category)
        
        # Filter functionalities based on available file types
        available_functionalities = {}
        unavailable_functionalities = {}
        
        for func_id, func_data in functionalities.items():
            # Check if all required file types are available
            requirements_met = all(req in available_file_types for req in func_data['requires'])
            
            if requirements_met:
                available_functionalities[func_id] = func_data
            else:
                unavailable_functionalities[func_id] = func_data
        
        # Create dropdown options - cleaner without section headers
        dropdown_options = []

        # Add available functions directly
        for func_id, func_data in available_functionalities.items():
            status_icon = "✅" if func_data['status'] == 'ready' else "🚧"
            dropdown_options.append(f"{status_icon} {func_data['name']}")

        # Add unavailable functions directly
        for func_id, func_data in unavailable_functionalities.items():
            dropdown_options.append(f"❌ {func_data['name']}")

        # Show dropdown without label
        selected_option = st.selectbox(
            "Analysis Function",
            options=["Select function..."] + dropdown_options,
            help="Choose the analysis you want to perform",
            label_visibility="collapsed"
        )
        
        # Show description for selected function
        if selected_option not in ["-- Select a function --", "--- Available Functions ---", "--- Unavailable (Missing Required Files) ---"]:
            # Find the selected function
            selected_func_id = None
            selected_func_data = None
            
            for func_id, func_data in functionalities.items():
                if func_data['name'] in selected_option:
                    selected_func_id = func_id
                    selected_func_data = func_data
                    break
            
            if selected_func_data:
                # Show function details
                st.info(f"**Description:** {selected_func_data['description']}")
                
                # Show required files
                req_labels = {
                    'customer_journals': '📋 Customer Journals',
                    'ui_journals': '🖥️ UI Journals',
                    'registry_files': '📝 Registry Files'
                }
                required_files_str = ", ".join([req_labels.get(req, req) for req in selected_func_data['requires']])
                st.caption(f"**Required Files:** {required_files_str}")
                
                st.markdown("---")
                
                # Check if requirements are met
                requirements_met = all(req in available_file_types for req in selected_func_data['requires'])
                
                if not requirements_met:
                    missing = [req for req in selected_func_data['requires'] if req not in available_file_types]
                    missing_str = ", ".join([req_labels.get(m, m) for m in missing])
                    st.error(f"❌ **Cannot proceed:** Missing required files: {missing_str}")
                    st.info("💡 Please upload a ZIP file containing these file types.")
                
                elif selected_func_data['status'] == 'construction':
                    st.warning("**Under Construction**")
                
                else:
                    # Function is ready - show the actual functionality
                    # ============================================
                    # FUNCTION IMPLEMENTATIONS START HERE
                    # ============================================
                    
                    if selected_func_id == "transaction_stats":
                        render_transaction_stats()
                    
                    elif selected_func_id == "individual_transaction":
                        render_individual_transaction_analysis()
    
    else:
        st.error("⚠️ Processing result not found. Please upload a ZIP file again.")

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #666; font-size: 12px;'>
        DN Log Analyser • Built with FastAPI & Streamlit
    </div>
""", unsafe_allow_html=True)