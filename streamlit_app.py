import streamlit as st
import requests
import json
import pandas as pd
from pathlib import Path
import io
import zipfile
import re
from datetime import datetime
from typing import List, Tuple, Dict
import difflib

# Page configuration
st.set_page_config(
    page_title="DN Diagnostics Platform",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional CSS
st.markdown("""
    <style>
    /* Global Styles */
    .main {
        background-color: #0a0a0a;
        color: #e0e0e0;
    }
    
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }
    
    /* Sidebar Styles */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a1a 0%, #0f0f0f 100%);
        border-right: 1px solid #2a2a2a;
    }
    
    [data-testid="stSidebar"] h2 {
        color: #ffffff;
        font-weight: 600;
        font-size: 1.1rem;
        margin-bottom: 1.5rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Typography */
    h1 {
        color: #ffffff !important;
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        margin-bottom: 0.5rem !important;
        letter-spacing: -0.5px !important;
    }
    
    h2 {
        color: #ffffff !important;
        font-size: 1.75rem !important;
        font-weight: 600 !important;
        margin: 2rem 0 1rem 0 !important;
        border-bottom: 2px solid #2563eb;
        padding-bottom: 0.5rem;
    }
    
    h3 {
        color: #e0e0e0 !important;
        font-size: 1.25rem !important;
        font-weight: 600 !important;
        margin: 1.5rem 0 0.75rem 0 !important;
    }
    
    h4, h5, h6 {
        color: #c0c0c0 !important;
        font-weight: 500 !important;
    }
    
    p, span, div, label {
        color: #b0b0b0 !important;
        line-height: 1.6 !important;
    }
    
    /* Button Styles - Uniform and Professional */
    .stButton > button {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        color: #ffffff;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.95rem;
        letter-spacing: 0.3px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 6px rgba(37, 99, 235, 0.2);
        width: 100%;
        height: 48px;
        text-transform: none;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%);
        box-shadow: 0 6px 12px rgba(37, 99, 235, 0.35);
        transform: translateY(-1px);
    }
    
    .stButton > button:active {
        transform: translateY(0);
        box-shadow: 0 2px 4px rgba(37, 99, 235, 0.3);
    }
    
    .stButton > button:disabled {
        background: linear-gradient(135deg, #374151 0%, #1f2937 100%);
        color: #6b7280;
        cursor: not-allowed;
        box-shadow: none;
    }
    
    /* File Uploader */
    [data-testid="stFileUploader"] {
        background-color: #1a1a1a;
        border: 2px dashed #404040;
        border-radius: 12px;
        padding: 2rem;
        transition: all 0.3s ease;
    }
    
    [data-testid="stFileUploader"]:hover {
        border-color: #2563eb;
        background-color: #1f1f1f;
    }
    
    /* Select Box - Uniform Style */
    .stSelectbox > div > div {
        background-color: #1a1a1a;
        border: 1px solid #404040;
        border-radius: 8px;
        color: #e0e0e0;
        height: 48px;
        transition: all 0.3s ease;
    }
    
    .stSelectbox > div > div:hover {
        border-color: #2563eb;
        background-color: #1f1f1f;
    }
    
    /* Text Input */
    .stTextInput > div > div > input {
        background-color: #1a1a1a;
        border: 1px solid #404040;
        border-radius: 8px;
        color: #e0e0e0;
        height: 48px;
        padding: 0 1rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #2563eb;
        box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.1);
    }
    
    /* Metric Cards */
    [data-testid="stMetricValue"] {
        font-size: 1.75rem;
        font-weight: 700;
        color: #ffffff;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.875rem;
        color: #9ca3af;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 500;
    }
    
    /* Data Tables */
    .dataframe {
        border: 1px solid #2a2a2a !important;
        border-radius: 8px;
        overflow: hidden;
    }
    
    .dataframe thead tr th {
        background-color: #1a1a1a !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        font-size: 0.75rem;
        letter-spacing: 0.5px;
        padding: 1rem !important;
    }
    
    .dataframe tbody tr:hover {
        background-color: #1f1f1f !important;
    }
    
    /* Info/Warning/Success Boxes */
    .stAlert {
        border-radius: 8px;
        border-left-width: 4px;
        padding: 1rem 1.25rem;
    }
    
    /* Construction Badge */
    .construction-badge {
        display: inline-block;
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: #000000;
        padding: 0.375rem 0.875rem;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Section Divider */
    hr {
        border: none;
        border-top: 1px solid #2a2a2a;
        margin: 2rem 0;
    }
    
    /* Diff Viewer Styles */
    .diff-viewer {
        display: flex;
        gap: 1rem;
        margin-top: 1.5rem;
    }
    
    .diff-pane {
        flex: 1;
        background-color: #1a1a1a;
        border: 1px solid #2a2a2a;
        border-radius: 8px;
        padding: 1rem;
        overflow-x: auto;
        font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
        font-size: 0.875rem;
    }
    
    .diff-pane-header {
        background-color: #0f0f0f;
        padding: 0.75rem 1rem;
        border-bottom: 1px solid #2a2a2a;
        font-weight: 600;
        color: #ffffff;
        border-radius: 8px 8px 0 0;
        margin: -1rem -1rem 1rem -1rem;
    }
    
    .diff-line {
        padding: 0.25rem 0.5rem;
        white-space: pre-wrap;
        word-break: break-all;
        border-left: 3px solid transparent;
    }
    
    .diff-line-number {
        display: inline-block;
        width: 50px;
        color: #666666;
        text-align: right;
        margin-right: 1rem;
        user-select: none;
        font-weight: 500;
    }
    
    .diff-content-change {
        background-color: rgba(239, 68, 68, 0.15);
        border-left-color: #ef4444;
    }
    
    .diff-whitespace-change {
        background-color: rgba(168, 85, 247, 0.12);
        border-left-color: #a855f7;
    }
    
    .diff-identical {
        background-color: transparent;
    }
    
    /* Legend Items */
    .legend-item {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        background-color: #1a1a1a;
        border-radius: 6px;
        font-size: 0.875rem;
        font-weight: 500;
    }
    
    .legend-color {
        width: 20px;
        height: 20px;
        border-radius: 4px;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background-color: #1a1a1a;
        padding: 0.5rem;
        border-radius: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 6px;
        color: #9ca3af;
        font-weight: 500;
        padding: 0.75rem 1.5rem;
        transition: all 0.2s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #0f0f0f;
        color: #e0e0e0;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #2563eb;
        color: #ffffff;
    }
    
    /* Download Button */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #059669 0%, #047857 100%);
        color: #ffffff;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.95rem;
        transition: all 0.3s ease;
        width: 100%;
        height: 48px;
    }
    
    .stDownloadButton > button:hover {
        background: linear-gradient(135deg, #047857 0%, #065f46 100%);
        transform: translateY(-1px);
    }
    </style>
""", unsafe_allow_html=True)

# API Configuration
API_BASE_URL = "http://localhost:8000/api/v1"

# Initialize session state
def init_session_state():
    if 'zip_processed' not in st.session_state:
        st.session_state.zip_processed = False
    if 'processing_result' not in st.session_state:
        st.session_state.processing_result = None
    if 'selected_function' not in st.session_state:
        st.session_state.selected_function = None

init_session_state()

# ============================================
# UTILITY FUNCTIONS
# ============================================

def safe_decode(blob: bytes) -> str:
    """Safely decode bytes to string"""
    encs = ["utf-8-sig", "utf-16", "utf-16-le", "utf-16-be", "cp1252", "latin-1", "utf-8"]
    for e in encs:
        try:
            return blob.decode(e)
        except Exception:
            continue
    return blob.decode("utf-8", errors="replace")

def parse_registry_file(content: bytes) -> pd.DataFrame:
    """Parse registry file content into DataFrame"""
    lines = safe_decode(content).splitlines()
    
    rows = []
    current_section = None
    section_re = re.compile(r"^\s*\[(.+?)\]\s*$")
    kv_re = re.compile(r'^\s*(@|".+?"|[^=]+?)\s*=\s*(.+?)\s*$')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        m = section_re.match(line)
        if m:
            current_section = m.group(1).strip()
            continue
        
        if current_section:
            mv = kv_re.match(line)
            if mv:
                key_raw, value_raw = mv.groups()
                key = key_raw.strip('"') if key_raw != "@" else "@"
                
                rows.append({
                    "Path": current_section,
                    "Key": key,
                    "Value": value_raw.strip()
                })
    
    return pd.DataFrame(rows)

def compare_registry_dataframes(df_a: pd.DataFrame, df_b: pd.DataFrame) -> dict:
    """Compare two registry DataFrames"""
    if df_a.empty or df_b.empty:
        return {
            "changed": [],
            "added": [],
            "removed": [],
            "identical_count": 0
        }
    
    merged = df_a.merge(df_b, on=["Path", "Key"], how="outer", suffixes=("_A", "_B"), indicator=True)
    
    both = merged[merged["_merge"] == "both"]
    changed = both[both["Value_A"] != both["Value_B"]][["Path", "Key", "Value_A", "Value_B"]].to_dict('records')
    added = merged[merged["_merge"] == "right_only"][["Path", "Key", "Value_B"]].rename(columns={"Value_B": "Value"}).to_dict('records')
    removed = merged[merged["_merge"] == "left_only"][["Path", "Key", "Value_A"]].rename(columns={"Value_A": "Value"}).to_dict('records')
    identical = both[both["Value_A"] == both["Value_B"]]
    
    return {
        "changed": changed,
        "added": added,
        "removed": removed,
        "identical_count": len(identical)
    }

def detect_line_difference(line1: str, line2: str) -> str:
    """Detect type of difference between two lines"""
    if line1 == line2:
        return "identical"
    if line1.replace(' ', '').replace('\t', '') == line2.replace(' ', '').replace('\t', ''):
        return "whitespace"
    return "content"

def render_side_by_side_diff(content1: str, content2: str, filename1: str, filename2: str):
    """Render side-by-side diff with color coding"""
    lines1 = content1.splitlines()
    lines2 = content2.splitlines()
    
    max_lines = max(len(lines1), len(lines2))
    
    st.markdown("### File Comparison")
    st.caption(f"Comparing: {filename1} vs {filename2}")
    
    # Legend
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="legend-item"><div class="legend-color" style="background-color: rgba(239, 68, 68, 0.15);"></div>Content Changes</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="legend-item"><div class="legend-color" style="background-color: rgba(168, 85, 247, 0.12);"></div>Whitespace Only</div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="legend-item"><div class="legend-color" style="background-color: transparent; border: 1px solid #404040;"></div>Identical Lines</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown(f"#### {filename1}")
        html_left = '<div class="diff-pane"><div class="diff-pane-header">Original File</div>'
        
        for i in range(max_lines):
            line1 = lines1[i] if i < len(lines1) else ""
            line2 = lines2[i] if i < len(lines2) else ""
            
            diff_type = detect_line_difference(line1, line2)
            
            if diff_type == "content":
                css_class = "diff-content-change"
            elif diff_type == "whitespace":
                css_class = "diff-whitespace-change"
            else:
                css_class = "diff-identical"
            
            line1_escaped = line1.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            
            html_left += f'<div class="diff-line {css_class}"><span class="diff-line-number">{i+1}</span>{line1_escaped}</div>'
        
        html_left += '</div>'
        st.markdown(html_left, unsafe_allow_html=True)
    
    with col_right:
        st.markdown(f"#### {filename2}")
        html_right = '<div class="diff-pane"><div class="diff-pane-header">Modified File</div>'
        
        for i in range(max_lines):
            line1 = lines1[i] if i < len(lines1) else ""
            line2 = lines2[i] if i < len(lines2) else ""
            
            diff_type = detect_line_difference(line1, line2)
            
            if diff_type == "content":
                css_class = "diff-content-change"
            elif diff_type == "whitespace":
                css_class = "diff-whitespace-change"
            else:
                css_class = "diff-identical"
            
            line2_escaped = line2.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            
            html_right += f'<div class="diff-line {css_class}"><span class="diff-line-number">{i+1}</span>{line2_escaped}</div>'
        
        html_right += '</div>'
        st.markdown(html_right, unsafe_allow_html=True)

# ============================================
# ANALYSIS FUNCTIONS
# ============================================

def render_transaction_stats():
    """Render transaction statistics"""
    
    if st.button("Generate Statistics", use_container_width=True):
        with st.spinner("Analyzing transactions..."):
            try:
                response = requests.get(f"{API_BASE_URL}/analyze-customer-journals")
                
                if response.status_code == 200:
                    analysis_data = response.json()
                    st.session_state['transaction_analysis'] = analysis_data
                    
                    st.success("Analysis completed successfully.")
                    
                    st.markdown("### Overview")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Transactions", analysis_data['total_transactions'])
                    with col2:
                        st.metric("Successful", analysis_data['successful'])
                    with col3:
                        st.metric("Unsuccessful", analysis_data['unsuccessful'])
                    with col4:
                        st.metric("Unknown Status", analysis_data['unknown'])
                    
                    st.markdown("---")
                    
                    st.markdown("### Transaction Type Breakdown")
                    
                    transactions_df = pd.DataFrame(analysis_data['transactions'])
                    type_stats_list = []
                    
                    for txn_type in transactions_df['Transaction Type'].unique():
                        type_df = transactions_df[transactions_df['Transaction Type'] == txn_type]
                        
                        total_count = len(type_df)
                        successful_count = len(type_df[type_df['End State'] == 'Successful'])
                        unsuccessful_count = len(type_df[type_df['End State'] == 'Unsuccessful'])
                        unknown_count = len(type_df[type_df['End State'] == 'Unknown'])
                        
                        success_rate = (successful_count / total_count * 100) if total_count > 0 else 0
                        
                        durations = []
                        for duration_str in type_df['Duration']:
                            if isinstance(duration_str, str) and duration_str != 'N/A':
                                try:
                                    duration_sec = float(duration_str.replace('s', ''))
                                    durations.append(duration_sec)
                                except ValueError:
                                    continue
                        
                        if durations:
                            min_duration = min(durations)
                            max_duration = max(durations)
                            avg_duration = sum(durations) / len(durations)
                        else:
                            min_duration = None
                            max_duration = None
                            avg_duration = None
                        
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
                    
                    type_stats = pd.DataFrame(type_stats_list)
                    type_stats = type_stats.sort_values('Total Count', ascending=False)
                    type_stats.index = range(1, len(type_stats) + 1)
                    
                    st.dataframe(type_stats, use_container_width=True, height=400)
                    
                    csv = type_stats.to_csv(index=False)
                    st.download_button(
                        label="Download Statistics (CSV)",
                        data=csv,
                        file_name="transaction_statistics.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                    
                else:
                    st.error(f"Error: {response.json().get('detail', 'Unknown error occurred.')}")
            
            except Exception as e:
                st.error(f"Error: {str(e)}")

def render_individual_transaction_analysis():
    """Render individual transaction analysis"""
    st.markdown("### Individual Transaction Analysis")
    
    if 'transaction_analysis' not in st.session_state:
        if st.button("Load Transactions", use_container_width=True):
            with st.spinner("Loading transactions..."):
                try:
                    response = requests.get(f"{API_BASE_URL}/analyze-customer-journals")
                    
                    if response.status_code == 200:
                        analysis_data = response.json()
                        st.session_state['transaction_analysis'] = analysis_data
                        st.success("Transactions loaded successfully.")
                        st.rerun()
                    else:
                        st.error(f"Error: {response.json().get('detail', 'Unknown error occurred.')}")
                
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    else:
        analysis_data = st.session_state['transaction_analysis']
        transactions_df = pd.DataFrame(analysis_data['transactions'])
        
        transaction_options = [
            f"{row['Transaction ID']} - {row['Transaction Type']} ({row['End State']})"
            for _, row in transactions_df.iterrows()
        ]
        
        selected_txn_option = st.selectbox(
            "Select Transaction",
            options=["Select a transaction"] + transaction_options,
            key="selected_transaction"
        )
        
        if selected_txn_option != "Select a transaction":
            selected_txn_id = selected_txn_option.split(" - ")[0]
            txn_data = transactions_df[transactions_df['Transaction ID'] == selected_txn_id].iloc[0]
            
            st.markdown("---")
            st.markdown(f"### Transaction Details: {selected_txn_id}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Type", txn_data['Transaction Type'])
                st.metric("State", txn_data['End State'])
            with col2:
                st.metric("Start Time", txn_data['Start Time'])
                st.metric("End Time", txn_data['End Time'])
            with col3:
                st.metric("Duration", txn_data['Duration'])
                st.caption(f"Source: {txn_data['Source_File']}")
            
            st.markdown("---")
            st.markdown("### Transaction Log")
            st.code(txn_data['Transaction Log'], language='log')

def render_registry_single():
    """Render single registry file viewer"""
    st.markdown("### Registry File Viewer")

    file_categories = st.session_state.processing_result['categories']
    registry_files = file_categories.get('registry_files', {}).get('files', [])

    if not registry_files:
        st.warning("No registry files found in the uploaded package.")
        return

    file_map = {Path(f).name: f for f in registry_files}

    selected_file_name = st.selectbox(
        "Select Registry File",
        options=["Select a file"] + list(file_map.keys()),
        key="reg_single_select"
    )

    if selected_file_name != "Select a file":
        file_path = file_map[selected_file_name]
        
        with st.spinner("Loading registry file..."):
            try:
                with open(file_path, 'rb') as f:
                    content = f.read()
                
                df = parse_registry_file(content)
                
                if not df.empty:
                    st.success(f"Loaded {selected_file_name} successfully.")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Entries", len(df))
                    with col2:
                        st.metric("Unique Paths", df['Path'].nunique())
                    with col3:
                        st.metric("Unique Keys", df['Key'].nunique())
                    
                    st.markdown("---")
                    search_term = st.text_input("Search Registry", placeholder="Search in path, key, or value", key="reg_search")
                    
                    display_df = df
                    if search_term:
                        mask = (
                            df['Path'].str.contains(search_term, case=False, na=False) |
                            df['Key'].str.contains(search_term, case=False, na=False) |
                            df['Value'].str.contains(search_term, case=False, na=False)
                        )
                        display_df = df[mask]
                        st.info(f"Found {len(display_df)} matching entries.")
                    
                    st.dataframe(display_df, use_container_width=True, height=400)
                    
                    csv = display_df.to_csv(index=False)
                    st.download_button(
                        label="Download as CSV",
                        data=csv,
                        file_name=f"{Path(selected_file_name).stem}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                else:
                    st.warning("No entries found in the registry file.")
                    
            except Exception as e:
                st.error(f"Error loading file: {str(e)}")

def render_registry_compare():
    """Render registry file comparison"""
    st.markdown("### Registry File Comparison")
    st.info("Only files with the same name can be compared.")

    file_categories = st.session_state.processing_result['categories']
    registry_files = file_categories.get('registry_files', {}).get('files', [])

    if len(registry_files) < 2:
        st.warning("At least two registry files are required for comparison.")
        return

    file_groups = {}
    for file_path in registry_files:
        base_name = Path(file_path).stem
        if base_name not in file_groups:
            file_groups[base_name] = []
        file_groups[base_name].append(file_path)
    
    comparable_groups = {name: files for name, files in file_groups.items() if len(files) >= 2}
    
    if not comparable_groups:
        st.warning("No comparable files found. Files must have the same name to be compared.")
        return
    
    selected_group = st.selectbox(
        "Select File Group",
        options=list(comparable_groups.keys()),
        key="reg_compare_group"
    )
    
    if selected_group:
        files_in_group = comparable_groups[selected_group]
        
        st.caption(f"Found {len(files_in_group)} versions of '{selected_group}'.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            file1_path = st.selectbox(
                "Original File",
                options=files_in_group,
                format_func=lambda x: f"{Path(x).parent.name}/{Path(x).name}",
                index=0,
                key="reg_file1"
            )
        
        with col2:
            file2_path = st.selectbox(
                "Modified File",
                options=files_in_group,
                format_func=lambda x: f"{Path(x).parent.name}/{Path(x).name}",
                index=1 if len(files_in_group) > 1 else 0,
                key="reg_file2"
            )
        
        if st.button("Compare Files", use_container_width=True):
            if file1_path == file2_path:
                st.error("Please select two different file versions to compare.")
                return

            with st.spinner("Comparing files..."):
                try:
                    with open(file1_path, 'rb') as f:
                        content1 = f.read()
                    with open(file2_path, 'rb') as f:
                        content2 = f.read()
                    
                    text1 = safe_decode(content1)
                    text2 = safe_decode(content2)
                    
                    df1 = parse_registry_file(content1)
                    df2 = parse_registry_file(content2)
                    
                    st.success("Comparison completed successfully.")
                    
                    tab1, tab2 = st.tabs(["Raw Text Comparison", "Structured Comparison"])
                    
                    with tab1:
                        filename1 = f"{Path(file1_path).parent.name}/{Path(file1_path).name}"
                        filename2 = f"{Path(file2_path).parent.name}/{Path(file2_path).name}"
                        render_side_by_side_diff(text1, text2, filename1, filename2)
                        
                        st.markdown("---")
                        st.markdown("### Statistics")
                        
                        lines1 = text1.splitlines()
                        lines2 = text2.splitlines()
                        max_lines = max(len(lines1), len(lines2))
                        
                        content_changes = 0
                        whitespace_changes = 0
                        identical = 0
                        
                        for i in range(max_lines):
                            line1 = lines1[i] if i < len(lines1) else ""
                            line2 = lines2[i] if i < len(lines2) else ""
                            diff_type = detect_line_difference(line1, line2)
                            
                            if diff_type == "content":
                                content_changes += 1
                            elif diff_type == "whitespace":
                                whitespace_changes += 1
                            else:
                                identical += 1
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Total Lines", max_lines)
                        with col2:
                            st.metric("Content Changes", content_changes)
                        with col3:
                            st.metric("Whitespace Changes", whitespace_changes)
                        with col4:
                            st.metric("Identical Lines", identical)
                    
                    with tab2:
                        comparison = compare_registry_dataframes(df1, df2)
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Changed Entries", len(comparison['changed']))
                        with col2:
                            st.metric("Added Entries", len(comparison['added']))
                        with col3:
                            st.metric("Removed Entries", len(comparison['removed']))
                        with col4:
                            st.metric("Identical Entries", comparison['identical_count'])
                        
                        st.markdown("---")
                        
                        subtab1, subtab2, subtab3, subtab4 = st.tabs([
                            f"Changed ({len(comparison['changed'])})",
                            f"Added ({len(comparison['added'])})",
                            f"Removed ({len(comparison['removed'])})",
                            f"Identical ({comparison['identical_count']})"
                        ])

                        with subtab1:
                            if comparison['changed']:
                                df_changed = pd.DataFrame(comparison['changed'])
                                st.dataframe(df_changed, use_container_width=True, height=400)
                                
                                csv = df_changed.to_csv(index=False)
                                st.download_button(
                                    "Download Changed Entries",
                                    csv,
                                    "registry_changed.csv",
                                    "text/csv",
                                    use_container_width=True
                                )
                            else:
                                st.info("No changed entries found.")
                        
                        with subtab2:
                            if comparison['added']:
                                df_added = pd.DataFrame(comparison['added'])
                                st.dataframe(df_added, use_container_width=True, height=400)
                                
                                csv = df_added.to_csv(index=False)
                                st.download_button(
                                    "Download Added Entries",
                                    csv,
                                    "registry_added.csv",
                                    "text/csv",
                                    use_container_width=True
                                )
                            else:
                                st.info("No added entries found.")
                        
                        with subtab3:
                            if comparison['removed']:
                                df_removed = pd.DataFrame(comparison['removed'])
                                st.dataframe(df_removed, use_container_width=True, height=400)
                                
                                csv = df_removed.to_csv(index=False)
                                st.download_button(
                                    "Download Removed Entries",
                                    csv,
                                    "registry_removed.csv",
                                    "text/csv",
                                    use_container_width=True
                                )
                            else:
                                st.info("No removed entries found.")
                        
                        with subtab4:
                            st.info(f"{comparison['identical_count']} entries were identical in both files.")
                        
                except Exception as e:
                    st.error(f"Error comparing files: {str(e)}")

def render_under_construction(function_name: str):
    """Render under construction message"""
    st.markdown(f"### {function_name}")
    st.warning("This feature is currently under development.")
    st.markdown("""
    **Planned Features:**
    - Complete implementation of functionality
    - Advanced analysis capabilities
    - Comprehensive reporting options
    - Export functionality
    """)

# ============================================
# MAIN APPLICATION
# ============================================

with st.sidebar:
    st.markdown("## Navigation")
    st.markdown("---")
    
    if st.session_state.zip_processed:
        st.markdown("### Current Session")
        result = st.session_state.processing_result
        st.metric("Total Files", result['total_files'])
        
        st.markdown("---")
        if st.button("Upload New Package", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            init_session_state()
            st.rerun()
    else:
        st.markdown("### Quick Guide")
        st.markdown("""
        **Process:**
        1. Upload diagnostic package
        2. Review detected files
        3. Select analysis function
        4. View and export results
        
        **Supported Files:**
        - Customer Journals
        - UI Journals  
        - TRC Files
        - Registry Files
        """)

st.title("DN Diagnostics Platform")
st.caption("Comprehensive analysis tool for Diebold Nixdorf diagnostic files.")

if not st.session_state.zip_processed:
    st.markdown("## Upload Diagnostic Package")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Select ZIP Archive",
            type=['zip'],
            help="Upload a ZIP file containing diagnostic files (max 500 MB)"
        )
    
    with col2:
        st.markdown("**Requirements:**")
        st.caption("• ZIP format only")
        st.caption("• Maximum 500 MB")
        st.caption("• Valid diagnostic files")

    if uploaded_file is not None:
        file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
        st.info(f"File: {uploaded_file.name} ({file_size_mb:.2f} MB)")
        
        with st.spinner("Processing package..."):
            try:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/zip")}
                
                response = requests.post(
                    f"{API_BASE_URL}/process-zip", 
                    files=files,
                    timeout=120
                )
                
                if response.status_code == 200:
                    result = response.json()
                    st.session_state.zip_processed = True
                    st.session_state.processing_result = result
                    
                    st.success("Package processed successfully.")
                    st.rerun()
                else:
                    error_detail = response.json().get('detail', 'Unknown error occurred.')
                    st.error(f"Error: {error_detail}")
                    
            except requests.exceptions.Timeout:
                st.error("Request timeout. The file may be too large or the server is not responding.")
            except requests.exceptions.ConnectionError:
                st.error("Connection error. Please ensure the FastAPI server is running on localhost:8000.")
            except Exception as e:
                st.error(f"Error: {str(e)}")

else:
    result = st.session_state.processing_result
    categories = result['categories']
    
    st.markdown("## Detected Files")
    
    cols = st.columns(5)
    
    category_display = {
        'customer_journals': ('Customer Journals', '📋'),
        'ui_journals': ('UI Journals', '🖥️'),
        'trc_trace': ('TRC Trace', '📝'),
        'trc_error': ('TRC Error', '⚠️'),
        'registry_files': ('Registry Files', '📄')
    }
    
    for idx, (category, (label, icon)) in enumerate(category_display.items()):
        count = categories.get(category, {}).get('count', 0)
        with cols[idx]:
            st.metric(label, count)
    
    st.markdown("---")
    
    st.markdown("## Analysis Functions")
    
    functionalities = {
        "transaction_stats": {
            "name": "Transaction Type Statistics",
            "description": "Analyze transaction types, success rates, and performance metrics.",
            "requires": ["customer_journals"],
            "status": "ready"
        },
        "individual_transaction": {
            "name": "Individual Transaction Analysis",
            "description": "Detailed analysis of specific transaction logs and data.",
            "requires": ["customer_journals"],
            "status": "ready"
        },
        "ui_flow_individual": {
            "name": "UI Flow Analysis",
            "description": "Visualize user interface flow for specific transactions.",
            "requires": ["customer_journals", "ui_journals"],
            "status": "construction"
        },
        "llm_feedback": {
            "name": "AI-Powered Analysis",
            "description": "Leverage AI for intelligent insights and recommendations.",
            "requires": ["customer_journals"],
            "status": "construction"
        },
        "consolidated_flow": {
            "name": "Consolidated Transaction Flow",
            "description": "View aggregated transaction flows across multiple sessions.",
            "requires": ["customer_journals", "ui_journals"],
            "status": "construction"
        },
        "transaction_comparison": {
            "name": "Transaction Comparison",
            "description": "Compare two transactions side by side with detailed analysis.",
            "requires": ["customer_journals", "ui_journals"],
            "status": "construction"
        },
        "registry_single": {
            "name": "Registry File Viewer",
            "description": "View and analyze individual registry file contents.",
            "requires": ["registry_files"],
            "status": "ready"
        },
        "registry_compare": {
            "name": "Registry File Comparison",
            "description": "Compare two registry files with side-by-side difference view.",
            "requires": ["registry_files"],
            "status": "ready"
        },
        "acu_parser": {
            "name": "ACU Parser",
            "description": "Parse and analyze ACU diagnostic files.",
            "requires": ["customer_journals"],
            "status": "construction"
        }
    }
    
    available_file_types = [cat for cat, data in categories.items() if data.get('count', 0) > 0]
    
    available_funcs = []
    construction_funcs = []
    unavailable_funcs = []
    
    for func_id, func_data in functionalities.items():
        requirements_met = all(req in available_file_types for req in func_data['requires'])
        
        if requirements_met:
            if func_data['status'] == 'ready':
                available_funcs.append((func_id, func_data))
            else:
                construction_funcs.append((func_id, func_data))
        else:
            unavailable_funcs.append((func_id, func_data))
    
    dropdown_options = ["Select a function"]
    
    if available_funcs:
        dropdown_options.append("─── Available Functions ───")
        for func_id, func_data in available_funcs:
            dropdown_options.append(f"{func_data['name']}")
    
    if construction_funcs:
        dropdown_options.append("─── Under Development ───")
        for func_id, func_data in construction_funcs:
            dropdown_options.append(f"{func_data['name']}")
    
    if unavailable_funcs:
        dropdown_options.append("─── Unavailable Functions ───")
        for func_id, func_data in unavailable_funcs:
            missing = [req for req in func_data['requires'] if req not in available_file_types]
            dropdown_options.append(f"{func_data['name']} (Missing: {', '.join(missing)})")
    
    selected_option = st.selectbox(
        "Select Analysis Function",
        options=dropdown_options,
        key="function_selector"
    )
    
    selected_func_id = None
    selected_func_data = None
    
    if selected_option not in ["Select a function"] and not selected_option.startswith("───"):
        clean_option = selected_option.split(" (Missing:")[0]
        
        for func_id, func_data in functionalities.items():
            if func_data['name'] in clean_option:
                selected_func_id = func_id
                selected_func_data = func_data
                break
    
    if selected_func_data:
        st.markdown("---")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"### {selected_func_data['name']}")
        with col2:
            if selected_func_data['status'] == 'construction':
                st.markdown('<span class="construction-badge">Under Development</span>', unsafe_allow_html=True)
        
        st.info(selected_func_data['description'])
        
        req_labels = {
            'customer_journals': 'Customer Journals',
            'ui_journals': 'UI Journals',
            'trc_trace': 'TRC Trace',
            'trc_error': 'TRC Error',
            'registry_files': 'Registry Files'
        }
        required_files_str = ", ".join([req_labels.get(req, req) for req in selected_func_data['requires']])
        st.caption(f"Required Files: {required_files_str}")
        
        st.markdown("---")
        
        requirements_met = all(req in available_file_types for req in selected_func_data['requires'])
        
        if not requirements_met:
            missing = [req for req in selected_func_data['requires'] if req not in available_file_types]
            missing_str = ", ".join([req_labels.get(m, m) for m in missing])
            st.error(f"Cannot proceed. Missing required files: {missing_str}")
            st.info("Please upload a package containing the required file types.")
        
        elif selected_func_data['status'] == 'construction':
            render_under_construction(selected_func_data['name'])
        
        else:
            if selected_func_id == "transaction_stats":
                render_transaction_stats()
            
            elif selected_func_id == "individual_transaction":
                render_individual_transaction_analysis()

            elif selected_func_id == "registry_single":
                render_registry_single()
            
            elif selected_func_id == "registry_compare":
                render_registry_compare()

st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #666666; font-size: 0.875rem;'>
        DN Diagnostics Platform v1.0.0 | Built with FastAPI & Streamlit<br>
        © 2025 Diebold Nixdorf Analysis Tools
    </div>
""", unsafe_allow_html=True)