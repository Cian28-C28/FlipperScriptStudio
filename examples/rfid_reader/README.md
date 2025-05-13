# RFID Reader Example

This example demonstrates how to create an RFID reader application for the Flipper Zero using FlipperScriptStudio.

## Overview

The RFID Reader application allows you to:
- Detect and read 125 kHz RFID cards
- Display the card data on screen
- Save the card data to the Flipper Zero's storage
- Provide visual and sound notifications when a card is detected

## Block Structure

The application consists of the following key blocks:

1. **App Entry Point**: The main entry point of the application, named `rfid_reader_app`.
2. **App Init**: Initializes the application state and resources.
3. **GUI Init**: Sets up the graphical user interface.
4. **RFID Init**: Initializes the RFID subsystem.
5. **Notification Init**: Sets up the notification system for providing feedback.
6. **Display Text**: Shows the application title and instructions.
7. **RFID Read**: Waits for an RFID card to be presented to the device.
8. **RFID Data Check**: Checks if valid RFID data was read.
9. **Notification Success**: Provides feedback when a card is detected.
10. **Display RFID Data**: Shows the card data on screen.
11. **Save Dialog**: Asks the user if they want to save the card data.
12. **Save RFID Data**: Saves the card data to storage if requested.
13. **Wait For Exit**: Waits for the user to press the back button.
14. **Cleanup**: Releases all resources.
15. **App Exit**: Exits the application.

## Generated Code

When built, this visual script generates C code that interacts with the Flipper Zero's RFID subsystem. Here's a simplified version of what the generated code might look like:

```c
#include <furi.h>
#include <gui/gui.h>
#include <input/input.h>
#include <notification/notification.h>
#include <notification/notification_messages.h>
#include <storage/storage.h>
#include <dialogs/dialogs.h>
#include <lib/lfrfid/lfrfid.h>

typedef struct {
    Gui* gui;
    ViewPort* view_port;
    NotificationApp* notifications;
    DialogsApp* dialogs;
    LFRFIDWorker* worker;
    ProtocolDict* dict;
    RfidData* rfid_data;
    bool card_detected;
    char card_info[64];
} RFIDReaderApp;

// Draw callback for the viewport
static void draw_callback(Canvas* canvas, void* context) {
    RFIDReaderApp* app = context;
    canvas_clear(canvas);
    
    // Draw title
    canvas_set_font(canvas, FontPrimary);
    canvas_draw_str_aligned(canvas, 64, 12, AlignCenter, AlignCenter, "RFID Reader");
    
    // Draw instructions or card data
    canvas_set_font(canvas, FontSecondary);
    if(app->card_detected) {
        canvas_draw_str_aligned(canvas, 64, 32, AlignCenter, AlignCenter, app->card_info);
    } else {
        canvas_draw_str_aligned(canvas, 64, 32, AlignCenter, AlignCenter, "Waiting for RFID card...");
    }
}

// Input callback for the viewport
static void input_callback(InputEvent* input_event, void* context) {
    furi_assert(context);
    RFIDReaderApp* app = context;
    
    if(input_event->type == InputTypeShort && input_event->key == InputKeyBack) {
        view_port_enabled_set(app->view_port, false);
    }
}

// RFID worker callback
static void rfid_worker_callback(LFRFIDWorkerEvent event, void* context) {
    RFIDReaderApp* app = context;
    
    if(event == LFRFIDWorkerEventReadDone) {
        app->card_detected = true;
        notification_message(app->notifications, &sequence_success);
        
        // Format card info
        ProtocolId protocol = lfrfid_worker_get_protocol(app->worker);
        const char* protocol_name = protocol_dict_get_name(app->dict, protocol);
        uint64_t card_id = lfrfid_worker_get_card_id(app->worker);
        
        snprintf(app->card_info, sizeof(app->card_info), "%s: %012llX", protocol_name, card_id);
        
        // Request GUI update
        view_port_update(app->view_port);
    }
}

int32_t rfid_reader_app(void* p) {
    UNUSED(p);
    
    // Allocate application state
    RFIDReaderApp* app = malloc(sizeof(RFIDReaderApp));
    memset(app, 0, sizeof(RFIDReaderApp));
    
    // Initialize GUI
    app->gui = furi_record_open(RECORD_GUI);
    app->view_port = view_port_alloc();
    view_port_draw_callback_set(app->view_port, draw_callback, app);
    view_port_input_callback_set(app->view_port, input_callback, app);
    gui_add_view_port(app->gui, app->view_port, GuiLayerFullscreen);
    
    // Initialize notifications
    app->notifications = furi_record_open(RECORD_NOTIFICATION);
    
    // Initialize dialogs
    app->dialogs = furi_record_open(RECORD_DIALOGS);
    
    // Initialize RFID subsystem
    app->dict = protocol_dict_alloc(lfrfid_protocols, LFRFIDProtocolMax);
    app->worker = lfrfid_worker_alloc(app->dict);
    lfrfid_worker_start_thread(app->worker);
    lfrfid_worker_read_start(app->worker, rfid_worker_callback, app);
    
    // Main loop
    view_port_enabled_set(app->view_port, true);
    
    // Wait until back button is pressed
    while(view_port_is_enabled(app->view_port)) {
        furi_delay_ms(100);
        
        // If card was detected, ask to save
        if(app->card_detected) {
            // Stop reading
            lfrfid_worker_read_stop(app->worker);
            
            // Ask if user wants to save
            DialogMessage* message = dialog_message_alloc();
            dialog_message_set_header(message, "Save RFID data?", 64, 32, AlignCenter, AlignCenter);
            dialog_message_set_buttons(message, "No", NULL, "Yes");
            
            DialogMessageButton result = dialog_message_show(app->dialogs, message);
            dialog_message_free(message);
            
            if(result == DialogMessageButtonRight) {
                // Save the card data
                Storage* storage = furi_record_open(RECORD_STORAGE);
                FuriString* file_path = furi_string_alloc();
                
                // Generate filename based on card ID
                uint64_t card_id = lfrfid_worker_get_card_id(app->worker);
                furi_string_printf(file_path, "/ext/lfrfid/%012llX.rfid", card_id);
                
                // Save file
                FlipperFormat* file = flipper_format_file_alloc(storage);
                if(flipper_format_file_open_always(file, furi_string_get_cstr(file_path))) {
                    lfrfid_save_key_data(file, app->worker);
                    flipper_format_file_close(file);
                    notification_message(app->notifications, &sequence_success);
                }
                
                flipper_format_free(file);
                furi_string_free(file_path);
                furi_record_close(RECORD_STORAGE);
            }
            
            // Reset for next card
            app->card_detected = false;
            memset(app->card_info, 0, sizeof(app->card_info));
            view_port_update(app->view_port);
            
            // Start reading again
            lfrfid_worker_read_start(app->worker, rfid_worker_callback, app);
        }
    }
    
    // Cleanup
    lfrfid_worker_read_stop(app->worker);
    lfrfid_worker_stop_thread(app->worker);
    lfrfid_worker_free(app->worker);
    protocol_dict_free(app->dict);
    
    view_port_enabled_set(app->view_port, false);
    gui_remove_view_port(app->gui, app->view_port);
    view_port_free(app->view_port);
    
    furi_record_close(RECORD_GUI);
    furi_record_close(RECORD_NOTIFICATION);
    furi_record_close(RECORD_DIALOGS);
    
    free(app);
    
    return 0;
}
```

## Building the Application

To build this application using FlipperScriptStudio:

1. Open the `rfid_reader.fsp` file in FlipperScriptStudio
2. Click on the "Build" button in the toolbar
3. The application will be compiled using uFBT
4. The resulting FAP file can be found in the `dist` directory

## Running the Application

To run the application on your Flipper Zero:

1. Copy the FAP file to your Flipper Zero's SD card in the `apps` directory
2. Navigate to "Apps" on your Flipper Zero
3. Find and select "RFID Reader"
4. The application will start and wait for an RFID card
5. When a card is detected:
   - The device will play a success sound
   - The card data will be displayed on screen
   - You'll be asked if you want to save the card data
6. Press the back button to exit the application

## Hardware Interaction

This example demonstrates how to interact with the Flipper Zero's hardware:

- The 125 kHz RFID reader is used to detect and read cards
- The notification system provides feedback when a card is detected
- The storage system is used to save card data
- The GUI system displays information to the user

## Learning Points

This example demonstrates:
- How to initialize and use the RFID subsystem
- How to provide user feedback through notifications
- How to handle user input through dialogs
- How to save data to the Flipper Zero's storage
- How to create a more complex application flow with conditions and branches

## Next Steps

After understanding this example, you can explore more advanced features:
- Adding support for different RFID card types
- Implementing card emulation functionality
- Creating a card database with search capabilities
- Adding more interactive elements to the user interface