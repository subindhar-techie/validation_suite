"""
MNO File Validator - Data field validation logic
"""
import re
import os
import sys
from typing import List, Tuple
from pathlib import Path

# Add the modules path to sys.path
current_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
modules_path = os.path.join(project_root, 'modules')

if modules_path not in sys.path:
    sys.path.insert(0, modules_path)

from .validation_base import BaseValidator, ValidationResult
from ..utils.file_utils import luhn_check

class DataFieldValidator(BaseValidator):
    """Handles data field validation between IN and CNUM files"""
    
    def validate_data_fields(self, in_file: Path, cnum_file: Path, 
                           sim_quantity: int) -> ValidationResult:
        """Validate ALL data fields match exactly between IN and CNUM files"""
        try:
            with open(in_file, 'r', encoding='utf-8') as f:
                in_lines = f.readlines()
            
            with open(cnum_file, 'r', encoding='utf-8') as f:
                cnum_lines = f.readlines()
            
            if len(in_lines) < 15 + sim_quantity:
                error_msg = (
                    f"IN file has only {len(in_lines)} lines, "
                    f"expected {15 + sim_quantity}"
                )
                return ValidationResult(False, error_msg, [])
            
            if len(cnum_lines) < 15 + sim_quantity:
                error_msg = (
                    f"CNUM file has only {len(cnum_lines)} lines, "
                    f"expected {15 + sim_quantity}"
                )
                return ValidationResult(False, error_msg, [])
            
            in_data_lines = in_lines[15:15+sim_quantity]
            cnum_data_lines = cnum_lines[15:15+sim_quantity]
            
            errors = []
            total_checked = 0
            
            for i in range(len(in_data_lines)):
                in_line = in_data_lines[i].strip()
                cnum_line = cnum_data_lines[i].strip()
                
                if not in_line or not cnum_line:
                    continue
                
                in_fields = in_line.split('\t')
                cnum_fields = cnum_line.split('\t')
                
                field_mapping = [
                    ("IMPU", 0), ("IMPI", 1), ("IMSI", 2), 
                    ("IMSI I", 3), ("ICCID", 4)
                ]
                
                line_errors = self._validate_data_line_fields(
                    in_fields, cnum_fields, field_mapping, i + 16
                )
                errors.extend(line_errors)
                
                pin_errors = self._validate_pin_fields(cnum_fields, i + 16)
                errors.extend(pin_errors)
                
                total_checked += 1
                
                if total_checked % 1000 == 0:
                    self.log(f"  Checked {total_checked}/{sim_quantity} lines...")
            
            if errors:
                error_msg = (
                    f"Data validation failed - {len(errors)} errors found "
                    f"in {total_checked} lines"
                )
                return ValidationResult(False, error_msg, errors[:50])
            
            success_msg = (
                f"All data fields validated successfully - "
                f"{total_checked} lines checked with no errors"
            )
            return ValidationResult(True, success_msg, [])
            
        except Exception as e:
            return ValidationResult(False, f"Error during data validation: {str(e)}", [])
    
    def _validate_data_line_fields(self, in_fields: List[str], 
                                 cnum_fields: List[str],
                                 field_mapping: List[tuple], 
                                 line_number: int) -> List[str]:
        """Validate fields in a single data line"""
        errors = []
        
        for field_name, idx in field_mapping:
            if len(in_fields) <= idx:
                errors.append(f"Line {line_number}: IN file missing {field_name} field")
                continue
            
            if len(cnum_fields) <= idx:
                errors.append(f"Line {line_number}: CNUM file missing {field_name} field")
                continue
            
            in_value = in_fields[idx]
            cnum_value = cnum_fields[idx]
            
            if field_name == "ICCID":
                iccid_errors = self._validate_iccid_fields(
                    in_value, cnum_value, line_number
                )
                errors.extend(iccid_errors)
            else:
                if in_value != cnum_value:
                    error_msg = (
                        f"ERR: {field_name} Data Mismatch "
                        f"(Expected: {cnum_value}) "
                        f"(Found: {in_value}) "
                        f"[Line: {line_number}]"
                    )
                    errors.append(error_msg)
        
        return errors
    
    def _validate_iccid_fields(self,
                            in_iccid: str,
                            cnum_iccid: str,
                            line_number: int) -> List[str]:
        """
        Validate ICCID fields:
        - CNUM ICCID must have 20 digits (includes Luhn digit)
        - Input ICCID may be 19 or 20 digits
        - First 19 digits must match
        - If input has 20 digits, it must match full CNUM ICCID (including Luhn)
        """
        errors = []

        # --- Clean up spaces or newlines ---
        in_iccid = in_iccid.strip()
        cnum_iccid = cnum_iccid.strip()

        # --- Check CNUM ICCID length ---
        if len(cnum_iccid) != 20:
            errors.append(
                f"ERR: CNUM ICCID Length Mismatch "
                f"(Expected: 20 digits) "
                f"(Found: {len(cnum_iccid)} digits) "
                f"[Line: {line_number}]"
            )
            return errors

        # --- Input must have at least 19 digits ---
        if len(in_iccid) < 19:
            errors.append(
                f"ERR: ICCID Length Mismatch "
                f"(Expected: 19 or 20 digits) "
                f"(Found: {len(in_iccid)} digits) "
                f"[Line: {line_number}]"
            )
            return errors

        cnum_prefix_19 = cnum_iccid[:19]

        # --- Case 1: Input ICCID is 19 digits ---
        if len(in_iccid) == 19:
            if in_iccid != cnum_prefix_19:
                errors.append(
                    f"ERR: ICCID Data Mismatch "
                    f"(Expected: {cnum_prefix_19}) "
                    f"(Found: {in_iccid}) "
                    f"[Line: {line_number}]"
                )

        # --- Case 2: Input ICCID is 20 digits (should match full CNUM) ---
        elif len(in_iccid) == 20:
            if in_iccid != cnum_iccid:
                errors.append(
                    f"ERR: ICCID Data Mismatch (20-digit input) "
                    f"(Expected full match: {cnum_iccid}) "
                    f"(Found: {in_iccid}) "
                    f"[Line: {line_number}]"
                )

        # --- Case 3: Input > 20 digits (invalid) ---
        else:
            errors.append(
                f"ERR: ICCID Length Invalid "
                f"(Expected: 19 or 20 digits) "
                f"(Found: {len(in_iccid)} digits) "
                f"[Line: {line_number}]"
            )

        return errors

    
    def _validate_pin_fields(self, cnum_fields: List[str], 
                           line_number: int) -> List[str]:
        """Validate PIN and PUK fields"""
        errors = []
        
        if len(cnum_fields) > 5 and cnum_fields[5] != "1234":
            error_msg = (
                f"ERR: PIN1 Data Mismatch "
                f"(Expected: 1234) "
                f"(Found: {cnum_fields[5]}) "
                f"[Line: {line_number}]"
            )
            errors.append(error_msg)
        
        if len(cnum_fields) > 7 and cnum_fields[7] != "4321":
            error_msg = (
                f"ERR: PIN2 Data Mismatch "
                f"(Expected: 4321) "
                f"(Found: {cnum_fields[7]}) "
                f"[Line: {line_number}]"
            )
            errors.append(error_msg)
        
        return errors