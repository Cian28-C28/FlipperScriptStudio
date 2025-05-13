"""
Manifest Model Module

This module provides the data model for Flipper Zero app manifests.
"""

import os
import re
from PyQt6.QtCore import QObject, pyqtSignal


class Manifest(QObject):
    """
    Data model for a Flipper Zero app manifest.
    """
    
    manifestChanged = pyqtSignal(dict)  # Emitted when manifest data changes
    
    def __init__(self):
        """Initialize a new manifest."""
        super().__init__()
        
        # Default manifest data
        self.data = {
            "name": "New Flipper App",
            "appid": "new_flipper_app",
            "version": "1.0",
            "entry_point": "app_main",
            "requires": ["gui"],
            "stack_size": 1024,
            "icon": None
        }
        
    def set_data(self, data):
        """
        Set the manifest data.
        
        Args:
            data: Dictionary of manifest data
        """
        if self.data != data:
            self.data = data.copy()
            self.manifestChanged.emit(self.data)
            
    def get_data(self):
        """
        Get the manifest data.
        
        Returns:
            dict: Dictionary of manifest data
        """
        return self.data.copy()
        
    def set_value(self, key, value):
        """
        Set a manifest value.
        
        Args:
            key: Manifest key
            value: Manifest value
        """
        if key in self.data and self.data[key] != value:
            self.data[key] = value
            self.manifestChanged.emit(self.data)
            
    def get_value(self, key, default=None):
        """
        Get a manifest value.
        
        Args:
            key: Manifest key
            default: Default value if key doesn't exist
            
        Returns:
            The manifest value or default
        """
        return self.data.get(key, default)
        
    def validate(self):
        """
        Validate the manifest data.
        
        Returns:
            tuple: (is_valid, error_message)
        """
        # Check required fields
        if not self.data.get("name"):
            return False, "App Name is required"
            
        if not self.data.get("appid"):
            return False, "App ID is required"
            
        # Check app ID format (lowercase, underscores, no spaces)
        app_id = self.data.get("appid", "")
        if not re.match(r'^[a-z0-9_]+$', app_id):
            return False, "App ID must contain only lowercase letters, numbers, and underscores"
            
        # Check version format
        version = self.data.get("version", "")
        if not version:
            return False, "Version is required"
            
        # Check entry point
        entry_point = self.data.get("entry_point", "")
        if not entry_point:
            return False, "Entry Point is required"
            
        # Check requirements
        if not self.data.get("requires"):
            return False, "At least one requirement must be selected"
            
        return True, ""
        
    def generate_manifest_text(self):
        """
        Generate manifest.txt content from the current data.
        
        Returns:
            str: Content for manifest.txt file
        """
        lines = []
        
        # Add basic info
        lines.append(f"App(")
        lines.append(f"    appid=\"{self.data.get('appid', '')}\"")
        lines.append(f"    name=\"{self.data.get('name', '')}\"")
        lines.append(f"    apptype=FlipperAppType.EXTERNAL")
        lines.append(f"    entry_point=\"{self.data.get('entry_point', 'app_main')}\"")
        lines.append(f"    stack_size={self.data.get('stack_size', 1024)}")
        lines.append(f"    version=\"{self.data.get('version', '1.0')}\"")
        
        # Add icon if present
        icon = self.data.get("icon")
        if icon:
            icon_filename = os.path.basename(icon)
            lines.append(f"    icon=\"{icon_filename}\"")
            
        # Add requirements
        reqs = self.data.get("requires", [])
        if reqs:
            lines.append("    requires=[")
            for req in reqs:
                lines.append(f"        \"{req}\",")
            lines.append("    ]")
            
        lines.append(")")
        
        return "\n".join(lines)
        
    def load_from_text(self, text):
        """
        Load manifest data from manifest.txt content.
        
        Args:
            text: Content of manifest.txt
            
        Returns:
            bool: True if manifest was loaded successfully, False otherwise
        """
        try:
            # Extract app ID
            app_id_match = re.search(r'appid="([^"]+)"', text)
            if app_id_match:
                self.data["appid"] = app_id_match.group(1)
                
            # Extract name
            name_match = re.search(r'name="([^"]+)"', text)
            if name_match:
                self.data["name"] = name_match.group(1)
                
            # Extract entry point
            entry_point_match = re.search(r'entry_point="([^"]+)"', text)
            if entry_point_match:
                self.data["entry_point"] = entry_point_match.group(1)
                
            # Extract stack size
            stack_size_match = re.search(r'stack_size=(\d+)', text)
            if stack_size_match:
                self.data["stack_size"] = int(stack_size_match.group(1))
                
            # Extract version
            version_match = re.search(r'version="([^"]+)"', text)
            if version_match:
                self.data["version"] = version_match.group(1)
                
            # Extract icon
            icon_match = re.search(r'icon="([^"]+)"', text)
            if icon_match:
                self.data["icon"] = icon_match.group(1)
                
            # Extract requirements
            requires_match = re.search(r'requires=\[(.*?)\]', text, re.DOTALL)
            if requires_match:
                requires_text = requires_match.group(1)
                requires = []
                for req_match in re.finditer(r'"([^"]+)"', requires_text):
                    requires.append(req_match.group(1))
                self.data["requires"] = requires
                
            # Emit signal
            self.manifestChanged.emit(self.data)
            
            return True
        except Exception as e:
            print(f"Error loading manifest from text: {e}")
            return False