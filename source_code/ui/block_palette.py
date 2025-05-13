"""
Block Palette Module

This module provides the palette of available blocks for the drag-and-drop interface.
"""

from PyQt6.QtCore import Qt, QSize, QMimeData, pyqtSignal
from PyQt6.QtGui import QColor, QPen, QBrush, QPainter, QDrag, QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QLineEdit, QTreeWidget, QTreeWidgetItem, QSizePolicy
)


class BlockPaletteItem(QFrame):
    """
    Represents a block in the palette that can be dragged onto the canvas.
    """
    
    def __init__(self, block_type, name, description="", color=None, parent=None):
        """
        Initialize a new block palette item.
        
        Args:
            block_type: Type of block
            name: Display name
            description: Block description
            color: Block color
            parent: Parent widget
        """
        super().__init__(parent)
        self.block_type = block_type
        self.name = name
        self.description = description
        self.color = color or QColor(100, 100, 100)
        
        # Set up appearance
        self.setFrameShape(QFrame.Shape.Box)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setLineWidth(1)
        self.setMinimumHeight(30)
        self.setMaximumHeight(30)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # Enable mouse tracking for hover effects
        self.setMouseTracking(True)
        
        # Track hover state
        self.hover = False
        
    def paintEvent(self, event):
        """Paint the block palette item."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw background
        if self.hover:
            painter.fillRect(self.rect(), QBrush(self.color.lighter(120)))
        else:
            painter.fillRect(self.rect(), QBrush(self.color))
            
        # Draw border
        painter.setPen(QPen(self.color.darker(150), 1))
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))
        
        # Draw text
        painter.setPen(Qt.GlobalColor.white)
        font = QFont()
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(self.rect().adjusted(10, 0, -10, 0), 
                        Qt.AlignmentFlag.AlignVCenter, self.name)
        
    def enterEvent(self, event):
        """Handle mouse enter events."""
        self.hover = True
        self.update()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """Handle mouse leave events."""
        self.hover = False
        self.update()
        super().leaveEvent(event)
        
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.position()
        super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event):
        """Handle mouse move events."""
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
            
        # Check if the mouse has moved far enough to start a drag
        if (event.position() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
            return
            
        # Start drag operation
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(self.block_type)
        drag.setMimeData(mime_data)
        
        # Create a pixmap of the item for the drag cursor
        pixmap = self.grab()
        drag.setPixmap(pixmap)
        drag.setHotSpot(event.position().toPoint())
        
        # Execute drag
        drag.exec(Qt.DropAction.CopyAction)
        
    def sizeHint(self):
        """Return the preferred size of the item."""
        return QSize(200, 30)


class BlockPalette(QWidget):
    """
    Palette of available blocks that can be dragged onto the canvas.
    """
    
    blockDragged = pyqtSignal(str)  # Emitted when a block is dragged from the palette
    
    def __init__(self, parent=None):
        """
        Initialize a new block palette.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Set up layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Create search box
        self.search_layout = QHBoxLayout()
        self.search_label = QLabel("Search:")
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search blocks...")
        self.search_box.textChanged.connect(self.filter_blocks)
        self.search_layout.addWidget(self.search_label)
        self.search_layout.addWidget(self.search_box)
        self.layout.addLayout(self.search_layout)
        
        # Create tree widget for categories
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(10)
        self.tree.setAnimated(True)
        self.tree.setSelectionMode(QTreeWidget.SelectionMode.NoSelection)
        self.layout.addWidget(self.tree)
        
        # Dictionary to store category items
        self.categories = {}
        
        # Dictionary to store block items
        self.block_items = {}
        
    def add_category(self, category_id, name, color=None, description=""):
        """
        Add a category to the palette.
        
        Args:
            category_id: Unique identifier for the category
            name: Display name
            color: Category color
            description: Category description
            
        Returns:
            The created category item
        """
        # Create category item
        item = QTreeWidgetItem(self.tree)
        item.setText(0, name)
        item.setToolTip(0, description)
        item.setExpanded(True)
        
        # Store category
        self.categories[category_id] = {
            'item': item,
            'name': name,
            'color': color or QColor(100, 100, 100),
            'description': description
        }
        
        return item
        
    def add_block(self, category_id, block_type, name, description=""):
        """
        Add a block to the palette.
        
        Args:
            category_id: ID of the category to add the block to
            block_type: Type of block
            name: Display name
            description: Block description
            
        Returns:
            The created block item
        """
        if category_id not in self.categories:
            return None
            
        category = self.categories[category_id]
        category_item = category['item']
        
        # Create block item
        item = QTreeWidgetItem(category_item)
        item.setText(0, name)
        item.setToolTip(0, description)
        
        # Create block widget
        block_widget = BlockPaletteItem(
            block_type=block_type,
            name=name,
            description=description,
            color=category['color']
        )
        
        # Set item widget
        self.tree.setItemWidget(item, 0, block_widget)
        
        # Store block item
        self.block_items[block_type] = {
            'item': item,
            'widget': block_widget,
            'category': category_id,
            'name': name,
            'description': description
        }
        
        return item
        
    def load_blocks_from_factory(self, block_factory):
        """
        Load blocks from a block factory.
        
        Args:
            block_factory: Block factory to load from
            
        Returns:
            Number of blocks loaded
        """
        # Clear existing items
        self.tree.clear()
        self.categories = {}
        self.block_items = {}
        
        # Load categories
        categories = block_factory.get_categories()
        for category_id, category_info in categories.items():
            self.add_category(
                category_id=category_id,
                name=category_info.get('name', category_id),
                color=QColor(category_info.get('color', '#808080')),
                description=category_info.get('description', '')
            )
            
        # Load blocks
        block_count = 0
        for category_id in categories:
            block_types = block_factory.get_blocks_in_category(category_id)
            for block_type in block_types:
                block_info = block_factory.get_block_info(block_type)
                if not block_info:
                    continue
                    
                self.add_block(
                    category_id=category_id,
                    block_type=block_type,
                    name=block_info.get('name', block_type),
                    description=block_info.get('description', '')
                )
                block_count += 1
                
        return block_count
        
    def filter_blocks(self, text):
        """
        Filter blocks by search text.
        
        Args:
            text: Search text
        """
        # Show all items if search is empty
        if not text:
            for category_id, category in self.categories.items():
                category['item'].setHidden(False)
                
            for block_type, block in self.block_items.items():
                block['item'].setHidden(False)
                
            return
            
        # Convert to lowercase for case-insensitive search
        search_text = text.lower()
        
        # Hide all categories initially
        for category_id, category in self.categories.items():
            category['item'].setHidden(True)
            
        # Show matching blocks and their categories
        for block_type, block in self.block_items.items():
            if (search_text in block['name'].lower() or 
                search_text in block['description'].lower() or
                search_text in block_type.lower()):
                # Show this block
                block['item'].setHidden(False)
                
                # Show its category
                category_id = block['category']
                if category_id in self.categories:
                    self.categories[category_id]['item'].setHidden(False)
            else:
                # Hide this block
                block['item'].setHidden(True)