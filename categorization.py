from pathlib import Path
from typing import Dict, List
from modules.configManager import detect_file_type

class CategorizationService:
    """
    Step 3: Categorize extracted files by type
    """
    
    def __init__(self):
        self.categories = {
            'customer_journals': [],
            'ui_journals': [],
            'trc_trace': [],
            'trc_error': [],
            'registry_files': []
        }
    
    def categorize_files(self, extract_path: Path) -> Dict[str, List[str]]:
        """
        Categorize all files in the extracted directory.
        
        Args:
            extract_path: Path to the directory containing extracted files
            
        Returns:
            Dictionary with categorized file lists
        """
        # Find all files
        all_files = list(extract_path.rglob("*"))
        
        # Initialize fresh categories
        file_categories = {
            'customer_journals': [],
            'ui_journals': [],
            'trc_trace': [],
            'trc_error': [],
            'registry_files': []
        }
        
        # Categorize each file
        for file_path in all_files:
            if file_path.is_file():
                category = self._detect_category(file_path)
                if category:
                    file_categories[category].append(str(file_path))
        
        return file_categories
    
    def _detect_category(self, file_path: Path) -> str:
        """
        Detect which category a file belongs to.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Category name or None
        """
        file_type = detect_file_type(str(file_path))
        
        if "Customer Journal" in file_type:
            return 'customer_journals'
        elif "UI Journal" in file_type:
            return 'ui_journals'
        elif "TRC Trace" in file_type:
            return 'trc_trace'
        elif "TRC Error" in file_type:
            return 'trc_error'
        elif (file_path.suffix.lower() == '.reg' or 
              file_path.name.lower().endswith('reg.txt') or 
              'registry' in file_path.name.lower()):
            return 'registry_files'
        
        return None