# Hello World Example

This is a simple "Hello World" application for the Flipper Zero, created using FlipperScriptStudio.

## Overview

This example demonstrates the most basic functionality of a Flipper Zero application:
- Initializing the GUI
- Displaying text on the screen
- Waiting for user input
- Exiting the application

## Block Structure

The application consists of the following blocks:

1. **App Entry Point**: The main entry point of the application, named `app_main`.
2. **GUI Init**: Initializes the GUI system of the Flipper Zero.
3. **Display Text**: Shows the text "Hello, World!" centered on the screen.
4. **GUI Refresh**: Updates the display to show the rendered content.
5. **Wait for Input**: Pauses execution until the user presses a button or a timeout occurs.
6. **App Exit**: Exits the application with a success code.

## Generated Code

When built, this visual script generates C code similar to the following:

```c
#include <furi.h>
#include <gui/gui.h>
#include <input/input.h>

typedef struct {
    Gui* gui;
    ViewPort* view_port;
} HelloWorldApp;

static void draw_callback(Canvas* canvas, void* context) {
    UNUSED(context);
    canvas_clear(canvas);
    canvas_set_font(canvas, FontPrimary);
    canvas_draw_str_aligned(canvas, 32, 32, AlignCenter, AlignCenter, "Hello, World!");
}

static void input_callback(InputEvent* input_event, void* context) {
    furi_assert(context);
    HelloWorldApp* app = context;
    if(input_event->type == InputTypeShort && input_event->key == InputKeyBack) {
        // Exit on back button press
        view_port_enabled_set(app->view_port, false);
    }
}

int32_t app_main(void* p) {
    UNUSED(p);
    
    // Allocate application state
    HelloWorldApp* app = malloc(sizeof(HelloWorldApp));
    
    // Initialize GUI
    app->gui = furi_record_open(RECORD_GUI);
    app->view_port = view_port_alloc();
    view_port_draw_callback_set(app->view_port, draw_callback, app);
    view_port_input_callback_set(app->view_port, input_callback, app);
    gui_add_view_port(app->gui, app->view_port, GuiLayerFullscreen);
    
    // Main loop
    view_port_enabled_set(app->view_port, true);
    furi_delay_ms(5000);  // Wait for 5 seconds or until back button is pressed
    
    // Cleanup
    view_port_enabled_set(app->view_port, false);
    gui_remove_view_port(app->gui, app->view_port);
    view_port_free(app->view_port);
    furi_record_close(RECORD_GUI);
    free(app);
    
    return 0;
}
```

## Building the Application

To build this application using FlipperScriptStudio:

1. Open the `hello_world.fsp` file in FlipperScriptStudio
2. Click on the "Build" button in the toolbar
3. The application will be compiled using uFBT
4. The resulting FAP file can be found in the `dist` directory

## Running the Application

To run the application on your Flipper Zero:

1. Copy the FAP file to your Flipper Zero's SD card in the `apps` directory
2. Navigate to "Apps" on your Flipper Zero
3. Find and select "Hello World"
4. The application will display "Hello, World!" on the screen
5. After 5 seconds or when you press the back button, the application will exit

## Learning Points

This example demonstrates:
- Basic application structure for Flipper Zero apps
- How to initialize and use the GUI system
- How to display text on the screen
- How to handle user input
- Proper application cleanup and resource management

## Next Steps

After understanding this example, you can explore more complex applications like:
- Adding interactive elements
- Using different GUI components
- Working with hardware features like RFID or SubGHz