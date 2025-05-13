"""
Main Window Module

This module provides the main application window for FlipperScriptStudio.
"""

import os
import json
import tempfile
import logging
from PyQt6.QtCore import Qt, QSettings, QSize, QPoint, pyqtSignal, QProcess
from PyQt6.QtGui import QAction, QIcon, QKeySequence
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QToolBar, QStatusBar, QFileDialog, QMessageBox, QDockWidget,
    QApplication, QTabWidget
)

from blocks import BlockFactory
from models.project import Project
from codegen import CodeGenerator, CodeValidator
from ufbt import UfbtBuilder, UfbtConfig, UfbtDeployer
from utils.furi_helpers import FuriComponentHelper

from .canvas import BlockCanvas
from .block_palette import BlockPalette
from .property_editor import PropertyEditor
from .manifest_editor import ManifestEditor
from .export_dialog import ExportDialog
from .build_output import BuildOutputWidget


class MainWindow(QMainWindow):
    """
    Main application window for FlipperScriptStudio.
    """
    
    projectChanged = pyqtSignal(str)  # Emitted when project changes
    
    def __init__(self):
        """Initialize the main window."""
        super().__init__()
        
        # Set window properties
        self.setWindowTitle("FlipperScriptStudio")
        self.setMinimumSize(1024, 768)
        
        # Initialize settings
        self.settings = QSettings("FlipperScriptStudio", "FlipperScriptStudio")
        
        # Initialize project
        self.project = Project()
        
        # Initialize block factory
        self.block_factory = None
        
        # Initialize code generator
        self.code_generator = None
        
        # Initialize uFBT components
        self.ufbt_config = UfbtConfig()
        self.ufbt_builder = UfbtBuilder(self.ufbt_config)
        self.ufbt_deployer = UfbtDeployer(self.ufbt_config)
        
        # Set up UI
        self.setup_ui()
        
        # Load settings
        self.load_settings()
        
        # Load block definitions
        self.load_block_definitions()
        
        # Initialize code generator
        self.code_generator = CodeGenerator(self.block_factory)
        
        # Create new project
        self.new_project()
        
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def setup_ui(self):
        """Set up the user interface."""
        # Create central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Create main layout
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Create main splitter
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_layout.addWidget(self.main_splitter)
        
        # Create block palette
        self.block_palette = BlockPalette()
        self.block_palette.setMinimumWidth(200)
        self.block_palette.setMaximumWidth(300)
        
        # Create canvas
        self.canvas = BlockCanvas()
        
        # Create property editor
        self.property_editor = PropertyEditor()
        self.property_editor.setMinimumWidth(200)
        self.property_editor.setMaximumWidth(300)
        
        # Add widgets to main splitter
        self.main_splitter.addWidget(self.block_palette)
        self.main_splitter.addWidget(self.canvas)
        self.main_splitter.addWidget(self.property_editor)
        
        # Set splitter sizes
        self.main_splitter.setSizes([200, 600, 200])
        
        # Create dock widgets
        self.create_dock_widgets()
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Create menu bar
        self.create_menus()
        
        # Create toolbar
        self.create_toolbar()
        
        # Connect signals
        self.connect_signals()
        
    def create_dock_widgets(self):
        """Create dock widgets."""
        # Create manifest editor dock widget
        self.manifest_dock = QDockWidget("Manifest Editor", self)
        self.manifest_dock.setAllowedAreas(
            Qt.DockWidgetArea.BottomDockWidgetArea | 
            Qt.DockWidgetArea.RightDockWidgetArea
        )
        self.manifest_editor = ManifestEditor()
        self.manifest_dock.setWidget(self.manifest_editor)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.manifest_dock)
        
        # Create build output dock widget
        self.build_dock = QDockWidget("Build Output", self)
        self.build_dock.setAllowedAreas(
            Qt.DockWidgetArea.BottomDockWidgetArea | 
            Qt.DockWidgetArea.RightDockWidgetArea
        )
        self.build_output = BuildOutputWidget()
        self.build_dock.setWidget(self.build_output)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.build_dock)
        
        # Initially hide build output
        self.build_dock.hide()
        
    def create_menus(self):
        """Create application menus."""
        # File menu
        self.file_menu = self.menuBar().addMenu("&File")
        
        # New project action
        self.new_action = QAction("&New Project", self)
        self.new_action.setShortcut(QKeySequence.StandardKey.New)
        self.new_action.triggered.connect(self.new_project)
        self.file_menu.addAction(self.new_action)
        
        # Open project action
        self.open_action = QAction("&Open Project...", self)
        self.open_action.setShortcut(QKeySequence.StandardKey.Open)
        self.open_action.triggered.connect(self.open_project)
        self.file_menu.addAction(self.open_action)
        
        # Save project action
        self.save_action = QAction("&Save Project", self)
        self.save_action.setShortcut(QKeySequence.StandardKey.Save)
        self.save_action.triggered.connect(self.save_project)
        self.file_menu.addAction(self.save_action)
        
        # Save project as action
        self.save_as_action = QAction("Save Project &As...", self)
        self.save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        self.save_as_action.triggered.connect(self.save_project_as)
        self.file_menu.addAction(self.save_as_action)
        
        self.file_menu.addSeparator()
        
        # Export submenu
        self.export_menu = self.file_menu.addMenu("&Export")
        
        # Export source action
        self.export_source_action = QAction("Export &Source Code...", self)
        self.export_source_action.triggered.connect(self.export_source)
        self.export_menu.addAction(self.export_source_action)
        
        # Export binary action
        self.export_binary_action = QAction("Export &Binary (FAP)...", self)
        self.export_binary_action.triggered.connect(self.export_binary)
        self.export_menu.addAction(self.export_binary_action)
        
        # Export with options action
        self.export_options_action = QAction("Export with &Options...", self)
        self.export_options_action.triggered.connect(self.export_with_options)
        self.export_menu.addAction(self.export_options_action)
        
        self.file_menu.addSeparator()
        
        # Exit action
        self.exit_action = QAction("E&xit", self)
        self.exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        self.exit_action.triggered.connect(self.close)
        self.file_menu.addAction(self.exit_action)
        
        # Edit menu
        self.edit_menu = self.menuBar().addMenu("&Edit")
        
        # Undo action
        self.undo_action = QAction("&Undo", self)
        self.undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        self.undo_action.triggered.connect(self.undo)
        self.edit_menu.addAction(self.undo_action)
        
        # Redo action
        self.redo_action = QAction("&Redo", self)
        self.redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        self.redo_action.triggered.connect(self.redo)
        self.edit_menu.addAction(self.redo_action)
        
        self.edit_menu.addSeparator()
        
        # Delete action
        self.delete_action = QAction("&Delete", self)
        self.delete_action.setShortcut(QKeySequence.StandardKey.Delete)
        self.delete_action.triggered.connect(self.delete_selected)
        self.edit_menu.addAction(self.delete_action)
        
        # View menu
        self.view_menu = self.menuBar().addMenu("&View")
        
        # Zoom in action
        self.zoom_in_action = QAction("Zoom &In", self)
        self.zoom_in_action.setShortcut(QKeySequence.StandardKey.ZoomIn)
        self.zoom_in_action.triggered.connect(self.zoom_in)
        self.view_menu.addAction(self.zoom_in_action)
        
        # Zoom out action
        self.zoom_out_action = QAction("Zoom &Out", self)
        self.zoom_out_action.setShortcut(QKeySequence.StandardKey.ZoomOut)
        self.zoom_out_action.triggered.connect(self.zoom_out)
        self.view_menu.addAction(self.zoom_out_action)
        
        # Reset zoom action
        self.reset_zoom_action = QAction("&Reset Zoom", self)
        self.reset_zoom_action.setShortcut("Ctrl+0")
        self.reset_zoom_action.triggered.connect(self.reset_zoom)
        self.view_menu.addAction(self.reset_zoom_action)
        
        self.view_menu.addSeparator()
        
        # Toggle manifest editor action
        self.toggle_manifest_action = QAction("&Manifest Editor", self)
        self.toggle_manifest_action.setCheckable(True)
        self.toggle_manifest_action.setChecked(True)
        self.toggle_manifest_action.triggered.connect(self.toggle_manifest_editor)
        self.view_menu.addAction(self.toggle_manifest_action)
        
        # Toggle build output action
        self.toggle_build_output_action = QAction("&Build Output", self)
        self.toggle_build_output_action.setCheckable(True)
        self.toggle_build_output_action.setChecked(False)
        self.toggle_build_output_action.triggered.connect(self.toggle_build_output)
        self.view_menu.addAction(self.toggle_build_output_action)
        
        # Build menu
        self.build_menu = self.menuBar().addMenu("&Build")
        
        # Build action
        self.build_action = QAction("&Build App", self)
        self.build_action.setShortcut("F7")
        self.build_action.triggered.connect(self.build_app)
        self.build_menu.addAction(self.build_action)
        
        # Clean and build action
        self.clean_build_action = QAction("&Clean and Build", self)
        self.clean_build_action.setShortcut("Shift+F7")
        self.clean_build_action.triggered.connect(self.clean_and_build_app)
        self.build_menu.addAction(self.clean_build_action)
        
        self.build_menu.addSeparator()
        
        # Deploy action
        self.deploy_action = QAction("&Deploy to Flipper", self)
        self.deploy_action.setShortcut("F5")
        self.deploy_action.triggered.connect(self.deploy_app)
        self.build_menu.addAction(self.deploy_action)
        
        # Tools menu
        self.tools_menu = self.menuBar().addMenu("&Tools")
        
        # Update SDK action
        self.update_sdk_action = QAction("&Update SDK", self)
        self.update_sdk_action.triggered.connect(self.update_sdk)
        self.tools_menu.addAction(self.update_sdk_action)
        
        # SDK status action
        self.sdk_status_action = QAction("SDK &Status", self)
        self.sdk_status_action.triggered.connect(self.show_sdk_status)
        self.tools_menu.addAction(self.sdk_status_action)
        
        # Help menu
        self.help_menu = self.menuBar().addMenu("&Help")
        
        # About action
        self.about_action = QAction("&About", self)
        self.about_action.triggered.connect(self.show_about)
        self.help_menu.addAction(self.about_action)
        
    def create_toolbar(self):
        """Create application toolbar."""
        self.toolbar = QToolBar("Main Toolbar")
        self.toolbar.setMovable(False)
        self.addToolBar(self.toolbar)
        
        # Add actions to toolbar
        self.toolbar.addAction(self.new_action)
        self.toolbar.addAction(self.open_action)
        self.toolbar.addAction(self.save_action)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.build_action)
        self.toolbar.addAction(self.deploy_action)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.export_options_action)
        
    def connect_signals(self):
        """Connect widget signals to slots."""
        # Canvas signals
        self.canvas.blockSelected.connect(self.on_block_selected)
        self.canvas.blockMoved.connect(self.on_block_moved)
        self.canvas.connectionCreated.connect(self.on_connection_created)
        self.canvas.connectionDeleted.connect(self.on_connection_deleted)
        
        # Property editor signals
        self.property_editor.propertyChanged.connect(self.on_property_changed)
        
        # Manifest editor signals
        self.manifest_editor.manifestChanged.connect(self.on_manifest_changed)
        
        # Build output signals
        self.build_output.buildFinished.connect(self.on_build_finished)
        
        # Project signals
        self.project.projectChanged.connect(self.on_project_changed)
        
    def load_settings(self):
        """Load application settings."""
        # Load window geometry
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        else:
            # Default size and position
            self.resize(1200, 800)
            self.move(100, 100)
            
        # Load window state
        state = self.settings.value("windowState")
        if state:
            self.restoreState(state)
            
        # Load splitter sizes
        splitter_sizes = self.settings.value("splitterSizes")
        if splitter_sizes:
            self.main_splitter.setSizes(splitter_sizes)
            
    def save_settings(self):
        """Save application settings."""
        # Save window geometry
        self.settings.setValue("geometry", self.saveGeometry())
        
        # Save window state
        self.settings.setValue("windowState", self.saveState())
        
        # Save splitter sizes
        self.settings.setValue("splitterSizes", self.main_splitter.sizes())
        
    def load_block_definitions(self):
        """Load block definitions from file."""
        # Look for block definitions in standard locations
        search_paths = [
            "./research/visual_scripting/block_definitions.json",
            "./block_definitions.json",
            "../research/visual_scripting/block_definitions.json"
        ]
        
        definitions_file = None
        for path in search_paths:
            if os.path.exists(path):
                definitions_file = path
                break
                
        if not definitions_file:
            QMessageBox.warning(
                self,
                "Block Definitions Not Found",
                "Could not find block definitions file. The application may not function correctly."
            )
            return
            
        # Create block factory
        self.block_factory = BlockFactory(definitions_file)
        
        # Load blocks into palette
        block_count = self.block_palette.load_blocks_from_factory(self.block_factory)
        
        self.status_bar.showMessage(f"Loaded {block_count} blocks from definitions")
        
    def new_project(self):
        """Create a new project."""
        # Check if current project needs saving
        if self.project.is_modified() and not self.confirm_discard_changes():
            return
            
        # Create new project
        self.project = Project()
        
        # Clear canvas
        self.canvas.clear()
        
        # Reset manifest editor
        self.manifest_editor.set_manifest_data(self.project.get_manifest())
        
        # Update window title
        self.update_window_title()
        
        # Update status
        self.status_bar.showMessage("New project created")
        
    def open_project(self):
        """Open an existing project."""
        # Check if current project needs saving
        if self.project.is_modified() and not self.confirm_discard_changes():
            return
            
        # Show file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Project",
            "",
            "Flipper Script Projects (*.fsp);;All Files (*)"
        )
        
        if not file_path:
            return
            
        # Load project
        self.load_project(file_path)
        
    def load_project(self, file_path):
        """
        Load a project from file.
        
        Args:
            file_path: Path to project file
        """
        # Create new project
        new_project = Project()
        
        # Load project from file
        if not new_project.load(file_path):
            QMessageBox.critical(
                self,
                "Error Opening Project",
                f"Failed to open project from {file_path}"
            )
            return False
            
        # Set as current project
        self.project = new_project
        
        # Update manifest editor
        self.manifest_editor.set_manifest_data(self.project.get_manifest())
        
        # Update canvas
        canvas_data = self.project.get_canvas()
        if not self.canvas.from_dict(canvas_data, self.block_factory):
            QMessageBox.warning(
                self,
                "Warning",
                "Failed to load some blocks or connections"
            )
            
        # Update window title
        self.update_window_title()
        
        # Update status
        self.status_bar.showMessage(f"Project loaded from {file_path}")
        
        # Emit signal
        self.projectChanged.emit(file_path)
        
        return True
        
    def save_project(self):
        """Save the current project."""
        if not self.project.get_file_path():
            return self.save_project_as()
            
        # Update project data from canvas
        self.project.set_canvas(self.canvas.to_dict())
        
        # Save project
        if not self.project.save():
            QMessageBox.critical(
                self,
                "Error Saving Project",
                f"Failed to save project to {self.project.get_file_path()}"
            )
            return False
            
        # Update window title
        self.update_window_title()
        
        # Update status
        self.status_bar.showMessage(f"Project saved to {self.project.get_file_path()}")
        
        return True
        
    def save_project_as(self):
        """Save the current project with a new name."""
        # Show file dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Project",
            "",
            "Flipper Script Projects (*.fsp);;All Files (*)"
        )
        
        if not file_path:
            return False
            
        # Add extension if not present
        if not file_path.lower().endswith('.fsp'):
            file_path += '.fsp'
            
        # Update project data from canvas
        self.project.set_canvas(self.canvas.to_dict())
        
        # Save project
        if not self.project.save(file_path):
            QMessageBox.critical(
                self,
                "Error Saving Project",
                f"Failed to save project to {file_path}"
            )
            return False
            
        # Update window title
        self.update_window_title()
        
        # Update status
        self.status_bar.showMessage(f"Project saved to {file_path}")
        
        return True
        
    def export_source(self):
        """Export the project as source code."""
        self.export_with_options(export_type="source")
        
    def export_binary(self):
        """Export the project as a binary (FAP)."""
        self.export_with_options(export_type="binary")
        
    def export_with_options(self, export_type=None):
        """
        Export the project with options.
        
        Args:
            export_type: Type of export (source or binary)
        """
        # Create export dialog
        dialog = ExportDialog(self)
        
        # Set export type if specified
        if export_type:
            if export_type == "source":
                dialog.export_source_radio.setChecked(True)
                dialog.export_binary_radio.setChecked(False)
            elif export_type == "binary":
                dialog.export_source_radio.setChecked(False)
                dialog.export_binary_radio.setChecked(True)
                
        # Connect export signal
        dialog.exportRequested.connect(self.handle_export)
        
        # Show dialog
        dialog.exec()
        
    def handle_export(self, export_options):
        """
        Handle export request.
        
        Args:
            export_options: Dictionary of export options
        """
        # Validate manifest
        valid, error_message = self.manifest_editor.validate()
        if not valid:
            QMessageBox.warning(
                self,
                "Invalid Manifest",
                f"Cannot export app: {error_message}"
            )
            return
            
        # Get output directory
        output_dir = export_options.get("output_dir")
        if not output_dir:
            output_dir = QFileDialog.getExistingDirectory(
                self,
                "Select Output Directory",
                ""
            )
            
        if not output_dir:
            return
            
        # Get manifest data
        manifest_data = self.manifest_editor.get_manifest_data()
        app_id = manifest_data.get("appid", "flipper_app")
        
        # Update project data from canvas
        self.project.set_canvas(self.canvas.to_dict())
        
        # Generate code
        try:
            # Show build output dock
            self.build_dock.show()
            self.toggle_build_output_action.setChecked(True)
            
            # Clear build output
            self.build_output.clear_output()
            
            # Generate code
            self.build_output.append_message("Generating code...", self.build_output.info_format)
            generated_code = self.code_generator.generate_code(
                self.project,
                self.project.get_canvas()
            )
            
            if "error" in generated_code:
                self.build_output.append_message(
                    f"Code generation failed: {generated_code['error']}",
                    self.build_output.error_format
                )
                return
                
            # Create app directory
            app_dir = os.path.join(output_dir, app_id)
            os.makedirs(app_dir, exist_ok=True)
            
            # Create application structure
            success, message = self.ufbt_builder.create_app_structure(
                app_id,
                output_dir,
                generated_code
            )
            
            if not success:
                self.build_output.append_message(
                    f"Failed to create application structure: {message}",
                    self.build_output.error_format
                )
                return
                
            self.build_output.append_message(message, self.build_output.success_format)
            
            # Create manifest
            success, message = self.ufbt_builder.create_application_manifest(
                manifest_data,
                output_dir,
                app_id
            )
            
            if not success:
                self.build_output.append_message(
                    f"Failed to create manifest: {message}",
                    self.build_output.error_format
                )
                return
                
            self.build_output.append_message(message, self.build_output.success_format)
            
            # Build if requested
            if export_options.get("build", False):
                self.build_output.append_message("Building application...", self.build_output.info_format)
                
                # Build the app
                success, stdout, stderr = self.ufbt_builder.build_app(
                    app_dir,
                    clean=export_options.get("clean_build", False)
                )
                
                # Display build output
                if stdout:
                    self.build_output.append_build_output(stdout)
                    
                if stderr:
                    self.build_output.append_build_output(stderr)
                    
                if success:
                    self.build_output.append_message("Build successful", self.build_output.success_format)
                    
                    # Create FAP if requested
                    if export_options.get("create_fap", False):
                        self.build_output.append_message("Creating FAP package...", self.build_output.info_format)
                        
                        success, fap_path, error = self.ufbt_builder.create_fap_package(
                            app_dir,
                            output_dir
                        )
                        
                        if success:
                            self.build_output.append_message(
                                f"FAP package created: {fap_path}",
                                self.build_output.success_format
                            )
                            
                            # Deploy if requested
                            if export_options.get("deploy", False):
                                self.deploy_fap(fap_path, export_options)
                        else:
                            self.build_output.append_message(
                                f"Failed to create FAP package: {error}",
                                self.build_output.error_format
                            )
                else:
                    self.build_output.append_message("Build failed", self.build_output.error_format)
                    
            # Show success message
            QMessageBox.information(
                self,
                "Export Successful",
                f"Application exported to {app_dir}"
            )
            
            # Update status
            self.status_bar.showMessage(f"Application exported to {app_dir}")
            
        except Exception as e:
            self.logger.exception("Export error")
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to export application: {str(e)}"
            )
            
    def deploy_fap(self, fap_path, export_options):
        """
        Deploy a FAP file to a Flipper Zero device.
        
        Args:
            fap_path: Path to the FAP file
            export_options: Dictionary of export options
        """
        deploy_method = export_options.get("deploy_method", "none")
        device = export_options.get("device", "Auto-detect")
        
        if deploy_method == "usb":
            # Deploy via USB
            self.build_output.append_message("Deploying to Flipper via USB...", self.build_output.info_format)
            
            device_port = None
            if device != "Auto-detect":
                # Extract port from device string (e.g., "Flipper Zero (COM3)")
                import re
                port_match = re.search(r'\(([^)]+)\)', device)
                if port_match:
                    device_port = port_match.group(1)
                    
            success, message = self.ufbt_deployer.install_app(fap_path, device_port)
            
            if success:
                self.build_output.append_message(message, self.build_output.success_format)
            else:
                self.build_output.append_message(message, self.build_output.error_format)
                
        elif deploy_method == "file":
            # Deploy via file copy
            self.build_output.append_message("Copying to mounted Flipper...", self.build_output.info_format)
            
            success, message = self.ufbt_deployer.copy_to_flipper(fap_path)
            
            if success:
                self.build_output.append_message(message, self.build_output.success_format)
            else:
                self.build_output.append_message(message, self.build_output.error_format)
                
    def build_app(self):
        """Build the Flipper Zero application."""
        self.export_with_options(export_type="source")
        
    def clean_and_build_app(self):
        """Clean and build the Flipper Zero application."""
        # Create export options with clean build
        export_options = {
            "export_type": "source",
            "build": True,
            "clean_build": True,
            "create_fap": True
        }
        
        # Show export dialog
        dialog = ExportDialog(self)
        dialog.export_source_radio.setChecked(True)
        dialog.build_checkbox.setChecked(True)
        dialog.clean_build_checkbox.setChecked(True)
        dialog.create_fap_checkbox.setChecked(True)
        
        # Connect export signal
        dialog.exportRequested.connect(self.handle_export)
        
        # Show dialog
        dialog.exec()
        
    def deploy_app(self):
        """Deploy the application to a Flipper Zero device."""
        # Create export options with deploy
        export_options = {
            "export_type": "binary",
            "build": True,
            "create_fap": True,
            "deploy": True
        }
        
        # Show export dialog
        dialog = ExportDialog(self)
        dialog.export_binary_radio.setChecked(True)
        dialog.build_checkbox.setChecked(True)
        dialog.create_fap_checkbox.setChecked(True)
        dialog.deploy_checkbox.setChecked(True)
        dialog.deploy_usb_radio.setChecked(True)
        
        # Refresh devices
        dialog.refresh_devices()
        
        # Connect export signal
        dialog.exportRequested.connect(self.handle_export)
        
        # Show dialog
        dialog.exec()
        
    def update_sdk(self):
        """Update the uFBT SDK."""
        # Show build output dock
        self.build_dock.show()
        self.toggle_build_output_action.setChecked(True)
        
        # Clear build output
        self.build_output.clear_output()
        
        self.build_output.append_message("Updating SDK...", self.build_output.info_format)
        
        # Update SDK
        success, message = self.ufbt_config.update_sdk()
        
        if success:
            self.build_output.append_message(message, self.build_output.success_format)
        else:
            self.build_output.append_message(message, self.build_output.error_format)
            
    def show_sdk_status(self):
        """Show the uFBT SDK status."""
        # Show build output dock
        self.build_dock.show()
        self.toggle_build_output_action.setChecked(True)
        
        # Clear build output
        self.build_output.clear_output()
        
        # Get SDK state
        sdk_state = self.ufbt_config.sdk_state
        
        if not sdk_state:
            self.build_output.append_message("SDK status not available", self.build_output.error_format)
            return
            
        # Display SDK status
        self.build_output.append_message("SDK Status:", self.build_output.info_format)
        self.build_output.append_message(f"Version: {self.ufbt_config.get_sdk_version()}")
        self.build_output.append_message(f"Target: {self.ufbt_config.get_sdk_target()}")
        self.build_output.append_message(f"SDK Directory: {self.ufbt_config.get_sdk_dir()}")
        
        # Check if SDK is installed
        if not self.ufbt_config.is_sdk_installed():
            self.build_output.append_message("SDK is not installed", self.build_output.error_format)
            self.build_output.append_message("Run 'Update SDK' to install it", self.build_output.info_format)
            
    def undo(self):
        """Undo the last action."""
        # TODO: Implement undo functionality
        self.status_bar.showMessage("Undo functionality not yet implemented")
        
    def redo(self):
        """Redo the last undone action."""
        # TODO: Implement redo functionality
        self.status_bar.showMessage("Redo functionality not yet implemented")
        
    def delete_selected(self):
        """Delete selected blocks."""
        # Get selected items from canvas
        selected_items = self.canvas.scene.selectedItems()
        
        # Remove selected blocks
        for item in selected_items:
            if hasattr(item, 'block_id'):
                self.canvas.remove_block(item)
                
        # Mark project as modified
        self.project.set_modified(True)
        
    def zoom_in(self):
        """Zoom in on the canvas."""
        self.canvas.scale(1.2, 1.2)
        
    def zoom_out(self):
        """Zoom out on the canvas."""
        self.canvas.scale(1/1.2, 1/1.2)
        
    def reset_zoom(self):
        """Reset canvas zoom to 100%."""
        # Reset transform
        self.canvas.resetTransform()
        
    def toggle_manifest_editor(self):
        """Toggle visibility of the manifest editor."""
        if self.manifest_dock.isVisible():
            self.manifest_dock.hide()
        else:
            self.manifest_dock.show()
            
        # Update action state
        self.toggle_manifest_action.setChecked(self.manifest_dock.isVisible())
        
    def toggle_build_output(self):
        """Toggle visibility of the build output."""
        if self.build_dock.isVisible():
            self.build_dock.hide()
        else:
            self.build_dock.show()
            
        # Update action state
        self.toggle_build_output_action.setChecked(self.build_dock.isVisible())
        
    def show_about(self):
        """Show the about dialog."""
        QMessageBox.about(
            self,
            "About FlipperScriptStudio",
            "FlipperScriptStudio\n\n"
            "A visual scripting environment for Flipper Zero app development.\n\n"
            "Version 1.0"
        )
        
    def on_block_selected(self, block):
        """
        Handle block selection.
        
        Args:
            block: Selected block
        """
        # Update property editor
        self.property_editor.set_block(block)
        
    def on_block_moved(self, block):
        """
        Handle block movement.
        
        Args:
            block: Moved block
        """
        # Mark project as modified
        self.project.set_modified(True)
        
    def on_connection_created(self, output_connector, input_connector):
        """
        Handle connection creation.
        
        Args:
            output_connector: Output connector
            input_connector: Input connector
        """
        # Mark project as modified
        self.project.set_modified(True)
        
    def on_connection_deleted(self, output_connector, input_connector):
        """
        Handle connection deletion.
        
        Args:
            output_connector: Output connector
            input_connector: Input connector
        """
        # Mark project as modified
        self.project.set_modified(True)
        
    def on_property_changed(self, name, value):
        """
        Handle property changes.
        
        Args:
            name: Property name
            value: New property value
        """
        # Mark project as modified
        self.project.set_modified(True)
        
    def on_manifest_changed(self, manifest_data):
        """
        Handle manifest changes.
        
        Args:
            manifest_data: New manifest data
        """
        # Update project manifest
        self.project.set_manifest(manifest_data)
        
    def on_build_finished(self, success, message):
        """
        Handle build completion.
        
        Args:
            success: Whether the build was successful
            message: Completion message
        """
        if success:
            self.status_bar.showMessage("Build completed successfully")
        else:
            self.status_bar.showMessage(f"Build failed: {message}")
            
    def on_project_changed(self):
        """Handle project changes."""
        # Update window title
        self.update_window_title()
        
    def update_window_title(self):
        """Update the window title based on the current project."""
        title = "FlipperScriptStudio"
        
        if self.project.get_file_path():
            filename = os.path.basename(self.project.get_file_path())
            title = f"{filename} - {title}"
            
        if self.project.is_modified():
            title = f"*{title}"
            
        self.setWindowTitle(title)
        
    def confirm_discard_changes(self):
        """
        Confirm discarding changes to the current project.
        
        Returns:
            bool: True if changes can be discarded, False otherwise
        """
        if not self.project.is_modified():
            return True
            
        reply = QMessageBox.question(
            self,
            "Unsaved Changes",
            "The current project has unsaved changes. Do you want to save them?",
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save
        )
        
        if reply == QMessageBox.StandardButton.Save:
            return self.save_project()
        elif reply == QMessageBox.StandardButton.Discard:
            return True
        else:
            return False
            
    def closeEvent(self, event):
        """Handle window close event."""
        # Check if project needs saving
        if self.project.is_modified() and not self.confirm_discard_changes():
            event.ignore()
            return
            
        # Save settings
        self.save_settings()
        
        # Accept the event
        event.accept()