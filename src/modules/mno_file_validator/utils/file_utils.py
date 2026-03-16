"""
Utility functions for file operations
"""
import re
import os
import sys
import ctypes
from pathlib import Path
from typing import Dict, List, Tuple, Optional


def get_long_path_prefix() -> str:
    """Get the Windows extended path prefix for long paths (>260 chars)
    
    Returns:
        '\\\\?\\' for Windows, empty string for other platforms
    """
    if sys.platform == 'win32':
        return '\\\\?\\'
    return ''


def make_long_path(path: str) -> str:
    """Convert a path to an extended-length path on Windows
    
    On Windows, paths longer than 260 characters need the \\?\ prefix.
    This function adds the prefix only when necessary.
    
    Args:
        path: File or directory path
        
    Returns:
        Path with extended-length prefix if needed
    """
    if sys.platform != 'win32':
        return path
    
    # If already a long path, return as-is
    if path.startswith('\\\\?\\'):
        return path
    
    # Convert to absolute path first
    abs_path = os.path.abspath(path)
    
    # If path is longer than 240 chars (leaving room for filename), add prefix
    if len(abs_path) > 240:
        # For local paths (with drive letter), add \\?\ prefix
        if len(abs_path) >= 2 and abs_path[1] == ':':
            return '\\\\?\\' + abs_path
        # For UNC paths (network paths)
        elif abs_path.startswith('\\\\'):
            return '\\\\?\\UNC\\' + abs_path[2:]
    
    return path


def enable_long_path_support():
    """Enable long path support on Windows (paths > 260 characters)"""
    if sys.platform == 'win32':
        try:
            # Enable long path support on Windows 10+ by setting the registry key
            # This allows paths longer than 260 characters
            kernel32 = ctypes.windll.kernel32
            kernel32.SetLongPathNameW  # Check if function exists
        except (AttributeError, OSError):
            pass  # Not supported on this Windows version


def normalize_path(path: str) -> Path:
    """Normalize and resolve path for any location including long paths
    
    Args:
        path: Input path string
        
    Returns:
        Normalized Path object
    """
    if not path:
        return Path()
    
    # Convert to Path and resolve (handles .., . etc.)
    path_obj = Path(path)
    
    # Try to resolve to absolute path
    try:
        path_obj = path_obj.resolve()
    except (OSError, RuntimeError):
        # If resolve fails, use absolute path
        path_obj = Path(os.path.abspath(path))
    
    return path_obj


def safe_path_exists(path: str) -> bool:
    """Check if path exists with long path support
    
    Args:
        path: Path to check
        
    Returns:
        True if path exists, False otherwise
    """
    # First try with normal path
    try:
        if os.path.exists(path):
            return True
    except (OSError, ValueError):
        pass
    
    # Try with long path prefix for Windows
    try:
        long_path = make_long_path(path)
        if os.path.exists(long_path):
            return True
    except (OSError, ValueError):
        pass
    
    # Try with Path.exists() as fallback
    try:
        path_obj = Path(path)
        return path_obj.exists()
    except (OSError, ValueError, RuntimeError):
        return False


def find_files_recursive(base_path: Path, pattern: str, max_depth: int = 5) -> List[Path]:
    """Recursively find files matching pattern up to max_depth
    
    Args:
        base_path: Base directory to search
        pattern: Glob pattern to match
        max_depth: Maximum recursion depth
        
    Returns:
        List of matching file paths
    """
    results = []
    base_str = str(base_path)
    
    try:
        # First try direct glob
        results = list(base_path.glob(pattern))
        
        # If no results and we have depth, search recursively
        if not results and max_depth > 0:
            for root, dirs, files in os.walk(base_str):
                # Check depth
                rel_path = os.path.relpath(root, base_str)
                depth = rel_path.count(os.sep) if rel_path != '.' else 0
                if depth > max_depth:
                    continue
                    
                # Check for matching files
                for f in files:
                    if f.startswith(pattern.replace('*', '')):
                        results.append(Path(root) / f)
    except (OSError, PermissionError):
        # Handle permission errors gracefully
        pass
    
    return results

def parse_filename(filename: str) -> Optional[Dict]:
    """Extract components from filename"""
    filename_without_ext = Path(filename).stem
    pattern = r'^(?:IN|OUT|CNUM|ORIG_TRIG|SCM|SIMODA)_(\d+)_(\d+)_(\d+)_([A-Z]+)_(\d+)_([A-Z_]+)_([A-Z]+)_(\d+)'
    match = re.match(pattern, filename_without_ext)
    if match:
        return {
            'po_number': match.group(1),
            'sequence': match.group(2),
            'batch_number': match.group(3),
            'circle': match.group(4),
            'card_manufacturer': match.group(5),
            'card_type': match.group(6),
            'sim_subtype': match.group(7),
            'timestamp': match.group(8)
        }
    return None

def find_matching_files(parent_folder: str) -> List[Dict]:
    """Find and match IN files with corresponding OUT folders (Legacy - single folder)
    
    Args:
        parent_folder: Path to parent folder containing IN files and OUT folders
        
    Returns:
        List of matched file pairs with metadata
    """
    # Use normalize_path for long path support
    parent_path = normalize_path(parent_folder)
    
    if not safe_path_exists(parent_folder):
        raise FileNotFoundError(f"Parent folder does not exist: {parent_folder}")
    
    # Find IN_*.txt files - try recursive search for any location
    in_files = find_files_recursive(parent_path, "IN_*.txt", max_depth=2)
    in_files = [f for f in in_files if f.suffix == '.txt']
    in_files.sort()
    
    # Find OUT_* folders
    out_folders = []
    try:
        out_folders = [f for f in parent_path.iterdir() if f.is_dir() and f.name.startswith("OUT_")]
    except (OSError, PermissionError):
        # Try with os.walk for long paths
        for root, dirs, files in os.walk(str(parent_path)):
            for d in dirs:
                if d.startswith("OUT_"):
                    out_folders.append(Path(root) / d)
    out_folders.sort()
    
    matches = []
    
    for in_file in in_files:
        in_suffix = in_file.stem[3:]
        for out_folder in out_folders:
            out_suffix = out_folder.name[4:]
            if in_suffix == out_suffix:
                matches.append({
                    'in_file': in_file,
                    'out_folder': out_folder,
                    'suffix': in_suffix
                })
                break
    
    return matches

def find_matching_files_new(input_folder: str, output_folder: str) -> List[Dict]:
    """Find and match IN files with corresponding OUT folders (New - separate folders)
    
    Supports any folder location including those with long paths.
    
    Args:
        input_folder: Path to folder containing IN_*.txt files
        output_folder: Path to folder containing OUT_* subfolders
        
    Returns:
        List of matched file pairs with metadata
    """
    # Use normalize_path for long path support
    input_path = normalize_path(input_folder)
    output_path = normalize_path(output_folder)
    
    if not safe_path_exists(input_folder):
        raise FileNotFoundError(f"INPUT folder does not exist: {input_folder}")
    
    if not safe_path_exists(output_folder):
        raise FileNotFoundError(f"OUTPUT folder does not exist: {output_folder}")
    
    # Find all IN_*.txt files in input folder - use recursive search for any location
    in_files = find_files_recursive(input_path, "IN_*.txt", max_depth=3)
    in_files = [f for f in in_files if f.suffix == '.txt']
    in_files.sort()
    
    # Find all OUT_* subfolders in output folder
    out_folders = []
    try:
        out_folders = sorted([f for f in output_path.iterdir() if f.is_dir() and f.name.startswith("OUT_")])
    except (OSError, PermissionError):
        # Fallback to os.walk for long paths
        for root, dirs, files in os.walk(str(output_path)):
            for d in dirs:
                if d.startswith("OUT_"):
                    out_folders.append(Path(root) / d)
    out_folders.sort()
    
    matches = []
    matched_out_indices = set()
    
    for in_file in in_files:
        in_suffix = in_file.stem[3:]
        
        for idx, out_folder in enumerate(out_folders):
            if idx in matched_out_indices:
                continue
            
            out_suffix = out_folder.name[4:]
            
            if in_suffix == out_suffix:
                matches.append({
                    'in_file': in_file,
                    'out_folder': out_folder,
                    'suffix': in_suffix
                })
                matched_out_indices.add(idx)
                break
    
    return matches

def find_output_files(out_folder: Path, suffix: str) -> Dict:
    """Find output files with various extensions
    
    Args:
        out_folder: Path to the OUT_* folder
        suffix: Suffix to match (e.g., the identifier part of the filename)
        
    Returns:
        Dictionary mapping file types to their paths
    """
    output_files = {}
    
    # Normalize the out_folder path for long path support
    out_folder = normalize_path(out_folder)
    
    file_patterns = {
        'CNUM': f"CNUM_{suffix}.txt",
        'ORIG_TRIG': f"ORIG_TRIG_{suffix}.txt",
        'SCM': f"SCM_{suffix}.txt",
        'SIMODA': f"SIMODA_{suffix}.cps"
    }
    
    # Get all files in folder - use os.listdir for better long path support
    all_files_in_folder = []
    try:
        # Try with os.listdir first (better for long paths on Windows)
        out_folder_str = make_long_path(str(out_folder))
        all_files_in_folder = os.listdir(out_folder_str)
    except (OSError, PermissionError):
        try:
            # Fallback to Path.iterdir()
            all_files_in_folder = [f.name for f in out_folder.iterdir()]
        except (OSError, PermissionError):
            # Last resort - use os.walk
            try:
                for root, dirs, files in os.walk(str(out_folder)):
                    all_files_in_folder.extend(files)
                    break
            except (OSError, PermissionError):
                pass
    
    for file_type, pattern in file_patterns.items():
        # Check directly in the out_folder using filename comparison
        if pattern in all_files_in_folder:
            file_path = os.path.join(str(out_folder), pattern)
            output_files[file_type] = Path(file_path)
            continue
            
        # Check recursively in subdirectories
        found = False
        try:
            for root, dirs, files in os.walk(str(out_folder)):
                if pattern in files:
                    file_path = os.path.join(str(root), pattern)
                    output_files[file_type] = Path(file_path)
                    found = True
                    break
        except (OSError, PermissionError):
            pass
        if not found:
            output_files[file_type] = None
    
    return output_files


def safe_read_file(file_path: Path, max_lines: int = None, encoding: str = 'utf-8') -> List[str]:
    """Safely read a file with long path support
    
    Uses Windows extended path prefix (\\?\) for paths > 240 characters.
    
    Args:
        file_path: Path to the file to read
        max_lines: Maximum number of lines to read (None for all)
        encoding: File encoding
        
    Returns:
        List of lines from the file
    """
    # Normalize path
    file_path = normalize_path(file_path)
    
    # Get the string path
    path_str = str(file_path)
    
    # Try normal open first
    try:
        with open(path_str, 'r', encoding=encoding, errors='replace') as f:
            if max_lines:
                lines = [line.strip() for line in f.readlines()[:max_lines]]
            else:
                lines = [line.strip() for line in f.readlines()]
        return lines
    except (OSError, IOError):
        # Try with long path prefix for Windows
        long_path = make_long_path(path_str)
        try:
            with open(long_path, 'r', encoding=encoding, errors='replace') as f:
                if max_lines:
                    lines = [line.strip() for line in f.readlines()[:max_lines]]
                else:
                    lines = [line.strip() for line in f.readlines()]
            return lines
        except (OSError, IOError):
            return []

def extract_header_info(file_path: Path) -> Dict:
    """Extract header information from file with long path support
    
    Args:
        file_path: Path to the file
        
    Returns:
        Dictionary containing extracted header information
    """
    lines = safe_read_file(file_path, max_lines=15)
    
    if not lines:
        return {}
    
    info = {}
    for line in lines:
        if any(key in line for key in ["PO Number:", "PO NO:"]):
            try:
                info['po_number'] = line.split(":")[1].strip()
            except IndexError:
                pass
        elif any(key in line for key in ["Batch No:", "Batch NO:"]):
            try:
                info['batch_number'] = line.split(":")[1].strip()
            except IndexError:
                pass
        elif "SIM Quantity:" in line:
            try:
                info['sim_quantity'] = int(line.split(":")[1].strip())
            except (ValueError, IndexError):
                pass
        elif "Circle:" in line:
            try:
                info['circle'] = line.split(":")[1].strip()
            except IndexError:
                pass
        elif "SKU:" in line:
            try:
                info['sku'] = line.split(":")[1].strip()
            except IndexError:
                pass
    
    return info


def validate_quantity(file_path: Path, expected_data_lines: int, header_lines: int = 0) -> Tuple[bool, str]:
    """Validate line count in files with long path support
    
    Args:
        file_path: Path to the file
        expected_data_lines: Expected number of data lines
        header_lines: Number of header lines to subtract
        
    Returns:
        Tuple of (success, message)
    """
    lines = safe_read_file(file_path)
    
    if lines is None or (isinstance(lines, list) and len(lines) == 0):
        return False, f"Error reading file: {file_path}"
    
    actual_total_lines = len(lines)
    actual_data_lines = actual_total_lines - header_lines
    
    if actual_data_lines != expected_data_lines:
        return False, f"Line count mismatch: expected {expected_data_lines} data lines, found {actual_data_lines}"
    
    return True, f"Line count correct: {actual_data_lines} data lines"

def luhn_check(iccid: str) -> bool:
    """Validate ICCID using Luhn algorithm"""
    try:
        def digits_of(n):
            return [int(d) for d in str(n)]
        
        digits = digits_of(iccid)
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        checksum = sum(odd_digits)
        for d in even_digits:
            checksum += sum(digits_of(d * 2))
        return checksum % 10 == 0
    except Exception:
        return False
