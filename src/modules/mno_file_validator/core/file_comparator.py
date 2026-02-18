"""
MNO File Comparator - Core validation logic (Refactored)
"""
import os
import sys
from typing import Dict, List, Tuple, Optional, Callable

# Add the modules path to sys.path to fix imports
current_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
modules_path = os.path.join(project_root, 'modules')

if modules_path not in sys.path:
    sys.path.insert(0, modules_path)

# Now use absolute imports
# Change from:
from mno_file_validator.core.simoda_validator import SIMODAValidator
from mno_file_validator.core.validation_base import BaseValidator
# etc.

# To:
from .simoda_validator import SIMODAValidator
from .validation_base import BaseValidator
from .header_validator import HeaderValidator
from .data_field_validator import DataFieldValidator
from .scm_validator import SCMValidator
from ..utils.excel_report_generator import ExcelReportGenerator
from ..utils.file_utils import (
    parse_filename, find_matching_files, find_output_files,
    extract_header_info, validate_quantity
)

class MNOFileComparator(BaseValidator):
    """Main file comparator class with all validation logic"""
    
    def __init__(self):
        super().__init__()
        self.chip_type = "SAMSUNG 340"
        self.excel_reports = []
        
        # Initialize validators
        self.header_validator = HeaderValidator()
        self.data_field_validator = DataFieldValidator()
        self.scm_validator = SCMValidator()
        self.simoda_validator = SIMODAValidator()
        self.excel_generator = ExcelReportGenerator()
    
    def set_log_callback(self, callback: Callable):
        """Set the logging callback for all validators"""
        super().set_log_callback(callback)
        self.header_validator.set_log_callback(callback)
        self.data_field_validator.set_log_callback(callback)
        self.scm_validator.set_log_callback(callback)
        self.simoda_validator.set_log_callback(callback)
    
    def set_chip_type(self, chip_type: str):
        """Set the chip type for relevant validators"""
        self.chip_type = chip_type
        self.scm_validator.set_chip_type(chip_type)
        self.simoda_validator.set_chip_type(chip_type)
    
    def clear_tracking(self):
        """Clear batch tracking data"""
        super().clear_tracking()
        self.scm_validator.clear_tracking()
        self.excel_reports.clear()
    
    def run_validation(self, parent_folder: str) -> Tuple[int, int]:
        """Run the complete validation process"""
        matches = find_matching_files(parent_folder)
        self.log(f"Found {len(matches)} IN file and OUT folder pairs")
        
        if not matches:
            self.log("ERROR: No matching IN files and OUT folders found", "ERROR")
            return 0, 0
        
        success_count = 0
        failure_count = 0
        
        for batch_index, match in enumerate(matches):
            batch_success = self.process_batch(batch_index, match)
            if batch_success:
                success_count += 1
            else:
                failure_count += 1
        
        return success_count, failure_count
    
    def process_batch(self, batch_index: int, match: Dict) -> bool:
        """Process a single batch of files"""
        try:
            batch_info = parse_filename(match['in_file'].name)
            batch_number = batch_info.get('batch_number', 'Unknown') if batch_info else 'Unknown'
            po_number = batch_info.get('po_number', 'Unknown') if batch_info else 'Unknown'
            
            self.log(f"\n{'='*60}")
            self.log(f"Processing Batch {batch_index+1}: "
                    f"Batch No: {batch_number}, PO: {po_number}")
            self.log(f"{'='*60}")
            self.log(f"INPUT: {match['in_file'].name}")
            self.log(f"OUTPUT: {match['out_folder'].name}")

            self.current_in_filename = match['in_file'].name
        
                        
            # Find output files
            output_files = find_output_files(match['out_folder'], match['suffix'])
            
            # Check for missing files
            missing_files = [
                name for name, path in output_files.items() 
                if path is None
            ]
            if missing_files:
                self.log(f"❌ FAIL: Missing output files: {', '.join(missing_files)}", 
                        "ERROR")
                self.excel_reports.append({
                    'batch_number': batch_number,
                    'po_number': po_number,
                    'sim_quantity': 0,
                    'validation_results': self._create_validation_results(False, "Missing output files"),
                    'all_passed': False
                })
                return False
            
            # Extract header information
            header_info = extract_header_info(match['in_file'])
            sim_quantity = header_info.get('sim_quantity')
            po_number_from_header = header_info.get('po_number')
            batch_number_from_header = header_info.get('batch_number')
            sku = header_info.get('sku')
            
            if not sim_quantity:
                self.log("❌ FAIL: Could not extract SIM Quantity from IN file", "ERROR")
                self.excel_reports.append({
                    'batch_number': batch_number,
                    'po_number': po_number,
                    'sim_quantity': 0,
                    'validation_results': self._create_validation_results(False, "Missing SIM quantity"),
                    'all_passed': False
                })
                return False
            
            if not batch_number_from_header:
                self.log("❌ FAIL: Could not extract Batch Number from IN file", "ERROR")
                self.excel_reports.append({
                    'batch_number': batch_number,
                    'po_number': po_number,
                    'sim_quantity': sim_quantity,
                    'validation_results': self._create_validation_results(False, "Missing batch number"),
                    'all_passed': False
                })
                return False
            
            self.log(f"SIM Quantity: {sim_quantity}")
            self.log(f"PO Number: {po_number_from_header}")
            self.log(f"Batch Number: {batch_number_from_header}")
            self.log(f"SKU: {sku}")
            
            # Extract CNUM ICCIDs and IMSIs for SCM and SIMODA validation
            cnum_iccids, cnum_imsis = self.extract_cnum_iccids_imsis(output_files['CNUM'], sim_quantity)
            
            # Run all validations
            validation_results = {}
            
            # 1. ORIG_TRIG Validation
            self.log(f"\n1. ORIG_TRIG Validation:")
            orig_trig_result = self.validate_orig_trig(output_files['ORIG_TRIG'], output_files)
            validation_results['ORIG_TRIG'] = orig_trig_result.to_tuple()
            self._log_validation_result("ORIG_TRIG", orig_trig_result.to_tuple())
            
            # 2. Header Validation
            self.log(f"\n2. Header Validation:")
            header_result = self.header_validator.validate_headers(match['in_file'], output_files['CNUM'])
            validation_results['HEADER'] = header_result.to_tuple()
            self._log_validation_result("HEADER", header_result.to_tuple())
            
            # 3. Data Field Validation
            self.log(f"\n3. Data Field Validation:")
            data_result = self.data_field_validator.validate_data_fields(
                match['in_file'], output_files['CNUM'], sim_quantity
            )
            validation_results['DATA_FIELD'] = data_result.to_tuple()
            self._log_validation_result("DATA_FIELD", data_result.to_tuple())
            
            # 4. CNUM Quantity Validation
            self.log(f"\n4. CNUM Quantity Validation:")
            cnum_quantity_success, cnum_quantity_message = validate_quantity(
                output_files['CNUM'], sim_quantity, 15
            )
            cnum_quantity_result = (cnum_quantity_success, cnum_quantity_message, [])
            validation_results['CNUM_QUANTITY'] = cnum_quantity_result
            self._log_validation_result("CNUM_QUANTITY", cnum_quantity_result)
            
            # 5. SCM Quantity Validation
            self.log(f"\n5. SCM Quantity Validation:")
            scm_quantity_success, scm_quantity_message = validate_quantity(
                output_files['SCM'], sim_quantity, 1
            )
            scm_quantity_result = (scm_quantity_success, scm_quantity_message, [])
            validation_results['SCM_QUANTITY'] = scm_quantity_result
            self._log_validation_result("SCM_QUANTITY", scm_quantity_result)
            
            # 6. SCM Validation (with ICCID/IMSI validation)
            self.log(f"\n6. SCM Validation:")
            scm_result = self.scm_validator.validate_scm_structure(
                output_files['SCM'], sim_quantity, po_number_from_header,
                batch_number_from_header, sku, batch_index,
                cnum_iccids, cnum_imsis
            )
            validation_results['SCM_STRUCTURE'] = scm_result.to_tuple()
            self._log_validation_result("SCM_STRUCTURE", scm_result.to_tuple())
            
            # 7. SIMODA Validation
            self.log(f"\n7. SIMODA Validation:")
            simoda_result = self.simoda_validator.validate_simoda_file(
                output_files['SIMODA'], cnum_iccids, cnum_imsis
            )
            validation_results['SIMODA'] = simoda_result.to_tuple()
            self._log_validation_result("SIMODA", simoda_result.to_tuple())
            
            # Determine overall result
            all_passed = all(result[0] for result in validation_results.values())
            
            # Store batch data for Excel report
            self.excel_reports.append({
                'batch_number': batch_number_from_header,
                'po_number': po_number_from_header,
                'sim_quantity': sim_quantity,
                'validation_results': validation_results,
                'all_passed': all_passed
            })
            
            # Final batch result
            self.log(f"\n{'='*60}")
            if all_passed:
                self.log(f"✅ BATCH {batch_number}: ALL VALIDATIONS PASSED", "SUCCESS")
                return True
            else:
                self.log(f"❌ BATCH {batch_number}: VALIDATION FAILED", "ERROR")
                return False
            
        except Exception as e:
            self.log(f"❌ Error processing batch: {str(e)}", "ERROR")
            return False
        
    def extract_key_from_in_filename(self, filename: str) -> str:
        filename = filename.replace(".txt", "").replace(".cps", "")
        if filename.startswith("IN_"):
            filename = filename[3:]  # remove IN_
        return filename
            
    
    def validate_orig_trig(self, orig_trig_file, output_files):
        """Validate ORIG_TRIG contains correct filenames derived from IN file
        and give detailed difference output when mismatch happens.
        """

        from .validation_base import ValidationResult
        import os

        if not orig_trig_file or not orig_trig_file.exists():
            return ValidationResult(False, "ORIG_TRIG file not found", [])

        # Get IN filename
        in_filename = self.current_in_filename

        # Build key
        key = in_filename.replace(".txt", "").replace(".cps", "")
        if key.startswith("IN_"):
            key = key[3:]

        # Expected filenames
        expected_files = {
            "CNUM":   f"CNUM_{key}.txt",
            "SCM":    f"SCM_{key}.txt",
            "SIMODA": f"SIMODA_{key}.cps"
        }

        # Read ORIG_TRIG
        try:
            with open(orig_trig_file, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            return ValidationResult(False, f"Error reading ORIG_TRIG file: {str(e)}", [])

        # Process lines
        orig_lines = [ln.strip() for ln in content.splitlines()]
        orig_lower = [ln.lower() for ln in orig_lines]

        missing = []
        detailed_errors = []

        for section, expected in expected_files.items():
            expected_lower = expected.lower()

            # Check if present exactly
            found = any(expected_lower in line for line in orig_lower)

            if not found:
                missing.append(expected)

                # Find close matches: same prefix (CNUM_, SCM_, SIMODA_)
                prefix = section.lower()
                close_matches = [ln for ln in orig_lines if ln.lower().startswith(prefix)]

                error_msg = f"""
    Expected: {expected}
    Found lines with same prefix ({section}):
        { close_matches if close_matches else 'None found' }
    Full ORIG_TRIG lines:
        {orig_lines}
                """

                detailed_errors.append(error_msg.strip())

        if missing:
            msg = (
                "ORIG_TRIG missing required references:\n"
                + "\n".join([f"• {m}" for m in missing])
            )

            return ValidationResult(False, msg, detailed_errors)

        return ValidationResult(True, "ORIG_TRIG contains all required filenames", [])
    
    def extract_cnum_iccids_imsis(self, cnum_file, sim_quantity):
        """Extract ICCIDs and IMSIs from CNUM file"""
        try:
            with open(cnum_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            data_lines = lines[15:15+sim_quantity]
            
            iccids = []
            imsis = []
            
            for line in data_lines:
                fields = line.strip().split('\t')
                if len(fields) >= 5:
                    iccids.append(fields[4])
                    imsis.append(fields[2])
            
            return iccids, imsis
            
        except Exception as e:
            return [], []
    
    def generate_excel_reports(self, parent_folder: str):
        """Generate professional Excel reports for all batches"""
        try:
            excel_path = self.excel_generator.generate_excel_reports(self.excel_reports, parent_folder)
            self.log(f"✅ Excel report generated: {excel_path}", "SUCCESS")
            return excel_path
        except Exception as e:
            self.log(f"❌ Error generating Excel report: {str(e)}", "ERROR")
            raise
    
    def _create_validation_results(self, success: bool, message: str) -> Dict:
        """Create validation results structure for failed batches"""
        return {
            'ORIG_TRIG': (success, message, []),
            'HEADER': (success, message, []),
            'DATA_FIELD': (success, message, []),
            'CNUM_QUANTITY': (success, message, []),
            'SCM_QUANTITY': (success, message, []),
            'SCM_STRUCTURE': (success, message, []),
            'SIMODA': (success, message, [])
        }
    
    def _log_validation_result(self, validation_name: str, result: Tuple[bool, str, List[str]]):
        """Log validation result with proper formatting"""
        success, message, errors = result
        if success:
            self.log(f"✅ PASS: {message}", "SUCCESS")
        else:
            self.log(f"❌ FAIL: {message}", "ERROR")
            for error in errors[:3]:
                self.log(f"   - {error}", "ERROR")