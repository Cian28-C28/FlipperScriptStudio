"""
FURI Helpers Module

This module provides helper functions for working with FURI components in Flipper Zero applications.
"""

import os
import logging
from typing import Dict, List, Set, Tuple, Optional

logger = logging.getLogger(__name__)


class FuriComponentHelper:
    """
    Helper class for working with FURI components.
    """
    
    # Standard FURI components and their include files
    COMPONENTS = {
        "gui": {
            "includes": ["#include <gui/gui.h>", "#include <gui/view_port.h>"],
            "records": ["RECORD_GUI"],
            "state_fields": ["Gui* gui;", "ViewPort* view_port;"],
            "init_code": [
                "app->view_port = view_port_alloc();",
                "view_port_draw_callback_set(app->view_port, ${app_name}_render_callback, app);",
                "view_port_input_callback_set(app->view_port, ${app_name}_input_callback, app);",
                "app->gui = furi_record_open(RECORD_GUI);",
                "gui_add_view_port(app->gui, app->view_port, GuiLayerFullscreen);"
            ],
            "cleanup_code": [
                "view_port_enabled_set(app->view_port, false);",
                "gui_remove_view_port(app->gui, app->view_port);",
                "view_port_free(app->view_port);",
                "furi_record_close(RECORD_GUI);"
            ]
        },
        "storage": {
            "includes": ["#include <storage/storage.h>"],
            "records": ["RECORD_STORAGE"],
            "state_fields": ["Storage* storage;"],
            "init_code": ["app->storage = furi_record_open(RECORD_STORAGE);"],
            "cleanup_code": ["furi_record_close(RECORD_STORAGE);"]
        },
        "subghz": {
            "includes": ["#include <lib/subghz/subghz.h>"],
            "records": ["RECORD_SUBGHZ"],
            "state_fields": ["SubGhz* subghz;"],
            "init_code": ["app->subghz = furi_record_open(RECORD_SUBGHZ);"],
            "cleanup_code": ["furi_record_close(RECORD_SUBGHZ);"]
        },
        "nfc": {
            "includes": ["#include <lib/nfc/nfc.h>"],
            "records": ["RECORD_NFC"],
            "state_fields": ["Nfc* nfc;"],
            "init_code": ["app->nfc = furi_record_open(RECORD_NFC);"],
            "cleanup_code": ["furi_record_close(RECORD_NFC);"]
        },
        "infrared": {
            "includes": ["#include <lib/infrared/infrared.h>"],
            "records": ["RECORD_INFRARED"],
            "state_fields": ["Infrared* infrared;"],
            "init_code": ["app->infrared = furi_record_open(RECORD_INFRARED);"],
            "cleanup_code": ["furi_record_close(RECORD_INFRARED);"]
        },
        "bt": {
            "includes": ["#include <bt/bt_service.h>"],
            "records": ["RECORD_BT"],
            "state_fields": ["BtService* bt;"],
            "init_code": ["app->bt = furi_record_open(RECORD_BT);"],
            "cleanup_code": ["furi_record_close(RECORD_BT);"]
        }
    }
    
    @classmethod
    def get_component_includes(cls, component_name: str) -> List[str]:
        """
        Get include statements for a FURI component.
        
        Args:
            component_name: Name of the component
            
        Returns:
            list: List of include statements
        """
        component = cls.COMPONENTS.get(component_name)
        if component:
            return component.get("includes", [])
        return []
        
    @classmethod
    def get_component_records(cls, component_name: str) -> List[str]:
        """
        Get record names for a FURI component.
        
        Args:
            component_name: Name of the component
            
        Returns:
            list: List of record names
        """
        component = cls.COMPONENTS.get(component_name)
        if component:
            return component.get("records", [])
        return []
        
    @classmethod
    def get_component_state_fields(cls, component_name: str) -> List[str]:
        """
        Get state fields for a FURI component.
        
        Args:
            component_name: Name of the component
            
        Returns:
            list: List of state field declarations
        """
        component = cls.COMPONENTS.get(component_name)
        if component:
            return component.get("state_fields", [])
        return []
        
    @classmethod
    def get_component_init_code(cls, component_name: str, app_name: str) -> List[str]:
        """
        Get initialization code for a FURI component.
        
        Args:
            component_name: Name of the component
            app_name: Name of the application
            
        Returns:
            list: List of initialization code lines
        """
        component = cls.COMPONENTS.get(component_name)
        if component:
            init_code = component.get("init_code", [])
            return [line.replace("${app_name}", app_name) for line in init_code]
        return []
        
    @classmethod
    def get_component_cleanup_code(cls, component_name: str, app_name: str) -> List[str]:
        """
        Get cleanup code for a FURI component.
        
        Args:
            component_name: Name of the component
            app_name: Name of the application
            
        Returns:
            list: List of cleanup code lines
        """
        component = cls.COMPONENTS.get(component_name)
        if component:
            cleanup_code = component.get("cleanup_code", [])
            return [line.replace("${app_name}", app_name) for line in cleanup_code]
        return []
        
    @classmethod
    def get_all_components(cls) -> List[str]:
        """
        Get a list of all available FURI components.
        
        Returns:
            list: List of component names
        """
        return list(cls.COMPONENTS.keys())


class FuriCodeSnippets:
    """
    Common code snippets for Flipper Zero applications.
    """
    
    @staticmethod
    def get_app_state_struct(app_name: str, components: List[str]) -> str:
        """
        Generate the application state structure.
        
        Args:
            app_name: Name of the application
            components: List of required components
            
        Returns:
            str: Application state structure code
        """
        lines = [
            f"typedef struct {{",
        ]
        
        # Add fields for each component
        for component in components:
            lines.extend(FuriComponentHelper.get_component_state_fields(component))
            
        # Add variables structure
        lines.extend([
            "    struct {",
            "        // Variables will be added here",
            "    } variables;",
            f"}} {app_name}_state_t;"
        ])
        
        return os.linesep.join(lines)
        
    @staticmethod
    def get_app_init_code(app_name: str, components: List[str]) -> str:
        """
        Generate application initialization code.
        
        Args:
            app_name: Name of the application
            components: List of required components
            
        Returns:
            str: Application initialization code
        """
        lines = [
            f"// Allocate app state",
            f"{app_name}_state_t* app = malloc(sizeof({app_name}_state_t));"
        ]
        
        # Add initialization code for each component
        for component in components:
            lines.extend(FuriComponentHelper.get_component_init_code(component, app_name))
            
        return os.linesep.join(lines)
        
    @staticmethod
    def get_app_cleanup_code(app_name: str, components: List[str]) -> str:
        """
        Generate application cleanup code.
        
        Args:
            app_name: Name of the application
            components: List of required components
            
        Returns:
            str: Application cleanup code
        """
        lines = [
            f"static void {app_name}_free(void* p) {{",
            f"    {app_name}_state_t* app = ({app_name}_state_t*)p;"
        ]
        
        # Add cleanup code for each component
        for component in components:
            lines.extend(FuriComponentHelper.get_component_cleanup_code(component, app_name))
            
        lines.extend([
            "    // Free app state",
            "    free(app);",
            "}"
        ])
        
        return os.linesep.join(lines)
        
    @staticmethod
    def get_render_callback(app_name: str) -> str:
        """
        Generate a render callback function.
        
        Args:
            app_name: Name of the application
            
        Returns:
            str: Render callback function code
        """
        return f"""
static void {app_name}_render_callback(Canvas* canvas, void* ctx) {{
    furi_assert(ctx);
    {app_name}_state_t* app = ctx;
    
    canvas_clear(canvas);
    canvas_set_font(canvas, FontPrimary);
    canvas_draw_str(canvas, 0, 10, "{app_name}");
}}
"""
        
    @staticmethod
    def get_input_callback(app_name: str) -> str:
        """
        Generate an input callback function.
        
        Args:
            app_name: Name of the application
            
        Returns:
            str: Input callback function code
        """
        return f"""
static void {app_name}_input_callback(InputEvent* event, void* ctx) {{
    furi_assert(ctx);
    {app_name}_state_t* app = ctx;
    
    if(event->type == InputTypePress) {{
        // Handle button press
    }}
}}
"""