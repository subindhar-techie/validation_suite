import re
import csv

def extract_value(response_line, prefix, length=None):
    """Extract hex string after prefix from response_line."""
    pattern = re.escape(prefix) + r'([0-9A-Fa-f]+)'
    print(f"Pattern: {pattern}")  # Debugging
    match = re.search(pattern, response_line)
    if match:
        val = match.group(1)  # Extract the matched value
        if length:
            val = val[:length]  # Limit the length if needed
        return val.upper()  # Ensure the value is in uppercase for consistency
    return None

def extract_from_pcom(file_path, line_num, pattern):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        if line_num is not None:
            # Extract from a specific line with a literal prefix (like "%HOME_IMSI")
            if line_num - 1 < len(lines):
                line = lines[line_num - 1].strip()
                # Escape the prefix for regex match
                regex_pattern = re.escape(pattern) + r'([0-9A-Fa-f]+)'
                match = re.search(regex_pattern, line)
                if match:
                    return match.group(1)
        else:
            # If line_num is None, pattern is a full regex, so search entire file line-by-line
            for line in lines:
                match = re.search(pattern, line)
                if match:
                    return match.group(1)
    except Exception as e:
        print(f"Error extracting from PCOM: {e}")
    return None

def extract_from_cnum(file_path, line_num, col_idx, special_logic=False):
    """Extract value from CNUM file with optional special logic."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter='\t')
            for i, row in enumerate(reader):
                if i == line_num - 1:  # Correcting for 0-indexed row
                    if col_idx < len(row):  # Ensure column exists
                        value = row[col_idx].strip()
                        
                        # Debugging print to verify what's in that column
                        print(f"Line {i + 1}, Column {col_idx}: {value}")  # Debugging print

                        # Apply special logic: Only take the first value if multiple are found
                        if special_logic:
                            values = value.split()
                            print(f"Special logic applied, first value: {values[0]}")  # Debugging print
                            return values[0] if values else None
                        return value
                    else:
                        print(f"Column {col_idx} out of bounds for row {i + 1}.")
    except Exception as e:
        print(f"Error extracting from CNUM: {e}")
    return None

def extract_from_scm(file_path, line_num, col_idx):
    """Extract value from SCM file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter='\t')  # Using tab delimiter
            for i, row in enumerate(reader):
                if i == line_num - 1:  # Ensure we are at the correct line
                    if col_idx < len(row):  # Ensure column index is valid
                        return row[col_idx].strip()  # Return the value at the specified column
                    else:
                        print(f"Error: Column {col_idx} out of bounds on line {i + 1}")
    except Exception as e:
        print(f"Error: {e}")
    return None

def extract_multiple_keys(file_path, pattern):
    """Extract all matching values from SIM ODA file using the pattern."""
    matches = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                match = re.search(pattern, line.strip())
                if match:
                    matches.append(match.group(1))
    except Exception as e:
        print(f"Error reading SIM ODA file: {e}")
    return matches

def extract_from_sim_oda(file_path, base_line_num, pattern, search_range=2, fallback=False):
    """Extract value from SIM ODA file by searching around the base line number, with optional full-file fallback."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        # Search ±search_range lines around base_line_num
        start = max(0, base_line_num - search_range - 1)
        end = min(len(lines), base_line_num + search_range)
        for i in range(start, end):
            line = lines[i].strip()
            match = re.search(pattern, line)
            if match:
                return match.group(1)
        # If not found, do full file scan (optional)
        if fallback:
            for line in lines:
                match = re.search(pattern, line.strip())
                if match:
                    return match.group(1)
    except Exception as e:
        print(f"Error reading file: {e}")
    return None