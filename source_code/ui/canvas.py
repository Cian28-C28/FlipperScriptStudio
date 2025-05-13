"""
Canvas Module

This module provides the canvas component for the drag-and-drop interface.
"""

from PyQt6.QtCore import Qt, QPointF, pyqtSignal, QRectF
from PyQt6.QtGui import QPen, QBrush, QColor, QPainter, QPainterPath
from PyQt6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsItem, 
    QGraphicsLineItem, QGraphicsPathItem
)

from blocks import BaseBlock, BlockConnector


class ConnectionLine(QGraphicsPathItem):
    """
    Represents a connection line between two block connectors.
    """
    
    def __init__(self, start_connector=None, end_connector=None, parent=None):
        """
        Initialize a new connection line.
        
        Args:
            start_connector: Starting connector
            end_connector: Ending connector
            parent: Parent item
        """
        super().__init__(parent)
        self.start_connector = start_connector
        self.end_connector = end_connector
        self.temp_end_point = None
        
        # Set appearance
        self.setPen(QPen(QColor(100, 100, 100), 2, Qt.PenStyle.SolidLine, 
                        Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        self.setZValue(-1)  # Draw lines below blocks
        
        self.update_path()
        
    def set_start_connector(self, connector):
        """Set the starting connector."""
        self.start_connector = connector
        self.update_path()
        
    def set_end_connector(self, connector):
        """Set the ending connector."""
        self.end_connector = connector
        self.temp_end_point = None
        self.update_path()
        
    def set_temp_end_point(self, point):
        """Set a temporary end point for the line."""
        self.temp_end_point = point
        self.update_path()
        
    def update_path(self):
        """Update the path of the connection line."""
        path = QPainterPath()
        
        # Get start point
        if self.start_connector:
            start_pos = self.start_connector.scenePos()
            start_point = QPointF(start_pos.x(), start_pos.y())
        else:
            return
            
        # Get end point
        if self.end_connector:
            end_pos = self.end_connector.scenePos()
            end_point = QPointF(end_pos.x(), end_pos.y())
        elif self.temp_end_point:
            end_point = self.temp_end_point
        else:
            return
            
        # Draw a bezier curve
        path.moveTo(start_point)
        
        # Calculate control points for the curve
        dx = end_point.x() - start_point.x()
        control_offset = min(abs(dx) * 0.5, 80)
        
        if self.start_connector and not self.start_connector.is_input:
            # Output connector (on right side)
            control1 = QPointF(start_point.x() + control_offset, start_point.y())
        else:
            # Input connector (on left side)
            control1 = QPointF(start_point.x() - control_offset, start_point.y())
            
        if self.end_connector and self.end_connector.is_input:
            # Input connector (on left side)
            control2 = QPointF(end_point.x() - control_offset, end_point.y())
        else:
            # Output connector (on right side) or temporary point
            control2 = QPointF(end_point.x() + control_offset, end_point.y())
            
        path.cubicTo(control1, control2, end_point)
        self.setPath(path)
        
    def paint(self, painter, option, widget):
        """Paint the connection line."""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Set color based on connection type
        if self.start_connector:
            if self.start_connector.connector_type == "flow":
                self.setPen(QPen(QColor(50, 150, 250), 2.5, Qt.PenStyle.SolidLine, 
                               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            else:
                self.setPen(QPen(QColor(250, 180, 50), 2.5, Qt.PenStyle.SolidLine, 
                               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        
        super().paint(painter, option, widget)


class BlockCanvas(QGraphicsView):
    """
    Canvas for placing and connecting blocks.
    """
    
    blockSelected = pyqtSignal(object)  # Emitted when a block is selected
    blockMoved = pyqtSignal(object)  # Emitted when a block is moved
    connectionCreated = pyqtSignal(object, object)  # Emitted when a connection is created
    connectionDeleted = pyqtSignal(object, object)  # Emitted when a connection is deleted
    
    def __init__(self, parent=None):
        """
        Initialize a new block canvas.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Set up the scene
        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(-2000, -2000, 4000, 4000)
        self.setScene(self.scene)
        
        # Set view properties
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        
        # Set up grid
        self.grid_size = 20
        self.grid_enabled = True
        
        # Connection handling
        self.temp_connection = None
        self.active_connector = None
        
        # Zoom level
        self.zoom_level = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 3.0
        
        # Track mouse position for panning
        self.last_mouse_pos = None
        self.is_panning = False
        
        # Dictionary of blocks on the canvas
        self.blocks = {}
        
        # Dictionary of connections
        self.connections = {}
        
    def add_block(self, block):
        """
        Add a block to the canvas.
        
        Args:
            block: Block to add
            
        Returns:
            The added block
        """
        self.scene.addItem(block)
        self.blocks[block.block_id] = block
        
        # Connect signals
        block.blockSelected.connect(self.on_block_selected)
        block.blockMoved.connect(self.on_block_moved)
        
        # Connect connector signals
        for connector_id, connector in block.input_connectors.items():
            connector.connectionChanged.connect(self.on_connection_changed)
            
        for connector_id, connector in block.output_connectors.items():
            connector.connectionChanged.connect(self.on_connection_changed)
            
        return block
        
    def remove_block(self, block):
        """
        Remove a block from the canvas.
        
        Args:
            block: Block to remove
        """
        # Remove all connections to/from this block
        for connector_id, connector in list(block.input_connectors.items()):
            if connector.connected_to:
                self.delete_connection(connector, connector.connected_to)
                
        for connector_id, connector in list(block.output_connectors.items()):
            if connector.connected_to:
                self.delete_connection(connector, connector.connected_to)
                
        # Remove the block
        self.scene.removeItem(block)
        if block.block_id in self.blocks:
            del self.blocks[block.block_id]
            
    def get_block(self, block_id):
        """
        Get a block by ID.
        
        Args:
            block_id: ID of the block
            
        Returns:
            The block or None if not found
        """
        return self.blocks.get(block_id)
        
    def clear(self):
        """Clear all blocks and connections from the canvas."""
        self.scene.clear()
        self.blocks = {}
        self.connections = {}
        self.temp_connection = None
        self.active_connector = None
        
    def startConnection(self, connector):
        """
        Start creating a connection from a connector.
        
        Args:
            connector: Connector to start from
        """
        self.active_connector = connector
        
        # Create a temporary connection line
        self.temp_connection = ConnectionLine(connector)
        self.scene.addItem(self.temp_connection)
        
    def on_block_selected(self, block, selected):
        """
        Handle block selection.
        
        Args:
            block: Selected block
            selected: Whether the block is selected
        """
        if selected:
            self.blockSelected.emit(block)
            
    def on_block_moved(self, block):
        """
        Handle block movement.
        
        Args:
            block: Moved block
        """
        self.blockMoved.emit(block)
        
        # Update connections
        for connector_id, connector in block.input_connectors.items():
            if connector.connected_to:
                connection_id = self.get_connection_id(connector, connector.connected_to)
                if connection_id in self.connections:
                    self.connections[connection_id].update_path()
                    
        for connector_id, connector in block.output_connectors.items():
            if connector.connected_to:
                connection_id = self.get_connection_id(connector, connector.connected_to)
                if connection_id in self.connections:
                    self.connections[connection_id].update_path()
                    
    def on_connection_changed(self, connector, connected_to):
        """
        Handle connection changes.
        
        Args:
            connector: Connector that changed
            connected_to: Connector it's connected to (or None)
        """
        if connected_to:
            # Create a new connection
            self.create_connection(connector, connected_to)
        else:
            # Delete the connection
            if connector.connected_to:
                self.delete_connection(connector, connector.connected_to)
                
    def create_connection(self, connector1, connector2):
        """
        Create a connection between two connectors.
        
        Args:
            connector1: First connector
            connector2: Second connector
            
        Returns:
            The created connection line
        """
        # Determine which is input and which is output
        if connector1.is_input:
            input_connector = connector1
            output_connector = connector2
        else:
            input_connector = connector2
            output_connector = connector1
            
        # Create a connection line
        connection = ConnectionLine(output_connector, input_connector)
        self.scene.addItem(connection)
        
        # Store the connection
        connection_id = self.get_connection_id(connector1, connector2)
        self.connections[connection_id] = connection
        
        # Emit signal
        self.connectionCreated.emit(output_connector, input_connector)
        
        return connection
        
    def delete_connection(self, connector1, connector2):
        """
        Delete a connection between two connectors.
        
        Args:
            connector1: First connector
            connector2: Second connector
        """
        connection_id = self.get_connection_id(connector1, connector2)
        if connection_id in self.connections:
            connection = self.connections[connection_id]
            self.scene.removeItem(connection)
            del self.connections[connection_id]
            
            # Disconnect the connectors
            if connector1.connected_to == connector2:
                connector1.connected_to = None
            if connector2.connected_to == connector1:
                connector2.connected_to = None
                
            # Emit signal
            if connector1.is_input:
                self.connectionDeleted.emit(connector2, connector1)
            else:
                self.connectionDeleted.emit(connector1, connector2)
                
    def get_connection_id(self, connector1, connector2):
        """
        Get a unique ID for a connection between two connectors.
        
        Args:
            connector1: First connector
            connector2: Second connector
            
        Returns:
            Unique connection ID
        """
        # Sort by parent block ID to ensure consistent IDs
        block1 = connector1.parentItem()
        block2 = connector2.parentItem()
        
        if block1.block_id < block2.block_id:
            return f"{block1.block_id}.{connector1.connector_id}-{block2.block_id}.{connector2.connector_id}"
        else:
            return f"{block2.block_id}.{connector2.connector_id}-{block1.block_id}.{connector1.connector_id}"
            
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if event.button() == Qt.MouseButton.MiddleButton:
            # Start panning
            self.is_panning = True
            self.last_mouse_pos = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        elif event.button() == Qt.MouseButton.LeftButton:
            # Check if we're creating a connection
            if self.active_connector:
                # Find item under cursor
                pos = self.mapToScene(event.position().toPoint())
                items = self.scene.items(pos)
                
                for item in items:
                    if isinstance(item, BlockConnector) and item != self.active_connector:
                        # Check if connection is valid
                        if self.active_connector.is_input != item.is_input:
                            # Check connector types
                            if self.active_connector.connector_type == item.connector_type:
                                # Create connection
                                if self.active_connector.is_input:
                                    item.connect_to(self.active_connector)
                                else:
                                    self.active_connector.connect_to(item)
                                    
                                # Clean up temporary connection
                                if self.temp_connection:
                                    self.scene.removeItem(self.temp_connection)
                                    self.temp_connection = None
                                    
                                self.active_connector = None
                                event.accept()
                                return
                
                # No valid connector found, cancel connection
                if self.temp_connection:
                    self.scene.removeItem(self.temp_connection)
                    self.temp_connection = None
                    
                self.active_connector = None
                event.accept()
            else:
                super().mousePressEvent(event)
        else:
            super().mousePressEvent(event)
            
    def mouseMoveEvent(self, event):
        """Handle mouse move events."""
        if self.is_panning and self.last_mouse_pos:
            # Pan the view
            delta = event.position() - self.last_mouse_pos
            self.last_mouse_pos = event.position()
            
            # Adjust the scroll bars
            h_bar = self.horizontalScrollBar()
            v_bar = self.verticalScrollBar()
            
            h_bar.setValue(h_bar.value() - delta.x())
            v_bar.setValue(v_bar.value() - delta.y())
            
            event.accept()
        elif self.active_connector and self.temp_connection:
            # Update temporary connection line
            pos = self.mapToScene(event.position().toPoint())
            self.temp_connection.set_temp_end_point(pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)
            
    def mouseReleaseEvent(self, event):
        """Handle mouse release events."""
        if event.button() == Qt.MouseButton.MiddleButton:
            # Stop panning
            self.is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)
            
    def wheelEvent(self, event):
        """Handle mouse wheel events for zooming."""
        # Calculate zoom factor
        zoom_factor = 1.1
        if event.angleDelta().y() < 0:
            zoom_factor = 1.0 / zoom_factor
            
        # Apply zoom
        new_zoom = self.zoom_level * zoom_factor
        if self.min_zoom <= new_zoom <= self.max_zoom:
            self.zoom_level = new_zoom
            self.scale(zoom_factor, zoom_factor)
            
    def keyPressEvent(self, event):
        """Handle key press events."""
        if event.key() == Qt.Key.Key_Delete:
            # Delete selected items
            selected_items = self.scene.selectedItems()
            for item in selected_items:
                if isinstance(item, BaseBlock):
                    self.remove_block(item)
            event.accept()
        else:
            super().keyPressEvent(event)
            
    def drawBackground(self, painter, rect):
        """Draw the canvas background with grid."""
        super().drawBackground(painter, rect)
        
        # Fill background
        painter.fillRect(rect, QBrush(QColor(40, 40, 40)))
        
        # Draw grid if enabled
        if self.grid_enabled:
            # Calculate grid spacing based on zoom level
            effective_grid_size = self.grid_size
            
            # Get visible area
            left = int(rect.left()) - (int(rect.left()) % effective_grid_size)
            top = int(rect.top()) - (int(rect.top()) % effective_grid_size)
            
            # Create grid pen
            grid_pen = QPen(QColor(60, 60, 60))
            grid_pen.setWidth(1)
            painter.setPen(grid_pen)
            
            # Draw vertical lines
            for x in range(left, int(rect.right()), effective_grid_size):
                painter.drawLine(x, rect.top(), x, rect.bottom())
                
            # Draw horizontal lines
            for y in range(top, int(rect.bottom()), effective_grid_size):
                painter.drawLine(rect.left(), y, rect.right(), y)
                
    def to_dict(self):
        """
        Convert canvas state to dictionary representation.
        
        Returns:
            dict: Dictionary representation of the canvas
        """
        # Convert blocks
        blocks_data = []
        for block_id, block in self.blocks.items():
            blocks_data.append(block.to_dict())
            
        # Convert connections
        connections_data = []
        for connection_id, connection in self.connections.items():
            if connection.start_connector and connection.end_connector:
                start_block = connection.start_connector.parentItem()
                end_block = connection.end_connector.parentItem()
                
                connections_data.append({
                    "from": {
                        "block": start_block.block_id,
                        "port": connection.start_connector.connector_id
                    },
                    "to": {
                        "block": end_block.block_id,
                        "port": connection.end_connector.connector_id
                    }
                })
                
        return {
            "blocks": blocks_data,
            "connections": connections_data
        }
        
    def from_dict(self, data, block_factory):
        """
        Restore canvas state from dictionary representation.
        
        Args:
            data: Dictionary representation of the canvas
            block_factory: Factory for creating blocks
            
        Returns:
            bool: True if canvas was restored successfully, False otherwise
        """
        try:
            # Clear current canvas
            self.clear()
            
            # Create blocks
            for block_data in data.get("blocks", []):
                block_id = block_data.get("id")
                block_type = block_data.get("type")
                
                if not block_id or not block_type:
                    continue
                    
                block = block_factory.create_block(block_type, block_id)
                if not block:
                    continue
                    
                # Set position
                block.setPos(block_data.get("x", 0), block_data.get("y", 0))
                
                # Set properties
                for prop_name, prop_value in block_data.get("properties", {}).items():
                    block.set_property(prop_name, prop_value)
                    
                # Add to canvas
                self.add_block(block)
                
            # Create connections
            for conn_data in data.get("connections", []):
                from_data = conn_data.get("from", {})
                to_data = conn_data.get("to", {})
                
                from_block_id = from_data.get("block")
                from_port = from_data.get("port")
                to_block_id = to_data.get("block")
                to_port = to_data.get("port")
                
                if not all([from_block_id, from_port, to_block_id, to_port]):
                    continue
                    
                from_block = self.get_block(from_block_id)
                to_block = self.get_block(to_block_id)
                
                if not from_block or not to_block:
                    continue
                    
                from_connector = from_block.output_connectors.get(from_port)
                to_connector = to_block.input_connectors.get(to_port)
                
                if not from_connector or not to_connector:
                    continue
                    
                # Create connection
                from_connector.connect_to(to_connector)
                
            return True
        except Exception as e:
            print(f"Error restoring canvas: {e}")
            return False