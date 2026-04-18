"""
MNO File Validator - SIMODA file validation logic
"""
import re
import os
import sys
from typing import List, Tuple, Optional, Callable
from pathlib import Path
from datetime import datetime
from .validation_base import BaseValidator, ValidationResult


def _make_long_path(path) -> str:
    """Convert path to extended-length path on Windows for long paths (>240 chars)"""
    if sys.platform != 'win32':
        return str(path)
    
    path_str = str(path)
    if path_str.startswith('\\\\?\\'):
        return path_str
    
    abs_path = os.path.abspath(path_str)
    if len(abs_path) > 240:
        if len(abs_path) >= 2 and abs_path[1] == ':':
            return '\\\\?\\' + abs_path
        elif abs_path.startswith('\\\\'):
            return '\\\\?\\UNC\\' + abs_path[2:]
    return path_str


def _safe_open(path, mode='r', encoding='utf-8', errors='replace'):
    """Open file with long path support on Windows"""
    long_path = _make_long_path(path)
    return open(long_path, mode, encoding=encoding, errors=errors)


class SIMODAValidator(BaseValidator):
    """Handles SIMODA file validation"""
    
    def __init__(self, log_callback: Optional[Callable] = None):
        super().__init__(log_callback)
        self.chip_type = "SAMSUNG 340"
    
    def set_chip_type(self, chip_type: str):
        """Set the chip type"""
        self.chip_type = chip_type
    
    def validate_simoda_file(self, simoda_file: Path, 
                           cnum_iccids: List[str], 
                           cnum_imsis: List[str]) -> ValidationResult:
        """Validate SIMODA file - FAST VERSION checking all ICCIDs/IMSIs with line numbers"""
        chip_codes = {
            "SAMSUNG 340": 'Chip("S3FW9FG")',
            "SAMSUNG 480": 'Chip("S3FW9FV")', 
            "TRANSA 380": 'Chip("TSS380A1")',
            "SLM17800" : 'Chip("SLM17ECB800B")'
        }
        
        expected_code = chip_codes.get(self.chip_type)
        
        if not expected_code:
            return ValidationResult(False, f"Unknown chip type: {self.chip_type}", [])
        
        try:
            # Try different encodings
            encodings = ['utf-8', 'latin-1', 'cp1252']
            content = ""
            lines = []
            
            for encoding in encodings:
                try:
                    with _safe_open(simoda_file, 'r', encoding) as f:
                        lines = f.readlines()
                        content = ''.join(lines)
                    break
                except UnicodeDecodeError:
                    continue
            
            errors = []
            
            # Find line numbers for chip code
            chip_line_number = 0
            chip_pattern = r'Chip\("[^"]+"\)'
            chip_matches = []
            
            for line_num, line in enumerate(lines, 1):
                line_chip_matches = re.findall(chip_pattern, line)
                if line_chip_matches:
                    chip_matches.extend(line_chip_matches)
                    chip_line_number = line_num
                    break
            
            # Check chip code with line number
            if chip_matches:
                actual_code = chip_matches[0]
                if actual_code != expected_code:
                    error_msg = (
                        f"ERR: Chip Code Data Mismatch "
                        f"(Expected: {expected_code}) "
                        f"(Found: {actual_code}) "
                        f"[Line: {chip_line_number}]"
                    )
                    errors.append(error_msg)
            else:
                error_msg = (
                    f"ERR: Chip Code Missing "
                    f"(Expected: {expected_code}) "
                    f"(Found: Not Present in SIMODA file)"
                )
                errors.append(error_msg)
            
            # FAST CHECK: Use set operations for quick lookup of all ICCIDs
            start_time = datetime.now()
            
            # Convert to sets for fast membership testing
            cnum_iccids_set = set(cnum_iccids)
            cnum_imsis_set = set(cnum_imsis)
            
            # Find all numbers in content that match ICCID/IMSI patterns
            # Include more variations to catch different formats
            all_iccids_in_content = set()
            
            # Find all 19-20 digit sequences
            for match in re.finditer(r'\d{19,20}', content):
                all_iccids_in_content.add(match.group())
            
            # Also check for quoted ICCIDs
            for match in re.finditer(r'"\d{19,20}"', content):
                all_iccids_in_content.add(match.group().strip('"'))
            
            # Also check for ICCIDs with possible separators
            for match in re.finditer(r'\d{5}[\s\-]?\d{5}[\s\-]?\d{5}[\s\-]?\d{4,5}', content):
                cleaned = match.group().replace(' ', '').replace('-', '')
                if len(cleaned) >= 19:
                    all_iccids_in_content.add(cleaned[:20])  # Take first 20 chars
            
            all_imsis_in_content = set()
            for match in re.finditer(r'\d{15}', content):
                all_imsis_in_content.add(match.group())
            
            # Find missing ICCIDs and IMSIs using set difference
            missing_iccids = cnum_iccids_set - all_iccids_in_content
            missing_imsis = cnum_imsis_set - all_imsis_in_content
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            self.log(f"  SIMODA validation processed {len(cnum_iccids)} ICCIDs and "
                    f"{len(cnum_imsis)} IMSIs in {processing_time:.3f} seconds")
            
            # Find line numbers for missing ICCIDs/IMSIs by searching the file
            if missing_iccids:
                missing_iccids_list = list(missing_iccids)
                for iccid in missing_iccids_list:
                    line_number = self._find_iccid_line_number(iccid, lines)
                    if line_number > 0:
                        error_msg = (
                            f"ERR: ICCID Data Issue "
                            f"(Expected: {iccid}) "
                            f"Not Present in SIMODA file"
                        )
                    else:
                        error_msg = (
                            f"ERR: ICCID Data Missing "
                            f"(Expected: {iccid}) "
                            f"Not Present in SIMODA file"
                        )
                    errors.append(error_msg)
            
            if missing_imsis:
                missing_imsis_list = list(missing_imsis)
                for imsi in missing_imsis_list:
                    line_number = self._find_imsi_line_number(imsi, lines)
                    if line_number > 0:
                        error_msg = (
                            f"ERR: IMSI Data Issue "
                            f"(Expected: {imsi}) "
                            f"Not Present in SIMODA file"
                            f"[Line: {line_number}]"
                        )
                    else:
                        error_msg = (
                            f"ERR: IMSI Data Missing "
                            f"(Expected: {imsi}) "
                            f"Not Present in SIMODA file"
                        )
                    errors.append(error_msg)
            
            if errors:
                error_msg = f"SIMODA validation failed - {len(errors)} issues found"
                return ValidationResult(False, error_msg, errors)
            
            return ValidationResult(True, "SIMODA validation passed - chip code, ICCIDs and IMSIs verified", [])
            
        except Exception as e:
            return ValidationResult(False, f"Error reading SIMODA file: {str(e)}", [])

    def _find_iccid_line_number(self, iccid: str, lines: List[str]) -> int:
        """Find the line number where an ICCID might be present with formatting issues"""
        variations = [
            iccid,
            f'"{iccid}"',
            f"'{iccid}'",
            iccid.replace('', ' ').strip(),
        ]
        
        for line_num, line in enumerate(lines, 1):
            for variation in variations:
                if variation in line:
                    return line_num
        
        # If not found, check for partial matches
        for line_num, line in enumerate(lines, 1):
            if iccid[:10] in line:
                return line_num
        
        return 0

    def _find_imsi_line_number(self, imsi: str, lines: List[str]) -> int:
        """Find the line number where an IMSI might be present with formatting issues"""
        variations = [
            imsi,
            f'"{imsi}"',
            f"'{imsi}'",
            imsi.replace('', ' ').strip(),
        ]
        
        for line_num, line in enumerate(lines, 1):
            for variation in variations:
                if variation in line:
                    return line_num
        
        # If not found, check for partial matches
        for line_num, line in enumerate(lines, 1):
            if imsi[:10] in line:
                return line_num
        
        return 0