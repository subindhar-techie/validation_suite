import os
import sys

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, 'src'))

try:
    from modules.first_card_validation.core.qr_processor import process_qr_code_wbiot
    print("SUCCESS: Imported process_qr_code_wbiot")
except ImportError as e:
    print(f"FAILED: Import error: {e}")
    sys.exit(1)

def test_image(image_path):
    print(f"\n--- Testing Image: {image_path} ---")
    if not os.path.exists(image_path):
        print(f"ERROR: File not found at {image_path}")
        return

    print("Targeting scanning and extraction...")
    results = process_qr_code_wbiot(image_path)
    
    print("\n--- FINAL RESULTS ---")
    if results:
        for k, v in results.items():
            print(f"{k}: {v}")
    else:
        print("RESULT: No barcodes or QR codes detected.")

if __name__ == "__main__":
    # Path provided by the user
    target_path = r"C:/Users/m.subindar/OneDrive - Rosmerta Technologies Ltd/Desktop/Testing Folder/RTLP10071/OUTER5000.jpg"
    test_image(target_path)
