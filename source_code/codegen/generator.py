"""
Code Generator Module

This module provides the main code generator class for translating visual blocks to C code.
"""

import os
import re
import logging
from typing import Dict, List, Set, Tuple, Optional, Any

logger = logging.getLogger(__name__)


class CodeGenerator:
    """
    Generates C code from visual blocks.
    """
    
    def __init__(self, block_factory=None):
        """
        Initialize the code generator.
        
        Args:
            block_factory: Factory for creating blocks
        """
        self.block_factory = block_factory
        self.includes = set()
        self.function_declarations = []
        self.function_definitions = []
        self.global_variables = []
        self.app_state_fields = []
        self.required_furi_components = set()
        
    def generate_code(self, project, canvas_data):
        """
        Generate C code from canvas data.
        
        Args:
            project: Project object containing manifest data
            canvas_data: Dictionary containing blocks and connections
            
        Returns:
            dict: Dictionary containing generated code files
        """
        # Reset state
        self.includes = set()
        self.function_declarations = []
        self.function_definitions = []
        self.global_variables = []
        self.app_state_fields = []
        self.required_furi_components = set()
        
        # Get manifest data
        manifest = project.get_manifest()
        app_name = manifest.get("appid", "flipper_app")
        app_entry_point = manifest.get("entry_point", "app_main")
        
        # Add standard includes
        self.includes.add("#include <furi.h>")
        self.includes.add("#include <gui/gui.h>")
        self.includes.add("#include <input/input.h>")
        self.includes.add("#include <stdlib.h>")
        
        # Add includes for required components
        for req in manifest.get("requires", []):
            if req == "gui":
                self.required_furi_components.add("gui")
            elif req == "storage":
                self.includes.add("#include <storage/storage.h>")
                self.required_furi_components.add("storage")
            elif req == "subghz":
                self.includes.add("#include <lib/subghz/subghz.h>")
                self.required_furi_components.add("subghz")
            elif req == "nfc":
                self.includes.add("#include <lib/nfc/nfc.h>")
                self.required_furi_components.add("nfc")
            elif req == "infrared":
                self.includes.add("#include <lib/infrared/infrared.h>")
                self.required_furi_components.add("infrared")
            elif req == "bt":
                self.includes.add("#include <bt/bt_service.h>")
                self.required_furi_components.add("bt")
        
        # Generate app state structure
        self.app_state_fields.append("    ViewPort* view_port;")
        self.app_state_fields.append("    Gui* gui;")
        
        # Add fields for required components
        for component in self.required_furi_components:
            if component == "storage":
                self.app_state_fields.append("    Storage* storage;")
            elif component == "subghz":
                self.app_state_fields.append("    SubGhz* subghz;")
            elif component == "nfc":
                self.app_state_fields.append("    Nfc* nfc;")
            elif component == "infrared":
                self.app_state_fields.append("    Infrared* infrared;")
            elif component == "bt":
                self.app_state_fields.append("    BtService* bt;")
        
        # Add variables structure
        self.app_state_fields.append("    struct {")
        self.app_state_fields.append("        // Variables will be added here")
        self.app_state_fields.append("    } variables;")
        
        # Process blocks and connections
        blocks = canvas_data.get("blocks", [])
        connections = canvas_data.get("connections", [])
        
        # Create a dictionary of blocks by ID
        blocks_by_id = {block["id"]: block for block in blocks}
        
        # Create a dictionary of connections by block ID and port
        connections_by_source = {}
        for conn in connections:
            from_block = conn["from"]["block"]
            from_port = conn["from"]["port"]
            to_block = conn["to"]["block"]
            to_port = conn["to"]["port"]
            
            if from_block not in connections_by_source:
                connections_by_source[from_block] = {}
            connections_by_source[from_block][from_port] = (to_block, to_port)
        
        # Find entry point blocks (app_on_start)
        entry_blocks = [
            block for block in blocks 
            if block["type"] == "app_on_start"
        ]
        
        if not entry_blocks:
            logger.warning("No entry point block found")
            return {"error": "No entry point block found"}
        
        # Generate code for each entry point
        for entry_block in entry_blocks:
            self._process_block(
                entry_block, 
                blocks_by_id, 
                connections_by_source, 
                app_name
            )
        
        # Generate callback functions
        self._generate_callbacks(app_name)
        
        # Generate the main application code
        main_code = self._generate_main_code(app_name, app_entry_point)
        
        # Return the generated code
        return {
            "main.c": main_code
        }
    
    def _process_block(self, block, blocks_by_id, connections_by_source, app_name, processed_blocks=None):
        """
        Process a block and generate code for it.
        
        Args:
            block: Block to process
            blocks_by_id: Dictionary of blocks by ID
            connections_by_source: Dictionary of connections by source block ID and port
            app_name: Application name
            processed_blocks: Set of already processed block IDs
            
        Returns:
            str: Generated code for the block
        """
        if processed_blocks is None:
            processed_blocks = set()
            
        block_id = block["id"]
        if block_id in processed_blocks:
            return ""  # Already processed this block
            
        processed_blocks.add(block_id)
        
        block_type = block["type"]
        block_info = self.block_factory.get_block_info(block_type)
        
        if not block_info:
            logger.warning(f"Unknown block type: {block_type}")
            return ""
            
        # Get the code template for this block
        code_template = block_info.get("codeTemplate", "")
        if not code_template:
            logger.warning(f"No code template for block type: {block_type}")
            return ""
            
        # Replace variables in the template
        code = code_template
        
        # Replace app name
        code = code.replace("${app_name}", app_name)
        
        # Replace property values
        for prop_name, prop_value in block.get("properties", {}).items():
            placeholder = f"${{{prop_name}}}"
            if isinstance(prop_value, str):
                # Escape quotes in strings
                prop_value = f'"{prop_value}"'
            elif isinstance(prop_value, bool):
                prop_value = "true" if prop_value else "false"
            else:
                prop_value = str(prop_value)
                
            code = code.replace(placeholder, prop_value)
            
        # Process connections
        if block_id in connections_by_source:
            for port, (target_block_id, target_port) in connections_by_source[block_id].items():
                if port == "next":
                    # This is a flow connection, process the next block
                    target_block = blocks_by_id.get(target_block_id)
                    if target_block:
                        next_code = self._process_block(
                            target_block, 
                            blocks_by_id, 
                            connections_by_source, 
                            app_name,
                            processed_blocks
                        )
                        code = code.replace("${next_code}", next_code)
                    else:
                        code = code.replace("${next_code}", "")
                else:
                    # This is a data connection, not implemented yet
                    pass
        else:
            # No connections from this block
            code = code.replace("${next_code}", "")
            
        return code
    
    def _generate_callbacks(self, app_name):
        """
        Generate callback functions for the application.
        
        Args:
            app_name: Application name
        """
        # Generate render callback
        render_callback = f"""
static void {app_name}_render_callback(Canvas* canvas, void* ctx) {{
    furi_assert(ctx);
    {app_name}_state_t* app = ctx;
    
    canvas_clear(canvas);
    canvas_set_font(canvas, FontPrimary);
    canvas_draw_str(canvas, 0, 10, "{app_name}");
}}
"""
        self.function_definitions.append(render_callback)
        
        # Generate input callback
        input_callback = f"""
static void {app_name}_input_callback(InputEvent* event, void* ctx) {{
    furi_assert(ctx);
    {app_name}_state_t* app = ctx;
    
    if(event->type == InputTypePress) {{
        // Handle button press
    }}
}}
"""
        self.function_definitions.append(input_callback)
    
    def _generate_main_code(self, app_name, entry_point):
        """
        Generate the main application code.
        
        Args:
            app_name: Application name
            entry_point: Entry point function name
            
        Returns:
            str: Generated main code
        """
        # Generate app state structure
        app_state = f"""
/**
 * Application state structure
 */
typedef struct {{
{os.linesep.join(self.app_state_fields)}
}} {app_name}_state_t;
"""
        
        # Generate application cleanup function
        cleanup_function = f"""
static void {app_name}_free(void* p) {{
    {app_name}_state_t* app = ({app_name}_state_t*)p;
    
    // Free view port
    view_port_enabled_set(app->view_port, false);
    gui_remove_view_port(app->gui, app->view_port);
    view_port_free(app->view_port);
    
    // Close records
    furi_record_close(RECORD_GUI);
"""
        
        # Add cleanup for required components
        for component in self.required_furi_components:
            if component == "storage":
                cleanup_function += f"    furi_record_close(RECORD_STORAGE);\n"
            elif component == "subghz":
                cleanup_function += f"    furi_record_close(RECORD_SUBGHZ);\n"
            elif component == "nfc":
                cleanup_function += f"    furi_record_close(RECORD_NFC);\n"
            elif component == "infrared":
                cleanup_function += f"    furi_record_close(RECORD_INFRARED);\n"
            elif component == "bt":
                cleanup_function += f"    furi_record_close(RECORD_BT);\n"
                
        cleanup_function += f"""
    // Free app state
    free(app);
}}
"""
        
        # Combine all parts
        main_code = f"""/**
 * {app_name} application
 */

{os.linesep.join(sorted(self.includes))}

{app_state}

{os.linesep.join(self.function_declarations)}

{os.linesep.join(self.function_definitions)}

{cleanup_function}

/**
 * Application entry point
 */
int32_t {entry_point}(void* p) {{
    UNUSED(p);
    
    // Allocate app state
    {app_name}_state_t* app = malloc(sizeof({app_name}_state_t));
    
    // Initialize view port
    app->view_port = view_port_alloc();
    view_port_draw_callback_set(app->view_port, {app_name}_render_callback, app);
    view_port_input_callback_set(app->view_port, {app_name}_input_callback, app);
    
    // Open GUI and register view port
    app->gui = furi_record_open(RECORD_GUI);
    gui_add_view_port(app->gui, app->view_port, GuiLayerFullscreen);
"""
        
        # Add initialization for required components
        for component in self.required_furi_components:
            if component == "storage":
                main_code += f"    app->storage = furi_record_open(RECORD_STORAGE);\n"
            elif component == "subghz":
                main_code += f"    app->subghz = furi_record_open(RECORD_SUBGHZ);\n"
            elif component == "nfc":
                main_code += f"    app->nfc = furi_record_open(RECORD_NFC);\n"
            elif component == "infrared":
                main_code += f"    app->infrared = furi_record_open(RECORD_INFRARED);\n"
            elif component == "bt":
                main_code += f"    app->bt = furi_record_open(RECORD_BT);\n"
                
        main_code += f"""
    // Main application loop
    view_port_enabled_set(app->view_port, true);
    
    // Wait until the user exits the application
    while(1) {{
        furi_delay_ms(100);
    }}
    
    // Cleanup
    {app_name}_free(app);
    
    return 0;
}}
"""
        
        return main_code