import re
import os
import sys
from typing import Dict, List, Optional, Tuple, Any

class ScriptValidator:
    def __init__(self):
        self.script_commands = []
        self.machine_logs = []
        self.validation_results = []
        self.extracted_fields = {}
        self.field_values = {}
        
        # Track skipped lines for alignment
        self.script_skipped_count = 0
        self.machine_log_skipped_count = 0
        self.debug_mode = True
        
        # Statistics
        self.stats = {
            'total_commands': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'not_found': 0
        }

    @staticmethod
    def swap_pairs(hex_string: str) -> str:
        """Swap pairs of hex digits (used for IMSI)"""
        if len(hex_string) % 2 != 0:
            return hex_string
        swapped = ""
        for i in range(0, len(hex_string), 2):
            if i + 1 < len(hex_string):
                swapped += hex_string[i + 1] + hex_string[i]
        return swapped

    @staticmethod
    def hex_to_ascii(hex_string: str) -> str:
        """Convert hex string to ASCII"""
        try:
            ascii_string = ""
            for i in range(0, len(hex_string), 2):
                if i + 1 < len(hex_string):
                    hex_pair = hex_string[i:i + 2]
                    ascii_char = chr(int(hex_pair, 16))
                    if ascii_char.isprintable():
                        ascii_string += ascii_char
                    else:
                        ascii_string += "."
            return ascii_string
        except:
            return hex_string

    @staticmethod
    def ascii_to_hex(ascii_string: str) -> str:
        """Convert ASCII string to hex"""
        try:
            hex_string = ""
            for char in ascii_string:
                hex_string += format(ord(char), '02X')
            return hex_string
        except:
            return ascii_string

    @staticmethod
    def calculate_acc_from_imsi(imsi_hex: str) -> str:
        """Calculate ACC value from IMSI (2^last_digit of SWAPPED IMSI)"""
        try:
            if not imsi_hex:
                return "0001"
            
            # Swap the IMSI first
            swapped_imsi = ScriptValidator.swap_pairs(imsi_hex)
            
            # Get last digit of SWAPPED IMSI (in hex)
            last_digit_hex = swapped_imsi[-1]
            
            # Convert hex digit to integer
            last_digit = int(last_digit_hex, 16)
            
            # Calculate 2^last_digit
            acc_value = 2 ** last_digit
            
            # Convert to 4-digit hex with leading zeros
            acc_hex = f"{acc_value:04X}"
            
            return acc_hex
        except Exception as e:
            print(f"Error calculating ACC from IMSI: {e}")
            return "0001"

    def parse_script_file(self, script_path: str) -> bool:
        """Parse Variable Script file according to the specified format"""
        try:
            with open(script_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
                
                self.script_skipped_count = 0
                script_lines_to_process = []
                
                # Step 0: Skip Initial Irrelevant Lines
                for line_num, line in enumerate(lines, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Skip patterns: 0012000000SW9000, PPS:, AES_
                    if (line.startswith("0012000000SW9000") or 
                        line.startswith("PPS:") or 
                        line.startswith("AES_")):
                        if self.debug_mode and line_num <= 5:
                            print(f"SKIP SCRIPT: Skipping irrelevant script line {line_num}: {line[:50]}...")
                        self.script_skipped_count += 1
                        continue
                    
                    script_lines_to_process.append((line_num, line))
                
                print(f"✅ Filtered {len(script_lines_to_process)} script lines for validation")
                print(f"📊 Skipped {self.script_skipped_count} script lines")
                
                # Parse filtered lines
                for line_num, line in script_lines_to_process:
                    command = self._parse_variable_script_line_complete(line, line_num)
                    if command:
                        self.script_commands.append(command)
                        
            print(f"✅ Parsed {len(self.script_commands)} script commands")
            
            # Debug first 5 commands
            if self.debug_mode and self.script_commands:
                print("\n🔍 First 5 script commands:")
                for i, cmd in enumerate(self.script_commands[:5]):
                    apdu_preview = cmd.get('apdu', '')
                    if len(apdu_preview) > 30:
                        apdu_preview = apdu_preview[:30] + "..."
                    print(f"  {i+1}: Type='{cmd.get('type')}', APDU='{apdu_preview}', SW='{cmd.get('expected_sw', '')}'")
                    if cmd.get('result_field'):
                        print(f"     Result Field: {cmd.get('result_field')}")
                    if cmd.get('field_names'):
                        print(f"     Field Names: {cmd.get('field_names')}")
            
            return True
        except Exception as e:
            print(f"❌ Error parsing script file: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _parse_variable_script_line_complete(self, line: str, line_num: int) -> Optional[Dict]:
        """COMPLETE: Parse variable script line - FIXED LOGIC"""
        line = line.strip()
        if not line:
            return None
            
        # Skip PPS lines
        if "PPS:96SWFFFF" in line:
            return {"type": "skip", "original_line": line}
        
        # Skip complex C02C lines
        if 'C02C010022' in line and 'SW9000' in line:
            return {"type": "skip", "original_line": line}
        
        if self.debug_mode and line_num <= 3:
            print(f"DEBUG PARSING line {line_num}: {line}")
        
        # ============================================================
        # FIXED: Check for RESULT patterns FIRST
        # ============================================================
        
        # Pattern 1: Command + SW + RESULT with <FIELD> or %FIELD%
        # Examples: 
        # 00B0000003SW9000RESULT<MCCMNC>
        # 00B0000009SW9000RESULT%HOME_IMSI%
        result_field_pattern = r'^([A-F0-9]+)SW([0-9A-F]{4})RESULT([<%])([^>%]+)[>%]$'
        result_match = re.match(result_field_pattern, line)
        
        if result_match:
            apdu_part = result_match.group(1)
            expected_sw = result_match.group(2)
            delimiter = result_match.group(3)  # < or %
            result_field = result_match.group(4)
            
            return {
                'line_num': line_num,
                'original_line': line,
                'apdu': apdu_part,
                'expected_sw': expected_sw,
                'result_field': result_field,
                'type': 'command_sw_result_field'
            }
        
        # Pattern 2: Command + SW + RESULT hex
        # Example: 0026000102SW9000RESULTAF99
        result_hex_pattern = r'^([A-F0-9]+)SW([0-9A-F]{4})RESULT([0-9A-F]+)$'
        result_hex_match = re.match(result_hex_pattern, line)
        
        if result_hex_match:
            apdu_part = result_hex_match.group(1)
            expected_sw = result_hex_match.group(2)
            expected_result = result_hex_match.group(3)
            
            return {
                'line_num': line_num,
                'original_line': line,
                'apdu': apdu_part,
                'expected_sw': expected_sw,
                'expected_result': expected_result,
                'type': 'command_sw_result'
            }
        
        # ============================================================
        # Pattern 3: Command with field placeholders + SW
        # Example: 00D600002AFE85410110<PSK>FE80410210<DEK1>SW9000
        # ============================================================
        if 'SW' in line:
            sw_match = re.search(r'SW([0-9A-F]{4})$', line)
            if sw_match:
                expected_sw = sw_match.group(1)
                sw_start = line.rfind('SW')
                command_part = line[:sw_start]
                
                # Check for field placeholders in command part
                if '%' in command_part or '<' in command_part:
                    field_names_percent = re.findall(r'%([^%]+)%', command_part)
                    field_names_angle = re.findall(r'<([^>]+)>', command_part)
                    field_names = field_names_percent + field_names_angle
                    
                    return {
                        'line_num': line_num,
                        'original_line': line,
                        'apdu': command_part,
                        'expected_sw': expected_sw,
                        'field_names': field_names,
                        'type': 'command_with_fields_sw'
                    }
                
                # Pattern 4: Simple Command + SW
                return {
                    'line_num': line_num,
                    'original_line': line,
                    'apdu': command_part,
                    'expected_sw': expected_sw,
                    'type': 'command_sw'
                }
        
        # ============================================================
        # Pattern 5: Commands with field placeholders but no SW
        # ============================================================
        if '%' in line or '<' in line:
            field_names_percent = re.findall(r'%([^%]+)%', line)
            field_names_angle = re.findall(r'<([^>]+)>', line)
            field_names = field_names_percent + field_names_angle
            
            return {
                'line_num': line_num,
                'original_line': line,
                'apdu': line,
                'field_names': field_names,
                'type': 'command_with_fields'
            }
        
        if self.debug_mode:
            print(f"⚠️  Unrecognized pattern in script line {line_num}: {line[:50]}...")
        return None
                
    def parse_machine_log(self, log_path: str) -> bool:
        """Parse machine log file - COMPLETE PARSING"""
        try:
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
                
                print(f"📄 Total lines in machine log: {len(lines)}")
                
                # Parse all lines
                parsed_count = 0
                apdu_count = 0
                
                for line_num, line in enumerate(lines, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    log_entry = self._parse_machine_log_line_complete(line, line_num)
                    if log_entry:
                        self.machine_logs.append(log_entry)
                        parsed_count += 1
                        if log_entry.get('apdu'):
                            apdu_count += 1
                
                print(f"✅ Successfully parsed {parsed_count} machine log entries")
                print(f"📊 Found {apdu_count} APDU commands in machine log")
                
                # Debug sample
                if self.debug_mode and apdu_count > 0:
                    print("\n🔍 Sample APDU commands from machine log:")
                    apdu_entries = [log for log in self.machine_logs if log.get('apdu')]
                    for i, log in enumerate(apdu_entries[:3]):
                        print(f"  {i+1}: APDU='{log.get('apdu', '')[:30]}...', SW={log.get('sw', 'N/A')}, RESULT={log.get('result', 'N/A')}")
                
                return parsed_count > 0
        except Exception as e:
            print(f"❌ Error parsing machine log: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _parse_machine_log_line_complete(self, line: str, line_num: int) -> Optional[Dict]:
        """COMPLETE: Parse machine log line - ADDED SUPPORT FOR ALL SW/EXP FORMATS"""
        line = line.strip()
        if not line:
            return None
        
        # Skip complex C02C lines
        if 'C02C010022' in line and 'SW9000' in line and 'IN[' in line:
            return None
        
        # ============================================================
        # NEW: Handle IN[APDU] OUT[DATA] format FIRST
        # Example: IN[C027008028] OUT[07037F6B696D343030307810FFFFFFFFFFFFFFFFFFF1234567890CC00490807006C10300651700009000]
        # ============================================================
        in_out_match = re.search(r'IN\[([A-F0-9]+)\]\s+OUT\[([A-F0-9]+)\]', line)
        if in_out_match:
            apdu_value = in_out_match.group(1).upper()
            out_data = in_out_match.group(2).upper()
            
            # Extract SW from OUT data (last 4 chars)
            sw_value = None
            receive_value = out_data  # Store full OUT data as receive
            
            if len(out_data) >= 4:
                sw_value = out_data[-4:]  # Last 4 chars are SW
            
            # Debug output
            if self.debug_mode and line_num <= 10:
                print(f"  Parsed IN[]OUT[] format line {line_num}: APDU={apdu_value}, OUT={out_data[:20]}..., SW={sw_value}")
            
            return {
                'line_num': line_num,
                'original_line': line,
                'apdu': apdu_value,
                'sw': sw_value,
                'out': sw_value,  # SW value for OUT field
                'receive': receive_value,  # Full OUT data
                'result': None,
                'has_placeholder': False,
                'type': 'apdu_command'
            }
        
        # ============================================================
        # APDU EXTRACTION (original logic for other formats)
        # ============================================================
        apdu_value = None
        
        # Format 1: APDU in brackets [0050000010...]
        bracket_match = re.search(r'\[([A-F0-9]+)\]', line)
        if bracket_match:
            apdu_value = bracket_match.group(1)
        
        # Format 2: APDU=0050000010...
        if not apdu_value:
            apdu_eq_match = re.search(r'APDU\s*=\s*([A-F0-9]+)', line, re.IGNORECASE)
            if apdu_eq_match:
                apdu_value = apdu_eq_match.group(1)
        
        # Format 3: Command at beginning
        if not apdu_value:
            command_match = re.match(r'^([A-F0-9]{4,})', line)
            if command_match:
                apdu_value = command_match.group(1)
        
        # Format 4: Hex string without prefix
        if not apdu_value:
            hex_match = re.search(r'\b([A-F0-9]{10,})\b', line)
            if hex_match:
                apdu_value = hex_match.group(1)
        
        if not apdu_value:
            return None
        
        # ============================================================
        # STATUS WORD EXTRACTION - SUPPORTS ALL SW/EXP FORMATS
        # ============================================================
        sw_value = None
        exp_value = None
        out_value = None
        expect_value = None   # For EXPECT:XXXX format
        receive_value = None  # For RECEIVE:XXXX format
        
        # NEW: Check for EXPECT:XXXX RECEIVE:XXXX format
        expect_receive_match = re.search(r'EXPECT\s*:\s*([0-9A-F]{3,4})\s+RECEIVE\s*:\s*([0-9A-F]+)', line, re.IGNORECASE)
        if expect_receive_match:
            expect_value = expect_receive_match.group(1).upper()
            receive_value = expect_receive_match.group(2).upper()
            # In EXPECT:RECEIVE format, EXPECT is the expected SW, RECEIVE is actual response
            # SW should be extracted from RECEIVE (last 4 chars)
            if receive_value and len(receive_value) >= 4:
                sw_value = receive_value[-4:]  # Take last 4 chars as SW
            exp_value = expect_value
        
        # Check for OUT[XXXX] format (standalone OUT, not part of IN[]OUT[])
        if not out_value:
            out_match = re.search(r'OUT\[([0-9A-F]+)\]', line)
            if out_match:
                out_data = out_match.group(1).upper()
                out_value = out_data
                receive_value = out_data  # Store as receive
                # Extract SW from OUT data
                if len(out_data) >= 4 and not sw_value:
                    sw_value = out_data[-4:]  # Last 4 chars are SW
        
        # ============================================================
        # EXTRACT SW AND EXP - HANDLES ALL FORMATS AND ORDERS
        # ============================================================
        
        # 1. Try SW= EXP= format (equal sign, SW first)
        if not sw_value or not exp_value:
            sw_exp_eq_match = re.search(r'SW\s*=\s*([0-9A-F]{3,4})\s+EXP\s*=\s*([0-9A-F]{3,4})', line, re.IGNORECASE)
            if sw_exp_eq_match:
                if not sw_value:
                    sw_value = sw_exp_eq_match.group(1).upper()
                if not exp_value:
                    exp_value = sw_exp_eq_match.group(2).upper()
        
        # 2. Try EXP= SW= format (equal sign, EXP first)
        if not sw_value or not exp_value:
            exp_sw_eq_match = re.search(r'EXP\s*=\s*([0-9A-F]{3,4})\s+SW\s*=\s*([0-9A-F]{3,4})', line, re.IGNORECASE)
            if exp_sw_eq_match:
                if not exp_value:
                    exp_value = exp_sw_eq_match.group(1).upper()
                if not sw_value:
                    sw_value = exp_sw_eq_match.group(2).upper()
        
        # 3. Try SW: EXP: format (colon, SW first)
        if not sw_value or not exp_value:
            sw_exp_colon_match = re.search(r'SW\s*:\s*([0-9A-F]{3,4})\s+EXP\s*:\s*([0-9A-F]{3,4})', line, re.IGNORECASE)
            if sw_exp_colon_match:
                if not sw_value:
                    sw_value = sw_exp_colon_match.group(1).upper()
                if not exp_value:
                    exp_value = sw_exp_colon_match.group(2).upper()
        
        # 4. Try EXP: SW: format (colon, EXP first)
        if not sw_value or not exp_value:
            exp_sw_colon_match = re.search(r'EXP\s*:\s*([0-9A-F]{3,4})\s+SW\s*:\s*([0-9A-F]{3,4})', line, re.IGNORECASE)
            if exp_sw_colon_match:
                if not exp_value:
                    exp_value = exp_sw_colon_match.group(1).upper()
                if not sw_value:
                    sw_value = exp_sw_colon_match.group(2).upper()
        
        # 5. Try SW alone (any format)
        if not sw_value:
            # Try SW= format
            sw_eq_match = re.search(r'SW\s*=\s*([0-9A-F]{3,4})', line, re.IGNORECASE)
            if sw_eq_match:
                sw_value = sw_eq_match.group(1).upper()
            else:
                # Try SW: format
                sw_colon_match = re.search(r'SW\s*:\s*([0-9A-F]{3,4})', line, re.IGNORECASE)
                if sw_colon_match:
                    sw_value = sw_colon_match.group(1).upper()
        
        # 6. Try EXP alone (any format)
        if not exp_value:
            # Try EXP= format
            exp_eq_match = re.search(r'EXP\s*=\s*([0-9A-F]{3,4})', line, re.IGNORECASE)
            if exp_eq_match:
                exp_value = exp_eq_match.group(1).upper()
            else:
                # Try EXP: format
                exp_colon_match = re.search(r'EXP\s*:\s*([0-9A-F]{3,4})', line, re.IGNORECASE)
                if exp_colon_match:
                    exp_value = exp_colon_match.group(1).upper()
        
        # Try EXPECT alone (if not in EXPECT:RECEIVE pair)
        if not expect_value:
            expect_single_match = re.search(r'EXPECT\s*:\s*([0-9A-F]{3,4})', line, re.IGNORECASE)
            if expect_single_match:
                expect_value = expect_single_match.group(1).upper()
                # If we have EXPECT but no SW/EXP, use it as EXP
                if not exp_value:
                    exp_value = expect_value
        
        # Try RECEIVE alone (if not in EXPECT:RECEIVE pair)
        if not receive_value:
            receive_single_match = re.search(r'RECEIVE\s*:\s*([0-9A-F]+)', line, re.IGNORECASE)
            if receive_single_match:
                receive_value = receive_single_match.group(1).upper()
                # If we have RECEIVE but no SW, extract SW from last 4 chars
                if not sw_value and len(receive_value) >= 4:
                    sw_value = receive_value[-4:]
        
        # FIXED: Priority for SW value
        if not sw_value:
            if out_value and len(out_value) >= 4:
                # Extract SW from OUT data
                sw_value = out_value[-4:]
            elif exp_value:
                sw_value = exp_value
            elif expect_value:
                sw_value = expect_value
            elif receive_value and len(receive_value) >= 4:
                # Fallback: Extract SW from last 4 chars of RECEIVE
                sw_value = receive_value[-4:]
        
        # ============================================================
        # RESULT EXTRACTION
        # ============================================================
        result_value = None
        exp_result_value = None
        
        # For IN[]OUT[] format, check if OUT contains result data before SW
        if out_value and sw_value and len(out_value) > 4:
            # Check if OUT ends with SW
            if out_value.endswith(sw_value):
                result_part = out_value[:-4]  # Remove SW from end
                if result_part:
                    result_value = result_part
        
        # RESULT=041123
        result_match = re.search(r'RESULT\s*=\s*([0-9A-F]+)', line, re.IGNORECASE)
        if result_match:
            result_value = result_match.group(1).upper()
        
        # EXPResult=041123
        exp_result_match = re.search(r'EXPResult\s*=\s*([0-9A-F]+)', line, re.IGNORECASE)
        if exp_result_match:
            exp_result_value = exp_result_match.group(1).upper()
        
        # ============================================================
        # CHECK FOR PLACEHOLDERS
        # ============================================================
        has_placeholder = False
        placeholder_name = None
        
        if re.search(r'RESULT\s*=\s*<[^>]+>', line) or re.search(r'RESULT\s*=\s*%[^%]+%', line):
            has_placeholder = True
            placeholder_match = re.search(r'RESULT\s*=\s*(<[^>]+>|%[^%]+%)', line)
            if placeholder_match:
                placeholder_name = placeholder_match.group(1)
        
        # Debug output
        if self.debug_mode and line_num <= 10:
            status_info = []
            if sw_value: status_info.append(f"SW={sw_value}")
            if exp_value: status_info.append(f"EXP={exp_value}")
            if out_value: status_info.append(f"OUT={out_value}")
            if expect_value: status_info.append(f"EXPECT={expect_value}")
            if receive_value: status_info.append(f"RECEIVE={receive_value}")
            
            print(f"  Parsed line {line_num}: APDU={apdu_value[:20]}..., "
                f"Status: {', '.join(status_info) if status_info else 'N/A'}, "
                f"RESULT={result_value[:10] if result_value else 'N/A'}...")
        
        return {
            'line_num': line_num,
            'original_line': line,
            'apdu': apdu_value,
            'sw': sw_value,
            'exp': exp_value,
            'out': out_value,
            'expect': expect_value,     # Store EXPECT separately
            'receive': receive_value,   # Store RECEIVE separately
            'result': result_value,
            'exp_result': exp_result_value,
            'has_placeholder': has_placeholder,
            'placeholder_name': placeholder_name,
            'type': 'apdu_command'
        }
                
    def find_script_command_in_machine_logs(self, script_cmd: Dict, start_index: int = 0) -> int:
        """FIND: Smart matching algorithm"""
        script_apdu = script_cmd.get('apdu', '')
        script_type = script_cmd.get('type', '')
        
        if not script_apdu:
            if self.debug_mode:
                print(f"  ❌ Script command has no APDU")
            return -1
        
        if self.debug_mode:
            print(f"\n🔍 Searching for: Type='{script_type}', APDU='{script_apdu}'")
        
        # Get just the command bytes (first 4-8 chars)
        # 00B0000003 -> 00B0 (4 chars)
        # 00D600002A -> 00D6 (4 chars)
        script_command = script_apdu[:4] if len(script_apdu) >= 4 else script_apdu
        
        for i in range(start_index, len(self.machine_logs)):
            machine_log = self.machine_logs[i]
            machine_apdu = machine_log.get('apdu', '')
            
            if not machine_apdu:
                continue
            
            # Get machine command
            machine_command = machine_apdu[:4] if len(machine_apdu) >= 4 else machine_apdu
            
            if self.debug_mode and i < 2:
                print(f"  Checking machine log {i}: APDU='{machine_apdu[:30]}...'")
            
            # ============================================================
            # MATCHING STRATEGY 1: Exact APDU match (for simple commands)
            # ============================================================
            if script_apdu == machine_apdu:
                if self.debug_mode:
                    print(f"  ✅ EXACT APDU MATCH at index {i}")
                return i
            
            # ============================================================
            # MATCHING STRATEGY 2: Command match (for read commands)
            # ============================================================
            if script_command == machine_command:
                # Additional check: for read commands (00B0, 00B2, etc.)
                if script_command in ['00B0', '00B2', '00B1']:
                    if self.debug_mode:
                        print(f"  ✅ READ COMMAND MATCH at index {i}: {script_command}")
                    return i
            
            # ============================================================
            # MATCHING STRATEGY 3: Script APDU contained in machine APDU
            # ============================================================
            if script_apdu in machine_apdu:
                if self.debug_mode:
                    print(f"  ✅ SCRIPT IN MACHINE MATCH at index {i}")
                return i
            
            # ============================================================
            # MATCHING STRATEGY 4: Machine APDU contained in script APDU
            # ============================================================
            if machine_apdu in script_apdu:
                if self.debug_mode:
                    print(f"  ✅ MACHINE IN SCRIPT MATCH at index {i}")
                return i
            
            # ============================================================
            # MATCHING STRATEGY 5: First 10 chars match
            # ============================================================
            min_len = min(len(script_apdu), len(machine_apdu), 10)
            if min_len >= 6 and script_apdu[:min_len] == machine_apdu[:min_len]:
                if self.debug_mode:
                    print(f"  ✅ FIRST {min_len} CHARS MATCH at index {i}")
                return i
        
        if self.debug_mode:
            print(f"  ❌ Not found in machine logs")
            print(f"  Looking for command like: {script_command}")
        
        return -1

    def validate_script_vs_machine_log(self) -> str:
        """MAIN: Complete validation logic"""
        self.validation_results = []
        self.field_values = {}
        
        # Reset statistics
        self.stats = {
            'total_commands': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'not_found': 0
        }
        
        if not self.script_commands:
            return "❌ ERROR: No script commands to validate"
        
        if not self.machine_logs:
            return "❌ ERROR: No machine log entries"
        
        print(f"\n🚀 Starting COMPLETE validation")
        print(f"   Script commands: {len(self.script_commands)}")
        print(f"   Machine logs: {len(self.machine_logs)}")
        
        current_machine_index = 0
        total_commands = len(self.script_commands)
        
        for script_index, script_cmd in enumerate(self.script_commands):
            self.stats['total_commands'] += 1
            
            if self.debug_mode and script_index < 5:
                print(f"\n{'='*60}")
                print(f"Processing script command {script_index + 1}/{total_commands}")
                script_line = script_cmd.get('original_line', '')
                if len(script_line) > 80:
                    script_line = script_line[:80] + "..."
                print(f"Script: {script_line}")
            
            # Skip commands
            if script_cmd.get('type') == 'skip':
                self.validation_results.append({
                    'script_line': script_cmd['original_line'],
                    'status': 'SKIPPED',
                    'message': 'Command skipped (ATR and PPS)'
                })
                self.stats['skipped'] += 1
                continue
            
            # Find this script command in machine logs
            found_index = self.find_script_command_in_machine_logs(script_cmd, current_machine_index)
            
            if found_index >= 0:
                machine_log = self.machine_logs[found_index]
                current_machine_index = found_index + 1
                
                # Validate the command
                validation_result = self._validate_single_command_complete(script_cmd, machine_log)
                self.validation_results.append(validation_result)
                
                if validation_result.get('status') == 'PASS':
                    self.stats['passed'] += 1
                else:
                    self.stats['failed'] += 1
            else:
                # Command not found
                self.validation_results.append({
                    'script_line': script_cmd['original_line'],
                    'status': 'FAIL',
                    'message': 'Script command not found in machine logs'
                })
                self.stats['not_found'] += 1
                self.stats['failed'] += 1
        
        # Generate final report
        return self._generate_complete_validation_report()

    def _validate_single_command_complete(self, script_cmd: Dict, machine_log: Dict) -> Dict:
        """VALIDATE: Complete validation for a single command - ADDED EXPECT/RECEIVE SUPPORT WITH FALLBACK LOGIC"""
        script_apdu = script_cmd.get('apdu', '')
        script_sw = script_cmd.get('expected_sw', '')
        script_type = script_cmd.get('type', '')
        script_result_field = script_cmd.get('result_field', '')
        script_expected_result = script_cmd.get('expected_result', '')
        script_field_names = script_cmd.get('field_names', [])
        
        machine_apdu = machine_log.get('apdu', '')
        machine_sw = machine_log.get('sw', '')
        machine_exp = machine_log.get('exp', '')
        machine_out = machine_log.get('out', '')
        machine_expect = machine_log.get('expect', '')     # Get EXPECT value
        machine_receive = machine_log.get('receive', '')   # Get RECEIVE value
        machine_result = machine_log.get('result', '')
        machine_exp_result = machine_log.get('exp_result', '')
        
        errors = []
        detailed_info = []
        
        if self.debug_mode:
            print(f"  Validating: Type={script_type}, APDU={script_apdu}")
            print(f"  Script SW: {script_sw}")
            status_info = []
            if machine_sw: status_info.append(f"SW={machine_sw}")
            if machine_exp: status_info.append(f"EXP={machine_exp}")
            if machine_out: status_info.append(f"OUT={machine_out}")
            if machine_expect: status_info.append(f"EXPECT={machine_expect}")
            if machine_receive: status_info.append(f"RECEIVE={machine_receive}")
            print(f"  Machine status: {', '.join(status_info) if status_info else 'None'}")
        
        # ============================================================
        # STEP 1: CHECK ALL STATUS VALUES - WITH FALLBACK LOGIC FOR RECEIVE AND OUT
        # ============================================================
        if script_sw:
            detailed_info.append(f"Expected status: {script_sw}")
            
            # Collect all status values found in machine log
            status_values_found = []
            status_messages = []
            
            # Check all possible status formats
            status_types = [
                ("SW", machine_sw),
                ("EXP", machine_exp),
                ("OUT", machine_out),
                ("EXPECT", machine_expect),
                ("RECEIVE", machine_receive)
            ]
            
            for status_type, status_value in status_types:
                if status_value:
                    status_values_found.append((status_type, status_value))
                    if status_type == "OUT":
                        status_messages.append(f"OUT[{status_value}]")
                    else:
                        status_messages.append(f"{status_type}={status_value}")
            
            # Report what we found
            if status_messages:
                detailed_info.append(f"Found in machine log: {', '.join(status_messages)}")
            else:
                errors.append("No status values found in machine log")
                detailed_info.append("ERROR: No status values found")
            
            # Check EACH status value against expected SW - WITH FALLBACK FOR RECEIVE AND OUT
            matching_status = []
            mismatching_status = []
            
            for status_type, status_value in status_values_found:
                if status_type == "RECEIVE":
                    # Check exact match first
                    if status_value == script_sw:
                        matching_status.append((status_type, status_value))
                        detailed_info.append(f"{status_type} MATCH: {status_value} == {script_sw} ✓")
                    else:
                        # FALLBACK: Check last 4 digits of RECEIVE
                        clean_receive = status_value.replace(' ', '').replace(',', '').upper()
                        if len(clean_receive) >= 4:
                            last_4_chars = clean_receive[-4:]
                            if last_4_chars == script_sw:
                                matching_status.append((status_type, f"RECEIVE[{last_4_chars}]"))
                                detailed_info.append(f"{status_type} last 4 chars match: ...{last_4_chars} == {script_sw} ✓")
                                # Remove any RECEIVE mismatch error that was added
                                errors = [e for e in errors if not e.startswith("RECEIVE mismatch")]
                            else:
                                mismatching_status.append((status_type, status_value))
                                errors.append(f"{status_type} mismatch: expected {script_sw}, got {status_value}")
                                detailed_info.append(f"{status_type} MISMATCH: {status_value} != {script_sw}")
                        else:
                            mismatching_status.append((status_type, status_value))
                            errors.append(f"{status_type} mismatch: expected {script_sw}, got {status_value}")
                            detailed_info.append(f"{status_type} MISMATCH: {status_value} != {script_sw}")
                
                elif status_type == "OUT":
                    # Check exact match first
                    if status_value == script_sw:
                        matching_status.append((status_type, f"OUT[{status_value}]"))
                        detailed_info.append(f"{status_type} MATCH: [{status_value}] == {script_sw} ✓")
                    else:
                        # FALLBACK: Check last 4 digits of OUT data
                        clean_out = status_value.replace(' ', '').replace(',', '').upper()
                        if len(clean_out) >= 4:
                            last_4_chars = clean_out[-4:]
                            if last_4_chars == script_sw:
                                matching_status.append((status_type, f"OUT[{last_4_chars}]"))
                                detailed_info.append(f"{status_type} last 4 chars match: ...{last_4_chars} == {script_sw} ✓")
                                # Remove any OUT mismatch error that was added
                                errors = [e for e in errors if not e.startswith("OUT mismatch")]
                            else:
                                mismatching_status.append((status_type, f"OUT[{status_value}]"))
                                errors.append(f"{status_type} mismatch: expected {script_sw}, got [{status_value}]")
                                detailed_info.append(f"{status_type} MISMATCH: [{status_value}] != {script_sw}")
                        else:
                            mismatching_status.append((status_type, f"OUT[{status_value}]"))
                            errors.append(f"{status_type} mismatch: expected {script_sw}, got [{status_value}]")
                            detailed_info.append(f"{status_type} MISMATCH: [{status_value}] != {script_sw}")
                
                else:
                    # For other status types (SW, EXP, EXPECT), check exact match
                    if status_value == script_sw:
                        matching_status.append((status_type, status_value))
                        detailed_info.append(f"{status_type} MATCH: {status_value} == {script_sw} ✓")
                    else:
                        mismatching_status.append((status_type, status_value))
                        errors.append(f"{status_type} mismatch: expected {script_sw}, got {status_value}")
                        detailed_info.append(f"{status_type} MISMATCH: {status_value} != {script_sw}")
            
            # Special handling for EXPECT:RECEIVE format
            if machine_expect and machine_receive:
                if machine_expect == script_sw:
                    # Check RECEIVE with fallback logic
                    clean_receive = machine_receive.replace(' ', '').replace(',', '').upper()
                    if len(clean_receive) >= 4:
                        last_4_chars = clean_receive[-4:]
                        if last_4_chars == script_sw:
                            detailed_info.append(f"EXPECT matches and RECEIVE last 4 chars match: ...{last_4_chars} == {script_sw} ✓")
                        else:
                            detailed_info.append(f"EXPECT matches but RECEIVE last 4 chars differ: ...{last_4_chars}")
                    else:
                        detailed_info.append(f"RECEIVE too short: {clean_receive}")
                else:
                    detailed_info.append(f"EXPECT differs from expected SW")
            
            # If we have multiple status values, check if they match each other
            if len(status_values_found) > 1:
                unique_values = set(value for _, value in status_values_found)
                if len(unique_values) > 1:
                    status_display = []
                    for status_type, status_value in status_values_found:
                        if status_type == "OUT":
                            status_display.append(f"OUT[{status_value}]")
                        else:
                            status_display.append(f"{status_type}={status_value}")
                    detailed_info.append(f"WARNING: Multiple status values differ: {', '.join(status_display)}")
            
            # If no status values matched
            if not matching_status and status_values_found:
                detailed_info.append("FAIL: No status values matched expected SW")
        
        # ============================================================
        # STEP 2: HANDLE DIFFERENT COMMAND TYPES - WITH OUT FIELD SUPPORT
        # ============================================================
        
        # TYPE A: Command with RESULT field (00B0000003SW9000RESULT<MCCMNC>)
        if script_type == 'command_sw_result_field':
            detailed_info.append(f"Checking RESULT field: {script_result_field}")
            
            if not machine_result:
                # Check if RESULT data is in RECEIVE field (before SW)
                if machine_receive and script_sw:
                    clean_receive = machine_receive.replace(' ', '').replace(',', '').upper()
                    if len(clean_receive) > 4:
                        last_4_chars = clean_receive[-4:]
                        if last_4_chars == script_sw:
                            data_part = clean_receive[:-4]
                            if data_part:
                                self._process_and_store_field_complete(script_result_field, data_part)
                                detailed_info.append(f"Found RESULT in RECEIVE data: {data_part}")
                            else:
                                errors.append(f"RESULT missing for field '{script_result_field}' - empty data in RECEIVE")
                        else:
                            errors.append(f"RESULT missing for field '{script_result_field}'")
                    else:
                        errors.append(f"RESULT missing for field '{script_result_field}'")
                # Check if RESULT data is in OUT field (before SW)
                elif machine_out and script_sw:
                    clean_out = machine_out.replace(' ', '').replace(',', '').upper()
                    if len(clean_out) > 4:
                        last_4_chars = clean_out[-4:]
                        if last_4_chars == script_sw:
                            data_part = clean_out[:-4]
                            if data_part:
                                self._process_and_store_field_complete(script_result_field, data_part)
                                detailed_info.append(f"Found RESULT in OUT data: {data_part}")
                            else:
                                errors.append(f"RESULT missing for field '{script_result_field}' - empty data in OUT")
                        else:
                            errors.append(f"RESULT missing for field '{script_result_field}'")
                    else:
                        errors.append(f"RESULT missing for field '{script_result_field}'")
                else:
                    errors.append(f"RESULT missing for field '{script_result_field}'")
            else:
                # Store the extracted field value
                self._process_and_store_field_complete(script_result_field, machine_result)
                detailed_info.append(f"Found RESULT: {machine_result}")
                
                # Also check EXPResult if present
                if machine_exp_result and machine_result != machine_exp_result:
                    errors.append(f"RESULT and EXPResult mismatch: {machine_result} != {machine_exp_result}")
        
        # TYPE B: Command with fixed expected result (0026000102SW9000RESULTAF99)
        elif script_type == 'command_sw_result':
            detailed_info.append(f"Checking fixed RESULT: {script_expected_result}")
            
            if script_expected_result:
                result_matched = False
                
                # Check machine_result first
                if machine_result:
                    if machine_result == script_expected_result:
                        result_matched = True
                        detailed_info.append(f"Found expected RESULT: {machine_result}")
                    else:
                        errors.append(f"RESULT mismatch: expected {script_expected_result}, got {machine_result}")
                # Check if RESULT is in RECEIVE field (before SW)
                elif machine_receive and script_sw:
                    clean_receive = machine_receive.replace(' ', '').replace(',', '').upper()
                    # Check if RECEIVE ends with the expected SW
                    if len(clean_receive) >= 4:
                        last_4_chars = clean_receive[-4:]
                        if last_4_chars == script_sw:
                            # Extract data before SW
                            data_part = clean_receive[:-4]
                            if data_part == script_expected_result:
                                result_matched = True
                                detailed_info.append(f"Found expected RESULT in RECEIVE data: {data_part}")
                            elif data_part:
                                errors.append(f"RESULT mismatch: expected {script_expected_result}, got {data_part} (from RECEIVE)")
                            else:
                                errors.append("RESULT missing in machine log")
                        else:
                            # Maybe the whole RECEIVE is the result (without SW)
                            if clean_receive == script_expected_result:
                                result_matched = True
                                detailed_info.append(f"Found expected RESULT in RECEIVE: {clean_receive}")
                            else:
                                errors.append("RESULT missing in machine log")
                    else:
                        errors.append("RESULT missing in machine log")
                # Check if RESULT is in OUT field (before SW)
                elif machine_out and script_sw:
                    clean_out = machine_out.replace(' ', '').replace(',', '').upper()
                    # Check if OUT ends with the expected SW
                    if len(clean_out) >= 4:
                        last_4_chars = clean_out[-4:]
                        if last_4_chars == script_sw:
                            # Extract data before SW
                            data_part = clean_out[:-4]
                            if data_part == script_expected_result:
                                result_matched = True
                                detailed_info.append(f"Found expected RESULT in OUT data: {data_part}")
                            elif data_part:
                                errors.append(f"RESULT mismatch: expected {script_expected_result}, got {data_part} (from OUT)")
                            else:
                                errors.append("RESULT missing in machine log")
                        else:
                            # Maybe the whole OUT is the result (without SW)
                            if clean_out == script_expected_result:
                                result_matched = True
                                detailed_info.append(f"Found expected RESULT in OUT: {clean_out}")
                            else:
                                errors.append("RESULT missing in machine log")
                    else:
                        errors.append("RESULT missing in machine log")
                else:
                    errors.append("RESULT missing in machine log")
        
        # TYPE C: Command with field placeholders in APDU (00D600002AFE85410110<PSK>FE80410210<DEK1>SW9000)
        elif script_type == 'command_with_fields_sw':
            detailed_info.append(f"Extracting fields from APDU: {script_field_names}")
            
            if script_field_names and machine_apdu:
                pattern = re.escape(script_apdu)
                for field_name in script_field_names:
                    field_pattern_percent = re.escape(f'%{field_name}%')
                    field_pattern_angle = re.escape(f'<{field_name}>')
                    pattern = pattern.replace(field_pattern_percent, r'([A-F0-9]+)')
                    pattern = pattern.replace(field_pattern_angle, r'([A-F0-9]+)')
                
                match = re.match(pattern, machine_apdu, re.IGNORECASE)
                if match:
                    for idx, field_name in enumerate(script_field_names):
                        if idx < len(match.groups()):
                            field_value = match.group(idx + 1)
                            self._process_and_store_field_complete(field_name, field_value)
                            detailed_info.append(f"Extracted {field_name} = {field_value}")
                else:
                    errors.append(f"Could not extract fields {script_field_names} from APDU")
        
        # TYPE D: Simple Command + SW (0050000010...SW9000)
        elif script_type == 'command_sw':
            detailed_info.append("Checking simple command")
            
            # Check APDU data match
            if script_apdu and machine_apdu and script_apdu != machine_apdu:
                errors.append("APDU data mismatch")
        
        # ============================================================
        # STEP 3: ADDITIONAL VALIDATION
        # ============================================================
        # Check for placeholders in machine log (should not happen)
        if machine_log.get('has_placeholder'):
            errors.append(f"Machine log contains placeholder")
        
        # Check APDU length for write commands without placeholders
        if (script_apdu.startswith('00D6') or script_apdu.startswith('00D7')) and not script_field_names:
            if machine_apdu and len(machine_apdu) < len(script_apdu):
                errors.append(f"APDU data truncated")
        
        if errors:
            error_summary = ' | '.join(errors)
            
            if self.debug_mode:
                print(f"  ❌ Validation failed: {error_summary}")
            
            return {
                'script_line': script_cmd['original_line'],
                'machine_line': machine_log['original_line'],
                'status': 'FAIL',
                'message': error_summary,
                'detailed_info': detailed_info
            }
        else:
            # Build success message
            success_parts = []

            if script_sw:
                # Report which status value(s) matched with meaningful info
                status_details = []
                
                # SW field
                if machine_sw and machine_sw == script_sw:
                    status_details.append(f"SW={machine_sw}")
                
                # EXP field
                if machine_exp and machine_exp == script_sw:
                    status_details.append(f"Expected={machine_exp}")
                
                # OUT field - meaningful info about data length
                if machine_out:
                    clean_out = machine_out.replace(' ', '').replace(',', '').upper()
                    if clean_out == script_sw:
                        status_details.append(f"OUT={clean_out}")
                    elif len(clean_out) >= 4:
                        if clean_out[-4:] == script_sw:
                            data_len = len(clean_out) - 4
                            if data_len > 0:
                                status_details.append(f"OUT: {data_len} chars data + {script_sw}")
                            else:
                                status_details.append(f"OUT={clean_out}")
                        else:
                            status_details.append(f"OUT={clean_out} ({len(clean_out)} chars)")
                
                # EXPECT field
                if machine_expect and machine_expect == script_sw:
                    status_details.append(f"EXPECT={machine_expect}")
                
                # RECEIVE field - meaningful info about data length
                if machine_receive:
                    clean_receive = machine_receive.replace(' ', '').replace(',', '').upper()
                    if clean_receive == script_sw:
                        status_details.append(f"RECEIVE={clean_receive}")
                    elif len(clean_receive) >= 4:
                        if clean_receive[-4:] == script_sw:
                            data_len = len(clean_receive) - 4
                            if data_len > 0:
                                status_details.append(f"RECEIVE: {data_len} chars data + {script_sw}")
                            else:
                                status_details.append(f"RECEIVE={clean_receive}")
                        else:
                            status_details.append(f"RECEIVE={clean_receive} ({len(clean_receive)} chars)")
                
                if status_details:
                    success_parts.append(f"Status: {' | '.join(status_details)} ✅")
                else:
                    success_parts.append("Status: matched ✅")

            if script_type == 'command_sw' and script_apdu and machine_apdu:
                success_parts.append("APDU matched ✅")

            if script_result_field and machine_result:
                # Show FULL result data with length
                result_len = len(machine_result)
                success_parts.append(f"{script_result_field}={machine_result} ({result_len} chars) ✅")

            if script_expected_result and machine_result:
                # Show FULL result data with length
                result_len = len(machine_result)
                success_parts.append(f"RESULT={machine_result} ({result_len} chars) ✅")

            if script_field_names:
                extracted = []
                for field in script_field_names:
                    if field in self.field_values:
                        value = self.field_values[field]
                        value_len = len(value)
                        # SHOW FULL VALUE - NO TRUNCATION
                        extracted.append(f"{field}={value} ({value_len} chars)")
                
                if extracted:
                    success_parts.append(f"Fields: {' | '.join(extracted)} ✅")

            success_msg = "Command validation passed"
            if success_parts:
                success_msg += " | " + " | ".join(success_parts)

            if self.debug_mode:
                print(f"  ✅ {success_msg}")

            return {
                'script_line': script_cmd['original_line'],
                'machine_line': machine_log['original_line'],
                'status': 'PASS',
                'message': success_msg,
                'detailed_info': detailed_info
            }
                    
    def fix_ki_opc_issue(self):
        """
        FIXED: Handle all KI/OPC issues including your specific case
        """
        if self.debug_mode:
            print(f"\n🔧 CHECKING AND FIXING KI/OPC")
        
        # ============================================================
        # SPECIFIC CASE: KI=63, OPC=1 (YOUR EXACT CASE)
        # ============================================================
        if "KI" in self.field_values and "OPC" in self.field_values:
            ki = self.field_values["KI"]
            opc = self.field_values["OPC"]
            
            ki_len = len(ki)
            opc_len = len(opc)
            
            if self.debug_mode:
                print(f"  Current: KI={ki_len} chars, OPC={opc_len} chars")
                print(f"  KI: {ki}")
                print(f"  OPC: {opc}")
            
            # YOUR SPECIFIC CASE: KI=63, OPC=1
            if ki_len == 63 and opc_len == 1:
                if self.debug_mode:
                    print(f"  ⚠️  DETECTED YOUR EXACT CASE: KI=63, OPC=1")
                    print(f"     Applying specific fix...")
                
                # Split: First 32 chars = Real KI
                real_ki = ki[:32]
                
                # Next 31 chars = OPC partial
                opc_partial = ki[32:]
                
                # Combine: OPC partial (31) + OPC (1) = Complete OPC (32)
                complete_opc = opc_partial + opc
                
                # Update values
                self.field_values["KI"] = real_ki
                self.field_values["OPC"] = complete_opc
                
                if self.debug_mode:
                    print(f"  ✅ SPECIFIC FIX APPLIED:")
                    print(f"     Real KI (32 chars): {real_ki}")
                    print(f"     OPC partial (31 chars): {opc_partial}")
                    print(f"     + OPC (1 char): {opc}")
                    print(f"     = Complete OPC (32 chars): {complete_opc}")
                
                # Remove OPC_PARTIAL if exists
                if "OPC_PARTIAL" in self.field_values:
                    del self.field_values["OPC_PARTIAL"]
                
                return  # Exit after fixing specific case
        
        # ============================================================
        # GENERAL CASE: Fix ASCII OPC (your second issue)
        # ============================================================
        if "OPC" in self.field_values:
            opc = self.field_values["OPC"]
            opc_len = len(opc)
            
            if self.debug_mode:
                print(f"  OPC: {opc}")
                print(f"  OPC length: {opc_len} chars")
            
            # Check if OPC is in ASCII numbers format
            # Example: "63839393130303039313032303030303" = ASCII codes
            if 31 <= opc_len <= 32 and opc.isdigit():
                if self.debug_mode:
                    print(f"  ⚠️  OPC appears to be ASCII numbers (all digits)")
                
                # Convert ASCII numbers to hex
                hex_opc = ""
                try:
                    # Process in pairs of 2 digits
                    for i in range(0, len(opc), 2):
                        if i + 1 < len(opc):
                            ascii_pair = opc[i:i+2]
                            # Convert ASCII decimal to hex
                            hex_byte = format(int(ascii_pair), '02X')
                            hex_opc += hex_byte
                    
                    if hex_opc:
                        self.field_values["OPC"] = hex_opc
                        if self.debug_mode:
                            print(f"  ✅ Converted OPC from ASCII numbers to hex")
                            print(f"     Before: {opc}")
                            print(f"     After:  {hex_opc} ({len(hex_opc)} chars)")
                except Exception as e:
                    if self.debug_mode:
                        print(f"  ❌ Error converting ASCII numbers: {e}")
            
            # Check OPC length
            opc = self.field_values.get("OPC", "")
            opc_len = len(opc)
            
            if opc_len != 32:
                if self.debug_mode:
                    print(f"  ⚠️  OPC is {opc_len} chars (should be 32)")
                
                # Try to find missing part in OPC_PARTIAL
                if "OPC_PARTIAL" in self.field_values:
                    opc_partial = self.field_values["OPC_PARTIAL"]
                    combined = opc_partial + opc
                    
                    if len(combined) >= 32:
                        self.field_values["OPC"] = combined[:32]
                        del self.field_values["OPC_PARTIAL"]
                        
                        if self.debug_mode:
                            print(f"  ✅ Combined OPC_PARTIAL + OPC = 32 chars")
                            print(f"     Result: {self.field_values['OPC']}")
                    else:
                        self.field_values["OPC"] = combined
                        if self.debug_mode:
                            print(f"  ⚠️  Combined OPC still short: {len(combined)}/32 chars")
        
        # ============================================================
        # FIX KI LENGTH
        # ============================================================
        if "KI" in self.field_values:
            ki = self.field_values["KI"]
            ki_len = len(ki)
            
            if ki_len != 32:
                if ki_len > 32:
                    # Truncate KI to 32 chars
                    real_ki = ki[:32]
                    extra = ki[32:]
                    
                    self.field_values["KI"] = real_ki
                    
                    # Store extra as OPC_PARTIAL
                    if extra:
                        self.field_values["OPC_PARTIAL"] = extra
                    
                    if self.debug_mode:
                        print(f"  ⚠️  KI truncated from {ki_len} to 32 chars")
                        print(f"     Extra stored as OPC_PARTIAL: {extra}")
                else:
                    if self.debug_mode:
                        print(f"  ❌ KI is {ki_len} chars (should be 32)")

    def _process_and_store_field_complete(self, field_name: str, field_value: str) -> None:
        """PROCESS: Store field values - SIMPLIFIED AND FIXED"""
        if not field_value:
            return
        
        field_upper = field_name.upper()
        field_len = len(field_value)
        
        if self.debug_mode:
            print(f"  🔍 Processing: {field_name} = '{field_value[:30]}...' ({field_len} chars)")
        
        # ============================================================
        # CASE 1: OPC FIELD
        # ============================================================
        if field_upper == "OPC" or field_upper.endswith("_OPC"):
            # Store as-is for now, will be fixed in fix_ki_opc_issue()
            self.field_values["OPC"] = field_value
            
            if self.debug_mode:
                print(f"  ✅ Stored OPC: {field_value} ({field_len} chars)")
            
            # Apply fixes
            self.fix_ki_opc_issue()
            return
        
        # ============================================================
        # CASE 2: KI FIELD
        # ============================================================
        if field_upper == "KI" or field_upper.endswith("_KI"):
            # Store as-is for now, will be fixed in fix_ki_opc_issue()
            self.field_values["KI"] = field_value
            
            if self.debug_mode:
                print(f"  ✅ Stored KI: {field_value[:30]}... ({field_len} chars)")
            
            # Apply fixes
            self.fix_ki_opc_issue()
            return
        
        # ============================================================
        # CASE 3: 64-CHAR HEX FIELD (likely KI+OPC combined)
        # ============================================================
        if field_len == 64 and all(c in "0123456789ABCDEFabcdef" for c in field_value):
            ki = field_value[:32]
            opc = field_value[32:64]
            
            self.field_values["KI"] = ki.upper()
            self.field_values["OPC"] = opc.upper()
            
            if self.debug_mode:
                print(f"  ✅ Split 64-char field into KI and OPC")
                print(f"     KI: {ki}")
                print(f"     OPC: {opc}")
            return
        
        # ============================================================
        # CASE 4: 76-CHAR FIELD WITH PREFIX
        # ============================================================
        if field_len >= 76 and field_value.startswith("00D600002114"):
            # Format: 00D600002114 (12) + KI (32) + OPC (32) = 76 chars
            ki_opc_data = field_value[12:76]  # Skip 12, take next 64
            
            if len(ki_opc_data) >= 64:
                ki = ki_opc_data[:32]
                opc = ki_opc_data[32:64]
                
                self.field_values["KI"] = ki.upper()
                self.field_values["OPC"] = opc.upper()
                
                if self.debug_mode:
                    print(f"  ✅ Extracted KI+OPC from 76-char field")
                    print(f"     KI: {ki}")
                    print(f"     OPC: {opc}")
                return
        
        # ============================================================
        # CASE 5: OTHER FIELDS - Store normally
        # ============================================================
        self.field_values[field_name] = field_value
        
        # Special processing for other fields
        if "IMSI" in field_upper and "ASCII" not in field_upper:
            swapped = self.swap_pairs(field_value)
            self.field_values[f"{field_name}_SWAPPED"] = swapped
        
        elif "ICCID" in field_upper and "ASCII" not in field_upper:
            swapped = self.swap_pairs(field_value)
            self.field_values[f"{field_name}_SWAPPED"] = swapped

        elif "PIN" in field_upper and field_value.endswith('FFFFFFFF'):
            clean_pin = field_value[:-8]
            self.field_values[f"{field_name}_CLEAN"] = clean_pin

    @staticmethod
    def ascii_numbers_to_hex(ascii_numbers: str) -> str:
        """
        Convert ASCII number string to hex - FIXED VERSION
        Example: "63839393130303039313032303030303" → hex string
        """
        try:
            hex_string = ""
            # Process pairs of digits (ASCII decimal codes)
            for i in range(0, len(ascii_numbers), 2):
                if i + 1 < len(ascii_numbers):
                    # Get two ASCII digits (e.g., "63")
                    ascii_pair = ascii_numbers[i:i+2]
                    # Convert ASCII decimal code to hex byte
                    # Example: "63" (decimal) → 0x3F
                    decimal_value = int(ascii_pair)
                    hex_byte = format(decimal_value, '02X')
                    hex_string += hex_byte
            return hex_string
        except Exception as e:
            print(f"Error converting ASCII numbers to hex: {e}")
            return ascii_numbers

    def finalize_ki_opc(self):
        """
        Final cleanup - SIMPLIFIED
        """
        if self.debug_mode:
            print(f"\n🔧 FINAL KI/OPC CHECK")
        
        # Check KI
        if "KI" in self.field_values:
            ki = self.field_values["KI"]
            ki_len = len(ki)
            
            if ki_len != 32:
                if self.debug_mode:
                    print(f"  ❌ KI is {ki_len} chars (should be 32)")
        
        # Check OPC
        if "OPC" in self.field_values:
            opc = self.field_values["OPC"]
            opc_len = len(opc)
            
            if opc_len != 32:
                if self.debug_mode:
                    print(f"  ❌ OPC is {opc_len} chars (should be 32)")
            else:
                if self.debug_mode:
                    print(f"  ✅ OPC is correct: 32 chars")

    def _generate_complete_validation_report(self, max_results: int = None) -> str:
        """REPORT: Generate comprehensive validation report"""
        report_lines = []
        
        report_lines.append("=" * 80)
        report_lines.append("COMPLETE MACHINE LOG VALIDATION REPORT")
        report_lines.append("=" * 80)
        
        # ============================================================
        # SUMMARY STATISTICS
        # ============================================================
        report_lines.append("\n📊 VALIDATION SUMMARY")
        report_lines.append("-" * 80)
        
        total = self.stats['total_commands']
        passed = self.stats['passed']
        failed = self.stats['failed']
        # skipped = self.stats['skipped']
        not_found = self.stats['not_found']
        
        report_lines.append(f"Total Commands Processed: {total}")
        report_lines.append(f"Passed: {passed}")
        report_lines.append(f"Failed: {failed}")
        # report_lines.append(f"Skipped: {skipped}")
        report_lines.append(f"Not Found: {not_found}")
        
        # Calculate success rate
        # success_rate = 0
        # if total > 0:
        #     success_rate = (passed / total) * 100
        #     report_lines.append(f"Success Rate: {success_rate:.1f}%")
        
        # ============================================================
        # FAILURE ANALYSIS
        # ============================================================
        failure_counts = {
            'sw_mismatches': 0,
            'result_mismatches': 0,
            'missing_results': 0,
            'placeholder_errors': 0,
            'other_errors': 0,
            'not_found_errors': 0
        }
        
        if failed > 0:
            report_lines.append("\n🔍 FAILURE ANALYSIS")
            report_lines.append("-" * 80)
            
            # Count failure types
            for result in self.validation_results:
                if result.get('status') == 'FAIL':
                    message = result.get('message', '').lower()
                    if 'not found' in message:
                        failure_counts['not_found_errors'] += 1
                    elif any(status in message for status in ['sw', 'exp', 'out', 'expect', 'receive']):
                        failure_counts['sw_mismatches'] += 1
                    elif 'result' in message and 'mismatch' in message:
                        failure_counts['result_mismatches'] += 1
                    elif 'missing' in message:
                        failure_counts['missing_results'] += 1
                    elif 'placeholder' in message:
                        failure_counts['placeholder_errors'] += 1
                    else:
                        failure_counts['other_errors'] += 1
            
            # Display failure counts
            if failure_counts['sw_mismatches'] > 0:
                report_lines.append(f"SW/Status Mismatches: {failure_counts['sw_mismatches']}")
            if failure_counts['result_mismatches'] > 0:
                report_lines.append(f"Result Mismatches: {failure_counts['result_mismatches']}")
            if failure_counts['missing_results'] > 0:
                report_lines.append(f"Missing Results: {failure_counts['missing_results']}")
            if failure_counts['placeholder_errors'] > 0:
                report_lines.append(f"Placeholder Errors: {failure_counts['placeholder_errors']}")
            if failure_counts['not_found_errors'] > 0:
                report_lines.append(f"Not Found Errors: {failure_counts['not_found_errors']}")
            if failure_counts['other_errors'] > 0:
                report_lines.append(f"Other Errors: {failure_counts['other_errors']}")
        
        # ============================================================
        # VALIDATION RULES
        # ============================================================
        # report_lines.append("\n⚖️  VALIDATION RULES APPLIED")
        # report_lines.append("-" * 80)
        # report_lines.append("1. Command matching by APDU command bytes")
        # report_lines.append("2. EXACT SW (Status Word) match required")
        # # report_lines.append("3. Checks all status formats: SW=, EXP=, OUT[], EXPECT:, RECEIVE:")
        # report_lines.append("4. RESULT field extraction and validation")
        # # report_lines.append("5. Machine log must contain actual values (no placeholders)")
        # # report_lines.append("6. APDU data integrity checks for write commands")
        # report_lines.append("7. KI/OPC field splitting (64 chars → 32 KI + 32 OPC)")
        
        # ============================================================
        # DETAILED RESULTS
        # ============================================================
        report_lines.append(f"\n📋 DETAILED RESULTS")
        report_lines.append("-" * 80)
        
        # Determine how many results to show
        if max_results is None:
            results_to_show = self.validation_results
        else:
            results_to_show = self.validation_results[:max_results]
        
        for i, result in enumerate(results_to_show):
            status = result.get('status', 'UNKNOWN')
            message = result.get('message', '')
            
            if status == 'PASS':
                icon = "✅"
            elif status == 'FAIL':
                icon = "❌"
            elif status == 'SKIPPED':
                icon = "⏭️"
            else:
                icon = "❓"
            
            report_lines.append(f"{i+1:3d}. {icon} {status}: {message}")
            
            if status == 'FAIL':
                script_line = result.get('script_line', '')
                if script_line:
                    if len(script_line) > 100:
                        script_line = script_line[:100] + "..."
                    report_lines.append(f"     Script: {script_line}")
                
                machine_line = result.get('machine_line', '')
                if machine_line:
                    if len(machine_line) > 100:
                        machine_line = machine_line[:100] + "..."
                    report_lines.append(f"     Machine: {machine_line}")
            
            report_lines.append("")
        
        # If we limited the display, show a message
        if max_results is not None and len(self.validation_results) > max_results:
            remaining = len(self.validation_results) - max_results
            report_lines.append(f"... and {remaining} more results (total: {len(self.validation_results)}) ...")
        
        # ============================================================
        # EXTRACTED FIELDS
        # ============================================================
        if self.field_values:
            report_lines.append("\n🔍 EXTRACTED FIELD VALUES")
            report_lines.append("-" * 80)
            
            # Categorize fields
            imsi_fields = {}
            iccid_fields = {}
            psk_fields = {}
            dek_fields = {}
            ki_fields = {}
            opc_fields = {}
            combined_key_fields = {}
            pin_fields = {}
            other_fields = {}
            
            for field_name, field_value in sorted(self.field_values.items()):
                # Skip internal processing fields
                if any(suffix in field_name for suffix in ['_SWAPPED', '_CALCULATED', '_CLEAN', '_ASCII', '_HEX']):
                    continue
                
                field_upper = field_name.upper()
                
                if "IMSI" in field_upper:
                    imsi_fields[field_name] = field_value
                elif "ICCID" in field_upper:
                    iccid_fields[field_name] = field_value
                elif "PIN" in field_upper:
                    pin_fields[field_name] = field_value
                elif "PSK" in field_upper:
                    psk_fields[field_name] = field_value
                elif "DEK" in field_upper:
                    dek_fields[field_name] = field_value
                elif "KI" in field_upper and "OPC" not in field_upper:
                    ki_fields[field_name] = field_value
                elif "OPC" in field_upper and "KI" not in field_upper:
                    opc_fields[field_name] = field_value
                elif ("KI" in field_upper and "OPC" in field_upper) or "KIOPC" in field_upper:
                    combined_key_fields[field_name] = field_value
                else:
                    other_fields[field_name] = field_value
            
            # Display by category
            if imsi_fields:
                report_lines.append("\nIMSI Fields:")
                for field_name, field_value in imsi_fields.items():
                    swapped = self.field_values.get(f"{field_name}_SWAPPED", "N/A")
                    report_lines.append(f"  {field_name}: {field_value}")
                    # report_lines.append(f"    Swapped: {swapped}")
            
            if iccid_fields:
                report_lines.append("\nICCID Fields:")
                for field_name, field_value in iccid_fields.items():
                    # swapped = self.field_values.get(f"{field_name}_SWAPPED", "N/A")
                    report_lines.append(f"  {field_name}: {field_value}")
                    # report_lines.append(f"    Swapped: {swapped}")
            
            if ki_fields:
                report_lines.append("\nKI (Key Identifier) Fields:")
                for field_name, field_value in ki_fields.items():
                    display = field_value
                    if len(display) > 64:
                        display = display[:64] + "..."
                    report_lines.append(f"  {field_name}: {display}")
                    report_lines.append(f"    Length: {len(field_value)} chars")
            
            if opc_fields:
                report_lines.append("\nOPC (Operator Code) Fields:")
                for field_name, field_value in opc_fields.items():
                    display = field_value
                    if len(display) > 64:
                        display = display[:64] + "..."
                    report_lines.append(f"  {field_name}: {display}")
                    report_lines.append(f"    Length: {len(field_value)} chars")
            
            if combined_key_fields:
                report_lines.append("\nCombined Key Fields (KI+OPC):")
                for field_name, field_value in combined_key_fields.items():
                    report_lines.append(f"  {field_name}: {field_value}")
                    report_lines.append(f"    Length: {len(field_value)} chars")
                    
                    if len(field_value) >= 64:
                        ki_part = field_value[:32]
                        opc_part = field_value[32:64]
                        report_lines.append(f"    KI (first 32 chars): {ki_part}")
                        report_lines.append(f"    OPC (next 32 chars): {opc_part}")
                    elif len(field_value) == 32:
                        report_lines.append(f"    Note: Only 32 chars - could be KI or OPC")
            
            if psk_fields:
                report_lines.append("\nPSK (Pre-Shared Key) Fields:")
                for field_name, field_value in psk_fields.items():
                    display = field_value
                    if len(display) > 32:
                        display = display[:32] + "..."
                    report_lines.append(f"  {field_name}: {display}")
                    report_lines.append(f"    Length: {len(field_value)} chars")
            
            if dek_fields:
                report_lines.append("\nDEK (Data Encryption Key) Fields:")
                for field_name, field_value in dek_fields.items():
                    display = field_value
                    if len(display) > 32:
                        display = display[:32] + "..."
                    report_lines.append(f"  {field_name}: {display}")
                    report_lines.append(f"    Length: {len(field_value)} chars")
            
            if pin_fields:
                report_lines.append("\nPIN Fields:")
                for field_name, field_value in pin_fields.items():
                    clean = self.field_values.get(f"{field_name}_CLEAN", field_value)
                    ascii_pin = self.field_values.get(f"{field_name}_ASCII", "N/A")
                    report_lines.append(f"  {field_name}: {field_value}")
                    # report_lines.append(f"    Clean: {clean}")
                    if ascii_pin != "N/A":
                        report_lines.append(f"    ASCII: {ascii_pin}")
            
            if other_fields:
                report_lines.append("\nOther Fields:")
                for field_name, field_value in other_fields.items():
                    display = field_value
                    if len(display) > 50:
                        display = display[:50] + "..."
                    report_lines.append(f"  {field_name}: {display}")
        
        # ============================================================
        # ANALYSIS
        # ============================================================
        report_lines.append("\n💡 VALIDATION ANALYSIS")
        report_lines.append("-" * 80)
        
        if not_found > 0:
            report_lines.append(f"❌ {not_found} commands not found in machine logs")
            report_lines.append("   Possible reasons:")
            report_lines.append("   1. Script and machine log from different test runs")
            report_lines.append("   2. APDU parsing issues in machine log")
            report_lines.append("   3. Command synchronization mismatch")
        
        if failed > 0 and failure_counts['sw_mismatches'] > 0:
            sw_mismatches = failure_counts['sw_mismatches']
            report_lines.append(f"\n⚠️  {sw_mismatches} SW/status mismatches detected")
            report_lines.append("   Check for:")
            report_lines.append("   1. Different SW in script vs machine log")
            report_lines.append("   2. SW, EXP, OUT, EXPECT, or RECEIVE value mismatches")
            report_lines.append("   3. Machine log showing different status formats")
        
        # if passed == total:
        #     report_lines.append("✅ PERFECT VALIDATION: All commands passed!")
        # elif success_rate >= 90:
        #     report_lines.append(f"✅ EXCELLENT: {success_rate:.1f}% success rate")
        # elif success_rate >= 70:
        #     report_lines.append(f"⚠️  GOOD: {success_rate:.1f}% success rate")
        # elif success_rate >= 50:
        #     report_lines.append(f"⚠️  FAIR: {success_rate:.1f}% success rate")
        # else:
        #     report_lines.append(f"❌ POOR: {success_rate:.1f}% success rate")
        
        report_lines.append("\n" + "=" * 80)
        report_lines.append("END OF REPORT")
        report_lines.append("=" * 80)
        
        return "\n".join(report_lines)
    
    def save_report_to_file(self, filename: str = "complete_validation_report.txt") -> None:
        """Save validation report to file - SAVES ALL RESULTS"""
        report = self._generate_complete_validation_report()
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"\n📄 Report saved to: {filename}")
        except Exception as e:
            print(f"❌ Error saving report: {e}")

    def get_validation_results_for_gui(self, max_lines: int = None) -> str:
        """Get validation results formatted for GUI display - SHOWS ALL RESULTS"""
        gui_lines = []
        
        # Add header
        gui_lines.append("=" * 80)
        gui_lines.append("VALIDATION RESULTS - ALL COMMANDS")
        gui_lines.append("=" * 80)
        
        # Add summary
        total = self.stats['total_commands']
        passed = self.stats['passed']
        failed = self.stats['failed']
        
        gui_lines.append(f"\n📊 Summary: Passed: {passed} | Failed: {failed} | Total: {total}")
        
        if total > 0:
            success_rate = (passed / total) * 100
            gui_lines.append(f"📈 Success Rate: {success_rate:.1f}%")
        
        gui_lines.append("-" * 80)
        
        # Show all results or limited results
        if max_lines is None:
            results_to_show = self.validation_results
        else:
            results_to_show = self.validation_results[:max_lines]
        
        for i, result in enumerate(results_to_show):
            status = result.get('status', 'UNKNOWN')
            message = result.get('message', '')
            
            if status == 'PASS':
                icon = "✅"
                color_start = ""
                color_end = ""
            elif status == 'FAIL':
                icon = "❌"
                color_start = ""
                color_end = ""
            elif status == 'SKIPPED':
                icon = "⏭️"
                color_start = ""
                color_end = ""
            else:
                icon = "❓"
                color_start = ""
                color_end = ""
            
            # Format line number with enough space
            line_num_str = f"{i+1:4d}."
            
            # Truncate message if too long
            if len(message) > 100:
                message = message[:100] + "..."
            
            gui_lines.append(f"{line_num_str} {icon} {color_start}{status}: {message}{color_end}")
            
            if status == 'FAIL' and self.debug_mode:
                # Show script line for failures
                script_line = result.get('script_line', '')
                if script_line:
                    if len(script_line) > 80:
                        script_line = script_line[:80] + "..."
                    gui_lines.append(f"     Script: {script_line}")
        
        # If we limited the display, show a message
        if max_lines is not None and len(self.validation_results) > max_lines:
            remaining = len(self.validation_results) - max_lines
            gui_lines.append(f"\n... and {remaining} more results (total: {len(self.validation_results)})")
            gui_lines.append("Use 'Save Report' to see all results in detail.")
        
        return "\n".join(gui_lines)


def main():
    """Main function - UPDATED TO SHOW ALL RESULTS"""
    print("=" * 80)
    print("COMPLETE SCRIPT VALIDATOR - SHOWS ALL RESULTS")
    print("=" * 80)
    print("Fixes applied:")
    print("1. ✅ Shows ALL validation results (not just first 20)")
    print("2. ✅ Improved SW extraction (handles 3-4 digit SW values)")
    print("3. ✅ Detailed error reporting for SW mismatches")
    print("4. ✅ Handles EXP=611B SW=611 format")
    print("5. ✅ Shows exact failure reasons")
    print("=" * 80)
    
    validator = ScriptValidator()
    
    # File paths
    script_file = "variable_script.txt"
    machine_log = "machine_log.txt"
    
    # Check if files exist
    if not os.path.exists(script_file):
        print(f"❌ Script file not found: {script_file}")
        print("Please ensure 'variable_script.txt' exists in the current directory")
        return
    
    if not os.path.exists(machine_log):
        print(f"❌ Machine log file not found: {machine_log}")
        print("Please ensure 'machine_log.txt' exists in the current directory")
        return
    
    print(f"📄 Script file: {script_file}")
    print(f"📄 Machine log: {machine_log}")
    print()
    
    # Parse files
    print("🔄 Parsing script file...")
    if not validator.parse_script_file(script_file):
        print("❌ Failed to parse script file")
        return
    
    print("\n🔄 Parsing machine log...")
    if not validator.parse_machine_log(machine_log):
        print("❌ Failed to parse machine log")
        return
    
    # Run validation
    print("\n🔄 Running validation...")
    report = validator.validate_script_vs_machine_log()
    
    # Print report to console (can be limited for console display)
    print("\n" + "=" * 80)
    print("VALIDATION COMPLETE - CONSOLE VIEW (First 50 results)")
    print("=" * 80)
    
    # For console, show first 50 results
    console_report = validator._generate_complete_validation_report(max_results=50)
    print(console_report)
    
    # For GUI/Full display, you would use:
    # full_report = validator._generate_complete_validation_report()  # Shows ALL
    # or
    # gui_display = validator.get_validation_results_for_gui()  # Shows ALL in GUI format
    
    # Save full report to file (ALL results)
    validator.save_report_to_file()
    
    # Show what was fixed
    print("\n🔧 FIXES APPLIED:")
    print("1. Now shows ALL validation results in the report file")
    print("2. GUI can display all results using get_validation_results_for_gui()")
    print("3. Console shows first 50 results, file has all results")
    print("4. Each failure shows the exact reason and line numbers")
    print("\n📝 Note: Full report with ALL results saved to 'complete_validation_report.txt'")


if __name__ == "__main__":
    main()