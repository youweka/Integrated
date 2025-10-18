from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from modules.extraction import ZipExtractionService
from modules.categorization import CategorizationService
from modules.processing import ProcessingService
from modules.session import session_service
from modules.transaction_analyzer import TransactionAnalyzerService
from modules.schemas import (
    FileCategorizationResponse,
    AvailableFileTypesResponse,
    FileTypeSelectionRequest,
    CategoryCount
)
from pathlib import Path
from typing import Dict, List

router = APIRouter()

# Simple session ID for now (use UUID in production)
CURRENT_SESSION_ID = "current_session"


@router.post("/process-zip", response_model=FileCategorizationResponse)
async def process_zip_file(
    file: UploadFile = File(..., description="ZIP file to process")
):
    """
    Step 1: Receive and validate ZIP file upload
    """
    if not file.filename.endswith('.zip'):
        raise HTTPException(
            status_code=400,
            detail="Only ZIP files are accepted"
        )
    
    try:
        # Read the uploaded file
        zip_content = await file.read()
        
        # Step 2: Extract
        extraction_service = ZipExtractionService()
        extract_path = extraction_service.extract_zip(zip_content)
        
        # Step 3: Categorize
        categorization_service = CategorizationService()
        file_categories = categorization_service.categorize_files(extract_path)
        
        # Debug output
        print(f"🔍 DEBUG: About to create session")
        print(f"📁 File categories: {list(file_categories.keys())}")
        print(f"📊 File counts: {dict((k, len(v)) for k, v in file_categories.items())}")
        
        # Step 4: Store in session - CRITICAL LINE
        session_service.create_session(CURRENT_SESSION_ID, file_categories, extract_path)
        
        # Debug output
        print(f"✅ DEBUG: Session created successfully")
        print(f"🔍 DEBUG: Verifying session exists: {session_service.session_exists(CURRENT_SESSION_ID)}")
        
        # Step 5: Process and return results
        processing_service = ProcessingService()
        result = processing_service.prepare_response(file_categories, extract_path)
        
        return result
        
    except Exception as e:
        print(f"❌ ERROR in process_zip: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing ZIP file: {str(e)}"
        )


@router.get("/available-file-types", response_model=AvailableFileTypesResponse)
async def get_available_file_types(session_id: str = Query(default=CURRENT_SESSION_ID)):
    """
    Get available file types from the processed ZIP
    """
    # Check if session exists
    if not session_service.session_exists(session_id):
        raise HTTPException(
            status_code=404,
            detail="No processed ZIP found. Please upload a ZIP file first."
        )
    
    # Get file categories
    file_categories = session_service.get_file_categories(session_id)
    
    if not file_categories:
        raise HTTPException(
            status_code=404,
            detail="No file categories found"
        )
    
    # Filter only non-empty categories
    available_types = []
    type_details = {}
    
    for category, files in file_categories.items():
        if len(files) > 0:
            available_types.append(category)
            type_details[category] = CategoryCount(
                count=len(files),
                files=[Path(f).name for f in files]
            )
    
    return AvailableFileTypesResponse(
        available_types=available_types,
        type_details=type_details
    )


@router.post("/select-file-type")
async def select_file_type(
    request: FileTypeSelectionRequest,
    session_id: str = Query(default=CURRENT_SESSION_ID)
):
    """
    Select one or multiple file types and get available operations
    """
    # Check if session exists
    if not session_service.session_exists(session_id):
        raise HTTPException(
            status_code=404,
            detail="No processed ZIP found. Please upload a ZIP file first."
        )
    
    # Get file categories
    file_categories = session_service.get_file_categories(session_id)
    
    if not file_categories:
        raise HTTPException(
            status_code=404,
            detail="No file categories found"
        )
    
    # Get selected file types - convert enum to string
    try:
        selected_types = [ft.value if hasattr(ft, 'value') else str(ft) for ft in request.file_types]
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file types format: {str(e)}"
        )
    
    # Validate all selected types
    for selected_type in selected_types:
        if selected_type not in file_categories or len(file_categories[selected_type]) == 0:
            raise HTTPException(
                status_code=400,
                detail=f"No files found for type: {selected_type}"
            )
    
    # Store selected types in session
    session_service.update_session(session_id, 'selected_types', selected_types)
    
    # Define available operations for each file type
    operations_map = {
        "customer_journals": [
            "parse_transactions",
            "analyze_transactions",
            "generate_report",
            "root_cause_analysis",
            "transaction_flow_visualization"
        ],
        "ui_journals": [
            "parse_ui_events",
            "map_to_transactions",
            "generate_flow_diagram"
        ],
        "trc_trace": [
            "parse_trace",
            "analyze_errors",
            "generate_timeline"
        ],
        "trc_error": [
            "parse_errors",
            "categorize_errors",
            "generate_error_report"
        ],
        "registry_files": [
            "parse_registry",
            "compare_registries",
            "export_to_csv",
            "view_differences"
        ]
    }
    
    # Define combined operations
    combined_operations_map = {
        frozenset(["customer_journals", "ui_journals"]): [
            "map_transactions_to_ui_flow",
            "generate_combined_transaction_report",
            "visualize_complete_flow",
            "compare_transaction_flows"
        ],
        frozenset(["trc_trace", "trc_error"]): [
            "correlate_trace_and_errors",
            "generate_unified_error_report",
            "analyze_error_timeline"
        ]
    }
    
    # Build response
    type_details = {}
    for selected_type in selected_types:
        files = file_categories[selected_type]
        type_details[selected_type] = {
            "file_count": len(files),
            "files": [Path(f).name for f in files],
            "available_operations": operations_map.get(selected_type, [])
        }
    
    # Determine combined operations
    combined_ops = []
    if len(selected_types) > 1:
        types_set = frozenset(selected_types)
        if types_set in combined_operations_map:
            combined_ops = combined_operations_map[types_set]
        else:
            combined_ops = ["export_all_to_csv", "generate_combined_summary"]
    
    return {
        "selected_types": selected_types,
        "type_details": type_details,
        "combined_operations": combined_ops
    }


@router.get("/analyze-customer-journals")
async def analyze_customer_journals(session_id: str = Query(default=CURRENT_SESSION_ID)):
    """
    Analyze customer journal files and return transaction overview
    """
    # Check if session exists
    if not session_service.session_exists(session_id):
        raise HTTPException(
            status_code=404,
            detail="No processed ZIP found. Please upload a ZIP file first."
        )
    
    # Get file categories
    file_categories = session_service.get_file_categories(session_id)
    
    if not file_categories or 'customer_journals' not in file_categories:
        raise HTTPException(
            status_code=400,
            detail="No customer journal files found"
        )
    
    customer_journal_files = file_categories['customer_journals']
    
    if not customer_journal_files:
        raise HTTPException(
            status_code=400,
            detail="No customer journal files available"
        )
    
    try:
        # Analyze the files
        analyzer = TransactionAnalyzerService()
        transactions_df = analyzer.analyze_multiple_files(customer_journal_files)
        
        if transactions_df.empty:
            raise HTTPException(
                status_code=404,
                detail="No transactions found in the files"
            )
        
        # Convert DataFrame to dict for JSON response
        transactions_dict = transactions_df.to_dict('records')
        
        # Calculate summary statistics
        total_transactions = len(transactions_df)
        successful = len(transactions_df[transactions_df['End State'] == 'Successful'])
        unsuccessful = len(transactions_df[transactions_df['End State'] == 'Unsuccessful'])
        unknown = len(transactions_df[transactions_df['End State'] == 'Unknown'])
        unique_types = transactions_df['Transaction Type'].nunique()
        unique_files = transactions_df['Source_File'].nunique()
        
        # Store in session for later use
        session_service.update_session(session_id, 'transaction_data', transactions_dict)
        
        return {
            "total_transactions": total_transactions,
            "successful": successful,
            "unsuccessful": unsuccessful,
            "unknown": unknown,
            "unique_types": unique_types,
            "unique_files": unique_files,
            "transactions": transactions_dict
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing transactions: {str(e)}"
        )


@router.get("/current-selection")
async def get_current_selection(session_id: str = Query(default=CURRENT_SESSION_ID)):
    """
    Get the currently selected file type(s)
    """
    if not session_service.session_exists(session_id):
        raise HTTPException(
            status_code=404,
            detail="No session found"
        )
    
    session = session_service.get_session(session_id)
    selected_types = session.get('selected_types', [])
    
    if not selected_types:
        return {"selected_types": [], "message": "No file types selected yet"}
    
    return {"selected_types": selected_types}


@router.get("/debug-session")
async def debug_session(session_id: str = Query(default=CURRENT_SESSION_ID)):
    """
    Debug endpoint to check session contents
    """
    if not session_service.session_exists(session_id):
        return {
            "exists": False,
            "message": "Session not found"
        }
    
    session_data = session_service.get_session(session_id)
    
    return {
        "exists": True,
        "has_file_categories": 'file_categories' in session_data,
        "file_categories_keys": list(session_data.get('file_categories', {}).keys()) if 'file_categories' in session_data else [],
        "file_counts": {
            cat: len(files) 
            for cat, files in session_data.get('file_categories', {}).items()
        } if 'file_categories' in session_data else {},
        "selected_types": session_data.get('selected_types', []),
        "extraction_path": session_data.get('extraction_path', None)
    }