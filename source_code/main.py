#!/usr/bin/env python3
"""
FlipperScriptStudio

A visual scripting environment for Flipper Zero app development.
"""

import sys
import os
import argparse
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

from ui import MainWindow


def parse_arguments():
    """
    Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="FlipperScriptStudio - Visual scripting for Flipper Zero"
    )
    parser.add_argument(
        "project_file",
        nargs="?",
        help="Project file to open"
    )
    parser.add_argument(
        "--block-definitions",
        help="Path to block definitions JSON file"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    
    return parser.parse_args()


def main():
    """Main application entry point."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("FlipperScriptStudio")
    app.setOrganizationName("FlipperScriptStudio")
    
    # Set application icon
    icon_path = os.path.join(os.path.dirname(__file__), "assets", "icons", "app_icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Create main window
    main_window = MainWindow()
    main_window.show()
    
    # Open project file if specified
    if args.project_file and os.path.exists(args.project_file):
        main_window.load_project(args.project_file)
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()