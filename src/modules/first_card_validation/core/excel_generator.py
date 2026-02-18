import os
import re
import win32com.client as win32
from openpyxl import Workbook
from openpyxl.styles import Border, Side, PatternFill, Font, Alignment
from openpyxl.utils import get_column_letter
from openpyxl.drawing.image import Image as ExcelImage
import getpass
from datetime import datetime

# def protect_excel_file(filepath, password):
#     excel = win32.gencache.EnsureDispatch('Excel.Application')
#     excel.DisplayAlerts = False
#     wb = excel.Workbooks.Open(filepath)
#     wb.Password = password  # Set open password
#     wb.Save()
#     wb.Close()
#     excel.Quit()

def insert_image(ws, image_path, cell_location):
    try:
        print(f"Inserting image at {cell_location} from path: {image_path}")
        img = ExcelImage(image_path)  # For openpyxl image insertion
        img.width = 300  # Set image width (optional)
        img.height = 200  # Set image height (optional)
        ws.add_image(img, cell_location)  # Insert the image into the worksheet
        print(f"Image inserted at {cell_location}")
    except Exception as e:
        print(f"Error inserting image: {e}")



def save_report(wb, ml_path, pcom_path, iccid=None):
    try:
        # Create final report name using ICCID if available
        if iccid:
            # Clean ICCID for filename (remove any prefixes)
            clean_iccid = str(iccid).replace("ICCID_", "").strip()
            report_name = f"{clean_iccid}_validation_report.xlsx"
        else:
            # Fallback: Extract base filename (e.g., "Log_98195808050716183064")
            base_name = os.path.splitext(os.path.basename(ml_path))[0]

            # Remove "Log_" prefix if present
            if base_name.lower().startswith("log_"):
                raw_number = base_name[4:]
            else:
                raw_number = base_name

            # --- Pairwise swap each 2 digits ---
            swapped_number = ""
            for i in range(0, len(raw_number), 2):
                if i + 1 < len(raw_number):
                    swapped_number += raw_number[i+1] + raw_number[i]
                else:
                    swapped_number += raw_number[i]  # last digit if odd length

            # Create final report name
            report_name = f"{swapped_number}_Validation_Report.xlsx"

        # Save in PCOM folder if available, else Desktop
        if pcom_path and os.path.exists(os.path.dirname(pcom_path)):
            pcom_folder = os.path.dirname(pcom_path)
            report_path = os.path.join(pcom_folder, report_name)
        else:
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            report_path = os.path.join(desktop, report_name)

        wb.save(report_path)
        print(f"✅ Report saved successfully: {report_path}")
        return report_path

    except Exception as e:
        print(f"❌ Failed to save report: {e}")
        return None


def setup_excel_styles():
    yellow_fill = PatternFill(start_color='FFFF00', end_color='FFFF00', fill_type='solid')
    green_fill = PatternFill(start_color='00FF00', end_color='00FF00', fill_type='solid')
    red_fill = PatternFill(start_color='FF0000', end_color='FF0000', fill_type='solid')
    thick_border = Border(left=Side(style='thick'), right=Side(style='thick'),
                          top=Side(style='thick'), bottom=Side(style='thick'))
    dark_blue_fill = PatternFill(start_color='002060', end_color='002060', fill_type='solid')
    header_font = Font(color='FFFFFF', bold=True, size=12)
    
    return {
        'yellow_fill': yellow_fill,
        'green_fill': green_fill,
        'red_fill': red_fill,
        'thick_border': thick_border,
        'dark_blue_fill': dark_blue_fill,
        'header_font': header_font
    }

def setup_excel_headers(ws, styles):
    # First Card Validation Report section
    ws["A1"] = "First Card Validation Report"
    ws["A1"].fill = styles['dark_blue_fill']
    ws["A1"].font = Font(bold=True, color='FFFFFF', size=14)
    ws["A1"].alignment = Alignment(horizontal='left', vertical='center')
    ws.merge_cells("A1:B1")  # Adjust range as needed

    username = getpass.getuser()
    timestamp = datetime.today().strftime('%A, %d %B %Y %I:%M %p')

    # Write date to D1
    ws["D1"] = f"Date : {timestamp}"
    ws["D1"].fill = styles['dark_blue_fill']
    ws["D1"].font = Font(bold=True, color='FFFFFF', size=14)
    ws["D1"].alignment = Alignment(horizontal='left', vertical='center')
    ws.merge_cells("D1:E1")  # Adjust range as needed

    # Write username to D2
    ws["D2"] = f"User : {username}"
    ws["D2"].fill = styles['dark_blue_fill']
    ws["D2"].font = Font(bold=True, color='FFFFFF', size=14)
    ws["D2"].alignment = Alignment(horizontal='left', vertical='center')
    ws.merge_cells("D2:E2")  # Adjust range as needed

    ws.row_dimensions[1].height = 30  # Set height in points

    # Metadata labels
    pre_labels = [
        "Operator Name", "SOF NO", "PO NO", "Circle", "Chip",
        "Batch No & Batch QTY", "Total QTY", "Date of the verification", "Script used for Perso", "Final Verification Status",
    ]

    for i, label in enumerate(pre_labels, start=4):  # Start from row 3
        label_cell = ws.cell(row=i, column=1, value=label)
        label_cell.fill = styles['dark_blue_fill']
        label_cell.font = Font(bold=True, color='FFFFFF')
        label_cell.border = styles['thick_border']
        ws.cell(row=i, column=2).border = styles['thick_border']  # Value cell

    return pre_labels