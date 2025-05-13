"""
Manifest Editor Module

This module provides the editor for Flipper Zero app manifest data.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLabel, QLineEdit, QComboBox, QCheckBox, QPushButton,
    QFileDialog, QGroupBox, QScrollArea, QSizePolicy
)


class ManifestEditor(QWidget):
    """
    Editor for Flipper Zero app manifest data.
    """
    
    manifestChanged = pyqtSignal(dict)  # Emitted when manifest data changes
    
    def __init__(self, parent=None):
        """
        Initialize a new manifest editor.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Set up layout
        self.layout = QVBoxLayout(self)
        
        # Create scroll area for form
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        
        # Create form widget
        self.form_widget = QWidget()
        self.form_layout = QFormLayout(self.form_widget)
        self.form_layout.setContentsMargins(0, 0, 0, 0)
        self.form_layout.setSpacing(10)
        
        # Set scroll area widget
        self.scroll_area.setWidget(self.form_widget)
        self.layout.addWidget(self.scroll_area)
        
        # Create form fields
        self.create_basic_info_section()
        self.create_requirements_section()
        self.create_icon_section()
        
        # Dictionary to store manifest data
        self.manifest_data = {
            "name": "",
            "appid": "",
            "version": "1.0",
            "entry_point": "app_main",
            "requires": ["gui"],
            "stack_size": 1024,
            "icon": None
        }
        
        # Connect signals
        self.connect_signals()
        
    def create_basic_info_section(self):
        """Create the basic information section of the form."""
        # Basic Info Group
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout(basic_group)
        
        # App Name
        self.app_name_edit = QLineEdit()
        self.app_name_edit.setPlaceholderText("My Flipper App")
        basic_layout.addRow("App Name:", self.app_name_edit)
        
        # App ID
        self.app_id_edit = QLineEdit()
        self.app_id_edit.setPlaceholderText("my_flipper_app")
        basic_layout.addRow("App ID:", self.app_id_edit)
        
        # Version
        self.version_edit = QLineEdit()
        self.version_edit.setPlaceholderText("1.0")
        basic_layout.addRow("Version:", self.version_edit)
        
        # Entry Point
        self.entry_point_edit = QLineEdit()
        self.entry_point_edit.setPlaceholderText("app_main")
        basic_layout.addRow("Entry Point:", self.entry_point_edit)
        
        # Stack Size
        self.stack_size_edit = QLineEdit()
        self.stack_size_edit.setPlaceholderText("1024")
        basic_layout.addRow("Stack Size:", self.stack_size_edit)
        
        # Add to form
        self.form_layout.addRow(basic_group)
        
    def create_requirements_section(self):
        """Create the requirements section of the form."""
        # Requirements Group
        req_group = QGroupBox("Requirements")
        req_layout = QVBoxLayout(req_group)
        
        # Create checkboxes for common requirements
        self.req_gui = QCheckBox("GUI")
        self.req_gui.setChecked(True)  # GUI is required by default
        req_layout.addWidget(self.req_gui)
        
        self.req_storage = QCheckBox("Storage")
        req_layout.addWidget(self.req_storage)
        
        self.req_subghz = QCheckBox("SubGHz")
        req_layout.addWidget(self.req_subghz)
        
        self.req_nfc = QCheckBox("NFC")
        req_layout.addWidget(self.req_nfc)
        
        self.req_bt = QCheckBox("Bluetooth")
        req_layout.addWidget(self.req_bt)
        
        self.req_infrared = QCheckBox("Infrared")
        req_layout.addWidget(self.req_infrared)
        
        # Add to form
        self.form_layout.addRow(req_group)
        
    def create_icon_section(self):
        """Create the icon section of the form."""
        # Icon Group
        icon_group = QGroupBox("App Icon")
        icon_layout = QVBoxLayout(icon_group)
        
        # Icon preview
        self.icon_preview = QLabel("No icon selected")
        self.icon_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_preview.setMinimumHeight(64)
        self.icon_preview.setMinimumWidth(64)
        self.icon_preview.setStyleSheet("border: 1px solid gray;")
        icon_layout.addWidget(self.icon_preview)
        
        # Icon buttons layout
        icon_buttons_layout = QHBoxLayout()
        
        # Select icon button
        self.select_icon_button = QPushButton("Select Icon...")
        icon_buttons_layout.addWidget(self.select_icon_button)
        
        # Clear icon button
        self.clear_icon_button = QPushButton("Clear Icon")
        icon_buttons_layout.addWidget(self.clear_icon_button)
        
        icon_layout.addLayout(icon_buttons_layout)
        
        # Add to form
        self.form_layout.addRow(icon_group)
        
    def connect_signals(self):
        """Connect widget signals to slots."""
        # Basic info
        self.app_name_edit.textChanged.connect(self.update_manifest)
        self.app_id_edit.textChanged.connect(self.update_manifest)
        self.version_edit.textChanged.connect(self.update_manifest)
        self.entry_point_edit.textChanged.connect(self.update_manifest)
        self.stack_size_edit.textChanged.connect(self.update_manifest)
        
        # Requirements
        self.req_gui.stateChanged.connect(self.update_requirements)
        self.req_storage.stateChanged.connect(self.update_requirements)
        self.req_subghz.stateChanged.connect(self.update_requirements)
        self.req_nfc.stateChanged.connect(self.update_requirements)
        self.req_bt.stateChanged.connect(self.update_requirements)
        self.req_infrared.stateChanged.connect(self.update_requirements)
        
        # Icon
        self.select_icon_button.clicked.connect(self.select_icon)
        self.clear_icon_button.clicked.connect(self.clear_icon)
        
    def update_manifest(self):
        """Update the manifest data from form fields."""
        # Update basic info
        self.manifest_data["name"] = self.app_name_edit.text()
        self.manifest_data["appid"] = self.app_id_edit.text()
        self.manifest_data["version"] = self.version_edit.text() or "1.0"
        self.manifest_data["entry_point"] = self.entry_point_edit.text() or "app_main"
        
        # Update stack size
        try:
            stack_size = int(self.stack_size_edit.text())
            self.manifest_data["stack_size"] = stack_size
        except ValueError:
            self.manifest_data["stack_size"] = 1024
            
        # Emit signal
        self.manifestChanged.emit(self.manifest_data)
        
    def update_requirements(self):
        """Update the requirements list from checkboxes."""
        requirements = []
        
        # Check each requirement
        if self.req_gui.isChecked():
            requirements.append("gui")
        if self.req_storage.isChecked():
            requirements.append("storage")
        if self.req_subghz.isChecked():
            requirements.append("subghz")
        if self.req_nfc.isChecked():
            requirements.append("nfc")
        if self.req_bt.isChecked():
            requirements.append("bt")
        if self.req_infrared.isChecked():
            requirements.append("infrared")
            
        # Update manifest data
        self.manifest_data["requires"] = requirements
        
        # Emit signal
        self.manifestChanged.emit(self.manifest_data)
        
    def select_icon(self):
        """Open file dialog to select an icon."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Icon",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp);;All Files (*)"
        )
        
        if file_path:
            # Load the image
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                # Scale to 64x64 if needed
                if pixmap.width() > 64 or pixmap.height() > 64:
                    pixmap = pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio)
                    
                # Update preview
                self.icon_preview.setPixmap(pixmap)
                self.icon_preview.setText("")
                
                # Update manifest data
                self.manifest_data["icon"] = file_path
                
                # Emit signal
                self.manifestChanged.emit(self.manifest_data)
                
    def clear_icon(self):
        """Clear the selected icon."""
        self.icon_preview.setPixmap(QPixmap())
        self.icon_preview.setText("No icon selected")
        
        # Update manifest data
        self.manifest_data["icon"] = None
        
        # Emit signal
        self.manifestChanged.emit(self.manifest_data)
        
    def set_manifest_data(self, data):
        """
        Set the manifest data and update form fields.
        
        Args:
            data: Dictionary of manifest data
        """
        if not isinstance(data, dict):
            return
            
        # Store data
        self.manifest_data = data.copy()
        
        # Update basic info fields
        self.app_name_edit.setText(data.get("name", ""))
        self.app_id_edit.setText(data.get("appid", ""))
        self.version_edit.setText(data.get("version", "1.0"))
        self.entry_point_edit.setText(data.get("entry_point", "app_main"))
        self.stack_size_edit.setText(str(data.get("stack_size", 1024)))
        
        # Update requirements checkboxes
        requirements = data.get("requires", ["gui"])
        self.req_gui.setChecked("gui" in requirements)
        self.req_storage.setChecked("storage" in requirements)
        self.req_subghz.setChecked("subghz" in requirements)
        self.req_nfc.setChecked("nfc" in requirements)
        self.req_bt.setChecked("bt" in requirements)
        self.req_infrared.setChecked("infrared" in requirements)
        
        # Update icon preview
        icon_path = data.get("icon")
        if icon_path and isinstance(icon_path, str):
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                self.icon_preview.setPixmap(pixmap)
                self.icon_preview.setText("")
            else:
                self.icon_preview.setPixmap(QPixmap())
                self.icon_preview.setText("Icon not found")
        else:
            self.icon_preview.setPixmap(QPixmap())
            self.icon_preview.setText("No icon selected")
            
    def get_manifest_data(self):
        """
        Get the current manifest data.
        
        Returns:
            dict: Dictionary of manifest data
        """
        return self.manifest_data.copy()
        
    def validate(self):
        """
        Validate the manifest data.
        
        Returns:
            tuple: (is_valid, error_message)
        """
        # Check required fields
        if not self.manifest_data.get("name"):
            return False, "App Name is required"
            
        if not self.manifest_data.get("appid"):
            return False, "App ID is required"
            
        # Check app ID format (lowercase, underscores, no spaces)
        app_id = self.manifest_data.get("appid", "")
        if not all(c.islower() or c.isdigit() or c == '_' for c in app_id):
            return False, "App ID must contain only lowercase letters, numbers, and underscores"
            
        # Check version format
        version = self.manifest_data.get("version", "")
        if not version:
            return False, "Version is required"
            
        # Check entry point
        entry_point = self.manifest_data.get("entry_point", "")
        if not entry_point:
            return False, "Entry Point is required"
            
        # Check requirements
        if not self.manifest_data.get("requires"):
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
        lines.append(f"    appid=\"{self.manifest_data.get('appid', '')}\"")
        lines.append(f"    name=\"{self.manifest_data.get('name', '')}\"")
        lines.append(f"    apptype=FlipperAppType.EXTERNAL")
        lines.append(f"    entry_point=\"{self.manifest_data.get('entry_point', 'app_main')}\"")
        lines.append(f"    stack_size={self.manifest_data.get('stack_size', 1024)}")
        lines.append(f"    version=\"{self.manifest_data.get('version', '1.0')}\"")
        
        # Add icon if present
        icon = self.manifest_data.get("icon")
        if icon:
            import os
            icon_filename = os.path.basename(icon)
            lines.append(f"    icon=\"{icon_filename}\"")
            
        # Add requirements
        reqs = self.manifest_data.get("requires", [])
        if reqs:
            lines.append("    requires=[")
            for req in reqs:
                lines.append(f"        \"{req}\",")
            lines.append("    ]")
            
        lines.append(")")
        
        return "\n".join(lines)