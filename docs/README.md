# Jio_Validation_Suite Documentation

## Business Overview

Jio_Validation_Suite is a **Quality Assurance (QA) desktop application** used in **SIM card manufacturing** to ensure that SIM cards are properly programmed and match the expected records from network operators.

---

## The Business Problem

In SIM card manufacturing:
1. **Manufacturing plants** program SIM cards with customer data (ICCID, IMSI, etc.)
2. **Network operators** (Jio, Airtel) provide data files listing what should be programmed
3. **QA teams** need to verify:
   - Each SIM card has correct data programmed
   - The operator's records match what was actually programmed
   - The machines followed the correct programming scripts

**Jio_Validation_Suite automates this verification process** to prevent:
- Wrong SIM cards being shipped to customers
- Duplicate or missing ICCIDs
- Data mismatches between operator records and manufactured cards

---

## The Solution: Three Validation Modules

| Module | What It Validates | Why It Matters |
|--------|-------------------|----------------|
| **First Card Validation** | Individual SIM cards - comparing QR code scan vs master file | Ensures each SIM card is programmed correctly before shipping |
| **MNO File Validation** | Bulk files - operator data vs supplier records | Ensures batch totals match between operator and manufacturer |
| **Machine Log Validation** | Programming scripts vs actual machine operations | Ensures machines executed commands correctly |

---

## Folder Structure

The project is organized as follows:

```
Jio_Validation_Suite/
├── src/                          # Main source code
│   ├── main.py                   # Application entry point
│   ├── gui/                      # Graphical User Interface
│   │   ├── main_window.py        # Main window of the application
│   │   ├── theme.py              # Colors and styling
│   │   └── tabs/                 # Different validation tabs
│   │       ├── first_card_tab.py      # First card validation tab
│   │       ├── mno_file_tab.py        # MNO file validation tab
│   │       └── machine_log_tab.py     # Machine log validation tab
│   └── modules/                  # Core validation logic
│       ├── first_card_validation/     # First card validation module
│       ├── mno_file_validator/        # MNO file validation module
│       └── machine_log_validation/   # Machine log validation module
├── assets/                       # Images and icons
├── docs/                         # Documentation
├── tests/                        # Test files
└── scripts/                     # Helper scripts
```

---

## How the Application Works

1. **User Interface (GUI)**
   - The app opens a window with three tabs
   - Each tab handles a different type of validation
   - Users select files using buttons and see results in text areas

2. **Validation Flow**
   ```
   User selects files → System reads data → Validation checks data → Results shown
   ```

3. **Reports**
   - After validation, the system creates Excel reports
   - Reports show pass/fail status for each item
   - Reports help identify problems in SIM card data

---

## First_Card_Validation

### Business Purpose
This module validates **individual SIM cards** at the start of production. Before shipping a batch of SIM cards, QA teams must verify that the first card (sample) is programmed correctly. This catches programming errors early before an entire batch is processed.

### The Validation Process
1. **Scan QR Code** - The SIM card has a QR code printed on it containing the ICCID (SIM card serial number)
2. **Read Master File** - The SCM file contains all SIM cards that should be in the batch
3. **Match by ICCID** - Find the matching record in the master file using the ICCID from QR scan
4. **Compare All Fields** - Verify SKU, PO number, and other data match exactly
5. **Report Results** - Generate Excel report showing pass/fail for each field

### Why This Matters
- If the first card is wrong, the entire batch might be wrong
- QR scanning ensures no manual entry errors
- Excel reports serve as audit trail for quality records

### Required Inputs

**For JIO Operator:**
| Input File | Description | File Type |
|------------|-------------|-----------|
| Machine Log | Shows what was programmed on the SIM card | .txt |
| SCM File | Master record with all SIM card details | .txt |
| SIM ODA File | Operator data agreement file | .txt |
| QR Code Image | Photo of QR code on SIM card | .jpg, .png |

**For Airtel Operator:**
| Input File | Description | File Type |
|------------|-------------|-----------|
| Machine Log | Shows what was programmed on the SIM card | .txt |
| PCOM File | Production communication file | .txt |
| CNUM File | Customer number file | .txt |
| CPS File | Card personalization system file | .txt |
| QR Code Image | Photo of QR code on SIM card | .jpg, .png |

### JIO Profile Types
- **MOB**: Mobile profile - requires INNER LABEL 100 image
- **WBIOT**: Wideband IoT profile
- **NBIOT**: Narrowband IoT profile

### How It Works (Step by Step)

**Step 1: Select Operator**
- Choose JIO or Airtel from dropdown

**Step 2: Select Profile (JIO only)**
- Choose MOB, WBIOT, or NBIOT

**Step 3: Select Required Files**
- Browse and select each input file
- For JIO: Machine Log, SCM, SIM ODA, and QR image
- For Airtel: Machine Log, PCOM, CNUM, CPS, and QR image

**Step 4: Run Validation**
- Click "Run Validation" button

**Step 5: Processing**
1. System reads the QR code image
2. Extracts ICCID (SIM card number) from QR code
3. Reads SCM file to get all expected records
4. Finds matching record using ICCID
5. Compares all fields (SKU, PO, etc.)
6. Generates Excel report

### Output
- Excel report showing pass/fail for each field
- Details of what matched and what didn't

### Key Files
- `jio_validator.py` - Validates Jio SIM cards
- `airtel_validation.py` - Validates Airtel SIM cards
- `qr_processor.py` - Reads QR codes from images
- `validation_engine.py` - Main validation logic
- `excel_generator.py` - Creates Excel reports

---

## MNO_Validation

### Business Purpose
MNO (Mobile Network Operator) validation compares **batch totals** between what the operator (Jio/Airtel) sent and what the manufacturer delivered. This is a **reconciliation process** to ensure no SIM cards are missing or duplicated.

### The Business Scenario
1. **Operator sends**: SIMODA file with list of ICCIDs to be programmed
2. **Manufacturer programs**: SIM cards and creates SCM file as proof
3. **QA validates**: Compare the two files to ensure they match

### The Validation Process
1. **Read SIMODA files** - These come from the network operator (INPUT folder)
2. **Read SCM files** - These are generated by the manufacturer (OUTPUT folder)
3. **Compare quantities** - Does the batch have the same number of cards?
4. **Match ICCIDs** - Are all ICCIDs present in both files?
5. **Validate data fields** - Are dates, codes, and formats correct?
6. **Generate report** - Excel report showing reconciliation results

### Why This Matters
- Prevents financial losses from missing SIM cards
- Ensures operator billing matches actual deliveries
- Provides audit trail for inventory reconciliation

### Required Inputs

| Input | Description |
|-------|-------------|
| INPUT Folder | Folder containing .txt files (SIMODA files) |
| OUTPUT Folder | Folder containing subfolders with SCM files |

### Folder Structure Expected

```
INPUT Folder (selected by user):
├── SIMODA_001.txt
├── SIMODA_002.txt
└── ...

OUTPUT Folder (selected by user):
├── Batch_001/
│   └── SCM.txt
├── Batch_002/
│   └── SCM.txt
└── ...
```

### How It Works (Step by Step)

**Step 1: Select INPUT Folder**
- Browse and select folder containing SIMODA files
- These are .txt files from the network operator

**Step 2: Select OUTPUT Folder**
- Browse and select folder containing SCM subfolders
- Each subfolder has an SCM.txt file

**Step 3: Run Validation**
- Click "Validate" button

**Step 4: Processing**
1. System reads all SIMODA files from INPUT folder
2. For each batch in OUTPUT folder:
   - Reads SCM file
   - Compares quantities
   - Validates all ICCIDs match
   - Checks data fields (dates, codes)
   - Validates headers
3. Generates Excel report with results

### Validation Checks
- **Header Validation**: First 15 lines match between files
- **Quantity Check**: Number of SIMs match
- **ICCID Match**: All SIM card numbers present in both files
- **Data Field Validation**: All fields have correct data
- **SCM Structure**: File follows correct format

### Output
- Excel report showing:
  - Which batches passed
  - Which batches failed
  - Details of differences
  - Summary statistics

### Key Files
- `file_comparator.py` - Main comparison logic
- `header_validator.py` - Checks file headers
- `data_field_validator.py` - Validates data fields
- `scm_validator.py` - Validates SCM files
- `simoda_validator.py` - Validates SIMODA files
- `excel_report_generator.py` - Creates Excel reports
- `file_utils.py` - File reading and processing helpers

---

## Machine_Log_Validation

### Business Purpose
This module validates that the **programming machine executed commands correctly**. The machine follows a script (what should happen) and generates a log (what actually happened). QA teams need to verify the machine didn't skip any steps or produce errors.

### The Business Scenario
1. **Script file** - Created by engineers, specifies what commands to run (WRITE ICCID, WRITE IMSI, VERIFY, etc.)
2. **Machine execution** - The SIM programming machine runs these commands
3. **Machine log** - Records what actually happened during execution
4. **Validation** - Compare script commands with log entries to ensure full execution

### The Validation Process
1. **Read script file** - Contains programming commands (what SHOULD happen)
2. **Read machine log** - Contains actual operations (what DID happen)
3. **Match commands** - Line-by-line comparison of expected vs actual
4. **Track statistics** - Count passed, failed, skipped, and not-found operations
5. **Generate report** - Text report showing execution results

### Why This Matters
- Catches machine malfunctions before they affect many cards
- Ensures all SIM cards in a batch were fully programmed
- Provides evidence of proper manufacturing process for audits

### Data Conversion Features
The system handles different machine log formats:
- **Hex to ASCII**: Machine logs often use hex format for data
- **IMSI Swapping**: Some systems swap digit pairs and need correction

### Required Inputs

| Input File | Description | File Type |
|------------|-------------|-----------|
| Variable Script File | Programming commands - what SHOULD happen | .txt |
| Machine Log File | Actual operations - what DID happen | .txt |

### How It Works (Step by Step)

**Step 1: Select Variable Script File**
- Browse and select the script file
- Contains programming commands like:
  - WRITE ICCID
  - WRITE IMSI
  - VERIFY
  - ERASE

**Step 2: Select Machine Log File**
- Browse and select the machine log
- Contains actual operations performed

**Step 3: Run Validation**
- Click "Validate Machine Log" button

**Step 4: Processing**
1. System reads script file line by line
2. Reads machine log file line by line
3. Matches commands with log entries:
   - Extracts ICCID from both files
   - Extracts IMSI from both files
   - Compares each operation
4. Tracks statistics:
   - Passed: Commands matched successfully
   - Failed: Commands didn't match
   - Skipped: Lines skipped for alignment
   - Not Found: Commands in script but not in log

### Data Conversion
The system can convert:
- **Hex to ASCII**: Machine logs often use hex format
- **IMSI Swapping**: Some systems swap digit pairs

### Output
- Text log showing:
  - Total commands processed
  - Pass/fail/skip counts
  - Detailed results for each command

### Key Files
- `script_validator.py` - Main validation logic
- `helpers.py` - Helper functions

---

## Summary Table

| Module | Input Files | Output | Purpose |
|--------|-------------|--------|---------|
| First_Card_Validation (JIO) | Machine Log, SCM, SIM ODA, QR Image | Excel report | Validate Jio SIM cards |
| First_Card_Validation (Airtel) | Machine Log, PCOM, CNUM, CPS, QR Image | Excel report | Validate Airtel SIM cards |
| MNO_Validation | INPUT folder (SIMODA files), OUTPUT folder (SCM files) | Excel report | Compare operator files with supplier records |
| Machine_Log_Validation | Script file, Machine log file | Text report | Verify machine programming operations |

---

## Building the Application

### What is the `_internal` folder?

When you build the application using PyInstaller, it creates a folder called `_internal` next to your .exe file. This folder contains **all the supporting files** that Python needs to run your app.

Think of it like this:
- Your app needs many helper programs (like tkinter for buttons, openpyxl for Excel, PIL for images)
- These helpers are packed into the `_internal` folder
- Without this folder, your app cannot start

**Do not delete this folder!** Keep it together with the .exe file.

### Expected folder structure after build:
```
dist/
└── Data Validation Tool/
    ├── Data Validation Tool.exe    ← Your app
    └── _internal/                  ← Required helper files (KEEP THIS)
        ├── tkinter/
        ├── PIL/
        ├── openpyxl/
        └── ...
```

## Key Business Terms

| Term | Full Name | Business Meaning |
|------|-----------|------------------|
| **ICCID** | Integrated Circuit Card Identifier | Unique serial number printed on each SIM card - like a fingerprint |
| **IMSI** | International Mobile Subscriber Identity | Mobile network ID that connects SIM to carrier network |
| **SCM** | Supply Chain Management file | Manufacturer's record of all SIM cards in a batch |
| **SIMODA** | SIM Operator Data Agreement | Network operator's record of SIM cards they ordered |
| **SKU** | Stock Keeping Unit | Product code identifying SIM card type |
| **PO** | Purchase Order | Order number from network operator |
| **QR Code** | Quick Response code | Barcode on SIM card containing ICCID for scanning |
| **PCOM** | Production Communication file | Airtel's production data file |
| **CNUM** | Customer Number file | Airtel's customer assignment file |
| **CPS** | Card Personalization System file | Airtel's card programming specification |
| **MOB** | Mobile profile | Standard mobile SIM card type |
| **WBIOT** | Wideband IoT profile | 4G IoT SIM card type |
| **NBIOT** | Narrowband IoT profile | LPWAN IoT SIM card type |

---

## Typical QA Workflow

```
1. Receive SIMODA file from Jio/Airtel
         ↓
2. Program SIM cards using machine
         ↓
3. Run First Card Validation (sample check)
         ↓
4. Run Machine Log Validation (verify execution)
         ↓
5. Generate SCM file as proof
         ↓
6. Run MNO Validation (reconcile totals)
         ↓
7. Ship SIM cards with Excel audit report
```

---

## Summary Table

| Module | Input Files | Output | Business Question Answered |
|--------|-------------|--------|----------------------------|
| First_Card_Validation (JIO) | Machine Log, SCM, SIM ODA, QR Image | Excel report | Is this SIM card programmed correctly? |
| First_Card_Validation (Airtel) | Machine Log, PCOM, CNUM, CPS, QR Image | Excel report | Is this SIM card programmed correctly? |
| MNO_Validation | INPUT folder (SIMODA), OUTPUT folder (SCM) | Excel report | Do operator records match manufacturer records? |
| Machine_Log_Validation | Script file, Machine log | Text report | Did the machine execute all commands correctly? |
