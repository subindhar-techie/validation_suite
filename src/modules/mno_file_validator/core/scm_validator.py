"""
MNO File Validator - SCM file validation logic
"""
import re
import os
import sys
from typing import List, Tuple, Set, Optional, Callable, Dict
from pathlib import Path
from collections import defaultdict

# Add the modules path to sys.path
current_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
modules_path = os.path.join(project_root, 'modules')

if modules_path not in sys.path:
    sys.path.insert(0, modules_path)

from .validation_base import BaseValidator, ValidationResult


class ErrorGrouper:
    """Groups similar errors together for cleaner reporting"""
    
    def __init__(self):
        self.error_groups: Dict[str, List[int]] = {}
        
    def add_error(self, error_type: str, expected: str, found: str, line_num: int):
        """Add an error to the appropriate group"""
        # Create a key that uniquely identifies this error pattern
        group_key = f"{error_type}|{expected}|{found}"
        
        if group_key not in self.error_groups:
            self.error_groups[group_key] = []
        self.error_groups[group_key].append(line_num)
    
    def get_grouped_errors(self) -> List[Tuple[str, str, str, List[int]]]:
        """Get list of grouped errors with line ranges"""
        grouped = []
        for group_key, line_nums in self.error_groups.items():
            parts = group_key.split('|')
            error_type = parts[0]
            expected = parts[1]
            found = parts[2]
            
            # Sort line numbers
            line_nums.sort()
            
            # Create line range string
            line_range = self._format_line_range(line_nums)
            
            grouped.append((error_type, expected, found, line_nums, line_range))
        
        # Sort by first line number
        grouped.sort(key=lambda x: x[3][0])
        return grouped
    
    def _format_line_range(self, line_nums: List[int]) -> str:
        """Format line numbers into a readable range"""
        if not line_nums:
            return ""
        
        if len(line_nums) == 1:
            return f"Line {line_nums[0]}"
        
        # Find consecutive ranges
        ranges = []
        start = line_nums[0]
        end = line_nums[0]
        
        for i in range(1, len(line_nums)):
            if line_nums[i] == end + 1:
                end = line_nums[i]
            else:
                if start == end:
                    ranges.append(f"Line {start}")
                else:
                    ranges.append(f"Lines {start}-{end}")
                start = line_nums[i]
                end = line_nums[i]
        
        # Add the last range
        if start == end:
            ranges.append(f"Line {start}")
        else:
            ranges.append(f"Lines {start}-{end}")
        
        if len(ranges) == 1:
            return ranges[0]
        elif len(ranges) == 2:
            return f"{ranges[0]} and {ranges[1]}"
        else:
            return f"{ranges[0]}, {ranges[1]}, and {len(ranges)-2} more"


class SCMValidator(BaseValidator):
    """Handles SCM file structure validation"""
    
    def __init__(self, log_callback: Optional[Callable] = None):
        super().__init__(log_callback)
        self.chip_type = "SAMSUNG 340"
    
    def set_chip_type(self, chip_type: str):
        """Set the chip type"""
        self.chip_type = chip_type

    def _calculate_expected_msn(self, start_msn: str, record_position: int) -> str:
        """Calculate expected MSN based on start MSN and record position (changes every 500 records)"""
        # Parse the starting MSN (e.g., "A001")
        letter, number = self.parse_msn_serial(start_msn)
        if not letter or not number:
            return start_msn
        
        # Calculate how many 500-record blocks we've passed
        blocks_passed = record_position // 500
        
        # Calculate the new MSN
        new_number = number + blocks_passed
        
        # Handle overflow (A999 -> B001, etc.)
        if new_number > 999:
            extra_blocks = new_number // 1000
            remaining = new_number % 1000
            if remaining == 0:
                remaining = 1
            
            new_letter_ord = ord(letter) + extra_blocks
            if new_letter_ord > ord('Z'):
                # Wrap around if beyond Z
                cycles = (new_letter_ord - ord('A')) // 26
                new_letter_ord = ord('A') + ((new_letter_ord - ord('A')) % 26)
            
            letter = chr(new_letter_ord)
            number = remaining
        else:
            number = new_number
        
        return f"{letter}{number:03d}"    
    
    def validate_scm_structure(self, scm_file: Path, sim_quantity: int, 
                            po_number: str, batch_number: str, 
                            sku: str, batch_index: int,
                            cnum_iccids: List[str], cnum_imsis: List[str]) -> ValidationResult:
        """Validate SCM file structure with proper MSN and MSC format"""
        try:
            with open(scm_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            data_lines = lines[1:1+sim_quantity]
            
            if len(data_lines) != sim_quantity:
                error_msg = (
                    f"SCM line count mismatch: expected {sim_quantity} "
                    f"data lines, found {len(data_lines)}"
                )
                return ValidationResult(False, error_msg, [])
            
            processed_sku = self.process_sku_for_msn(sku) or "00000000"
            po_last_3 = (
                po_number[-3:] 
                if po_number and len(po_number) >= 3 
                else "000"
            )
            
            errors = []
            expected_urt = "URT"
            msc_values = set()
            
            # Get starting MSN and MSC for this batch
            expected_start_msn, expected_msc = self._get_starting_serials(batch_index)
            
            # FIX: Calculate MSN based on record position within batch
            current_expected_msn = expected_start_msn
            last_msn_in_batch = None
            
            for i, line in enumerate(data_lines, 2):
                fields = line.strip().split('\t')
                if len(fields) < 8:
                    errors.append(
                        f"Line {i}: Insufficient columns in SCM file, "
                        f"expected 8, found {len(fields)}"
                    )
                    continue
                
                # Extract all fields from SCM file
                skucode = fields[0] if len(fields) > 0 else ""
                batchno = fields[4]
                ponum = fields[5]
                vendercode = fields[6] if len(fields) > 6 else ""
                msn = fields[1]
                msc = fields[7]
                
                # Extract ICCID and IMSI from SCM file
                scm_iccid = fields[2] if len(fields) > 2 else ""
                scm_imsi = fields[3] if len(fields) > 3 else ""
                
                # Validate SKUCODE
                if skucode != sku:
                    errors.append(
                        f"ERR: SKUCODE Mismatch "
                        f"(Expected: {sku}) "
                        f"(Found: {skucode}) "
                        f"[Line: {i}]"
                    )
                
                # Validate basic fields
                basic_errors = self._validate_scm_basic_fields(
                    batchno, ponum, batch_number, po_number, i
                )
                errors.extend(basic_errors)
                
                # FIX: Calculate expected MSN based on position (every 500 records change)
                record_position_in_batch = i - 2  # Line numbers start from 2
                expected_msn_for_record = self._calculate_expected_msn(
                    expected_start_msn, record_position_in_batch
                )
                
                # Validate MSN structure
                msn_errors, last_msn_in_batch = self._validate_msn_structure(
                    msn, processed_sku, po_last_3, expected_urt,
                    expected_msn_for_record, i
                )
                errors.extend(msn_errors)
                
                # Validate MSC structure
                msc_errors, _ = self._validate_msc_structure(
                    msc, processed_sku, po_last_3, expected_urt,
                    expected_msc, msc_values, i
                )
                errors.extend(msc_errors)
                
                # Validate ICCID and IMSI in SCM file
                iccid_imsi_errors = self._validate_scm_iccid_imsi(
                    scm_iccid, scm_imsi, i
                )
                errors.extend(iccid_imsi_errors)
                
                # Cross-validate ICCID and IMSI between SCM and CNUM
                if i-2 < len(cnum_iccids) and i-2 < len(cnum_imsis):
                    expected_iccid = cnum_iccids[i-2]
                    expected_imsi = cnum_imsis[i-2]
                    
                    cross_validation_errors = self._validate_scm_cnum_cross_reference(
                        scm_iccid, scm_imsi, expected_iccid, expected_imsi, i
                    )
                    errors.extend(cross_validation_errors)
            
            # Store tracking data
            self.batch_tracking[f"batch_{batch_index}"] = {
                'last_msn': last_msn_in_batch,
                'last_msc': expected_msc
            }
            
            # Note: Removed the "Multiple MSCs found in batch" error as per requirements
            
            if errors:
                error_msg = (
                    f"SCM Validation failed - "
                    f"{len(errors)} errors found"
                )
                return ValidationResult(False, error_msg, errors)
            
            msc_display = list(msc_values)[0] if msc_values else 'N/A'
            success_msg = (
                f"SCM structure validated - MSN blocks from {expected_start_msn} to {last_msn_in_batch}, MSC: {msc_display}"
            )
            return ValidationResult(True, success_msg, [])
            
        except Exception as e:
            return ValidationResult(False, f"Error during SCM validation: {str(e)}", [])
                
    def _get_starting_serials(self, batch_index: int) -> Tuple[str, str]:
        """Get starting MSN and MSC serials for batch"""
        if batch_index == 0:
            return "A001", "MC01"
        else:
            prev_batch_key = f"batch_{batch_index-1}"
            if prev_batch_key in self.batch_tracking:
                prev_data = self.batch_tracking[prev_batch_key]
                # Get the last MSN from previous batch and calculate next starting point
                last_msn_prev = prev_data.get('last_msn', 'A001')
                expected_start_msn = self.get_next_msn_serial(last_msn_prev)
                expected_msc = self.get_next_msc_serial(prev_data.get('last_msc'))
                return expected_start_msn, expected_msc
            else:
                # Calculate starting MSN based on batch index (each batch has multiple MSN blocks)
                base_msn = "A001"
                for i in range(batch_index):
                    # Each batch advances MSN by the number of 500-record blocks it contains
                    # Assuming each batch has sim_quantity records
                    blocks_in_batch = (500 + 499) // 500  # Ceiling division
                    for block in range(blocks_in_batch):
                        base_msn = self.get_next_msn_serial(base_msn)
                return base_msn, "MC01"
    
    def _validate_scm_basic_fields(self, batchno: str, ponum: str,
                                 batch_number: str, po_number: str, 
                                 line_num: int) -> List[str]:
        """Validate basic SCM fields"""
        errors = []
        
        if batchno != batch_number:
            error_msg = (
                f"ERR: Batch Number Data Mismatch "
                f"(Expected: {batch_number}) "
                f"(Found: {batchno}) "
                f"[Line: {line_num}]"
            )
            errors.append(error_msg)
        
        if ponum != po_number:
            error_msg = (
                f"ERR: PO Number Data Mismatch "
                f"(Expected: {po_number}) "
                f"(Found: {ponum}) "
                f"[Line: {line_num}]"
            )
            errors.append(error_msg)
        
        return errors
    
    def _validate_msn_structure(self, msn: str, processed_sku: str,
                            po_last_3: str, expected_urt: str,
                            current_expected_msn: str, 
                            line_num: int) -> Tuple[List[str], str]:
        """Validate MSN structure with strict sequential checking"""
        errors = []
        last_msn = None
        
        if len(msn) != 18:
            error_msg = (
                f"ERR: MSN Length Mismatch "
                f"(Expected: 18 characters) "
                f"(Found: {len(msn)} characters) "
                f"[Line: {line_num}]"
            )
            errors.append(error_msg)
        else:
            msn_urt = msn[:3]
            msn_sku = msn[3:11]
            msn_po = msn[11:14]
            msn_serial = msn[14:]
            
            # STRICT VALIDATION - Remove empty checks
            if msn_urt != expected_urt:
                error_msg = (
                    f"ERR: MSN URT Code Mismatch "
                    f"(Expected: {expected_urt}) "
                    f"(Found: {msn_urt}) "
                    f"[Line: {line_num}]"
                )
                errors.append(error_msg)
            
            # REMOVED EMPTY CHECK: Always validate SKU
            if msn_sku != processed_sku:
                error_msg = (
                    f"ERR: MSN SKU Part Mismatch "
                    f"(Expected: {processed_sku}) "
                    f"(Found: {msn_sku}) "
                    f"[Line: {line_num}]"
                )
                errors.append(error_msg)
            
            # REMOVED EMPTY CHECK: Always validate PO
            if msn_po != po_last_3:
                error_msg = (
                    f"ERR: MSN PO Part Mismatch "
                    f"(Expected: {po_last_3}) "
                    f"(Found: {msn_po}) "
                    f"[Line: {line_num}]"
                )
                errors.append(error_msg)
            
            if not re.match(r'^[A-Z]\d{3}$', msn_serial):
                error_msg = (
                    f"ERR: MSN Serial Format Invalid "
                    f"(Expected: Format like A001) "
                    f"(Found: {msn_serial}) "
                    f"[Line: {line_num}]"
                )
                errors.append(error_msg)
            else:
                # ADD STRICT SEQUENTIAL VALIDATION
                if msn_serial != current_expected_msn:
                    error_msg = (
                        f"ERR: MSN Sequence Mismatch "
                        f"(Expected: {current_expected_msn}) "
                        f"(Found: {msn_serial}) "
                        f"[Line: {line_num}]"
                    )
                    errors.append(error_msg)
            
            last_msn = msn_serial
        
        return errors, last_msn

    def _validate_msc_structure(self, msc: str, processed_sku: str,
                            po_last_3: str, expected_urt: str,
                            expected_msc: str, msc_values: set,
                            line_num: int) -> Tuple[List[str], str]:
        """Validate MSC structure with strict consistency"""
        errors = []
        last_msc = None
        
        if len(msc) != 18:
            error_msg = (
                f"ERR: MSC Length Mismatch "
                f"(Expected: 18 characters) "
                f"(Found: {len(msc)} characters) "
                f"[Line: {line_num}]"
            )
            errors.append(error_msg)
        else:
            msc_urt = msc[:3]
            msc_sku = msc[3:11]
            msc_po = msc[11:14]
            msc_mc = msc[14:]
            
            # STRICT VALIDATION - Remove empty checks
            if msc_urt != expected_urt:
                error_msg = (
                    f"ERR: MSC URT Code Mismatch "
                    f"(Expected: {expected_urt}) "
                    f"(Found: {msc_urt}) "
                    f"[Line: {line_num}]"
                )
                errors.append(error_msg)
            
            # REMOVED EMPTY CHECK: Always validate SKU
            if msc_sku != processed_sku:
                error_msg = (
                    f"ERR: MSC SKU Part Mismatch "
                    f"(Expected: {processed_sku}) "
                    f"(Found: {msc_sku}) "
                    f"[Line: {line_num}]"
                )
                errors.append(error_msg)
            
            # REMOVED EMPTY CHECK: Always validate PO
            if msc_po != po_last_3:
                error_msg = (
                    f"ERR: MSC PO Part Mismatch "
                    f"(Expected: {po_last_3}) "
                    f"(Found: {msc_po}) "
                    f"[Line: {line_num}]"
                )
                errors.append(error_msg)
            
            if not re.match(r'^M[A-Z]\d{2}$', msc_mc):
                error_msg = (
                    f"ERR: MSC Format Invalid "
                    f"(Expected: Format like MC01) "
                    f"(Found: {msc_mc}) "
                    f"[Line: {line_num}]"
                )
                errors.append(error_msg)
            else:
                # STRICT MSC VALIDATION - Always check against expected_msc from validation logic
                # Use expected_msc consistently for ALL lines, not the first value found
                if msc_mc != expected_msc:
                    error_msg = (
                        f"ERR: MSC Sequence Mismatch "
                        f"(Expected: {expected_msc}) "
                        f"(Found: {msc_mc}) "
                        f"[Line: {line_num}]"
                    )
                    errors.append(error_msg)
                
                msc_values.add(msc_mc)
            
            last_msc = msc_mc
        
        return errors, last_msc
    
    def _validate_scm_iccid_imsi(self, scm_iccid: str, scm_imsi: str, 
                               line_num: int) -> List[str]:
        """Validate ICCID and IMSI fields in SCM file"""
        errors = []
        
        # Validate ICCID
        if not scm_iccid:
            errors.append(f"Line {line_num}: ICCID field is empty in SCM file")
        else:
            if len(scm_iccid) not in [19, 20]:
                errors.append(
                    f"ERR: SCM ICCID Length Invalid "
                    f"(Expected: 19 or 20 digits) "
                    f"(Found: {len(scm_iccid)} digits) "
                    f"[Line: {line_num}]"
                )
            
            if not scm_iccid.isdigit():
                errors.append(
                    f"ERR: SCM ICCID Contains Non-Digit Characters "
                    f"(Value: {scm_iccid}) "
                    f"[Line: {line_num}]"
                )
        
        # Validate IMSI
        if not scm_imsi:
            errors.append(f"Line {line_num}: IMSI field is empty in SCM file")
        else:
            if len(scm_imsi) != 15:
                errors.append(
                    f"ERR: SCM IMSI Length Invalid "
                    f"(Expected: 15 digits) "
                    f"(Found: {len(scm_imsi)} digits) "
                    f"[Line: {line_num}]"
                )
            
            if not scm_imsi.isdigit():
                errors.append(
                    f"ERR: SCM IMSI Contains Non-Digit Characters "
                    f"(Value: {scm_imsi}) "
                    f"[Line: {line_num}]"
                )
        
        return errors

    def _validate_scm_cnum_cross_reference(self, scm_iccid: str, scm_imsi: str,
                                         cnum_iccid: str, cnum_imsi: str,
                                         line_num: int) -> List[str]:
        """Cross-validate ICCID and IMSI between SCM and CNUM files"""
        errors = []
        
        # Compare ICCID between SCM and CNUM - Compare all 20 digits
        if scm_iccid and cnum_iccid:
            # Compare the complete ICCID (all 20 digits)
            if scm_iccid != cnum_iccid:
                errors.append(
                    f"ERR: ICCID Mismatch between SCM and CNUM "
                    f"(Expected: {cnum_iccid}) "
                    f"(Found: {scm_iccid}) "
                    f"[Line: {line_num}]"
                )
        
        # Compare IMSI between SCM and CNUM
        if scm_imsi and cnum_imsi and scm_imsi != cnum_imsi:
            errors.append(
                f"ERR: IMSI Mismatch between SCM and CNUM "
                f"(Expected: {cnum_imsi}) "
                f"(Found: {scm_imsi}) "
                f"[Line: {line_num}]"
            )
        
        return errors
    
    def process_sku_for_msn(self, sku: str) -> str:
        """Process SKU for MSN/MSC format"""
        if not sku:
            return ""
        sku_9_digit = sku.zfill(9)
        return sku_9_digit[1:] if len(sku_9_digit) == 9 else sku_9_digit
    
    def parse_msn_serial(self, msn_serial: str) -> Tuple[Optional[str], Optional[int]]:
        """Parse MSN serial (A001) to get letter and number"""
        if (len(msn_serial) == 4 and 
            msn_serial[0].isalpha() and 
            msn_serial[1:].isdigit()):
            return msn_serial[0], int(msn_serial[1:])
        return None, None
    
    def get_next_msn_serial(self, current_serial: str) -> str:
        """Get the next MSN serial in sequence"""
        if not current_serial:
            return "A001"
        
        letter, number = self.parse_msn_serial(current_serial)
        if not letter or not number:
            return "A001"
        
        if number < 999:
            return f"{letter}{number+1:03d}"
        else:
            next_letter = chr(ord(letter) + 1)
            if next_letter > 'Z':
                return "A001"
            return f"{next_letter}001"
    
    def parse_msc_serial(self, msc_serial: str) -> Tuple[Optional[str], Optional[int]]:
        """Parse MSC serial (MC01) to get prefix and number"""
        if (len(msc_serial) == 4 and 
            msc_serial[:2].isalpha() and 
            msc_serial[2:].isdigit()):
            return msc_serial[:2], int(msc_serial[2:])
        return None, None
    
    def get_next_msc_serial(self, current_msc: str) -> str:
        """Get the next MSC serial in sequence"""
        if not current_msc:
            return "MC01"
        
        prefix, number = self.parse_msc_serial(current_msc)
        if not prefix or not number:
            return "MC01"
        
        if number < 99:
            return f"{prefix}{number+1:02d}"
        else:
            first_letter = prefix[0]
            second_letter = prefix[1]
            
            if second_letter < 'Z':
                next_second_letter = chr(ord(second_letter) + 1)
                return f"{first_letter}{next_second_letter}01"
            else:
                next_first_letter = (
                    chr(ord(first_letter) + 1) 
                    if first_letter < 'Z' 
                    else 'A'
                )
                return f"{next_first_letter}A01"
