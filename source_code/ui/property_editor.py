"""
Property Editor Module

This module provides the property editor for block properties.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLabel, QLineEdit,
    QComboBox, QCheckBox, QSpinBox, QDoubleSpinBox,
    QColorDialog, QPushButton, QScrollArea, QSizePolicy,
    QGroupBox
)


class PropertyEditor(QWidget):
    """
    Editor for block properties.
    """
    
    propertyChanged = pyqtSignal(str, object)  # Emitted when a property changes
    
    def __init__(self, parent=None):
        """
        Initialize a new property editor.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Set up layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Create title label
        self.title_label = QLabel("Properties")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.layout.addWidget(self.title_label)
        
        # Create scroll area for form
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        
        # Create form widget
        self.form_widget = QWidget()
        self.form_layout = QFormLayout(self.form_widget)
        self.form_layout.setContentsMargins(0, 0, 0, 0)
        
        # Set scroll area widget
        self.scroll_area.setWidget(self.form_widget)
        self.layout.addWidget(self.scroll_area)
        
        # Dictionary to store property widgets
        self.property_widgets = {}
        
        # Currently selected block
        self.current_block = None
        
        # No selection label
        self.no_selection_label = QLabel("No block selected")
        self.no_selection_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.form_layout.addRow(self.no_selection_label)
        
    def set_block(self, block):
        """
        Set the block to edit properties for.
        
        Args:
            block: Block to edit properties for
        """
        # Clear existing property widgets
        self.clear_properties()
        
        # Store reference to block
        self.current_block = block
        
        if not block:
            # Show no selection label
            self.no_selection_label.setVisible(True)
            return
            
        # Hide no selection label
        self.no_selection_label.setVisible(False)
        
        # Set title
        self.title_label.setText(f"Properties: {block.title}")
        
        # Get block type information
        block_type = block.block_type
        
        # Add ID property
        self.add_text_property("ID", block.block_id, readonly=True)
        
        # Add type property
        self.add_text_property("Type", block_type, readonly=True)
        
        # Add custom properties based on block's properties
        for name, value in block.properties.items():
            self.add_property(name, value)
            
    def clear_properties(self):
        """Clear all property widgets."""
        # Remove all widgets from the form layout
        while self.form_layout.rowCount() > 0:
            self.form_layout.removeRow(0)
            
        # Clear property widgets dictionary
        self.property_widgets = {}
        
        # Reset title
        self.title_label.setText("Properties")
        
        # Add no selection label
        self.form_layout.addRow(self.no_selection_label)
        
    def add_property(self, name, value):
        """
        Add a property widget based on value type.
        
        Args:
            name: Property name
            value: Property value
        """
        if isinstance(value, bool):
            self.add_bool_property(name, value)
        elif isinstance(value, int):
            self.add_int_property(name, value)
        elif isinstance(value, float):
            self.add_float_property(name, value)
        elif isinstance(value, str):
            # Check if this is an enum property
            if self.current_block:
                # Get block type information
                block_type = self.current_block.block_type
                
                # Check if this property has enum options
                # For now, we'll just check for some common enum properties
                if name.lower() in ["button", "alignment", "font", "direction"]:
                    options = self.get_enum_options(name)
                    if options:
                        self.add_enum_property(name, value, options)
                        return
                        
            # Default to text property
            self.add_text_property(name, value)
        elif isinstance(value, list):
            # For now, we'll just display lists as text
            self.add_text_property(name, str(value))
        elif isinstance(value, dict):
            # For now, we'll just display dicts as text
            self.add_text_property(name, str(value))
        else:
            # Default to text property
            self.add_text_property(name, str(value))
            
    def add_text_property(self, name, value, readonly=False):
        """
        Add a text property widget.
        
        Args:
            name: Property name
            value: Property value
            readonly: Whether the property is read-only
        """
        # Create label
        label = QLabel(name)
        
        # Create line edit
        line_edit = QLineEdit()
        line_edit.setText(str(value))
        line_edit.setReadOnly(readonly)
        
        if readonly:
            line_edit.setStyleSheet("background-color: #f0f0f0;")
            
        # Connect signal
        if not readonly:
            line_edit.textChanged.connect(lambda text: self.on_property_changed(name, text))
            
        # Add to form
        self.form_layout.addRow(label, line_edit)
        
        # Store widget
        self.property_widgets[name] = line_edit
        
    def add_bool_property(self, name, value):
        """
        Add a boolean property widget.
        
        Args:
            name: Property name
            value: Property value
        """
        # Create checkbox
        checkbox = QCheckBox(name)
        checkbox.setChecked(value)
        
        # Connect signal
        checkbox.stateChanged.connect(lambda state: self.on_property_changed(name, state == Qt.CheckState.Checked))
        
        # Add to form
        self.form_layout.addRow("", checkbox)
        
        # Store widget
        self.property_widgets[name] = checkbox
        
    def add_int_property(self, name, value):
        """
        Add an integer property widget.
        
        Args:
            name: Property name
            value: Property value
        """
        # Create label
        label = QLabel(name)
        
        # Create spin box
        spin_box = QSpinBox()
        spin_box.setMinimum(-1000000)
        spin_box.setMaximum(1000000)
        spin_box.setValue(value)
        
        # Connect signal
        spin_box.valueChanged.connect(lambda val: self.on_property_changed(name, val))
        
        # Add to form
        self.form_layout.addRow(label, spin_box)
        
        # Store widget
        self.property_widgets[name] = spin_box
        
    def add_float_property(self, name, value):
        """
        Add a float property widget.
        
        Args:
            name: Property name
            value: Property value
        """
        # Create label
        label = QLabel(name)
        
        # Create spin box
        spin_box = QDoubleSpinBox()
        spin_box.setMinimum(-1000000.0)
        spin_box.setMaximum(1000000.0)
        spin_box.setDecimals(2)
        spin_box.setValue(value)
        
        # Connect signal
        spin_box.valueChanged.connect(lambda val: self.on_property_changed(name, val))
        
        # Add to form
        self.form_layout.addRow(label, spin_box)
        
        # Store widget
        self.property_widgets[name] = spin_box
        
    def add_enum_property(self, name, value, options):
        """
        Add an enum property widget.
        
        Args:
            name: Property name
            value: Property value
            options: List of possible values
        """
        # Create label
        label = QLabel(name)
        
        # Create combo box
        combo_box = QComboBox()
        combo_box.addItems(options)
        
        # Set current value
        index = combo_box.findText(value)
        if index >= 0:
            combo_box.setCurrentIndex(index)
            
        # Connect signal
        combo_box.currentTextChanged.connect(lambda text: self.on_property_changed(name, text))
        
        # Add to form
        self.form_layout.addRow(label, combo_box)
        
        # Store widget
        self.property_widgets[name] = combo_box
        
    def add_color_property(self, name, value):
        """
        Add a color property widget.
        
        Args:
            name: Property name
            value: Property value (QColor or color string)
        """
        # Create label
        label = QLabel(name)
        
        # Create color button
        color_button = QPushButton()
        color_button.setFixedSize(30, 30)
        
        # Set color
        if isinstance(value, QColor):
            color = value
        else:
            color = QColor(value)
            
        color_button.setStyleSheet(f"background-color: {color.name()};")
        
        # Connect signal
        color_button.clicked.connect(lambda: self.show_color_dialog(name, color))
        
        # Add to form
        self.form_layout.addRow(label, color_button)
        
        # Store widget
        self.property_widgets[name] = color_button
        
    def show_color_dialog(self, name, current_color):
        """
        Show color dialog for selecting a color.
        
        Args:
            name: Property name
            current_color: Current color
        """
        color = QColorDialog.getColor(current_color, self, f"Select {name} Color")
        if color.isValid():
            # Update button color
            button = self.property_widgets[name]
            button.setStyleSheet(f"background-color: {color.name()};")
            
            # Emit property changed signal
            self.on_property_changed(name, color)
            
    def on_property_changed(self, name, value):
        """
        Handle property value changes.
        
        Args:
            name: Property name
            value: New property value
        """
        if self.current_block:
            # Update block property
            self.current_block.set_property(name, value)
            
        # Emit signal
        self.propertyChanged.emit(name, value)
        
    def update_property(self, name, value):
        """
        Update a property widget with a new value.
        
        Args:
            name: Property name
            value: New property value
        """
        if name not in self.property_widgets:
            return
            
        widget = self.property_widgets[name]
        
        # Update widget based on type
        if isinstance(widget, QLineEdit):
            widget.setText(str(value))
        elif isinstance(widget, QCheckBox):
            widget.setChecked(bool(value))
        elif isinstance(widget, QSpinBox):
            widget.setValue(int(value))
        elif isinstance(widget, QDoubleSpinBox):
            widget.setValue(float(value))
        elif isinstance(widget, QComboBox):
            index = widget.findText(str(value))
            if index >= 0:
                widget.setCurrentIndex(index)
        elif isinstance(widget, QPushButton):
            # Assume this is a color button
            if isinstance(value, QColor):
                color = value
            else:
                color = QColor(value)
                
            widget.setStyleSheet(f"background-color: {color.name()};")
            
    def get_enum_options(self, name):
        """
        Get enum options for a property.
        
        Args:
            name: Property name
            
        Returns:
            list: List of enum options or None
        """
        # Common enum options
        name_lower = name.lower()
        
        if name_lower == "button":
            return ["Up", "Down", "Left", "Right", "Ok", "Back"]
        elif name_lower == "alignment":
            return ["Left", "Center", "Right", "Top", "Bottom"]
        elif name_lower == "font":
            return ["Primary", "Secondary", "Small", "Medium", "Big"]
        elif name_lower == "direction":
            return ["Horizontal", "Vertical"]
            
        return None