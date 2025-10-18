"""
Transaction Analyzer Service - Parses and analyzes customer journal files
"""

import pandas as pd
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from .configManager import xml_to_dict
import os

class TransactionAnalyzerService:
    """
    Service for parsing and analyzing customer journal transactions
    """
    
    def __init__(self):
        # Load configuration when service is initialized
        # Define paths relative to this file's location for portability
        base_dir = Path(__file__).resolve().parent
        possible_paths = [
            base_dir / 'config' / 'dnLogAtConfig.xml',        # e.g., project/modules/config/dnLogAtConfig.xml
            base_dir.parent / 'config' / 'dnLogAtConfig.xml', # e.g., project/config/dnLogAtConfig.xml
            base_dir / 'dnLogAtConfig.xml',                   # e.g., project/dnLogAtConfig.xml
        ]
        
        config_path = None
        for path in possible_paths:
            if path.exists():
                config_path = path
                break
        
        if config_path is None:
            raise FileNotFoundError(
                "dnLogAtConfig.xml not found. Please ensure the config file exists. Searched in:\n" +
                "\n".join(map(str, possible_paths))
            )
        
        self.real_dict, self.start_key, self.end_key, self.chain_key = xml_to_dict(config_path)
        
    def parse_customer_journal(self, file_path: str) -> pd.DataFrame:
        """
        Parse a customer journal file and return DataFrame with transactions
        
        Args:
            file_path: Path to the customer journal file
            
        Returns:
            DataFrame with transaction data
        """
        dummy = Path(file_path).stem
        
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Parse all lines first
        parsed_rows = []
        for line in lines:
            line = line.strip()
            if not line or set(line) <= {'*'}:
                continue
            match = re.match(r"^(\d{2}:\d{2}:\d{2})\s+(\d+)\s*(.*)", line)
            if match:
                timestamp_str, tid, message = match.groups()
                try:
                    timestamp = datetime.strptime(timestamp_str, "%H:%M:%S").time()
                except ValueError:
                    timestamp = None
                parsed_rows.append([timestamp, tid, message])
            else:
                parsed_rows.append([None, None, line])

        df = pd.DataFrame(parsed_rows, columns=["timestamp", "tid", "message"])
        
        transactions = self._find_all_transactions(df, dummy)
        
        return pd.DataFrame(transactions)
    
    def _find_all_transactions(self, df: pd.DataFrame, dummy: str) -> List[Dict]:
        """Find all individual transactions in the parsed data"""
        transactions_bounds = []
        i = 0
        
        while i < len(df):
            row = df.iloc[i]
            
            # Look for transaction start OR transaction chaining
            if (str(row["tid"]) in [str(tid) for tid in self.start_key] or 
                str(row["tid"]) in [str(tid) for tid in self.chain_key]):
                start_idx = i
                j = i + 1
                end_idx = None
                
                # Look for the corresponding end
                while j < len(df):
                    current_row = df.iloc[j]
                    
                    # Found an end TID
                    if str(current_row["tid"]) in [str(tid) for tid in self.end_key]:
                        end_idx = j
                        break
                    
                    # If we encounter another start or chaining, break
                    if ((str(current_row["tid"]) in [str(tid) for tid in self.start_key] or 
                        str(current_row["tid"]) in [str(tid) for tid in self.chain_key]) and j > i + 3):
                        break
                    
                    j += 1
                
                if end_idx is not None:
                    transactions_bounds.append((start_idx, end_idx))
                    i = end_idx + 1
                else:
                    i += 1
            else:
                i += 1
        
        transactions = []
        
        for start_idx, end_idx in transactions_bounds:
            txn_segment = df.iloc[start_idx:end_idx+1]
            
            # Find start details
            start_time = None
            txn_id = None
            matched_start_tid = None
            
            # Check for regular start
            for start_tid in self.start_key:
                start_matches = txn_segment[txn_segment["tid"] == str(start_tid)]
                if not start_matches.empty:
                    start_row = start_matches.iloc[0]
                    start_time = start_row["timestamp"]
                    match = re.search(r"Transaction no\. '([^']*)'", start_row["message"])
                    txn_id = match.group(1) if match and match.group(1).strip() else (dummy + start_time.strftime("%H%M%S"))
                    matched_start_tid = start_tid
                    break

            # If no regular start found, check for transaction chaining
            if start_time is None:
                for chain_tid in self.chain_key:
                    chain_matches = txn_segment[txn_segment["tid"] == str(chain_tid)]
                    if not chain_matches.empty:
                        start_row = chain_matches.iloc[0]
                        start_time = start_row["timestamp"]
                        txn_id = dummy + start_time.strftime("%H%M%S") if start_time else f"CHAIN_{dummy}"
                        matched_start_tid = chain_tid
                        break
            
            # Find end details
            end_time = None
            end_state = "Unknown"
            
            for end_tid in self.end_key:
                end_matches = txn_segment[txn_segment["tid"] == str(end_tid)]
                if not end_matches.empty:
                    end_row = end_matches.iloc[-1]
                    end_time = end_row["timestamp"]
                    end_msg = end_row["message"]
                    
                    if ("end-state'N'" in end_msg or "end-state'n'" in end_msg or 
                        "state 'N'" in end_msg or "state 'n'" in end_msg):
                        end_state = "Successful"
                    elif ("end-state'E'" in end_msg or "end-state'e'" in end_msg or 
                        "state 'E'" in end_msg or "state 'e'" in end_msg or 
                        "state 'C'" in end_msg or "state 'c'" in end_msg):
                        end_state = "Unsuccessful"
                    else:
                        end_state = "Unknown"
                    break
            
            # Find transaction type
            txn_type = "Unknown"
            func_matches = txn_segment[txn_segment["tid"] == "3217"]
            if not func_matches.empty:
                for _, func_row in func_matches.iterrows():
                    func_match = re.search(r"Function\s+'([^']+)'", func_row["message"])
                    if func_match:
                        func_id = func_match.group(1).split('/')[0]
                        txn_type = self.real_dict.get(func_id, func_id)
                        break
            
            # Create transaction log string
            txn_log_str = "\n".join([
                f"{r['timestamp'].strftime('%H:%M:%S') if r['timestamp'] else '??'} {r['tid']} {r['message']}"
                for _, r in txn_segment.iterrows()
            ])
            
            # Calculate duration
            duration = "N/A"
            if start_time and end_time:
                try:
                    duration_seconds = (datetime.combine(datetime.today(), end_time) - 
                                      datetime.combine(datetime.today(), start_time)).total_seconds()
                    if duration_seconds < 0:
                        duration_seconds += 24 * 3600
                    duration = f"{duration_seconds:.1f}s"
                except Exception:
                    duration = "N/A"
            
            transactions.append({
                "Transaction ID": txn_id,
                "Transaction Type": txn_type,
                "Start Time": start_time,
                "End Time": end_time,
                "Duration": duration,
                "End State": end_state,
                "Transaction Log": txn_log_str,
                "Source_File": Path(dummy).name
            })

        return transactions
    
    def analyze_multiple_files(self, file_paths: List[str]) -> pd.DataFrame:
        """
        Analyze multiple customer journal files
        
        Args:
            file_paths: List of file paths to analyze
            
        Returns:
            Combined DataFrame with all transactions
        """
        all_dfs = []
        
        for file_path in file_paths:
            try:
                df = self.parse_customer_journal(file_path)
                all_dfs.append(df)
            except Exception as e:
                print(f"Error parsing {file_path}: {e}")
                continue
        
        if not all_dfs:
            return pd.DataFrame()
        
        # Combine all dataframes
        combined_df = pd.concat(all_dfs, ignore_index=True)
        
        return combined_df