"""
Export Dialog Module

This module provides a dialog for configuring export options for Flipper Zero applications.
"""

import os
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QLineEdit, QComboBox, QCheckBox, QPushButton,
    QFileDialog, QDialogButtonBox, QTabWidget, QWidget
)


class ExportDialog(QDialog):
    """
    Dialog for configuring export options for Flipper Zero applications.
    """
    
    exportRequested = pyqtSignal(dict)  # Emitted when export is requested
    
    def __init__(self, parent=None):
        """
        Initialize the export dialog.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.setWindowTitle("Export Flipper Application")
        self.setMinimumWidth(500)
        
        # Create layout
        self.layout = QVBoxLayout(self)
        
        # Create tabs
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)
        
        # Create export options tab
        self.export_tab = QWidget()
        self.tabs.addTab(self.export_tab, "Export Options")
        
        # Create build options tab
        self.build_tab = QWidget()
        self.tabs.addTab(self.build_tab, "Build Options")
        
        # Create deployment tab
        self.deploy_tab = QWidget()
        self.tabs.addTab(self.deploy_tab, "Deployment")
        
        # Set up tabs
        self.setup_export_tab()
        self.setup_build_tab()
        self.setup_deploy_tab()
        
        # Create button box
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)
        
        # Initialize export options
        self.export_options = {
            "export_type": "source",
            "output_dir": "",
            "build": False,
            "clean_build": False,
            "create_fap": False,
            "deploy": False,
            "deploy_method": "none"
        }
        
    def setup_export_tab(self):
        """Set up the export options tab."""
        layout = QVBoxLayout(self.export_tab)
        
        # Export type group
        export_type_group = QGroupBox("Export Type")
        export_type_layout = QVBoxLayout(export_type_group)
        
        self.export_source_radio = QCheckBox("Export Source Code")
        self.export_source_radio.setChecked(True)
        export_type_layout.addWidget(self.export_source_radio)
        
        self.export_binary_radio = QCheckBox("Export Binary (FAP)")
        export_type_layout.addWidget(self.export_binary_radio)
        
        layout.addWidget(export_type_group)
        
        # Output directory group
        output_dir_group = QGroupBox("Output Directory")
        output_dir_layout = QHBoxLayout(output_dir_group)
        
        self.output_dir_edit = QLineEdit()
        output_dir_layout.addWidget(self.output_dir_edit)
        
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.browse_output_dir)
        output_dir_layout.addWidget(self.browse_button)
        
        layout.addWidget(output_dir_group)
        
        # Connect signals
        self.export_source_radio.toggled.connect(self.update_export_options)
        self.export_binary_radio.toggled.connect(self.update_export_options)
        self.output_dir_edit.textChanged.connect(self.update_export_options)
        
    def setup_build_tab(self):
        """Set up the build options tab."""
        layout = QVBoxLayout(self.build_tab)
        
        # Build options group
        build_options_group = QGroupBox("Build Options")
        build_options_layout = QVBoxLayout(build_options_group)
        
        self.build_checkbox = QCheckBox("Build after export")
        build_options_layout.addWidget(self.build_checkbox)
        
        self.clean_build_checkbox = QCheckBox("Clean build")
        build_options_layout.addWidget(self.clean_build_checkbox)
        
        self.create_fap_checkbox = QCheckBox("Create FAP package")
        build_options_layout.addWidget(self.create_fap_checkbox)
        
        layout.addWidget(build_options_group)
        
        # SDK options group
        sdk_options_group = QGroupBox("SDK Options")
        sdk_options_layout = QFormLayout(sdk_options_group)
        
        self.sdk_target_combo = QComboBox()
        self.sdk_target_combo.addItems(["f7", "f18"])
        sdk_options_layout.addRow("Target:", self.sdk_target_combo)
        
        self.sdk_channel_combo = QComboBox()
        self.sdk_channel_combo.addItems(["release", "rc", "dev"])
        sdk_options_layout.addRow("Channel:", self.sdk_channel_combo)
        
        layout.addWidget(sdk_options_group)
        
        # Connect signals
        self.build_checkbox.toggled.connect(self.update_export_options)
        self.clean_build_checkbox.toggled.connect(self.update_export_options)
        self.create_fap_checkbox.toggled.connect(self.update_export_options)
        self.sdk_target_combo.currentTextChanged.connect(self.update_export_options)
        self.sdk_channel_combo.currentTextChanged.connect(self.update_export_options)
        
    def setup_deploy_tab(self):
        """Set up the deployment tab."""
        layout = QVBoxLayout(self.deploy_tab)
        
        # Deploy options group
        deploy_options_group = QGroupBox("Deployment Options")
        deploy_options_layout = QVBoxLayout(deploy_options_group)
        
        self.deploy_checkbox = QCheckBox("Deploy after build")
        deploy_options_layout.addWidget(self.deploy_checkbox)
        
        # Deploy method group
        deploy_method_group = QGroupBox("Deploy Method")
        deploy_method_layout = QVBoxLayout(deploy_method_group)
        
        self.deploy_usb_radio = QCheckBox("Deploy via USB (Serial)")
        deploy_method_layout.addWidget(self.deploy_usb_radio)
        
        self.deploy_file_radio = QCheckBox("Copy to mounted Flipper")
        deploy_method_layout.addWidget(self.deploy_file_radio)
        
        deploy_options_layout.addWidget(deploy_method_group)
        
        layout.addWidget(deploy_options_group)
        
        # Device selection group
        device_group = QGroupBox("Device Selection")
        device_layout = QFormLayout(device_group)
        
        self.device_combo = QComboBox()
        self.device_combo.addItem("Auto-detect")
        device_layout.addRow("Device:", self.device_combo)
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_devices)
        device_layout.addRow("", self.refresh_button)
        
        layout.addWidget(device_group)
        
        # Connect signals
        self.deploy_checkbox.toggled.connect(self.update_export_options)
        self.deploy_usb_radio.toggled.connect(self.update_export_options)
        self.deploy_file_radio.toggled.connect(self.update_export_options)
        self.device_combo.currentTextChanged.connect(self.update_export_options)
        
    def browse_output_dir(self):
        """Open a file dialog to select the output directory."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            ""
        )
        
        if directory:
            self.output_dir_edit.setText(directory)
            
    def refresh_devices(self):
        """Refresh the list of connected devices."""
        # This would be implemented to detect connected Flipper Zero devices
        # For now, just add a placeholder
        self.device_combo.clear()
        self.device_combo.addItem("Auto-detect")
        self.device_combo.addItem("Flipper Zero (COM3)")
        
    def update_export_options(self):
        """Update the export options based on UI state."""
        # Export type
        if self.export_binary_radio.isChecked():
            self.export_options["export_type"] = "binary"
        else:
            self.export_options["export_type"] = "source"
            
        # Output directory
        self.export_options["output_dir"] = self.output_dir_edit.text()
        
        # Build options
        self.export_options["build"] = self.build_checkbox.isChecked()
        self.export_options["clean_build"] = self.clean_build_checkbox.isChecked()
        self.export_options["create_fap"] = self.create_fap_checkbox.isChecked()
        
        # SDK options
        self.export_options["sdk_target"] = self.sdk_target_combo.currentText()
        self.export_options["sdk_channel"] = self.sdk_channel_combo.currentText()
        
        # Deploy options
        self.export_options["deploy"] = self.deploy_checkbox.isChecked()
        
        # Deploy method
        if self.deploy_usb_radio.isChecked():
            self.export_options["deploy_method"] = "usb"
        elif self.deploy_file_radio.isChecked():
            self.export_options["deploy_method"] = "file"
        else:
            self.export_options["deploy_method"] = "none"
            
        # Device selection
        self.export_options["device"] = self.device_combo.currentText()
        
    def accept(self):
        """Handle dialog acceptance."""
        self.update_export_options()
        self.exportRequested.emit(self.export_options)
        super().accept()
        
    def get_export_options(self):
        """
        Get the current export options.
        
        Returns:
            dict: Dictionary of export options
        """
        return self.export_options.copy()