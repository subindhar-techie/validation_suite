"""
Utility functions for file operations
"""
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging

def parse_filename(filename: str) -> Optional[Dict]:
    """Extract components from filename"""
    filename_without_ext = Path(filename).stem
    pattern = r'^(?:IN|OUT|CNUM|ORIG_TRIG|SCM|SIMODA)_(\d+)_(\d+)_(\d+)_([A-Z]+)_(\d+)_([A-Z_]+)_([A-Z]+)_(\d+)'
    match = re.match(pattern, filename_without_ext)
    if match:
        return {
            'po_number': match.group(1),
            'sequence': match.group(2),
            'batch_number': match.group(3),
            'circle': match.group(4),
            'card_manufacturer': match.group(5),
            'card_type': match.group(6),
            'sim_subtype': match.group(7),
            'timestamp': match.group(8)
        }
    return None

def find_matching_files(parent_folder: str) -> List[Dict]:
    """Find and match IN files with corresponding OUT folders"""
    parent_path = Path(parent_folder)
    
    if not parent_path.exists():
        raise FileNotFoundError(f"Parent folder does not exist: {parent_folder}")
    
    in_files = list(parent_path.glob("IN_*.txt"))
    in_files.sort()
    
    out_folders = [f for f in parent_path.iterdir() if f.is_dir() and f.name.startswith("OUT_")]
    out_folders.sort()
    
    matches = []
    
    for in_file in in_files:
        in_suffix = in_file.stem[3:]
        for out_folder in out_folders:
            out_suffix = out_folder.name[4:]
            if in_suffix == out_suffix:
                matches.append({
                    'in_file': in_file,
                    'out_folder': out_folder,
                    'suffix': in_suffix
                })
                break
    
    return matches

def find_output_files(out_folder: Path, suffix: str) -> Dict:
    """Find output files with various extensions"""
    output_files = {}
    
    file_patterns = {
        'CNUM': [f"CNUM_{suffix}.txt", f"CNUM_{suffix}.TXT", f"CNUM_{suffix}"],
        'ORIG_TRIG': [f"ORIG_TRIG_{suffix}.txt", f"ORIG_TRIG_{suffix}.TXT", f"ORIG_TRIG_{suffix}"],
        'SCM': [f"SCM_{suffix}.txt", f"SCM_{suffix}.TXT", f"SCM_{suffix}"],
        'SIMODA': [f"SIMODA_{suffix}.cps", f"SIMODA_{suffix}.CPS", f"SIMODA_{suffix}.txt", f"SIMODA_{suffix}.TXT", f"SIMODA_{suffix}"]
    }
    
    for file_type, patterns in file_patterns.items():
        found = False
        for pattern in patterns:
            potential_file = out_folder / pattern
            if potential_file.exists():
                output_files[file_type] = potential_file
                found = True
                break
        if not found:
            output_files[file_type] = None
    
    return output_files

def extract_header_info(file_path: Path) -> Dict:
    """Extract header information from file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines()[:15]]
        
        info = {}
        for line in lines:
            if any(key in line for key in ["PO Number:", "PO NO:"]):
                info['po_number'] = line.split(":")[1].strip()
            elif any(key in line for key in ["Batch No:", "Batch NO:"]):
                info['batch_number'] = line.split(":")[1].strip()
            elif "SIM Quantity:" in line:
                try:
                    info['sim_quantity'] = int(line.split(":")[1].strip())
                except ValueError:
                    pass
            elif "Circle:" in line:
                info['circle'] = line.split(":")[1].strip()
            elif "SKU:" in line:
                info['sku'] = line.split(":")[1].strip()
        
        return info
    except Exception as e:
        logging.error(f"Error extracting header info from {file_path}: {str(e)}")
        return {}

def validate_quantity(file_path: Path, expected_data_lines: int, header_lines: int = 0) -> Tuple[bool, str]:
    """Validate line count in files"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        actual_total_lines = len(lines)
        actual_data_lines = actual_total_lines - header_lines
        
        if actual_data_lines != expected_data_lines:
            return False, f"Line count mismatch: expected {expected_data_lines} data lines, found {actual_data_lines}"
        
        return True, f"Line count correct: {actual_data_lines} data lines"
        
    except Exception as e:
        return False, f"Error counting lines: {str(e)}"

def luhn_check(iccid: str) -> bool:
    """Validate ICCID using Luhn algorithm"""
    try:
        def digits_of(n):
            return [int(d) for d in str(n)]
        
        digits = digits_of(iccid)
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        checksum = sum(odd_digits)
        for d in even_digits:
            checksum += sum(digits_of(d * 2))
        return checksum % 10 == 0
    except Exception:
        return False