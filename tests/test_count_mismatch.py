
import sys
import os
import unittest
from unittest.mock import MagicMock

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(os.path.join(parent_dir, 'src'))

from modules.first_card_validation.core.jio_validator import validate_outer_label_5000

class TestCountMismatch(unittest.TestCase):
    def test_msc_count_mismatch(self):
        # Mock SCMReader
        scm_reader = MagicMock()
        scm_reader.records = [{"ICCID": f"89910000000000000{i:03d}", "MSC": "URT12345678000MC01", "MSN": "URT12345678000A001"} for i in range(5000)]
        
        # Simulate 4999 records found instead of 5000
        scm_reader.get_record_by_iccid = MagicMock(side_effect=[
            ({"ICCID": "89910000000000000000"}, 0), # Try 1: Start
            ({"ICCID": "89910000000000004999"}, 4998), # Try 1: End (one less than expected 5000)
            ({"ICCID": "89910000000000004999"}, 4998), # Strict End Validation
            ({"ICCID": "89910000000000000000"}, 0), # MSN block checks ... 
            ({"ICCID": "89910000000000000000"}, 0),
            ({"ICCID": "89910000000000000000"}, 0),
            ({"ICCID": "89910000000000000000"}, 0),
            ({"ICCID": "89910000000000000000"}, 0),
            ({"ICCID": "89910000000000000000"}, 0),
            ({"ICCID": "89910000000000000000"}, 0),
            ({"ICCID": "89910000000000000000"}, 0),
            ({"ICCID": "89910000000000000000"}, 0),
            ({"ICCID": "89910000000000000000"}, 0),
        ])
        
        scm_reader.get_block = MagicMock(return_value=[{"MSN": "URT12345678000A001"}] * 500)

        label_data = {
            "ICCID Start": "89910000000000000000",
            "ICCID End": "89910000000000004999",
            "QTY": "5000",
            "MSC": "URT12345678000MC01",
            "MSN1": "URT12345678000A001",
            "MSN2": "URT12345678000A002",
            "MSN3": "URT12345678000A003",
            "MSN4": "URT12345678000A004",
            "MSN5": "URT12345678000A005",
            "MSN6": "URT12345678000A006",
            "MSN7": "URT12345678000A007",
            "MSN8": "URT12345678000A008",
            "MSN9": "URT12345678000A009",
            "MSN10": "URT12345678000A010",
        }

        results = validate_outer_label_5000(label_data, scm_reader)
        
        print("\nValidation Status:", results["status"])
        print("MSC Field Status:", results["field_status"].get("MSC"))
        for detail in results["details"]:
            print("Detail:", detail)

        self.assertEqual(results["field_status"]["MSC"], "FAIL")
        self.assertTrue(any("Count Mismatch" in d for d in results["details"]))
        
        # Verify that MSN blocks also failed
        self.assertEqual(results["field_status"]["MSN1"], "FAIL")
        self.assertEqual(results["field_status"]["MSN10"], "FAIL")
    def test_inner_msn_count_mismatch(self):
        # Mock SCMReader
        scm_reader = MagicMock()
        
        # Simulate Row 0 to Row 100
        # But Row 0 to 500 block only has 499 records
        scm_reader.get_record_by_iccid = MagicMock(side_effect=[
            ({"ICCID": "89910000000000000000"}, 0), # Order check: Try 1 Start
            ({"ICCID": "89910000000000000100"}, 100), # Order check: Try 1 End
            ({"ICCID": "89910000000000000100"}, 100), # Strict End Validation
            ({"ICCID": "89910000000000000000"}, 0), # Field Content loop...
            ({"ICCID": "89910000000000000001"}, 1),
            ({"ICCID": "89910000000000000002"}, 2),
        ])
        
        # Block check: Row 0 to 500
        scm_reader.get_block = MagicMock(side_effect=[
            [{"ICCID": "..."}] * 101, # get_block for range check
            [{"ICCID": "..."}] * 499  # get_block(0, 500) for MSN count check
        ])

        label_data = {
            "ICCID Start": "89910000000000000000",
            "ICCID End": "89910000000000000100",
            "QTY": "100",
            "PO": "450069906",
            "EAN": "499002064",
            "MSN": "URT99002064906A001"
        }

        from modules.first_card_validation.core.jio_validator import validate_jio_label
        results = validate_jio_label("100", label_data, scm_reader)
        
        print("\nInner Label MSN Check:", results["field_status"].get("MSN"))
        self.assertEqual(results["field_status"]["MSN"], "FAIL")
        self.assertTrue(any("MSN Block Count Mismatch" in d for d in results["details"]))

if __name__ == "__main__":
    unittest.main()
