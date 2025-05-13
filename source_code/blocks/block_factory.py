"""
Block Factory Module

This module provides functionality to create block instances from block definitions.
"""

import json
import os
from PyQt6.QtGui import QColor

from .base_block import BaseBlock


class BlockFactory:
    """
    Factory class for creating block instances from definitions.
    """
    
    def __init__(self, definitions_file=None):
        """
        Initialize the block factory.
        
        Args:
            definitions_file: Path to the JSON file containing block definitions
        """
        self.categories = {}
        self.block_types = {}
        
        if definitions_file and os.path.exists(definitions_file):
            self.load_definitions(definitions_file)
    
    def load_definitions(self, file_path):
        """
        Load block definitions from a JSON file.
        
        Args:
            file_path: Path to the JSON file containing block definitions
            
        Returns:
            bool: True if definitions were loaded successfully, False otherwise
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Process block categories
            for category in data.get('blockCategories', []):
                category_id = category.get('id')
                if not category_id:
                    continue
                    
                self.categories[category_id] = {
                    'name': category.get('name', category_id),
                    'color': category.get('color', '#808080'),
                    'description': category.get('description', '')
                }
                
                # Process blocks in this category
                for block_def in category.get('blocks', []):
                    block_id = block_def.get('id')
                    if not block_id:
                        continue
                        
                    self.block_types[block_id] = {
                        'category': category_id,
                        'name': block_def.get('name', block_id),
                        'type': block_def.get('type', 'generic'),
                        'description': block_def.get('description', ''),
                        'inputs': block_def.get('inputs', []),
                        'outputs': block_def.get('outputs', []),
                        'properties': block_def.get('properties', []),
                        'codeTemplate': block_def.get('codeTemplate', '')
                    }
            
            return True
        except Exception as e:
            print(f"Error loading block definitions: {e}")
            return False
    
    def get_categories(self):
        """
        Get all block categories.
        
        Returns:
            dict: Dictionary of category information
        """
        return self.categories
    
    def get_blocks_in_category(self, category_id):
        """
        Get all blocks in a specific category.
        
        Args:
            category_id: ID of the category
            
        Returns:
            list: List of block type IDs in the category
        """
        return [
            block_id for block_id, block_info in self.block_types.items()
            if block_info.get('category') == category_id
        ]
    
    def create_block(self, block_type, block_id=None):
        """
        Create a new block instance of the specified type.
        
        Args:
            block_type: Type of block to create
            block_id: Optional ID for the new block (generated if not provided)
            
        Returns:
            BaseBlock: New block instance or None if type is not found
        """
        if block_type not in self.block_types:
            return None
            
        block_info = self.block_types[block_type]
        category_id = block_info.get('category')
        category_info = self.categories.get(category_id, {})
        
        # Generate a unique ID if not provided
        if not block_id:
            import uuid
            block_id = f"{block_type}_{uuid.uuid4().hex[:8]}"
        
        # Create the block
        color = QColor(category_info.get('color', '#808080'))
        block = BaseBlock(
            block_id=block_id,
            block_type=block_type,
            title=block_info.get('name', block_type),
            color=color
        )
        
        # Add input connectors
        for input_def in block_info.get('inputs', []):
            input_id = input_def.get('id')
            if not input_id:
                continue
                
            block.add_input_connector(
                input_id,
                input_def.get('type', 'data'),
                input_def.get('description', input_id)
            )
            
            # Set default property value if specified
            if 'default' in input_def:
                block.set_property(input_id, input_def['default'])
        
        # Add output connectors
        for output_def in block_info.get('outputs', []):
            output_id = output_def.get('id')
            if not output_id:
                continue
                
            block.add_output_connector(
                output_id,
                output_def.get('type', 'data'),
                output_def.get('description', output_id)
            )
        
        # Set properties
        for prop_def in block_info.get('properties', []):
            prop_id = prop_def.get('id')
            if not prop_id or 'default' not in prop_def:
                continue
                
            block.set_property(prop_id, prop_def['default'])
        
        return block
    
    def get_block_info(self, block_type):
        """
        Get information about a specific block type.
        
        Args:
            block_type: Type of block
            
        Returns:
            dict: Block information or None if type is not found
        """
        return self.block_types.get(block_type)