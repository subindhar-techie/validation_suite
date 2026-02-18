"""
MNO File Validator - Excel report generation
"""

import os
import sys

# Add the modules path to sys.path
current_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
modules_path = os.path.join(project_root, 'modules')

if modules_path not in sys.path:
    sys.path.insert(0, modules_path)
    
import pandas as pd
import openpyxl
from pathlib import Path
from datetime import datetime
from typing import List, Dict
import re


class ExcelReportGenerator:
    """Handles Excel report generation for validation results"""
    
    def generate_excel_reports(self, excel_reports: List[Dict], parent_folder: str) -> Path:
        """Generate professional Excel reports for all batches"""
        if not excel_reports:
            raise ValueError("No validation data available for Excel reports")

        parent_name = Path(parent_folder).name  # Folder name only

        excel_filename = f"{parent_name}.xlsx"
        excel_path = Path(parent_folder) / excel_filename
        
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            # Create Executive Summary sheet
            self._create_executive_summary(writer, excel_reports)
            
            # Create Batch Details sheets
            self._create_batch_details(writer, excel_reports)

            # Create Error Details sheet
            self._create_error_details(writer, excel_reports)
        
        return excel_path

    
    def _create_executive_summary(self, writer, excel_reports: List[Dict]):
        """Create executive summary sheet with clickable batch numbers."""
        summary_data = []
        
        for report in excel_reports:
            # Count passed validations
            passed_count = sum(1 for result in report['validation_results'].values() if result[0])
            total_validations = len(report['validation_results'])
            
            summary_data.append({
                'Batch Number': report['batch_number'],
                'PO Number': report['po_number'],
                'SIM Quantity': report['sim_quantity'],
                'Overall Status': 'PASS' if report['all_passed'] else 'FAIL',
                'Passed Validations': passed_count,
                'Total Validations': total_validations,
            })
        
        if summary_data:
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Executive Summary', index=False)
            
            worksheet = writer.sheets['Executive Summary']
            
            # Auto-adjust columns width
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = (max_length + 2)
                worksheet.column_dimensions[column_letter].width = adjusted_width

            # ---------------------------------------------------------
            # ✅ ADD HYPERLINKS: Executive Summary → Batch Sheets
            # ---------------------------------------------------------
            for row_idx, report in enumerate(excel_reports, start=2):  # Row 2 onward
                batch_number = report['batch_number']
                sheet_name = f"Batch_{batch_number}"
                
                # Excel sheet name cannot exceed 31 characters
                if len(sheet_name) > 31:
                    sheet_name = sheet_name[:31]

                # Column A contains Batch Number
                cell = worksheet[f"A{row_idx}"]

                # Create internal hyperlink to the batch sheet
                cell.hyperlink = f"#{sheet_name}!A1"
                cell.style = "Hyperlink"
        
    def _create_batch_details(self, writer, excel_reports: List[Dict]):
        """Create detailed batch sheets with ALL errors for all validation types"""
        for report in excel_reports:
            sheet_name = f"Batch_{report['batch_number']}"
            if len(sheet_name) > 31:
                sheet_name = sheet_name[:31]
            
            batch_data = []
            validation_results = report['validation_results']
            
            for validation_name, (success, message, errors) in validation_results.items():
                status = "PASS" if success else "FAIL"
                error_count = len(errors)
                
                # Show ALL errors for ALL validation types
                if not success and errors:
                    if error_count <= 10:
                        all_errors = "\n".join([f"• {error}" for error in errors])
                        details = f"{message}\n\nAll Errors ({error_count}):\n{all_errors}"
                    else:
                        first_10_errors = "\n".join([f"• {error}" for error in errors[:10]])
                        details = f"{message}\n\nFirst 10 Errors (of {error_count} total):\n{first_10_errors}"
                else:
                    details = message
                
                batch_data.append({
                    'Validation Step': self._format_validation_name(validation_name),
                    'Status': status,
                    'Error Count': error_count,
                    'Details': details
                })
            
            batch_df = pd.DataFrame(batch_data)
            batch_df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Auto-adjust columns width and enable text wrapping
            worksheet = writer.sheets[sheet_name]
            
            # Set specific column widths
            worksheet.column_dimensions['A'].width = 25
            worksheet.column_dimensions['B'].width = 12
            worksheet.column_dimensions['C'].width = 12
            worksheet.column_dimensions['D'].width = 80
            
            # Enable text wrapping for all cells
            for row in worksheet.iter_rows():
                for cell in row:
                    cell.alignment = openpyxl.styles.Alignment(
                        wrap_text=True,
                        vertical='top',
                        horizontal='left'
                    )
            
            # Set specific row heights for rows with errors
            for idx, row_data in enumerate(batch_data, 2):
                if row_data['Error Count'] > 0:
                    error_count = row_data['Error Count']
                    base_height = 15
                    additional_height = min(error_count * 12, 150)
                    worksheet.row_dimensions[idx].height = base_height + additional_height
                else:
                    worksheet.row_dimensions[idx].height = 20
    
    # def _create_validation_details(self, writer, excel_reports: List[Dict]):
    #     """Create validation details across all batches"""
    #     validation_data = []
        
    #     for report in excel_reports:
    #         for validation_name, (success, message, errors) in report['validation_results'].items():
    #             validation_data.append({
    #                 'Batch Number': report['batch_number'],
    #                 'Validation Step': self._format_validation_name(validation_name),
    #                 'Status': 'PASS' if success else 'FAIL',
    #                 'Message': message,
    #                 'Error Count': len(errors),
    #                 'First Error': errors[0] if errors else 'N/A'
    #             })
        
    #     if validation_data:
    #         validation_df = pd.DataFrame(validation_data)
    #         validation_df.to_excel(writer, sheet_name='Validation Details', index=False)
    
    def _create_error_details(self, writer, excel_reports: List[Dict]):
        """Create detailed error breakdown"""
        error_data = []
        
        for report in excel_reports:
            for validation_name, (success, message, errors) in report['validation_results'].items():
                if not success and errors:
                    for error in errors:
                        error_data.append({
                            'Batch Number': report['batch_number'],
                            'Validation Step': self._format_validation_name(validation_name),
                            'Error Type': self._classify_error_type(error),
                            'Error Message': error,
                            # 'Line Number': self._extract_line_number(error),
                            # 'Severity': 'High' if 'Mismatch' in error else 'Medium'
                        })
        
        if error_data:
            error_df = pd.DataFrame(error_data)
            error_df.to_excel(writer, sheet_name='Error Details', index=False)
    
    def _format_validation_name(self, validation_name: str) -> str:
        """Format validation name for display"""
        names = {
            'ORIG_TRIG': 'ORIG_TRIG Validation',
            'HEADER': 'Header Validation',
            'DATA_FIELD': 'Data Field Validation',
            'CNUM_QUANTITY': 'CNUM Quantity Check',
            'SCM_QUANTITY': 'SCM Quantity Check',
            'SCM_STRUCTURE': 'SCM Validation',
            'SIMODA': 'SIMODA Validation'
        }
        return names.get(validation_name, validation_name)
    
    def _classify_error_type(self, error: str) -> str:
        """Classify error type"""
        error_lower = error.lower()
        if 'mismatch' in error_lower:
            return 'Data Mismatch'
        elif 'missing' in error_lower:
            return 'Missing Data'
        elif 'invalid' in error_lower or 'failed' in error_lower:
            return 'Validation Failed'
        elif 'length' in error_lower:
            return 'Length Issue'
        else:
            return 'General Error'
    
    def _extract_line_number(self, error: str) -> str:
        """Extract line number from error message"""
        line_match = re.search(r'Line\s+(\d+)', error)
        return line_match.group(1) if line_match else 'N/A'