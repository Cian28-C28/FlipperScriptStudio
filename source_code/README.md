# FlipperScriptStudio

A visual scripting environment for Flipper Zero app development.

## Overview

FlipperScriptStudio provides a drag-and-drop interface for creating Flipper Zero applications without writing code manually. The application features:

- Visual block-based programming interface
- Code generation from visual blocks to C code
- Integration with uFBT for building and deploying applications
- Support for all major Flipper Zero hardware features
- Project management with save/load functionality
- Application manifest editor
- Export to source code or compiled FAP files

## Requirements

- Python 3.8 or higher
- PyQt6
- uFBT (Flipper Zero Build Tool)
- GCC (for code validation)

## Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the application:
   ```
   python main.py
   ```

## Usage

### Creating a New Project

1. Start FlipperScriptStudio
2. Use the block palette on the left to drag blocks onto the canvas
3. Connect blocks by dragging from output connectors to input connectors
4. Configure block properties using the property editor on the right
5. Set application metadata in the manifest editor

### Building and Exporting

1. Use the "Export" menu to export your application
2. Choose between source code or binary (FAP) export
3. Configure build options as needed
4. Deploy directly to a connected Flipper Zero device

### uFBT Integration

FlipperScriptStudio integrates with uFBT to provide:
- SDK management
- Application building
- FAP package creation
- Deployment to Flipper Zero devices

## Block Types

The application includes blocks for:
- Events (app start, button press, timer)
- Display operations (draw text, shapes, etc.)
- SubGHz communication
- NFC and RFID operations
- GPIO control
- Notifications (LED, vibration, sound)
- Logic and flow control
- Data manipulation
- Storage operations
- Bluetooth functionality

## Project Structure

- `blocks/`: Block definitions and factory
- `codegen/`: Code generation from blocks to C
- `models/`: Data models for projects and manifests
- `ui/`: User interface components
- `ufbt/`: uFBT integration
- `utils/`: Utility functions and helpers

## License

This project is licensed under the MIT License - see the LICENSE file for details.