# tools/file_tools.py
"""
File operation tools - search, open, and manage files.
Searches entire PC across all drives.
"""

import os
import subprocess
import string
from pathlib import Path
from typing import List, Optional, Tuple, Dict
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed


def list_files(path: str) -> List[str]:
    """List files in a directory."""
    try:
        return [os.path.join(path, p) for p in os.listdir(path)]
    except FileNotFoundError:
        return []


def open_file(file_path: str) -> Tuple[bool, str]:
    """
    Open a file with its default application.
    
    Args:
        file_path: Path to the file or folder
    
    Returns:
        Tuple of (success, message)
    """
    try:
        # Expand user path (~)
        file_path = os.path.expanduser(file_path)
        
        if not os.path.exists(file_path):
            return False, f"File not found: {file_path}"
        
        # Use os.startfile on Windows
        os.startfile(file_path)
        return True, f"Opened {os.path.basename(file_path)}"
    except Exception as e:
        return False, f"Failed to open file: {e}"


def open_folder(folder_path: str = None) -> Tuple[bool, str]:
    """Open a folder in File Explorer."""
    if folder_path is None:
        folder_path = os.path.expanduser("~")
    else:
        folder_path = os.path.expanduser(folder_path)
    
    try:
        if not os.path.isdir(folder_path):
            return False, f"Folder not found: {folder_path}"
        
        subprocess.Popen(f'explorer "{folder_path}"', shell=True)
        return True, f"Opened {folder_path}"
    except Exception as e:
        return False, f"Failed to open folder: {e}"


def _get_all_drives() -> List[str]:
    """Get all available drive letters on Windows."""
    drives = []
    for letter in string.ascii_uppercase:
        drive = f"{letter}:\\"
        if os.path.exists(drive):
            drives.append(drive)
    return drives


def _get_skip_folders() -> List[str]:
    """Get folders to skip during search."""
    try:
        from config.loader import get_skip_folders
        return get_skip_folders()
    except ImportError:
        return [
            "Windows", "Program Files", "Program Files (x86)", 
            "ProgramData", "$Recycle.Bin", "node_modules", 
            "__pycache__", ".git", "venv", "AppData", 
            "System Volume Information", "Recovery",
            ".vscode", ".idea", "dist", "build"
        ]


def _search_drive(drive: str, query: str, max_results: int, 
                  extensions: List[str], skip_folders: List[str]) -> List[Dict]:
    """Search a single drive for matching files."""
    results = []
    query_lower = query.lower()
    
    try:
        for root, dirs, files in os.walk(drive):
            # Skip system/hidden folders
            dirs[:] = [d for d in dirs if d not in skip_folders and not d.startswith('.')]
            
            for file in files:
                if query_lower in file.lower():
                    # Check extension filter
                    if extensions:
                        if not any(file.lower().endswith(ext.lower()) for ext in extensions):
                            continue
                    
                    file_path = os.path.join(root, file)
                    try:
                        stat = os.stat(file_path)
                        results.append({
                            "name": file,
                            "path": file_path,
                            "size_bytes": stat.st_size,
                            "size_readable": _format_size(stat.st_size),
                            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            "drive": drive
                        })
                    except (OSError, PermissionError):
                        continue
                    
                    if len(results) >= max_results:
                        return results
    except (PermissionError, OSError):
        pass
    
    return results


def search_files(query: str, search_path: str = None, 
                 max_results: int = 20, 
                 extensions: List[str] = None,
                 search_all_drives: bool = True) -> List[Dict]:
    """
    Search for files matching a query across the entire PC.
    
    Args:
        query: Search query (filename pattern)
        search_path: Specific directory to search (if None, searches all drives)
        max_results: Maximum number of results
        extensions: Filter by file extensions (e.g., ['.txt', '.pdf'])
        search_all_drives: If True and no search_path, searches all drives
    
    Returns:
        List of matching files with metadata
    """
    if not query:
        return []
    
    skip_folders = _get_skip_folders()
    
    # Get max results from config
    try:
        from config.loader import get_max_results
        max_results = get_max_results()
    except ImportError:
        pass
    
    # If specific path given, search only there
    if search_path:
        search_path = os.path.expanduser(search_path)
        return _search_drive(search_path, query, max_results, extensions, skip_folders)
    
    # Get drives to search
    try:
        from config.loader import get_search_drives
        drives = get_search_drives()
    except ImportError:
        drives = _get_all_drives()
    
    # Search all drives in parallel for speed
    all_results = []
    
    with ThreadPoolExecutor(max_workers=len(drives)) as executor:
        futures = {
            executor.submit(_search_drive, drive, query, max_results, extensions, skip_folders): drive
            for drive in drives
        }
        
        for future in as_completed(futures):
            try:
                results = future.result()
                all_results.extend(results)
                
                # Stop if we have enough results
                if len(all_results) >= max_results:
                    break
            except Exception:
                continue
    
    # Sort by modification time (newest first) and limit results
    all_results.sort(key=lambda x: x.get("modified", ""), reverse=True)
    return all_results[:max_results]


def get_recent_files(folder_path: str = None, limit: int = 10) -> List[Dict]:
    """
    Get recently modified files in a directory.
    
    Args:
        folder_path: Directory to check (default: user's Documents)
        limit: Maximum number of files to return
    
    Returns:
        List of recent files sorted by modification time
    """
    if folder_path is None:
        folder_path = os.path.join(os.path.expanduser("~"), "Documents")
    
    files = []
    
    try:
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            if os.path.isfile(item_path):
                stat = os.stat(item_path)
                files.append({
                    "name": item,
                    "path": item_path,
                    "size_bytes": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime)
                })
    except (PermissionError, FileNotFoundError):
        return []
    
    # Sort by modification time (newest first)
    files.sort(key=lambda x: x["modified"], reverse=True)
    
    # Convert datetime to string for output
    for f in files[:limit]:
        f["modified"] = f["modified"].isoformat()
    
    return files[:limit]


def get_downloads() -> List[Dict]:
    """Get recent files from Downloads folder."""
    downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    return get_recent_files(downloads, limit=10)


def get_file_info(file_path: str) -> Dict:
    """Get detailed information about a file."""
    file_path = os.path.expanduser(file_path)
    
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}
    
    try:
        stat = os.stat(file_path)
        path = Path(file_path)
        
        return {
            "name": path.name,
            "path": str(path.absolute()),
            "extension": path.suffix,
            "size_bytes": stat.st_size,
            "size_readable": _format_size(stat.st_size),
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "is_directory": os.path.isdir(file_path)
        }
    except Exception as e:
        return {"error": str(e)}


def _format_size(size_bytes: int) -> str:
    """Format file size in human-readable form."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def create_folder(folder_path: str) -> Tuple[bool, str]:
    """Create a new folder."""
    try:
        folder_path = os.path.expanduser(folder_path)
        os.makedirs(folder_path, exist_ok=True)
        return True, f"Created folder: {folder_path}"
    except Exception as e:
        return False, f"Failed to create folder: {e}"


def _search_folders_in_drive(drive: str, query: str, max_results: int, 
                              skip_folders: List[str]) -> List[Dict]:
    """Search a single drive for matching folders."""
    results = []
    query_lower = query.lower()
    
    try:
        for root, dirs, _ in os.walk(drive):
            # Skip system/hidden folders
            dirs[:] = [d for d in dirs if d not in skip_folders and not d.startswith('.')]
            
            for folder in dirs:
                if query_lower in folder.lower():
                    folder_path = os.path.join(root, folder)
                    try:
                        stat = os.stat(folder_path)
                        results.append({
                            "name": folder,
                            "path": folder_path,
                            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            "drive": drive
                        })
                    except (OSError, PermissionError):
                        continue
                    
                    if len(results) >= max_results:
                        return results
    except (PermissionError, OSError):
        pass
    
    return results


def search_folders(query: str, search_path: str = None, 
                   max_results: int = 20,
                   search_all_drives: bool = True) -> List[Dict]:
    """
    Search for folders matching a query across the entire PC.
    
    Args:
        query: Search query (folder name pattern)
        search_path: Specific directory to search (if None, searches all drives)
        max_results: Maximum number of results
        search_all_drives: If True and no search_path, searches all drives
    
    Returns:
        List of matching folders with metadata
    """
    if not query:
        return []
    
    skip_folders = _get_skip_folders()
    
    # Get max results from config
    try:
        from config.loader import get_max_results
        max_results = get_max_results()
    except ImportError:
        pass
    
    # If specific path given, search only there
    if search_path:
        search_path = os.path.expanduser(search_path)
        return _search_folders_in_drive(search_path, query, max_results, skip_folders)
    
    # Get drives to search
    try:
        from config.loader import get_search_drives
        drives = get_search_drives()
    except ImportError:
        drives = _get_all_drives()
    
    # Search all drives in parallel for speed
    all_results = []
    
    with ThreadPoolExecutor(max_workers=len(drives)) as executor:
        futures = {
            executor.submit(_search_folders_in_drive, drive, query, max_results, skip_folders): drive
            for drive in drives
        }
        
        for future in as_completed(futures):
            try:
                results = future.result()
                all_results.extend(results)
                
                # Stop if we have enough results
                if len(all_results) >= max_results:
                    break
            except Exception:
                continue
    
    # Sort by modification time (newest first) and limit results
    all_results.sort(key=lambda x: x.get("modified", ""), reverse=True)
    return all_results[:max_results]


def find_and_open_folder(query: str) -> Tuple[bool, str]:
    """
    Find a folder by name and open it in Explorer.
    Searches across all drives.
    """
    results = search_folders(query, max_results=1)
    
    if results:
        folder_path = results[0]["path"]
        return open_folder(folder_path)
    else:
        return False, f"Folder not found: {query}"


def find_and_open_file(query: str) -> Tuple[bool, str]:
    """
    Find a file by name and open it.
    Searches across all drives.
    """
    results = search_files(query, max_results=1)
    
    if results:
        file_path = results[0]["path"]
        return open_file(file_path)
    else:
        return False, f"File not found: {query}"
