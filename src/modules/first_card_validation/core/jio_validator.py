import os
import re
import csv
import traceback

class SCMReader:
    def __init__(self, scm_path):
        self.scm_path = scm_path
        self.records = []
        self.header_map = {} # Original header -> Normalized Header
        self.data_by_iccid = {} # ICCID -> Row Index
        self.load_scm()

    def load_scm(self):
        """Loads SCM file with normalized headers and builds an ICCID index."""
        try:
            if not self.scm_path or not os.path.exists(self.scm_path):
                print(f"[WARN] SCM file not found: {self.scm_path}")
                return

            with open(self.scm_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Read first line to detect headers
                header_line = f.readline()
                if not header_line: return
                
                raw_headers = header_line.strip().split('\t')
                normalized_headers = [h.strip().upper().replace("_", "").replace(" ", "") for h in raw_headers]
                self.header_map = {normalized_headers[i]: raw_headers[i] for i in range(len(raw_headers))}
                
                # Use standard csv reader for the rest
                reader = csv.reader(f, delimiter='\t')
                for idx, row in enumerate(reader):
                    if not row: continue
                    # Pad row if columns are missing
                    if len(row) < len(raw_headers):
                        row += [""] * (len(raw_headers) - len(row))
                    
                    record = {normalized_headers[i]: row[i] for i in range(len(raw_headers))}
                    
                    # Apply aliases for internal consistency
                    sku_aliases = ["SKUCODE", "EAN", "MATNR", "PRODUCTCODE", "PARTNO"]
                    po_aliases = ["PONUM", "PO", "PURCHASEORDER", "PONO"]
                    
                    for alias in sku_aliases:
                        if alias in record and record[alias]: 
                            record["SKUCODE"] = record[alias]
                            break
                    for alias in po_aliases:
                        if alias in record and record[alias]: 
                            record["PONUM"] = record[alias]
                            break

                    self.records.append(record)
                    
                    # Index by ICCID (clean) - use the actual list index
                    iccid_val = record.get("ICCID", "")
                    if iccid_val:
                        clean_iccid = re.sub(r'\D', '', str(iccid_val))
                        self.data_by_iccid[clean_iccid] = len(self.records) - 1
                
                print(f"[PASS] Loaded {len(self.records)} records from SCM. Indexed {len(self.data_by_iccid)} ICCIDs.")
        except Exception as e:
            print(f"Error loading SCM: {e}")
            traceback.print_exc()

    def get_record_by_iccid(self, iccid):
        clean_iccid = re.sub(r'\D', '', str(iccid))
        # Exact match first
        if clean_iccid in self.data_by_iccid:
            idx = self.data_by_iccid[clean_iccid]
            return self.records[idx], idx
        
        # Try substring match if exact fails (expensive, but fallback)
        for clean_scm_iccid, idx in self.data_by_iccid.items():
            if clean_iccid in clean_scm_iccid or clean_scm_iccid in clean_iccid:
                return self.records[idx], idx
        return None, -1

    def get_block(self, start_index, quantity):
        if start_index == -1: return []
        return self.records[start_index : start_index + quantity]

def construct_msn(skucode, po, counter):
    try:
        prefix = "URT"
        # Original logic: 9-digit zfill, then slice from index 1 (8 digits)
        sku_val = str(skucode).strip()
        if sku_val.isdigit():
            sku_str = sku_val.zfill(9)
            sku_part = sku_str[1:] if len(sku_str) == 9 else sku_str[-8:]
        else:
            sku_part = sku_val[-8:]
            
        # Original logic: last 3 digits of PO
        po_str = str(po).strip()
        po_part = po_str[-3:] if len(po_str) >= 3 else po_str.zfill(3)
        return f"{prefix}{sku_part}{po_part}{counter}"
    except: return ""

def construct_msc(skucode, po, counter):
    try:
        prefix = "URT"
        # SKU part: strictly last 8 digits
        sku_str = str(skucode).strip()
        sku_part = sku_str[-8:] if len(sku_str) >= 8 else sku_str.zfill(8)
        # PO part: strictly last 3 digits
        po_str = str(po).strip()
        po_part = po_str[-3:] if len(po_str) >= 3 else po_str.zfill(3)
        return f"{prefix}{sku_part}{po_part}{counter}"
    except: return ""

def construct_pid(skucode, po, counter):
    try:
        prefix = "PRT"
        sku_part = str(skucode)[2:] if len(str(skucode)) > 2 else str(skucode)
        po_part = str(po)[-4:] if len(str(po)) >= 4 else str(po)
        return f"{prefix}{sku_part}{po_part}{counter}"
    except: return ""

def validate_jio_label(label_type, label_data, scm_reader, gui_circle=None):
    results = {"status": "PASS", "details": [], "field_status": {}}
    
    # 1. Normalize Inputs
    iccid_start = str(label_data.get("ICCID Start", "")).strip()
    iccid_end = str(label_data.get("ICCID End", "")).strip()
    po = str(label_data.get("PO", "")).strip()
    qty = str(label_data.get("QTY", "0")).strip()
    ean = str(label_data.get("EAN", "")).strip()
    msn = str(label_data.get("MSN", "")).strip()
    msc = str(label_data.get("MSC", "")).strip()
    pid = str(label_data.get("PID", "")).strip()

    expected_qty = int(label_type)

    # === ORDER-INDEPENDENT ALIGNMENT CHECK ===
    # Strategy: Find if (start, end) or (end, start) forms a valid block of 'expected_qty' in SCM
    # If found, we update iccid_start/end to match the SCM block order for consistent reporting.
    # print(f"[SCAN] Order-Independent Check: Scanning for block of {expected_qty}...")
    
    alignment_found = False
    scm_start_record, start_idx = scm_reader.get_record_by_iccid(iccid_start)
    
    # Check Try 1: As provided
    if scm_start_record and expected_qty > 1:
        end_idx_expected = start_idx + expected_qty - 1
        if end_idx_expected < len(scm_reader.records):
            scm_end_rec = scm_reader.records[end_idx_expected]
            scm_end_iccid = re.sub(r'\D', '', str(scm_end_rec.get("ICCID", "")))
            if scm_end_iccid == re.sub(r'\D', '', iccid_end):
                print(f"[PASS] Alignment found (As Scanned). Row {start_idx} to {end_idx_expected}")
                alignment_found = True

    # Try 2: Swapped - DISABLED per user request
    # We now use only what is scanned from the barcode without any swapping
    # if not alignment_found and iccid_end and expected_qty > 1:
    #     # This logic is disabled - use only as-scanned values

    # Default everything to PASS initially
    for k in label_data.keys(): results["field_status"][k] = "PASS"

    # 2. Basic Format Checks (Image Data Quality)
    if not iccid_start or len(re.sub(r'\D', '', iccid_start)) < 18:
        results["field_status"]["ICCID Start"] = "FAIL"
        results["details"].append("Invalid ICCID Start format")
    if po and not po.isdigit():
        results["field_status"]["PO"] = "FAIL"
        results["details"].append("PO should be numeric")
    if msn and not msn.startswith("URT"):
        results["field_status"]["MSN"] = "FAIL"
        results["details"].append("MSN should start with URT")

    # 3. Final SCM Record Validation
    if not scm_start_record:
        results["status"] = "FAIL"
        results["field_status"]["ICCID Start"] = "FAIL"
        
        # USER REQUEST: Calculate how many records are actually available
        # If End is found, we can calculate the gap
        if iccid_end:
            scm_end_record, end_idx = scm_reader.get_record_by_iccid(iccid_end)
            if scm_end_record:
                # We know where End is, but Start is missing
                # This means at least 1 record is missing from the beginning
                results["field_status"]["QTY"] = "FAIL"
                if msn: results["field_status"]["MSN"] = "FAIL"
                if msc: results["field_status"]["MSC"] = "FAIL"
                
                results["details"].append(f"ICCID Start: Starting ICCID missing")
                results["details"].append(f"QTY: Count mismatch (1+ records missing from start)")
                return results
        
        # Both Start and End are missing - complete batch failure
        results["field_status"]["QTY"] = "FAIL"
        if msn: results["field_status"]["MSN"] = "FAIL"
        if msc: results["field_status"]["MSC"] = "FAIL"
        
        results["details"].append(f"ICCID Start: Starting ICCID missing")
        results["details"].append(f"QTY: Batch count broken (Start record not found)")
        return results

    # print(f"[LOC] SCM Match: ICCID={iccid_start} found at Row Index {start_idx}")
    scm_record = scm_start_record # Alias for clarity

    # --- STRICT END VALIDATION ---
    scm_end_record = None
    end_idx = -1
    if iccid_end:
        scm_end_record, end_idx = scm_reader.get_record_by_iccid(iccid_end)
        if not scm_end_record:
            results["status"] = "FAIL"
            results["field_status"]["ICCID End"] = "FAIL"
            results["details"].append(f"End ICCID {iccid_end} not found in SCM")
    
    # 4. Range and Continuity Validation
    expected_qty = int(label_type)
    
    # Check 1: Does the printed QTY match expectation?
    clean_qty = re.sub(r'\D', '', str(qty))
    clean_expected = re.sub(r'\D', '', str(expected_qty))
    
    if clean_qty != clean_expected and clean_qty != "0": 
        results["field_status"]["QTY"] = "FAIL"
        results["details"].append(f"QTY Mismatch: Label='{qty}' ({clean_qty}), Expected='{expected_qty}'")
    
    # Check 2: Check SCM Gap (Continuity) - DISABLED per user request
    # We now use the scanned values directly without validating SCM continuity
    # This ensures the label values are used as-is without requiring consecutive records
    if iccid_end and start_idx != -1 and end_idx != -1:
        actual_scm_gap = end_idx - start_idx + 1
        
        # Validate: Start should be before End in SCM (start_idx < end_idx)
        if start_idx > end_idx:
            # ICCIDs are swapped - Start is after End in SCM
            results["field_status"]["ICCID Start"] = "FAIL"
            results["field_status"]["ICCID End"] = "FAIL"
            results["field_status"]["QTY"] = "FAIL"
            results["details"].append("ICCID Start/End appear to be swapped (Start ICCID comes after End in SCM)")
        else:
            # Check if QTY matches the count between Start and End ICCID
            if actual_scm_gap != expected_qty:
                # Count mismatch between label QTY and SCM records
                results["field_status"]["ICCID End"] = "FAIL"
                results["field_status"]["QTY"] = "FAIL"
                missing_count = expected_qty - actual_scm_gap
                results["details"].append(f"QTY: ICCID Present but {missing_count} Data Missing (Expected: {expected_qty}, Found: {actual_scm_gap})")
                results["status"] = "FAIL"
            else:
                # QTY matches
                results["field_status"]["ICCID End"] = "PASS"
                results["field_status"]["QTY"] = "PASS"
    elif iccid_end and (start_idx == -1 or end_idx == -1):
        # Both or one ICCID not found in SCM - still fail
        if start_idx == -1:
            results["field_status"]["ICCID Start"] = "FAIL"
        if end_idx == -1:
            results["field_status"]["ICCID End"] = "FAIL"
        results["field_status"]["QTY"] = "FAIL"
    elif not iccid_end and expected_qty > 1:
        results["field_status"]["QTY"] = "FAIL"
        results["details"].append("ICCID End missing on label for multi-card batch")
    
    # Check 3: Final fallback for QTY if no End ICCID (1-card or missing scan)
    if not iccid_end and expected_qty == 1:
        results["field_status"]["QTY"] = "PASS"
    elif not iccid_end and expected_qty > 1:
        results["field_status"]["QTY"] = "FAIL"

    # Get the actual records for field checks
    if iccid_end and end_idx != -1:
        block = scm_reader.get_block(start_idx, abs(end_idx - start_idx) + 1)
    else:
        block = scm_reader.get_block(start_idx, expected_qty)

    if len(block) < expected_qty:
         results["field_status"]["QTY"] = "FAIL"
         results["details"].append(f"SCM only has {len(block)} records remaining from this start point")

    # 5. Field Content Validation (Image vs SCM)
    scm_sku = scm_record.get("SKUCODE", "").strip()
    scm_po = scm_record.get("PONUM", "").strip()
    scm_msn = scm_record.get("MSN", "").strip()
    scm_msc = scm_record.get("MSC", "").strip()
    scm_pid = scm_record.get("PID", "").strip() # Added PID
    
    # Dynamic Match Fallback: If label value doesn't match header but exists in record (user request)
    if ean and ean != scm_sku and ean in scm_record.values():
        print(f"[INFO] Dynamic Header Match: Found EAN {ean} in SCM record (ignoring header mismatch)")
        scm_sku = ean
    
    if po and po != scm_po and po in scm_record.values():
        print(f"[INFO] Dynamic Header Match: Found PO {po} in SCM record (ignoring header mismatch)")
        scm_po = po

    # print(f"[DATA] SCM Values for Row {start_idx}: SKU={scm_sku}, PO={scm_po}, MSN={scm_msn}")

    if ean and ean != scm_sku:
        results["field_status"]["EAN"] = "FAIL"
        results["details"].append(f"EAN Mismatch: Label={ean}, SCM={scm_sku}")
    
    if po and po != scm_po:
        results["field_status"]["PO"] = "FAIL"
        results["details"].append(f"PO Mismatch: Label={po}, SCM={scm_po}")

    # 6. Logic Validation (Derived vs Scanned)
    if msn:
        # User Request: MSN counter increases every 500 (A001, A002, ...)
        # Current block = (start_idx // 500) + 1
        msn_block = (start_idx // 500) + 1
        expected_counter = f"A{str(msn_block).zfill(3)}"
        
        logic_msn = construct_msn(scm_sku, scm_po, expected_counter)
        if msn != logic_msn:
            results["field_status"]["MSN"] = "FAIL"
            results["details"].append(f"MSN Logic Mismatch: Expected {logic_msn}")
            results["status"] = "FAIL"
        if msn != scm_msn:
            results["field_status"]["MSN"] = "FAIL"
            results["details"].append(f"MSN SCM Mismatch: Label={msn}, SCM={scm_msn}")
            results["status"] = "FAIL"

    if msc:
        # For URT99...MC01, counter is MC01
        msc_counter = msc[-4:] if len(msc) >= 4 else "MC01"
        logic_msc = construct_msc(scm_sku, scm_po, msc_counter)
        if msc != logic_msc:
            results["field_status"]["MSC"] = "FAIL"
            results["details"].append(f"MSC Logic Mismatch: Expected {logic_msc}")
            results["status"] = "FAIL"
        if msc != scm_msc:
            results["field_status"]["MSC"] = "FAIL"
            results["details"].append(f"MSC SCM Mismatch: Label={msc}, SCM={scm_msc}")
            results["status"] = "FAIL"

    # 7. Circle Validation (Cross-check with GUI input)
    scanned_circle = label_data.get("Circle", label_data.get("CIRCLE"))
    circle = str(scanned_circle).strip() if scanned_circle is not None else ""
    
    if gui_circle is not None:
        is_artwork = (label_type == "1")
        
        if circle:
            # print(f"[GLOBAL] Circle Check: ROI='{circle}', GUI='{gui_circle}', Type='{label_type}'")
            if circle.upper() != gui_circle.upper():
                results["field_status"]["Circle"] = "FAIL"
                results["field_status"]["CIRCLE"] = "FAIL"
                results["details"].append(f"Circle Mismatch (Type {label_type}): Scanned={circle}, Expected(GUI)={gui_circle}")
            else:
                results["field_status"]["Circle"] = "PASS"
                results["field_status"]["CIRCLE"] = "PASS"
        elif gui_circle and not is_artwork:
             # Scanned Circle is empty but GUI has a value (Skip failure if it is Artwork)
             results["field_status"]["Circle"] = "FAIL"
             results["field_status"]["CIRCLE"] = "FAIL"
             results["details"].append(f"Circle Missing on Label: Expected(GUI)={gui_circle}")
        elif is_artwork:
            # Both are empty and it's artwork OR logic skipped failure because is_artwork
            results["field_status"]["Circle"] = "PASS"
            results["field_status"]["CIRCLE"] = "PASS"
            print(f"[INFO] Artwork Circle check skipped or passed (is_artwork={is_artwork}, scan_empty={not circle})")
        else:
            # Both are empty and not artwork -> PASS
            results["field_status"]["Circle"] = "PASS"
            results["field_status"]["CIRCLE"] = "PASS"
    
        # Also check against SCM if possible
        scm_circle = scm_record.get("CIRCLE", "").strip()
        if scm_circle and gui_circle.upper() != scm_circle.upper():
            print(f"[WARN] GUI Circle ({gui_circle}) differs from SCM Circle ({scm_circle})")

    if pid:
        pid_counter = pid[-4:] if len(pid) >= 4 else "A001"
        logic_pid = construct_pid(scm_sku, scm_po, pid_counter)
        if pid != logic_pid:
            results["field_status"]["PID"] = "FAIL"
            results["details"].append(f"PID Logic Mismatch: Expected {logic_pid}")
        if pid != scm_pid: # Changed from elif to if
            results["field_status"]["PID"] = "FAIL"
            results["details"].append(f"PID SCM Mismatch: Label={pid}, SCM={scm_pid}")

    # Final overall status
    if any(s == "FAIL" for s in results["field_status"].values()):
        results["status"] = "FAIL"
    
    # USER REQUEST: Individual MSN block count check (A001 should represent 500 units)
    # If the block start point doesn't have 500 records available in SCM, mark MSN as FAIL.
    if msn:
        msn_block_idx = (start_idx // 500) * 500
        msn_block_records = scm_reader.get_block(msn_block_idx, 500)
        if len(msn_block_records) < 500:
            results["field_status"]["MSN"] = "FAIL"
            results["details"].append(f"MSN Block Count Mismatch: Block starting at Row {msn_block_idx} only has {len(msn_block_records)} records in SCM (Expected 500)")
            results["status"] = "FAIL"

    # USER REQUEST: Propagate QTY/Continuity failures to MSN, MSC, and PID statuses
    if results["field_status"].get("QTY") == "FAIL" or results["field_status"].get("ICCID End") == "FAIL":
        for k in ["MSN", "MSC", "PID"]:
            if label_data.get(k):
                results["field_status"][k] = "FAIL"
        results["status"] = "FAIL"
    
    return results

def validate_outer_label_5000(label_data, scm_reader, gui_circle=None):
    results = {"status": "PASS", "details": [], "field_status": {}}
    for k in label_data.keys(): results["field_status"][k] = "PASS"

    iccid_start = str(label_data.get("ICCID Start", "")).strip()
    iccid_end = str(label_data.get("ICCID End", "")).strip()
    ean = str(label_data.get("EAN", "")).strip()
    po = str(label_data.get("PO", "")).strip()

    # Look up start and end
    scm_start_record, start_idx = scm_reader.get_record_by_iccid(iccid_start)

    # === ORDER-INDEPENDENT ALIGNMENT CHECK (Outer 5000) ===
    expected_qty = 5000
    alignment_found = False
    
    # Try 1: As provided
    if scm_start_record:
        end_idx_expected = start_idx + expected_qty - 1
        if end_idx_expected < len(scm_reader.records):
            scm_end_iccid = re.sub(r'\D', '', str(scm_reader.records[end_idx_expected].get("ICCID", "")))
            if scm_end_iccid == re.sub(r'\D', '', str(iccid_end)):
                print(f"[PASS] Outer Alignment found (As Scanned). Row {start_idx}")
                alignment_found = True

    # Try 2: Swapped - DISABLED per user request
    # We now use only what is scanned from the barcode without any swapping
    # if not alignment_found and iccid_end:
    #     print("[INFO] Trying swapped alignment for Outer...")
    #     # This logic is disabled - use only as-scanned values

    # Strict End Validation
    scm_end_record = None
    end_idx = -1
    if iccid_end:
        scm_end_record, end_idx = scm_reader.get_record_by_iccid(iccid_end)
        if not scm_end_record:
            results["status"] = "FAIL"
            results["field_status"]["ICCID End"] = "FAIL"
            results["details"].append(f"Outer End {iccid_end} not found in SCM")

    if not scm_start_record:
        results["status"] = "FAIL"
        results["field_status"]["ICCID Start"] = "FAIL"
        
        # USER REQUEST: Calculate how many records are actually available
        if iccid_end:
            scm_end_record_check, end_idx_check = scm_reader.get_record_by_iccid(iccid_end)
            if scm_end_record_check:
                # We know where End is, but Start is missing
                results["field_status"]["QTY"] = "FAIL"
                results["field_status"]["MSC"] = "FAIL"
                for i in range(1, 11):
                    results["field_status"][f"MSN{i}"] = "FAIL"
                    
                results["details"].append(f"ICCID Start: Starting ICCID missing")
                results["details"].append(f"QTY: Count mismatch (1+ records missing from start)")
                return results
        
        # Both Start and End are missing - complete batch failure
        results["field_status"]["QTY"] = "FAIL"
        results["field_status"]["MSC"] = "FAIL"
        for i in range(1, 11):
            results["field_status"][f"MSN{i}"] = "FAIL"
            
        results["details"].append(f"ICCID Start: Starting ICCID missing")
        results["details"].append(f"QTY: Batch count broken (Start record not found)")
        return results
    
    scm_record = scm_start_record
    scm_sku = scm_record.get("SKUCODE", "").strip()
    scm_po = scm_record.get("PONUM", "").strip()
    scm_msn = scm_record.get("MSN", "").strip()
    scm_msc = scm_record.get("MSC", "").strip()
    scm_pid = scm_record.get("PID", "").strip()

    # Dynamic Match Fallback (User request: Use value if header doesn't match)
    if ean and ean != scm_sku and ean in scm_record.values():
        scm_sku = ean
    if po and po != scm_po and po in scm_record.values():
        scm_po = po

    # Circle Validation
    circle = str(label_data.get("Circle", label_data.get("CIRCLE", ""))).strip()
    if gui_circle:
        if circle.upper() != gui_circle.upper():
            results["field_status"]["Circle"] = "FAIL"
            results["field_status"]["CIRCLE"] = "FAIL"
            results["details"].append(f"Outer Circle Mismatch: Scanned={circle}, Expected(GUI)={gui_circle}")
            results["status"] = "FAIL"
        else:
            results["field_status"]["Circle"] = "PASS"
            results["field_status"]["CIRCLE"] = "PASS"

    # Global QTY/Continuity check
    qty = str(label_data.get("QTY", "5000")).strip() 
    clean_qty = re.sub(r'\D', '', qty)
    label_batch_qty = int(clean_qty) if clean_qty else 5000
    
    # User Request: If QTY is 500 on both system and label, it's a golden sample
    # Dynamic expected_qty for continuity check
    expected_qty = label_batch_qty
    
    # Check 2: Check SCM Gap (Continuity) - Verify QTY by counting records between Start and End ICCID
    actual_scm_gap = expected_qty # Default
    if start_idx != -1 and end_idx != -1:
        actual_scm_gap = end_idx - start_idx + 1
        
        # Validate: Start should be before End in SCM (start_idx < end_idx)
        if start_idx > end_idx:
            # ICCIDs are swapped - Start is after End in SCM
            results["field_status"]["ICCID Start"] = "FAIL"
            results["field_status"]["ICCID End"] = "FAIL"
            results["field_status"]["QTY"] = "FAIL"
            results["details"].append("ICCID Start/End appear to be swapped (Start ICCID comes after End in SCM)")
        else:
            # Check if QTY matches the count between Start and End ICCID
            if actual_scm_gap != expected_qty:
                # Count mismatch between label QTY and SCM records
                results["field_status"]["ICCID End"] = "FAIL"
                results["field_status"]["QTY"] = "FAIL"
                missing_count = expected_qty - actual_scm_gap
                results["details"].append(f"QTY: ICCID Present but {missing_count} Data Missing (Expected: {expected_qty}, Found: {actual_scm_gap})")
                results["status"] = "FAIL"
            else:
                # QTY matches
                results["field_status"]["ICCID End"] = "PASS"
                results["field_status"]["QTY"] = "PASS"
    elif iccid_end:
        # One or both records missing from SCM - still fail
        if start_idx == -1:
            results["field_status"]["ICCID Start"] = "FAIL"
        if end_idx == -1:
            results["field_status"]["ICCID End"] = "FAIL"
        results["field_status"]["QTY"] = "FAIL"
    else:
        # No End ICCID provided? Fail if QTY > 500 (standard Outer usually has End)
        if label_batch_qty > 500:
            results["field_status"]["QTY"] = "FAIL"
            results["details"].append("Outer Label requires both Start and End ICCIDs for large quantities")
        else:
            results["field_status"]["QTY"] = "PASS"
            results["field_status"]["ICCID End"] = "PASS"

    if ean and ean != scm_sku:
        results["field_status"]["EAN"] = "FAIL"
        results["details"].append(f"Outer EAN Mismatch: Label={ean}, SCM={scm_sku}")
    
    if po and po != scm_po:
        results["field_status"]["PO"] = "FAIL"
        results["details"].append(f"Outer PO Mismatch: Label={po}, SCM={scm_po}")

    # 6. MSN/MSC/PID Logic Validation for Outer batch (against Master SCM Record)
    msn = str(label_data.get("MSN", "")).strip()
    msc = str(label_data.get("MSC", "")).strip()
    pid = str(label_data.get("PID", "")).strip()

    if msn:
        # User Request: MSN counter increases every 500 Globally
        # For a 5000 label, allow any of the 10 block counters in the batch (start to start+4500)
        valid_counters = []
        for i in range(1, 11):
            target_row = start_idx + (i-1)*500
            if target_row < len(scm_reader.records):
                block_num = (target_row // 500) + 1
                valid_counters.append(f"A{str(block_num).zfill(3)}")
        
        if msn[-4:] in valid_counters:
            # Matches one of the blocks in this range
            pass
        else:
            msn_block = (start_idx // 500) + 1
            expected_counter = f"A{str(msn_block).zfill(3)}"
            logic_msn = construct_msn(scm_sku, scm_po, expected_counter)
            
            # Logic check: If not in valid counters, flag it
            results["field_status"]["MSN"] = "FAIL"
            results["details"].append(f"Outer MSN Logic Mismatch: Scanned {msn[-4:]} not in valid blocks for this batch")
            results["status"] = "FAIL"

        if msn != scm_msn:
            # Still check against SCM record for the START row as baseline
            # if the user scanned A010 but aligned to Row 0, it's an SCM mismatch for Row 0
            # but we already allowed it in logic if it's one of the 10.
            # Let's be lenient: if it matches logic for any block in the range, and SKU/PO/Prefix are correct, PASS.
            if any(msn == construct_msn(scm_sku, scm_po, c) for c in valid_counters):
                results["field_status"]["MSN"] = "PASS"
            else:
                results["field_status"]["MSN"] = "FAIL"
                results["details"].append(f"Outer MSN SCM Mismatch: Label={msn}, SCM expected range alignment")
                results["status"] = "FAIL"

    if msc:
        msc_counter = msc[-4:] if len(msc) >= 4 else "MC01"
        logic_msc = construct_msc(scm_sku, scm_po, msc_counter)
        if msc != logic_msc:
            results["field_status"]["MSC"] = "FAIL"
            results["details"].append(f"Outer MSC Logic Mismatch: Expected {logic_msc}")
            results["status"] = "FAIL"
        if msc != scm_msc:
            results["field_status"]["MSC"] = "FAIL"
            results["details"].append(f"Outer MSC SCM Mismatch: Label={msc}, SCM={scm_msc}")
            results["status"] = "FAIL"

    if pid:
        pid_counter = pid[-4:] if len(pid) >= 4 else "A001"
        logic_pid = construct_pid(scm_sku, scm_po, pid_counter)
        if pid != logic_pid:
            results["field_status"]["PID"] = "FAIL"
            results["details"].append(f"Outer PID Logic Mismatch: Expected {logic_pid}")
            results["status"] = "FAIL"
        if pid != scm_pid: # Changed from elif to if
            results["field_status"]["PID"] = "FAIL"
            results["details"].append(f"Outer PID SCM Mismatch: Label={pid}, SCM={scm_pid}")
            results["status"] = "FAIL"

    # User Request: If production is less than 5000 (e.g. 500), only validate relevant blocks
    # Determine if there's a global continuity/count mismatch to propagate to sub-blocks
    global_count_fail = (actual_scm_gap != expected_qty)
    max_blocks = (actual_scm_gap + 499) // 500
    
    # Determine if there are missing records
    # When records are missing from the batch, we cannot determine which specific MSN block
    # the missing data belongs to. Therefore, we fail ALL MSN blocks from A002 onwards.
    missing_records = expected_qty - actual_scm_gap
    has_missing_records = missing_records > 0 and start_idx != -1

    total_msn_qty = 0
    for i in range(1, 11):
        msn_key = f"MSN{i}"
        label_msn = label_data.get(msn_key, "")
        
        # If this block index exceeds the production quantity, skip if empty
        if i > max_blocks:
            if not label_msn:
                continue
            # If scanned but shouldn't be there according to QTY, we'll still validate if present
        
        if not label_msn:
            if i <= max_blocks:
                # Missing a block that should have been there
                results["field_status"][msn_key] = "FAIL"
                results["details"].append(f"Missing mandatory sub-block {msn_key} for quantity {actual_scm_gap}")
            continue

        # Each MSN block represents 500 records
        total_msn_qty += 500

        # USER REQUEST: Check if this specific 500-record segment is complete
        # Calculate position for this block
        block_start_pos = start_idx + ((i-1) * 500)
        
        # Calculate how many complete 500-record blocks we have based on actual record count
        # If we have 4999 records, we have 9 complete blocks (4500) + 1 incomplete block (499)
        complete_blocks = actual_scm_gap // 500
        remaining_records = actual_scm_gap % 500
        
        # Check if this block is complete or incomplete
        # ALL blocks fail if there are missing records - we cannot determine which block is affected
        if i <= complete_blocks:
            # This block has 500 records - check if there are any missing records overall
            if has_missing_records:
                # Even full blocks fail because we don't know where the gap is
                results["field_status"][msn_key] = "FAIL"
                results["details"].append(f"{msn_key}: Data Missing in Batch")
                results["status"] = "FAIL"
                continue
            # No missing records - get block for further validation
            block = scm_reader.get_block(block_start_pos, 500)
        elif i == complete_blocks + 1 and remaining_records > 0:
            # This block has partial records - fail
            results["field_status"][msn_key] = "FAIL"
            results["details"].append(f"{msn_key}: Data Missing in Batch")
            results["status"] = "FAIL"
            continue
        else:
            # This block has no records - fail
            results["field_status"][msn_key] = "FAIL"
            results["details"].append(f"{msn_key}: Data Missing in Batch")
            results["status"] = "FAIL"
            continue
        
        # SCM record for this specific sub-block start
        block_record = block[0]
        scm_msn = block_record.get("MSN", "")
        
        # Logic check (Use Sequential Counter A001-A010 for sub-blocks)
        counter = f"A{str(i).zfill(3)}"
        logic_msn = construct_msn(scm_sku, scm_po, counter)
        
        if label_msn != logic_msn:
            results["field_status"][msn_key] = "FAIL"
            results["details"].append(f"{msn_key} Logic Mismatch: Expected {logic_msn}")
            results["status"] = "FAIL"
        if label_msn and label_msn != scm_msn: # Fixed: changed elif to if and added status=FAIL
            results["field_status"][msn_key] = "FAIL"
            results["details"].append(f"{msn_key} SCM Mismatch at block {i}")
            results["status"] = "FAIL"
            
    # Remove redundant/repeated MSC check below for clarity
    # MSC Count Mismatch Logic
    if msc:
        msc_label_qty = label_batch_qty # Usually 5000
        # print(f"[MSC] Count Check: MSN_SUM={total_msn_qty}, SCM_GAP={actual_scm_gap}, Label_QTY={msc_label_qty}")
        
        if total_msn_qty != msc_label_qty or actual_scm_gap != msc_label_qty:
            results["field_status"]["MSC"] = "FAIL"
            missing = msc_label_qty - actual_scm_gap if actual_scm_gap < msc_label_qty else 0
            if missing > 0:
                results["details"].append(f"MSC: ICCID Present but {missing} Data Missing")
            else:
                results["details"].append(f"Count Mismatch: Sum MSN={total_msn_qty}, SCM Records={actual_scm_gap}, Label QTY={msc_label_qty}")
            results["status"] = "FAIL"

    # Circle Validation for Outer (Ensuring it's also checked at the end/consolidated)
    circle = str(label_data.get("Circle", label_data.get("CIRCLE", ""))).strip()
    if gui_circle is not None:
        if circle.upper() != gui_circle.upper():
            results["field_status"]["Circle"] = "FAIL"
            results["field_status"]["CIRCLE"] = "FAIL"
            results["details"].append(f"Circle Mismatch (Outer): Scanned={circle}, Expected={gui_circle}")
            results["status"] = "FAIL"
        else:
            results["field_status"]["Circle"] = "PASS"
            results["field_status"]["CIRCLE"] = "PASS"

    if any(s == "FAIL" for s in results["field_status"].values()):
        results["status"] = "FAIL"
    
    return results
