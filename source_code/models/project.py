"""
Project Model Module

This module provides the data model for projects in the FlipperScriptStudio application.
"""

import os
import json
import datetime
from PyQt6.QtCore import QObject, pyqtSignal


class Project(QObject):
    """
    Data model for a FlipperScriptStudio project.
    """
    
    projectChanged = pyqtSignal()  # Emitted when project data changes
    manifestChanged = pyqtSignal(dict)  # Emitted when manifest data changes
    
    def __init__(self):
        """Initialize a new project."""
        super().__init__()
        
        # Project metadata
        self.metadata = {
            "name": "Untitled Project",
            "author": "",
            "description": "",
            "created": datetime.datetime.now().isoformat(),
            "modified": datetime.datetime.now().isoformat()
        }
        
        # Manifest data
        self.manifest = {
            "name": "New Flipper App",
            "appid": "new_flipper_app",
            "version": "1.0",
            "entry_point": "app_main",
            "requires": ["gui"],
            "stack_size": 1024,
            "icon": None
        }
        
        # Canvas data
        self.canvas = {
            "blocks": [],
            "connections": []
        }
        
        # Resources
        self.resources = []
        
        # Project file path
        self.file_path = None
        
        # Modified flag
        self.modified = False
        
    def set_metadata(self, key, value):
        """
        Set a metadata value.
        
        Args:
            key: Metadata key
            value: Metadata value
        """
        if key in self.metadata and self.metadata[key] != value:
            self.metadata[key] = value
            self.metadata["modified"] = datetime.datetime.now().isoformat()
            self.modified = True
            self.projectChanged.emit()
            
    def get_metadata(self, key, default=None):
        """
        Get a metadata value.
        
        Args:
            key: Metadata key
            default: Default value if key doesn't exist
            
        Returns:
            The metadata value or default
        """
        return self.metadata.get(key, default)
        
    def set_manifest(self, manifest_data):
        """
        Set the manifest data.
        
        Args:
            manifest_data: Dictionary of manifest data
        """
        if self.manifest != manifest_data:
            self.manifest = manifest_data.copy()
            self.modified = True
            self.manifestChanged.emit(self.manifest)
            self.projectChanged.emit()
            
    def get_manifest(self):
        """
        Get the manifest data.
        
        Returns:
            dict: Dictionary of manifest data
        """
        return self.manifest.copy()
        
    def set_canvas(self, canvas_data):
        """
        Set the canvas data.
        
        Args:
            canvas_data: Dictionary of canvas data
        """
        if self.canvas != canvas_data:
            self.canvas = canvas_data.copy()
            self.modified = True
            self.projectChanged.emit()
            
    def get_canvas(self):
        """
        Get the canvas data.
        
        Returns:
            dict: Dictionary of canvas data
        """
        return self.canvas.copy()
        
    def add_resource(self, name, resource_type, path):
        """
        Add a resource to the project.
        
        Args:
            name: Resource name
            resource_type: Resource type
            path: Resource path
            
        Returns:
            dict: The added resource
        """
        resource = {
            "name": name,
            "type": resource_type,
            "path": path
        }
        
        self.resources.append(resource)
        self.modified = True
        self.projectChanged.emit()
        
        return resource
        
    def remove_resource(self, name):
        """
        Remove a resource from the project.
        
        Args:
            name: Resource name
            
        Returns:
            bool: True if resource was removed, False otherwise
        """
        for i, resource in enumerate(self.resources):
            if resource["name"] == name:
                del self.resources[i]
                self.modified = True
                self.projectChanged.emit()
                return True
                
        return False
        
    def get_resources(self):
        """
        Get all resources.
        
        Returns:
            list: List of resources
        """
        return self.resources.copy()
        
    def load(self, file_path):
        """
        Load project from file.
        
        Args:
            file_path: Path to project file
            
        Returns:
            bool: True if project was loaded successfully, False otherwise
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Load metadata
            self.metadata = data.get("metadata", {})
            
            # Load manifest
            self.manifest = data.get("manifest", {})
            
            # Load canvas
            self.canvas = data.get("canvas", {"blocks": [], "connections": []})
            
            # Load resources
            self.resources = data.get("resources", [])
            
            # Set file path
            self.file_path = file_path
            
            # Reset modified flag
            self.modified = False
            
            # Emit signals
            self.manifestChanged.emit(self.manifest)
            self.projectChanged.emit()
            
            return True
        except Exception as e:
            print(f"Error loading project: {e}")
            return False
            
    def save(self, file_path=None):
        """
        Save project to file.
        
        Args:
            file_path: Path to save to (uses current path if None)
            
        Returns:
            bool: True if project was saved successfully, False otherwise
        """
        if file_path:
            self.file_path = file_path
            
        if not self.file_path:
            return False
            
        try:
            # Update modification time
            self.metadata["modified"] = datetime.datetime.now().isoformat()
            
            # Create project data
            data = {
                "version": "1.0",
                "metadata": self.metadata,
                "manifest": self.manifest,
                "canvas": self.canvas,
                "resources": self.resources
            }
            
            # Save to file
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
                
            # Reset modified flag
            self.modified = False
            
            # Emit signal
            self.projectChanged.emit()
            
            return True
        except Exception as e:
            print(f"Error saving project: {e}")
            return False
            
    def is_modified(self):
        """
        Check if project has been modified.
        
        Returns:
            bool: True if project has been modified, False otherwise
        """
        return self.modified
        
    def get_file_path(self):
        """
        Get the project file path.
        
        Returns:
            str: Project file path or None if not saved
        """
        return self.file_path
        
    def get_file_name(self):
        """
        Get the project file name.
        
        Returns:
            str: Project file name or "Untitled" if not saved
        """
        if self.file_path:
            return os.path.basename(self.file_path)
        else:
            return "Untitled"