"""
File I/O Module

This module provides utility functions for file operations.
"""

import os
import json
import shutil
import tempfile


def ensure_directory_exists(directory):
    """
    Ensure that a directory exists, creating it if necessary.
    
    Args:
        directory: Directory path
        
    Returns:
        bool: True if directory exists or was created, False otherwise
    """
    try:
        os.makedirs(directory, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating directory {directory}: {e}")
        return False


def read_json_file(file_path):
    """
    Read a JSON file.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        dict: JSON data or None if file could not be read
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading JSON file {file_path}: {e}")
        return None


def write_json_file(file_path, data):
    """
    Write data to a JSON file.
    
    Args:
        file_path: Path to JSON file
        data: Data to write
        
    Returns:
        bool: True if file was written successfully, False otherwise
    """
    try:
        # Create directory if it doesn't exist
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            
        # Write file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
            
        return True
    except Exception as e:
        print(f"Error writing JSON file {file_path}: {e}")
        return False


def read_text_file(file_path):
    """
    Read a text file.
    
    Args:
        file_path: Path to text file
        
    Returns:
        str: File contents or None if file could not be read
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading text file {file_path}: {e}")
        return None


def write_text_file(file_path, text):
    """
    Write text to a file.
    
    Args:
        file_path: Path to text file
        text: Text to write
        
    Returns:
        bool: True if file was written successfully, False otherwise
    """
    try:
        # Create directory if it doesn't exist
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            
        # Write file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(text)
            
        return True
    except Exception as e:
        print(f"Error writing text file {file_path}: {e}")
        return False


def copy_file(source, destination):
    """
    Copy a file.
    
    Args:
        source: Source file path
        destination: Destination file path
        
    Returns:
        bool: True if file was copied successfully, False otherwise
    """
    try:
        # Create directory if it doesn't exist
        directory = os.path.dirname(destination)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            
        # Copy file
        shutil.copy2(source, destination)
        
        return True
    except Exception as e:
        print(f"Error copying file from {source} to {destination}: {e}")
        return False


def create_temp_directory():
    """
    Create a temporary directory.
    
    Returns:
        str: Path to temporary directory or None if directory could not be created
    """
    try:
        return tempfile.mkdtemp()
    except Exception as e:
        print(f"Error creating temporary directory: {e}")
        return None


def remove_directory(directory):
    """
    Remove a directory and all its contents.
    
    Args:
        directory: Directory path
        
    Returns:
        bool: True if directory was removed successfully, False otherwise
    """
    try:
        shutil.rmtree(directory)
        return True
    except Exception as e:
        print(f"Error removing directory {directory}: {e}")
        return False


def list_files(directory, extension=None):
    """
    List files in a directory.
    
    Args:
        directory: Directory path
        extension: Optional file extension filter
        
    Returns:
        list: List of file paths or empty list if directory could not be read
    """
    try:
        files = []
        for file in os.listdir(directory):
            file_path = os.path.join(directory, file)
            if os.path.isfile(file_path):
                if extension is None or file.endswith(extension):
                    files.append(file_path)
        return files
    except Exception as e:
        print(f"Error listing files in directory {directory}: {e}")
        return []


def get_file_extension(file_path):
    """
    Get the extension of a file.
    
    Args:
        file_path: File path
        
    Returns:
        str: File extension (including the dot) or empty string if no extension
    """
    return os.path.splitext(file_path)[1]


def get_file_name(file_path):
    """
    Get the name of a file without extension.
    
    Args:
        file_path: File path
        
    Returns:
        str: File name without extension
    """
    return os.path.splitext(os.path.basename(file_path))[0]


def get_file_size(file_path):
    """
    Get the size of a file in bytes.
    
    Args:
        file_path: File path
        
    Returns:
        int: File size in bytes or -1 if file could not be accessed
    """
    try:
        return os.path.getsize(file_path)
    except Exception as e:
        print(f"Error getting file size for {file_path}: {e}")
        return -1