from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from enum import Enum

class CategoryCount(BaseModel):
    count: int = Field(..., description="Number of files in this category")
    files: List[str] = Field(..., description="List of file paths")

class FileCategorizationResponse(BaseModel):
    total_files: int = Field(..., description="Total number of files processed")
    extraction_path: str = Field(..., description="Path where files were extracted")
    categories: Dict[str, CategoryCount] = Field(
        ...,
        description="Categorized files by type"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_files": 10,
                "extraction_path": "temp_extracted_files",
                "categories": {
                    "customer_journals": {
                        "count": 2,
                        "files": ["temp_extracted_files/journal1.log"]
                    },
                    "ui_journals": {
                        "count": 1,
                        "files": ["temp_extracted_files/ui.log"]
                    }
                }
            }
        }


# NEW: Enum for file types
class FileTypeEnum(str, Enum):
    CUSTOMER_JOURNALS = "customer_journals"
    UI_JOURNALS = "ui_journals"
    TRC_TRACE = "trc_trace"
    TRC_ERROR = "trc_error"
    REGISTRY_FILES = "registry_files"


# NEW: Response for available file types
class AvailableFileTypesResponse(BaseModel):
    available_types: List[str] = Field(..., description="List of available file types")
    type_details: Dict[str, CategoryCount] = Field(..., description="Details for each type")
    
    class Config:
        json_schema_extra = {
            "example": {
                "available_types": ["customer_journals", "ui_journals"],
                "type_details": {
                    "customer_journals": {
                        "count": 2,
                        "files": ["file1.jrn", "file2.jrn"]
                    },
                    "ui_journals": {
                        "count": 1,
                        "files": ["ui.jrn"]
                    }
                }
            }
        }


# NEW: Request for selecting file type(s) and operation
class FileTypeSelectionRequest(BaseModel):
    file_types: List[FileTypeEnum] = Field(..., description="Selected file type(s)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "file_types": ["customer_journals", "ui_journals"]
            }
        }


# NEW: Details for a single file type
class FileTypeDetail(BaseModel):
    file_count: int = Field(..., description="Number of files of this type")
    files: List[str] = Field(..., description="List of files")
    available_operations: List[str] = Field(..., description="Operations available for this file type")


# NEW: Response for file type selection (supports multiple types)
class FileTypeSelectionResponse(BaseModel):
    selected_types: List[str] = Field(..., description="The selected file types")
    type_details: Dict[str, FileTypeDetail] = Field(..., description="Details for each selected type")
    combined_operations: List[str] = Field(..., description="Operations available when combining these types")
    
    class Config:
        json_schema_extra = {
            "example": {
                "selected_types": ["customer_journals", "ui_journals"],
                "type_details": {
                    "customer_journals": {
                        "file_count": 2,
                        "files": ["file1.jrn", "file2.jrn"],
                        "available_operations": ["parse", "analyze_transactions"]
                    },
                    "ui_journals": {
                        "file_count": 1,
                        "files": ["ui.jrn"],
                        "available_operations": ["parse_ui_events"]
                    }
                },
                "combined_operations": ["map_transactions_to_ui", "generate_combined_report"]
            }
        }