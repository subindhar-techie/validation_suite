import os
import sys
import unittest
from src.modules.first_card_validation.core.jio_validator import SCMReader, construct_msn, construct_msc, construct_pid, validate_jio_label, validate_outer_label_5000

class TestJioValidator(unittest.TestCase):
    def setUp(self):
        # Create a mock SCM file
        self.scm_path = "test_scm.txt"
        with open(self.scm_path, "w", encoding="utf-8") as f:
            f.write("SKUCODE\tMSN\tICCID\tIMSI\tBATCHNO\tPONUM\tVENDERCODE\tMSC\tPID\tCIRCLE\n")
            # 500 records for Inner/Outer testing
            for i in range(500):
                iccid = str(89918730506000450000 + i)
                # MSN is the same for the whole sub-block (A001 for first 500)
                msn = "URT99001964897A001"
                msc = f"URT99001964897MC{str(i+1).zfill(2)}"
                pid = f"PRT90019649897A{str(i+1).zfill(3)}"
                f.write(f"499001964\t{msn}\t{iccid}\t4058123456789\t50883\t450069897\t3795231\t{msc}\t{pid}\tMH\n")

    def tearDown(self):
        if os.path.exists(self.scm_path):
            os.remove(self.scm_path)

    def test_construction_logic(self):
        skucode = "499001964"
        po = "450069897"
        
        # New logic: SKU part is last 8 digits of 9-digit zfilled SKU (499001964 -> 99001964)
        # PO part is last 3 digits
        self.assertEqual(construct_msn(skucode, po, "A001"), "URT99001964897A001")
        self.assertEqual(construct_msc(skucode, po, "MC01"), "URT99001964897MC01")
        self.assertEqual(construct_pid(skucode, po, "A001"), "PRT90019649897A001")

    def test_validation_pass_with_circle(self):
        reader = SCMReader(self.scm_path)
        label_data = {
            "ICCID Start": "89918730506000450000",
            "ICCID End": "89918730506000450099",
            "QTY": "100",
            "MSN": "URT99001964897A001",
            "MSC": "URT99001964897MC01",
            "PID": "PRT90019649897A001",
            "PO": "450069897",
            "EAN": "499001964",
            "Circle": "MH"
        }
        # Pass "MH" from "GUI", logic uses block-based counter for main MSN
        # start_idx is 0, so block is 1 (A001)
        # MSN in SCM for row 0 is already A001 in setUp
        result = validate_jio_label("100", label_data, reader, gui_circle="MH")
        if result["status"] != "PASS":
            print(f"DEBUG: test_validation_pass_with_circle failed. Details: {result['details']}")
            print(f"DEBUG: field_status: {result['field_status']}")
        self.assertEqual(result["status"], "PASS")

    def test_validation_fail_circle(self):
        reader = SCMReader(self.scm_path)
        label_data = {
            "ICCID Start": "89918730506000450000",
            "ICCID End": "89918730506000450099",
            "QTY": "100",
            "MSN": "URT99001964897A001",
            "PO": "450069897",
            "EAN": "499001964",
            "Circle": "RJ" # Different from GUI
        }
        result = validate_jio_label("100", label_data, reader, gui_circle="MH")
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["field_status"]["Circle"], "FAIL")
        self.assertTrue(any("Circle Mismatch" in d for d in result["details"]))

    def test_validation_fail_iccid(self):
        reader = SCMReader(self.scm_path)
        label_data = {
            "ICCID Start": "89918730506000450001", # Wrong start
            "ICCID End": "89918730506000450099",
            "QTY": "100",
            "MSN": "URT99001964897A002",
            "PO": "450069897",
            "EAN": "499001964"
        }
        result = validate_jio_label("100", label_data, reader)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any("Continuity Error" in d or "Mismatch" in d for d in result["details"]))

    def test_validation_logic_v_scm_mismatch(self):
        # Test the fix for the 'elif' bug: Logic passes but SCM fails
        reader = SCMReader(self.scm_path)
        label_data = {
            "ICCID Start": "89918730506000450000",
            "ICCID End": "89918730506000450099",
            "QTY": "100",
            "MSN": "URT99001964897A001", # Logic Correct
            "MSC": "URT99001964897MC99", # Logic Matches MC99 format, but record has MC01
            "PO": "450069897",
            "EAN": "499001964"
        }
        # In the SCM record (setup), at index 0, MSC is URT99001964897MC01
        result = validate_jio_label("100", label_data, reader)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["field_status"]["MSC"], "FAIL")
        self.assertTrue(any("MSC SCM Mismatch" in d for d in result["details"]))

    def test_outer_label_5000_circle(self):
        # Setup 5000 records
        with open(self.scm_path, "w", encoding="utf-8") as f:
            f.write("SKUCODE\tMSN\tICCID\tIMSI\tBATCHNO\tPONUM\tVENDERCODE\tMSC\tPID\tCIRCLE\r\n")
            for i in range(5000):
                iccid = str(89918730506000450000 + i)
                # MSN increments sub-block number EVERY 500
                block_num = (i // 500) + 1
                msn = f"URT99001964897A{str(block_num).zfill(3)}"
                f.write(f"499001964\t{msn}\t{iccid}\t4058123456789\t50883\t450069897\t3795231\tURT99001964897MC01\tPRT90019649897A001\tMH\r\n")
        
    def test_validation_fail_gui_empty_label_has_data(self):
        reader = SCMReader(self.scm_path)
        label_data = {
            "ICCID Start": "89918730506000450000",
            "ICCID End": "89918730506000450099",
            "QTY": "100",
            "Circle": "MH"
        }
        # GUI is empty, but label has "MH" -> Should FAIL
        result = validate_jio_label("100", label_data, reader, gui_circle="")
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["field_status"].get("Circle"), "FAIL")

    def test_validation_pass_both_empty(self):
        reader = SCMReader(self.scm_path)
        label_data = {
            "ICCID Start": "89918730506000450000",
            "ICCID End": "89918730506000450099",
            "QTY": "100",
            "Circle": ""
        }
        # Both empty -> Should PASS
        result = validate_jio_label("100", label_data, reader, gui_circle="")
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["field_status"]["Circle"], "PASS")
        
        from src.modules.first_card_validation.core.jio_validator import validate_outer_label_5000
        reader = SCMReader(self.scm_path)
        label_data = {
            "ICCID Start": "89918730506000450000",
            "ICCID End": "89918730506000454999",
            "QTY": "5000",
            "Circle": "RJ" # Fail case
        }
        result = validate_outer_label_5000(label_data, reader, gui_circle="MH")
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["field_status"]["Circle"], "FAIL")
        
        # Pass case
        result = validate_outer_label_5000(label_data, reader, gui_circle="RJ")
        # Logic check might fail here because we didn't provide MSN/MSC in label_data, but Circle should PASS
        self.assertEqual(result["field_status"]["Circle"], "PASS")

    def test_golden_sample_500_pass(self):
        # Setup: Only 500 records between Start and End
        reader = SCMReader(self.scm_path)
        label_data = {
            "ICCID Start": "89918730506000450000",
            "ICCID End": "89918730506000450499", # 500 records gap
            "QTY": "500",
            "MSN1": "URT99001964897A001",
            "MSC": "URT99001964897MC01",
            "PID": "PRT90019649897A001",
            "Circle": "MH"
        }
        # Golden Sample: QTY 500, only MSN1 required
        result = validate_outer_label_5000(label_data, reader, gui_circle="MH")
        self.assertEqual(result["status"], "PASS")
        self.assertNotIn("MSN2", result["field_status"]) # Should not be an error

    def test_large_batch_missing_msn_fail(self):
        # Setup: 5000 records gap
        reader = SCMReader(self.scm_path)
        label_data = {
            "ICCID Start": "89918730506000450000",
            "ICCID End": "89918730506000454999", # 5000 records gap
            "QTY": "5000",
            "MSN1": "URT99001964897A001",
             # MSN2-MSN10 MISSING -> Should FAIL
        }
        result = validate_outer_label_5000(label_data, reader)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["field_status"]["MSN2"], "FAIL")

if __name__ == "__main__":
    unittest.main()
