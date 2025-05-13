"""
Base Block Module

This module defines the base class for all visual blocks in the FlipperScriptStudio application.
"""

from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal, QObject
from PyQt6.QtGui import QColor, QPen, QBrush, QPainter, QPainterPath
from PyQt6.QtWidgets import QGraphicsItem, QGraphicsObject, QGraphicsTextItem, QGraphicsRectItem


class BlockConnector(QGraphicsObject):
    """
    Represents a connection point on a block.
    """
    
    connectionChanged = pyqtSignal(object, object)  # Emitted when connection status changes
    
    def __init__(self, parent=None, connector_id="", connector_type="", is_input=True):
        """
        Initialize a new block connector.
        
        Args:
            parent: Parent block
            connector_id: Unique identifier for the connector
            connector_type: Type of data/flow the connector handles
            is_input: True if this is an input connector, False for output
        """
        super().__init__(parent)
        self.connector_id = connector_id
        self.connector_type = connector_type
        self.is_input = is_input
        self.connected_to = None
        self.setAcceptHoverEvents(True)
        self.hover = False
        
        # Set size and appearance
        self.radius = 6
        self.setZValue(1)  # Ensure connectors are drawn above blocks
        
    def boundingRect(self):
        """Define the bounding rectangle for the connector."""
        return QRectF(-self.radius, -self.radius, 
                     self.radius * 2, self.radius * 2)
    
    def paint(self, painter, option, widget):
        """Paint the connector."""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Set color based on connector type and state
        if self.connector_type == "flow":
            base_color = QColor(50, 150, 250)  # Blue for flow
        else:
            base_color = QColor(250, 180, 50)  # Orange for data
            
        if self.connected_to:
            # Connected state
            painter.setBrush(QBrush(base_color.darker(110)))
            painter.setPen(QPen(base_color.darker(130), 1.5))
        elif self.hover:
            # Hover state
            painter.setBrush(QBrush(base_color.lighter(110)))
            painter.setPen(QPen(base_color.lighter(130), 1.5))
        else:
            # Normal state
            painter.setBrush(QBrush(base_color))
            painter.setPen(QPen(base_color.darker(120), 1.5))
            
        # Draw the connector circle
        painter.drawEllipse(self.boundingRect())
        
    def hoverEnterEvent(self, event):
        """Handle hover enter events."""
        self.hover = True
        self.update()
        super().hoverEnterEvent(event)
        
    def hoverLeaveEvent(self, event):
        """Handle hover leave events."""
        self.hover = False
        self.update()
        super().hoverLeaveEvent(event)
        
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Start connection or disconnect existing
            if self.connected_to:
                old_connection = self.connected_to
                self.connected_to = None
                old_connection.connected_to = None
                self.connectionChanged.emit(self, None)
            else:
                # Signal that this connector is ready to connect
                self.scene().startConnection(self)
            self.update()
        super().mousePressEvent(event)
        
    def connect_to(self, other_connector):
        """
        Connect this connector to another connector.
        
        Args:
            other_connector: The connector to connect to
        
        Returns:
            bool: True if connection was successful, False otherwise
        """
        # Check if connection is valid (input to output or output to input)
        if self.is_input == other_connector.is_input:
            return False
            
        # Check if connector types are compatible
        if self.connector_type != other_connector.connector_type:
            return False
            
        # Disconnect any existing connections
        if self.connected_to:
            old_connection = self.connected_to
            self.connected_to = None
            old_connection.connected_to = None
            self.connectionChanged.emit(self, None)
            
        if other_connector.connected_to:
            old_connection = other_connector.connected_to
            other_connector.connected_to = None
            old_connection.connected_to = None
            other_connector.connectionChanged.emit(other_connector, None)
            
        # Make the new connection
        self.connected_to = other_connector
        other_connector.connected_to = self
        self.connectionChanged.emit(self, other_connector)
        other_connector.connectionChanged.emit(other_connector, self)
        
        self.update()
        other_connector.update()
        return True


class BaseBlock(QGraphicsObject):
    """
    Base class for all visual blocks in the application.
    """
    
    # Signals
    blockMoved = pyqtSignal(object)  # Emitted when block is moved
    blockSelected = pyqtSignal(object, bool)  # Emitted when block is selected/deselected
    propertyChanged = pyqtSignal(object, str, object)  # Emitted when a property changes
    
    def __init__(self, block_id="", block_type="", title="", color=None):
        """
        Initialize a new block.
        
        Args:
            block_id: Unique identifier for the block
            block_type: Type of the block
            title: Display title for the block
            color: Background color for the block
        """
        super().__init__()
        self.block_id = block_id
        self.block_type = block_type
        self.title = title
        self.color = color or QColor(100, 100, 100)
        self.selected = False
        self.width = 180
        self.height = 80
        self.header_height = 24
        self.corner_radius = 8
        
        # Enable item flags
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)
        
        # Create title text
        self.title_item = QGraphicsTextItem(self.title, self)
        self.title_item.setDefaultTextColor(Qt.GlobalColor.white)
        self.title_item.setPos(10, 4)
        self.title_item.setTextWidth(self.width - 20)
        
        # Initialize connectors
        self.input_connectors = {}
        self.output_connectors = {}
        
        # Properties dictionary
        self.properties = {}
        
    def boundingRect(self):
        """Define the bounding rectangle for the block."""
        return QRectF(0, 0, self.width, self.height)
    
    def paint(self, painter, option, widget):
        """Paint the block."""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw block body
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width, self.height, 
                           self.corner_radius, self.corner_radius)
        
        # Fill with block color
        painter.fillPath(path, QBrush(self.color))
        
        # Draw header section
        header_path = QPainterPath()
        header_path.addRoundedRect(0, 0, self.width, self.header_height, 
                                  self.corner_radius, self.corner_radius)
        header_path.addRect(0, self.header_height - self.corner_radius, 
                           self.width, self.corner_radius)
        painter.fillPath(header_path, QBrush(self.color.darker(120)))
        
        # Draw border
        if self.isSelected():
            painter.setPen(QPen(Qt.GlobalColor.white, 2))
        else:
            painter.setPen(QPen(self.color.darker(150), 1.5))
        painter.drawPath(path)
        
    def add_input_connector(self, connector_id, connector_type, description=""):
        """
        Add an input connector to the block.
        
        Args:
            connector_id: Unique identifier for the connector
            connector_type: Type of data/flow the connector handles
            description: Description of the connector
        """
        connector = BlockConnector(self, connector_id, connector_type, True)
        self.input_connectors[connector_id] = connector
        
        # Position the connector on the left side of the block
        y_pos = self.header_height + 20 + (len(self.input_connectors) - 1) * 20
        connector.setPos(0, y_pos)
        
        # Add a label for the connector
        label = QGraphicsTextItem(description or connector_id, self)
        label.setPos(12, y_pos - 10)
        label.setDefaultTextColor(Qt.GlobalColor.white)
        
        # Update block height if needed
        min_height = y_pos + 30
        if min_height > self.height:
            self.height = min_height
            self.update()
            
        return connector
        
    def add_output_connector(self, connector_id, connector_type, description=""):
        """
        Add an output connector to the block.
        
        Args:
            connector_id: Unique identifier for the connector
            connector_type: Type of data/flow the connector handles
            description: Description of the connector
        """
        connector = BlockConnector(self, connector_id, connector_type, False)
        self.output_connectors[connector_id] = connector
        
        # Position the connector on the right side of the block
        y_pos = self.header_height + 20 + (len(self.output_connectors) - 1) * 20
        connector.setPos(self.width, y_pos)
        
        # Add a label for the connector
        label = QGraphicsTextItem(description or connector_id, self)
        label.setPos(self.width - 12 - label.boundingRect().width(), y_pos - 10)
        label.setDefaultTextColor(Qt.GlobalColor.white)
        
        # Update block height if needed
        min_height = y_pos + 30
        if min_height > self.height:
            self.height = min_height
            self.update()
            
        return connector
        
    def set_property(self, name, value):
        """
        Set a property value.
        
        Args:
            name: Property name
            value: Property value
        """
        if name in self.properties and self.properties[name] != value:
            old_value = self.properties[name]
            self.properties[name] = value
            self.propertyChanged.emit(self, name, value)
            self.update()
            return True
        elif name not in self.properties:
            self.properties[name] = value
            self.propertyChanged.emit(self, name, value)
            self.update()
            return True
        return False
        
    def get_property(self, name, default=None):
        """
        Get a property value.
        
        Args:
            name: Property name
            default: Default value if property doesn't exist
            
        Returns:
            The property value or default
        """
        return self.properties.get(name, default)
        
    def itemChange(self, change, value):
        """Handle item changes."""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene():
            # Snap to grid
            grid_size = 10
            x = round(value.x() / grid_size) * grid_size
            y = round(value.y() / grid_size) * grid_size
            return QPointF(x, y)
        elif change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            # Emit signal when position changes
            self.blockMoved.emit(self)
        elif change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            # Emit signal when selection changes
            self.blockSelected.emit(self, value)
            
        return super().itemChange(change, value)
        
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Bring block to front when clicked
            self.setZValue(1)
            for item in self.scene().items():
                if item != self and isinstance(item, BaseBlock):
                    item.setZValue(0)
        super().mousePressEvent(event)
        
    def mouseReleaseEvent(self, event):
        """Handle mouse release events."""
        super().mouseReleaseEvent(event)
        
    def to_dict(self):
        """
        Convert block to dictionary representation.
        
        Returns:
            dict: Dictionary representation of the block
        """
        pos = self.pos()
        block_dict = {
            "id": self.block_id,
            "type": self.block_type,
            "x": pos.x(),
            "y": pos.y(),
            "properties": self.properties.copy()
        }
        return block_dict
        
    @classmethod
    def from_dict(cls, data):
        """
        Create a block from dictionary representation.
        
        Args:
            data: Dictionary representation of the block
            
        Returns:
            BaseBlock: New block instance
        """
        block = cls(
            block_id=data.get("id", ""),
            block_type=data.get("type", ""),
            title=data.get("title", "")
        )
        
        # Set position
        block.setPos(data.get("x", 0), data.get("y", 0))
        
        # Set properties
        for name, value in data.get("properties", {}).items():
            block.set_property(name, value)
            
        return block