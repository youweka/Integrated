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
import logging
import traceback

router = APIRouter()
logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Simple session ID
CURRENT_SESSION_ID = "current_session"

# Maximum file size: 500MB
MAX_FILE_SIZE = 500 * 1024 * 1024


@router.post("/process-zip", response_model=FileCategorizationResponse)
async def process_zip_file(
    file: UploadFile = File(..., description="ZIP file to process")
):
    """
    Ultra-robust ZIP processing endpoint
    - Validates file type and size
    - Streams file in chunks
    - Comprehensive error handling
    - Detailed logging
    """
    # Validate file extension
    if not file.filename.lower().endswith('.zip'):
        logger.warning(f"Invalid file type uploaded: {file.filename}")
        raise HTTPException(
            status_code=400,
            detail="Only ZIP files are accepted. Please upload a .zip file."
        )
    
    try:
        logger.info(f"=== Starting ZIP processing: {file.filename} ===")
        
        # Read file in chunks
        logger.info("Reading uploaded file...")
        zip_content = bytearray()
        chunk_size = 1024 * 1024  # 1MB chunks
        total_size = 0
        chunks_read = 0
        
        try:
            while chunk := await file.read(chunk_size):
                total_size += len(chunk)
                chunks_read += 1
                
                # Check size limit
                if total_size > MAX_FILE_SIZE:
                    logger.warning(f"File too large: {total_size} bytes")
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)} MB. Your file is {total_size // (1024*1024)} MB."
                    )
                
                zip_content.extend(chunk)
                
                # Log progress for large files
                if chunks_read % 50 == 0:
                    logger.info(f"Read {chunks_read} chunks ({total_size / (1024*1024):.2f} MB)...")
        
        except Exception as read_error:
            logger.error(f"Error reading file: {str(read_error)}")
            raise HTTPException(
                status_code=400,
                detail=f"Error reading uploaded file: {str(read_error)}"
            )
        
        logger.info(f"File received successfully: {total_size / (1024*1024):.2f} MB ({chunks_read} chunks)")
        
        # Convert to bytes
        zip_bytes = bytes(zip_content)
        
        # Step 2: Extract ZIP
        logger.info("Starting ZIP extraction...")
        extraction_service = ZipExtractionService()
        
        try:
            extract_path = extraction_service.extract_zip(zip_bytes)
            logger.info(f"Extraction successful: {extract_path}")
            
            # Get extraction info
            extraction_info = extraction_service.get_extraction_info(extract_path)
            logger.info(f"Extracted {extraction_info['total_files']} files ({extraction_info['total_size_mb']} MB)")
            
        except ValueError as ve:
            # Validation errors (bad ZIP, empty, etc.)
            logger.error(f"ZIP validation error: {str(ve)}")
            raise HTTPException(
                status_code=400,
                detail=str(ve)
            )
        except Exception as ext_error:
            logger.error(f"Extraction error: {str(ext_error)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500,
                detail=f"Failed to extract ZIP file: {str(ext_error)}"
            )
        
        # Optional: Cleanup old extractions in background
        try:
            extraction_service.cleanup_old_extracts(max_age_hours=24)
        except Exception as cleanup_error:
            logger.warning(f"Cleanup warning: {cleanup_error}")
        
        # Step 3: Categorize files
        logger.info("Starting file categorization...")
        categorization_service = CategorizationService()
        
        try:
            file_categories = categorization_service.categorize_files(extract_path)
            
            # Log categorization results
            total_categorized = sum(len(v) for v in file_categories.values())
            logger.info(f"Categorization complete: {total_categorized} files in {len(file_categories)} categories")
            
            for category, files in file_categories.items():
                if files:
                    logger.info(f"  - {category}: {len(files)} files")
            
        except Exception as cat_error:
            logger.error(f"Categorization error: {str(cat_error)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500,
                detail=f"Failed to categorize files: {str(cat_error)}"
            )
        
        # Step 4: Create session
        logger.info("Creating session...")
        try:
            session_service.create_session(CURRENT_SESSION_ID, file_categories, extract_path)
            logger.info("Session created successfully")
        except Exception as session_error:
            logger.error(f"Session creation error: {str(session_error)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create session: {str(session_error)}"
            )
        
        # Step 5: Prepare response
        logger.info("Preparing response...")
        processing_service = ProcessingService()
        
        try:
            result = processing_service.prepare_response(file_categories, extract_path)
            logger.info(f"=== Processing complete: {result.total_files} files categorized ===")
            return result
            
        except Exception as proc_error:
            logger.error(f"Response preparation error: {str(proc_error)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to prepare response: {str(proc_error)}"
            )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
        
    except Exception as e:
        # Catch-all for unexpected errors
        logger.error(f"Unexpected error in process_zip: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error processing ZIP file: {str(e)}"
        )


@router.get("/available-file-types", response_model=AvailableFileTypesResponse)
async def get_available_file_types(session_id: str = Query(default=CURRENT_SESSION_ID)):
    """Get available file types from the processed ZIP"""
    
    if not session_service.session_exists(session_id):
        raise HTTPException(
            status_code=404,
            detail="No processed ZIP found. Please upload a ZIP file first."
        )
    
    file_categories = session_service.get_file_categories(session_id)
    
    if not file_categories:
        raise HTTPException(
            status_code=404,
            detail="No file categories found"
        )
    
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
    """Select one or multiple file types"""
    
    if not session_service.session_exists(session_id):
        raise HTTPException(
            status_code=404,
            detail="No processed ZIP found. Please upload a ZIP file first."
        )
    
    file_categories = session_service.get_file_categories(session_id)
    
    if not file_categories:
        raise HTTPException(
            status_code=404,
            detail="No file categories found"
        )
    
    try:
        selected_types = [ft.value if hasattr(ft, 'value') else str(ft) for ft in request.file_types]
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file types format: {str(e)}"
        )
    
    for selected_type in selected_types:
        if selected_type not in file_categories or len(file_categories[selected_type]) == 0:
            raise HTTPException(
                status_code=400,
                detail=f"No files found for type: {selected_type}"
            )
    
    session_service.update_session(session_id, 'selected_types', selected_types)
    
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
    
    type_details = {}
    for selected_type in selected_types:
        files = file_categories[selected_type]
        type_details[selected_type] = {
            "file_count": len(files),
            "files": [Path(f).name for f in files],
            "available_operations": operations_map.get(selected_type, [])
        }
    
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
    """Analyze customer journal files"""
    
    if not session_service.session_exists(session_id):
        raise HTTPException(
            status_code=404,
            detail="No processed ZIP found. Please upload a ZIP file first."
        )
    
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
        logger.info(f"Analyzing {len(customer_journal_files)} customer journal files")
        
        analyzer = TransactionAnalyzerService()
        transactions_df = analyzer.analyze_multiple_files(customer_journal_files)
        
        if transactions_df.empty:
            raise HTTPException(
                status_code=404,
                detail="No transactions found in the files"
            )
        
        transactions_dict = transactions_df.to_dict('records')
        
        total_transactions = len(transactions_df)
        successful = len(transactions_df[transactions_df['End State'] == 'Successful'])
        unsuccessful = len(transactions_df[transactions_df['End State'] == 'Unsuccessful'])
        unknown = len(transactions_df[transactions_df['End State'] == 'Unknown'])
        unique_types = transactions_df['Transaction Type'].nunique()
        unique_files = transactions_df['Source_File'].nunique()
        
        session_service.update_session(session_id, 'transaction_data', transactions_dict)
        
        logger.info(f"Analysis complete: {total_transactions} transactions found")
        
        return {
            "total_transactions": total_transactions,
            "successful": successful,
            "unsuccessful": unsuccessful,
            "unknown": unknown,
            "unique_types": unique_types,
            "unique_files": unique_files,
            "transactions": transactions_dict
        }
        
    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(f"Error analyzing transactions: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing transactions: {str(e)}"
        )


@router.get("/current-selection")
async def get_current_selection(session_id: str = Query(default=CURRENT_SESSION_ID)):
    """Get currently selected file types"""
    
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
    """Debug endpoint to check session contents"""
    
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


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "DN Diagnostics API",
        "version": "1.0.0"
    }