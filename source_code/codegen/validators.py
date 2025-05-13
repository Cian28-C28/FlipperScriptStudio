"""
Code Validators Module

This module provides validators for generated C code.
"""

import re
import logging
import subprocess
import tempfile
import os
from typing import Tuple, List, Dict

logger = logging.getLogger(__name__)


class CodeValidator:
    """
    Validates generated C code.
    """
    
    def __init__(self):
        """Initialize the code validator."""
        pass
        
    def validate_syntax(self, code: str) -> Tuple[bool, str]:
        """
        Validate C code syntax using gcc.
        
        Args:
            code: C code to validate
            
        Returns:
            tuple: (is_valid, error_message)
        """
        # Create a temporary file with the code
        with tempfile.NamedTemporaryFile(suffix='.c', delete=False) as temp_file:
            temp_file_path = temp_file.name
            temp_file.write(code.encode('utf-8'))
            
        try:
            # Run gcc to check syntax only (-fsyntax-only)
            result = subprocess.run(
                ['gcc', '-fsyntax-only', '-Wall', temp_file_path],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                # Syntax error
                return False, result.stderr
            
            return True, ""
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
            
        finally:
            # Clean up the temporary file
            try:
                os.unlink(temp_file_path)
            except:
                pass
                
    def validate_includes(self, code: str) -> Tuple[bool, str]:
        """
        Validate that all required includes are present.
        
        Args:
            code: C code to validate
            
        Returns:
            tuple: (is_valid, error_message)
        """
        required_includes = [
            "#include <furi.h>",
            "#include <gui/gui.h>"
        ]
        
        for include in required_includes:
            if include not in code:
                return False, f"Missing required include: {include}"
                
        return True, ""
        
    def validate_entry_point(self, code: str, entry_point: str) -> Tuple[bool, str]:
        """
        Validate that the entry point function is defined.
        
        Args:
            code: C code to validate
            entry_point: Expected entry point function name
            
        Returns:
            tuple: (is_valid, error_message)
        """
        # Look for the entry point function definition
        pattern = r'int32_t\s+' + re.escape(entry_point) + r'\s*\([^)]*\)\s*{'
        if not re.search(pattern, code):
            return False, f"Missing entry point function: {entry_point}"
            
        return True, ""
        
    def validate_app_structure(self, code: str, app_name: str) -> Tuple[bool, str]:
        """
        Validate that the application structure is properly defined.
        
        Args:
            code: C code to validate
            app_name: Application name
            
        Returns:
            tuple: (is_valid, error_message)
        """
        # Check for app state structure
        state_pattern = r'typedef\s+struct\s+{[^}]*}\s+' + re.escape(app_name) + r'_state_t\s*;'
        if not re.search(state_pattern, code):
            return False, f"Missing app state structure: {app_name}_state_t"
            
        # Check for view port initialization
        if "view_port_alloc" not in code:
            return False, "Missing view port allocation"
            
        # Check for GUI initialization
        if "furi_record_open(RECORD_GUI)" not in code:
            return False, "Missing GUI initialization"
            
        return True, ""
        
    def validate_code(self, code: str, app_name: str, entry_point: str) -> Tuple[bool, List[str]]:
        """
        Validate the generated code.
        
        Args:
            code: C code to validate
            app_name: Application name
            entry_point: Entry point function name
            
        Returns:
            tuple: (is_valid, list_of_errors)
        """
        errors = []
        
        # Validate includes
        valid, error = self.validate_includes(code)
        if not valid:
            errors.append(error)
            
        # Validate entry point
        valid, error = self.validate_entry_point(code, entry_point)
        if not valid:
            errors.append(error)
            
        # Validate app structure
        valid, error = self.validate_app_structure(code, app_name)
        if not valid:
            errors.append(error)
            
        # Validate syntax if gcc is available
        try:
            valid, error = self.validate_syntax(code)
            if not valid:
                errors.append(f"Syntax error: {error}")
        except:
            logger.warning("GCC not available for syntax validation")
            
        return len(errors) == 0, errors