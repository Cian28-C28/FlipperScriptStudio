"""
uFBT Configuration Module

This module provides configuration management for uFBT integration.
"""

import os
import json
import logging
import platform
import subprocess
from pathlib import Path
from typing import Dict, Optional, List, Tuple

logger = logging.getLogger(__name__)


class UfbtConfig:
    """
    Configuration manager for uFBT integration.
    """
    
    DEFAULT_UFBT_HOME = os.path.expanduser("~/.ufbt")
    
    def __init__(self, ufbt_path: str = None):
        """
        Initialize the uFBT configuration.
        
        Args:
            ufbt_path: Path to the uFBT executable or repository
        """
        self.ufbt_path = ufbt_path or self._find_ufbt_path()
        self.ufbt_home = os.environ.get("UFBT_HOME", self.DEFAULT_UFBT_HOME)
        self.sdk_state = self._get_sdk_state()
        
    def _find_ufbt_path(self) -> str:
        """
        Find the uFBT executable in the system path.
        
        Returns:
            str: Path to uFBT executable or None if not found
        """
        try:
            # Try to find ufbt in PATH
            if platform.system() == "Windows":
                result = subprocess.run(
                    ["where", "ufbt"], 
                    capture_output=True, 
                    text=True, 
                    check=False
                )
                if result.returncode == 0:
                    return result.stdout.strip().split("\n")[0]
            else:
                result = subprocess.run(
                    ["which", "ufbt"], 
                    capture_output=True, 
                    text=True, 
                    check=False
                )
                if result.returncode == 0:
                    return result.stdout.strip()
                    
            # Check if ufbt is installed as a Python module
            try:
                import ufbt
                return "ufbt"  # Use module name directly
            except ImportError:
                pass
                
            # Look for ufbt in common locations
            common_paths = [
                "./temp/ufbt_repo/ufbt/__main__.py",
                "../temp/ufbt_repo/ufbt/__main__.py",
                "./ufbt_repo/ufbt/__main__.py"
            ]
            
            for path in common_paths:
                if os.path.exists(path):
                    return f"python {path}"
                    
            logger.warning("uFBT not found in PATH or common locations")
            return "ufbt"  # Default to just the name, hoping it's in PATH
            
        except Exception as e:
            logger.error(f"Error finding uFBT: {e}")
            return "ufbt"  # Default to just the name
            
    def _get_sdk_state(self) -> Dict:
        """
        Get the current SDK state from uFBT.
        
        Returns:
            dict: SDK state information
        """
        try:
            # Run ufbt status --json
            cmd = f"{self.ufbt_path} status --json"
            result = subprocess.run(
                cmd, 
                shell=True,
                capture_output=True, 
                text=True, 
                check=False
            )
            
            if result.returncode == 0:
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    logger.error("Failed to parse uFBT status output as JSON")
            else:
                logger.error(f"uFBT status command failed: {result.stderr}")
                
        except Exception as e:
            logger.error(f"Error getting SDK state: {e}")
            
        return {}
        
    def is_sdk_installed(self) -> bool:
        """
        Check if the SDK is installed.
        
        Returns:
            bool: True if SDK is installed, False otherwise
        """
        return "error" not in self.sdk_state
        
    def get_sdk_version(self) -> str:
        """
        Get the installed SDK version.
        
        Returns:
            str: SDK version or "unknown" if not available
        """
        return self.sdk_state.get("version", "unknown")
        
    def get_sdk_target(self) -> str:
        """
        Get the installed SDK target.
        
        Returns:
            str: SDK target or "f7" (default) if not available
        """
        return self.sdk_state.get("target", "f7")
        
    def get_sdk_dir(self) -> str:
        """
        Get the SDK directory.
        
        Returns:
            str: SDK directory path
        """
        return self.sdk_state.get("sdk_dir", os.path.join(self.ufbt_home, "current"))
        
    def update_sdk(self, target: str = None, channel: str = "release") -> Tuple[bool, str]:
        """
        Update the SDK.
        
        Args:
            target: Hardware target (f7 or f18)
            channel: Update channel (dev, rc, release)
            
        Returns:
            tuple: (success, message)
        """
        try:
            cmd = [self.ufbt_path, "update"]
            
            if target:
                cmd.extend(["--hw-target", target])
                
            if channel:
                cmd.extend(["--channel", channel])
                
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                # Refresh SDK state
                self.sdk_state = self._get_sdk_state()
                return True, "SDK updated successfully"
            else:
                return False, f"SDK update failed: {result.stderr}"
                
        except Exception as e:
            return False, f"SDK update error: {str(e)}"
            
    def get_furi_components(self) -> List[str]:
        """
        Get a list of available FURI components.
        
        Returns:
            list: List of FURI component names
        """
        # Standard components that are always available
        components = ["gui", "storage", "subghz", "nfc", "infrared", "bt"]
        
        return components