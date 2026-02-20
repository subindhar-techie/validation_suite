import os
import sys
import re
import cv2
import xml.etree.ElementTree as ET
import numpy as np

# --- Logging Setup ---
def log_debug(msg):
    try:
        log_path = os.path.join(os.path.expanduser("~"), "barcode_scanner.log")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"{msg}\n")
    except:
        pass
    print(msg)

log_debug("--- NEW SCAN SESSION ---")

# --- Environment Setup for pyzbar DLLs ---
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
    # Try multiple common locations
    dll_dirs = [
        base_path,
        os.path.join(base_path, 'pyzbar'),
    ]
    for d in dll_dirs:
        if os.path.exists(d):
            os.environ['PATH'] = d + os.pathsep + os.environ['PATH']
            if hasattr(os, 'add_dll_directory'):
                try:
                    os.add_dll_directory(d)
                except:
                    pass
            log_debug(f"DEBUG: Added DLL path: {d}")
            log_debug(f"DEBUG: Files in {d}: {os.listdir(d)}")

try:
    from pyzbar import pyzbar
    log_debug("DEBUG: pyzbar successfully imported")
except Exception as e:
    log_debug(f"DEBUG: pyzbar import failed: {e}")
    pyzbar = None

def clean_xml_string(xml_str):
    # Fix malformed XML: <VALUE</TAG> -> <TAG>VALUE</TAG>
    # Example: <URT00001234871A001</MSN1> -> <MSN1>URT00001234871A001</MSN1>
    xml_str = re.sub(r'<([^<>]+)</(\w+)>', r'<\2>\1</\2>', xml_str)
    
    xml_str = re.sub(r'<(/?)(\w+)\s+(\w+)>', r'<\1\2_\3>', xml_str)
    xml_str = re.sub(r'<\?xml.*?\?>', '', xml_str)
    xml_str = re.sub(r'<!--.*?-->', '', xml_str)
    xml_str = xml_str.strip()
    return f"<root>{xml_str}</root>"

def process_qr_code_wbiot(image_path):
    """
    Robust barcode and QR code processor for WBIOT/NBIOT.
    Accumulates results from ALL preprocessing steps to maximize detection.
    """
    img = cv2.imread(image_path)
    if img is None:
        log_debug(f"Image not found or unreadable: {image_path}")
        return {}

    all_results = {}
    all_raw_barcodes = set()

    def try_decode_and_accumulate(processed_img, method_name):
        # 1. Try pyzbar (1D/2D)
        if pyzbar:
            try:
                log_debug(f"DEBUG: Attempting pyzbar decode ({method_name})")
                barcodes = pyzbar.decode(processed_img)
                if barcodes:
                    log_debug(f"DEBUG: pyzbar found {len(barcodes)} barcodes in {method_name}")
                    for barcode in barcodes:
                        try:
                            data = barcode.data.decode('utf-8')
                            if not data: continue
                            
                            # Check if this is a long XML barcode
                            if len(data) > 100:
                                log_debug(f"FOUND LONG XML: {method_name} - length={len(data)}, data: {data[:200]}")
                            all_raw_barcodes.add(data)
                            if len(data) > 100:
                                log_debug(f"FOUND FULL: {method_name} - full XML: {data}")
                            
                            if '<' in data and '>' in data:
                                try:
                                    xml_data = clean_xml_string(data)
                                    log_debug(f"CLEANED XML: {xml_data[:200]}...")
                                    root = ET.fromstring(xml_data)
                                    # Create a section for this specific barcode's tags
                                    tag_entry = {}
                                    for child in root:
                                        tag_name = child.tag.upper()
                                        tag_val = child.text if child.text else ""
                                        tag_entry[tag_name] = tag_val
                                        # Also keep in flat results for backward compatibility
                                        all_results[tag_name] = tag_val
                                    
                                    if "BARCODE_TAGS" not in all_results:
                                        all_results["BARCODE_TAGS"] = []
                                    all_results["BARCODE_TAGS"].append(tag_entry)
                                except ET.ParseError:
                                    pass
                        except Exception as inner_e:
                            log_debug(f"DEBUG: Error processing barcode data: {inner_e}")
                            continue
            except Exception as e:
                log_debug(f"pyzbar error ({method_name}): {e}")

        # 2. Try OpenCV QRCodeDetector (QR only)
        try:
            detector = cv2.QRCodeDetector()
            data, _, _ = detector.detectAndDecode(processed_img)
            if data:
                all_raw_barcodes.add(data)
                log_debug(f"FOUND: {method_name} - OpenCV found: {data}")
                if '<' in data and '>' in data:
                    try:
                        xml_data = clean_xml_string(data)
                        log_debug(f"CLEANED XML (OpenCV): {xml_data[:200]}...")
                        root = ET.fromstring(xml_data)
                        tag_entry = {}
                        for child in root:
                            tag_name = child.tag.upper()
                            tag_val = child.text if child.text else ""
                            tag_entry[tag_name] = tag_val
                            all_results[tag_name] = tag_val
                        
                        if "BARCODE_TAGS" not in all_results:
                            all_results["BARCODE_TAGS"] = []
                        all_results["BARCODE_TAGS"].append(tag_entry)
                    except ET.ParseError:
                        pass
        except:
            pass

    # --- Preprocessing Steps ---
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 1. Grayscale
    try_decode_and_accumulate(gray, "Grayscale")

    # 2. Sharpening
    kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
    sharpened = cv2.filter2D(gray, -1, kernel)
    try_decode_and_accumulate(sharpened, "Sharpened")

    # 3. Contrast Enhancement (CLAHE)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8)) # Increased clipLimit
    contrast_img = clahe.apply(gray)
    try_decode_and_accumulate(contrast_img, "ContrastEnhanced")

    # 4. Otsu Thresholding (Aggressive)
    _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    try_decode_and_accumulate(otsu, "OtsuThreshold")

    # 5. Denoise and Edge Enhance
    denoised = cv2.bilateralFilter(gray, 9, 75, 75)
    try_decode_and_accumulate(denoised, "Denoised")
    
    # Laplacian (Edge Enhancement)
    laplacian = cv2.Laplacian(gray, cv2.CV_8U)
    edge_enhanced = cv2.addWeighted(gray, 1.5, laplacian, -0.5, 0)
    try_decode_and_accumulate(edge_enhanced, "EdgeEnhanced")

    # 6. Gamma Correction (More levels)
    for g in [0.4, 0.7, 1.3, 1.8]:
        gamma_table = np.array([((i / 255.0) ** (1.0 / g)) * 255 for i in np.arange(0, 256)]).astype("uint8")
        gamma_img = cv2.LUT(gray, gamma_table)
        try_decode_and_accumulate(gamma_img, f"Gamma_{g}")

    # 7. Scaling
    h, w = gray.shape[:2]
    if w > 2000 or h > 2000:
        resized = cv2.resize(gray, (w // 2, h // 2), interpolation=cv2.INTER_AREA)
        try_decode_and_accumulate(resized, "Downscaled")
    
    if w < 1200 or h < 1200:
        # High-res upscale (3x) for small barcodes
        resized_3x = cv2.resize(gray, (w * 3, h * 3), interpolation=cv2.INTER_CUBIC)
        try_decode_and_accumulate(resized_3x, "Upscaled_3x")
    
    if w < 800 or h < 800:
        resized_2x = cv2.resize(gray, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
        try_decode_and_accumulate(resized_2x, "Upscaled_2x")

    # --- Final Aggregation ---
    if all_raw_barcodes:
        raw_list = list(all_raw_barcodes)
        all_results["RAW_BARCODES"] = raw_list
        all_results["BARCODE_DATA"] = ", ".join(raw_list)
        return all_results

    log_debug(f"FAIL: No barcode or QR code found in image: {image_path}")
    return {}

def process_qr_code_mob(image_path):
    """Fallback for MOB logic if needed, but WBIOT is the primary target now"""
    return process_qr_code_wbiot(image_path)
