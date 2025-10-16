import zipfile
import io
import shutil
from pathlib import Path

class ZipExtractionService:
    """
    Step 2: Handle ZIP file extraction
    """
    
    def __init__(self, base_temp_dir: str = "temp_extracted_files"):
        self.base_temp_dir = Path(base_temp_dir)
    
    def extract_zip(self, zip_content: bytes) -> Path:
        """
        Extract ZIP file contents to temporary directory.
        
        Args:
            zip_content: Bytes content of the ZIP file
            
        Returns:
            Path to the extraction directory
        """
        # Create a persistent temp directory
        temp_extract_dir = self.base_temp_dir
        temp_extract_dir.mkdir(exist_ok=True)
        
        # Clear any old files
        if temp_extract_dir.exists():
            shutil.rmtree(temp_extract_dir)
            temp_extract_dir.mkdir()
        
        # Extract ZIP contents
        with zipfile.ZipFile(io.BytesIO(zip_content), "r") as zip_ref:
            zip_ref.extractall(temp_extract_dir)
        
        return temp_extract_dir