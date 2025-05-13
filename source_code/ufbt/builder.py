"""
uFBT Builder Module

This module provides functionality to build Flipper Zero applications using uFBT.
"""

import os
import re
import shutil
import logging
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

from .config import UfbtConfig

logger = logging.getLogger(__name__)


class UfbtBuilder:
    """
    Builder for Flipper Zero applications using uFBT.
    """
    
    def __init__(self, config: UfbtConfig = None):
        """
        Initialize the uFBT builder.
        
        Args:
            config: uFBT configuration
        """
        self.config = config or UfbtConfig()
        
    def create_app_structure(self, app_name: str, output_dir: str, files: Dict[str, str]) -> Tuple[bool, str]:
        """
        Create the application directory structure.
        
        Args:
            app_name: Application name
            output_dir: Output directory
            files: Dictionary of file names and contents
            
        Returns:
            tuple: (success, message)
        """
        try:
            # Create app directory
            app_dir = os.path.join(output_dir, app_name)
            os.makedirs(app_dir, exist_ok=True)
            
            # Write files
            for file_name, content in files.items():
                file_path = os.path.join(app_dir, file_name)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
            return True, f"Application structure created at {app_dir}"
            
        except Exception as e:
            return False, f"Failed to create application structure: {str(e)}"
            
    def create_application_manifest(self, manifest_data: Dict[str, Any], output_dir: str, app_name: str) -> Tuple[bool, str]:
        """
        Create the application manifest file.
        
        Args:
            manifest_data: Manifest data
            output_dir: Output directory
            app_name: Application name
            
        Returns:
            tuple: (success, message)
        """
        try:
            app_dir = os.path.join(output_dir, app_name)
            os.makedirs(app_dir, exist_ok=True)
            
            # Generate manifest content
            lines = []
            lines.append(f"App(")
            lines.append(f"    appid=\"{manifest_data.get('appid', app_name)}\"")
            lines.append(f"    name=\"{manifest_data.get('name', app_name)}\"")
            lines.append(f"    apptype=FlipperAppType.EXTERNAL")
            lines.append(f"    entry_point=\"{manifest_data.get('entry_point', 'app_main')}\"")
            lines.append(f"    stack_size={manifest_data.get('stack_size', 1024)}")
            lines.append(f"    version=\"{manifest_data.get('version', '1.0')}\"")
            
            # Add icon if present
            icon = manifest_data.get("icon")
            if icon and os.path.exists(icon):
                icon_filename = os.path.basename(icon)
                # Copy icon to app directory
                shutil.copy(icon, os.path.join(app_dir, icon_filename))
                lines.append(f"    icon=\"{icon_filename}\"")
                
            # Add requirements
            reqs = manifest_data.get("requires", [])
            if reqs:
                lines.append("    requires=[")
                for req in reqs:
                    lines.append(f"        \"{req}\",")
                lines.append("    ]")
                
            lines.append(")")
            
            # Write manifest file
            manifest_path = os.path.join(app_dir, "application.fam")
            with open(manifest_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(lines))
                
            return True, f"Manifest created at {manifest_path}"
            
        except Exception as e:
            return False, f"Failed to create manifest: {str(e)}"
            
    def build_app(self, app_dir: str, clean: bool = False) -> Tuple[bool, str, str]:
        """
        Build the application using uFBT.
        
        Args:
            app_dir: Application directory
            clean: Whether to clean before building
            
        Returns:
            tuple: (success, output, error)
        """
        try:
            # Prepare command
            cmd = [self.config.ufbt_path]
            
            if clean:
                cmd.append("clean")
                
            # Change to app directory
            cwd = os.getcwd()
            os.chdir(app_dir)
            
            try:
                # Run uFBT
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                if result.returncode == 0:
                    return True, result.stdout, ""
                else:
                    return False, result.stdout, result.stderr
            finally:
                # Restore working directory
                os.chdir(cwd)
                
        except Exception as e:
            return False, "", f"Build error: {str(e)}"
            
    def flash_app(self, app_dir: str) -> Tuple[bool, str, str]:
        """
        Flash the application to a connected Flipper Zero.
        
        Args:
            app_dir: Application directory
            
        Returns:
            tuple: (success, output, error)
        """
        try:
            # Prepare command
            cmd = [self.config.ufbt_path, "flash"]
            
            # Change to app directory
            cwd = os.getcwd()
            os.chdir(app_dir)
            
            try:
                # Run uFBT flash
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                if result.returncode == 0:
                    return True, result.stdout, ""
                else:
                    return False, result.stdout, result.stderr
            finally:
                # Restore working directory
                os.chdir(cwd)
                
        except Exception as e:
            return False, "", f"Flash error: {str(e)}"
            
    def create_fap_package(self, app_dir: str, output_dir: str = None) -> Tuple[bool, str, str]:
        """
        Create a FAP package from the application.
        
        Args:
            app_dir: Application directory
            output_dir: Output directory for the FAP file
            
        Returns:
            tuple: (success, fap_path, error)
        """
        try:
            # Prepare command
            cmd = [self.config.ufbt_path, "fap"]
            
            # Change to app directory
            cwd = os.getcwd()
            os.chdir(app_dir)
            
            try:
                # Run uFBT fap
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                if result.returncode == 0:
                    # Find the FAP file in the output
                    fap_path_match = re.search(r'Saved to: (.+\.fap)', result.stdout)
                    if fap_path_match:
                        fap_path = fap_path_match.group(1)
                        
                        # Copy to output directory if specified
                        if output_dir:
                            os.makedirs(output_dir, exist_ok=True)
                            fap_filename = os.path.basename(fap_path)
                            output_path = os.path.join(output_dir, fap_filename)
                            shutil.copy(fap_path, output_path)
                            return True, output_path, ""
                            
                        return True, fap_path, ""
                    else:
                        return False, "", "FAP file path not found in output"
                else:
                    return False, "", result.stderr
            finally:
                # Restore working directory
                os.chdir(cwd)
                
        except Exception as e:
            return False, "", f"FAP creation error: {str(e)}"