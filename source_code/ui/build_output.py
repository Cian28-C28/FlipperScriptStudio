"""
Build Output Module

This module provides a UI component for displaying build output and logs.
"""

import os
import re
import time
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QTextCursor, QColor, QTextCharFormat, QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QLabel, QProgressBar, QSplitter
)


class BuildOutputWidget(QWidget):
    """
    Widget for displaying build output and logs.
    """
    
    buildFinished = pyqtSignal(bool, str)  # Emitted when build finishes (success, message)
    
    def __init__(self, parent=None):
        """
        Initialize the build output widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Set up layout
        self.layout = QVBoxLayout(self)
        
        # Create status layout
        self.status_layout = QHBoxLayout()
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.status_layout.addWidget(self.progress_bar)
        
        self.layout.addLayout(self.status_layout)
        
        # Create output text edit
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.output_text.setFont(QFont("Courier New", 10))
        self.layout.addWidget(self.output_text)
        
        # Create button layout
        self.button_layout = QHBoxLayout()
        
        # Clear button
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_output)
        self.button_layout.addWidget(self.clear_button)
        
        # Copy button
        self.copy_button = QPushButton("Copy")
        self.copy_button.clicked.connect(self.copy_output)
        self.button_layout.addWidget(self.copy_button)
        
        # Save button
        self.save_button = QPushButton("Save Log")
        self.save_button.clicked.connect(self.save_output)
        self.button_layout.addWidget(self.save_button)
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_build)
        self.cancel_button.setEnabled(False)
        self.button_layout.addWidget(self.cancel_button)
        
        self.layout.addLayout(self.button_layout)
        
        # Initialize state
        self.is_building = False
        self.build_process = None
        self.build_timer = QTimer()
        self.build_timer.timeout.connect(self.update_progress)
        self.build_start_time = 0
        
        # Text formats for different message types
        self.error_format = QTextCharFormat()
        self.error_format.setForeground(QColor(255, 0, 0))
        
        self.warning_format = QTextCharFormat()
        self.warning_format.setForeground(QColor(255, 165, 0))
        
        self.success_format = QTextCharFormat()
        self.success_format.setForeground(QColor(0, 128, 0))
        
        self.info_format = QTextCharFormat()
        self.info_format.setForeground(QColor(0, 0, 255))
        
    def clear_output(self):
        """Clear the output text."""
        self.output_text.clear()
        
    def copy_output(self):
        """Copy the output text to clipboard."""
        self.output_text.selectAll()
        self.output_text.copy()
        cursor = self.output_text.textCursor()
        cursor.clearSelection()
        self.output_text.setTextCursor(cursor)
        
    def save_output(self):
        """Save the output text to a file."""
        from PyQt6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Log",
            "",
            "Log Files (*.log);;Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.output_text.toPlainText())
                
    def cancel_build(self):
        """Cancel the current build process."""
        if self.is_building and self.build_process:
            try:
                self.build_process.terminate()
                self.append_message("Build cancelled by user", self.info_format)
                self.set_building(False)
                self.buildFinished.emit(False, "Build cancelled by user")
            except Exception as e:
                self.append_message(f"Error cancelling build: {str(e)}", self.error_format)
                
    def set_building(self, building: bool):
        """
        Set the building state.
        
        Args:
            building: Whether a build is in progress
        """
        self.is_building = building
        self.cancel_button.setEnabled(building)
        
        if building:
            self.build_start_time = time.time()
            self.progress_bar.setValue(0)
            self.build_timer.start(100)  # Update every 100ms
            self.status_label.setText("Building...")
        else:
            self.build_timer.stop()
            self.progress_bar.setValue(100)
            
    def update_progress(self):
        """Update the progress bar during build."""
        if not self.is_building:
            return
            
        # Calculate elapsed time
        elapsed = time.time() - self.build_start_time
        
        # Estimate progress (this is just a visual indicator)
        # Assume build takes about 30 seconds max
        progress = min(int(elapsed / 30.0 * 100), 99)
        self.progress_bar.setValue(progress)
        
    def append_message(self, message: str, format: QTextCharFormat = None):
        """
        Append a message to the output text.
        
        Args:
            message: Message to append
            format: Text format to use
        """
        cursor = self.output_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        if format:
            cursor.insertText(message + "\n", format)
        else:
            cursor.insertText(message + "\n")
            
        self.output_text.setTextCursor(cursor)
        self.output_text.ensureCursorVisible()
        
    def append_build_output(self, output: str):
        """
        Append build output to the text edit, with syntax highlighting.
        
        Args:
            output: Build output text
        """
        lines = output.split('\n')
        
        for line in lines:
            if not line.strip():
                continue
                
            # Apply different formats based on line content
            if re.search(r'error:', line, re.IGNORECASE):
                self.append_message(line, self.error_format)
            elif re.search(r'warning:', line, re.IGNORECASE):
                self.append_message(line, self.warning_format)
            elif re.search(r'success|completed', line, re.IGNORECASE):
                self.append_message(line, self.success_format)
            else:
                self.append_message(line)
                
    def set_build_process(self, process):
        """
        Set the current build process.
        
        Args:
            process: Build process object
        """
        self.build_process = process
        self.set_building(True)
        
    def build_completed(self, success: bool, message: str = ""):
        """
        Handle build completion.
        
        Args:
            success: Whether the build was successful
            message: Completion message
        """
        self.set_building(False)
        
        if success:
            self.status_label.setText("Build Successful")
            self.append_message("Build completed successfully", self.success_format)
        else:
            self.status_label.setText("Build Failed")
            self.append_message(f"Build failed: {message}", self.error_format)
            
        self.buildFinished.emit(success, message)