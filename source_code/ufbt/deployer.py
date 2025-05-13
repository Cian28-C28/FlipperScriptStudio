"""
uFBT Deployer Module

This module provides functionality to deploy Flipper Zero applications to devices.
"""

import os
import re
import logging
import subprocess
import serial
import serial.tools.list_ports
from typing import Dict, List, Tuple, Optional

from .config import UfbtConfig

logger = logging.getLogger(__name__)


class UfbtDeployer:
    """
    Deployer for Flipper Zero applications.
    """
    
    def __init__(self, config: UfbtConfig = None):
        """
        Initialize the uFBT deployer.
        
        Args:
            config: uFBT configuration
        """
        self.config = config or UfbtConfig()
        
    def list_devices(self) -> List[Dict[str, str]]:
        """
        List connected Flipper Zero devices.
        
        Returns:
            list: List of dictionaries with device information
        """
        devices = []
        
        try:
            # List serial ports
            ports = serial.tools.list_ports.comports()
            
            for port in ports:
                # Check if this is likely a Flipper Zero
                if (port.vid == 0x0483 and port.pid == 0x5740) or "Flipper" in port.description:
                    devices.append({
                        "port": port.device,
                        "description": port.description,
                        "hardware_id": port.hwid,
                        "serial_number": port.serial_number
                    })
                    
        except Exception as e:
            logger.error(f"Error listing devices: {e}")
            
        return devices
        
    def deploy_app(self, app_dir: str, device_port: str = None) -> Tuple[bool, str]:
        """
        Deploy an application to a Flipper Zero device.
        
        Args:
            app_dir: Application directory
            device_port: Serial port of the device (optional)
            
        Returns:
            tuple: (success, message)
        """
        try:
            # Prepare command
            cmd = [self.config.ufbt_path, "launch"]
            
            if device_port:
                cmd.extend(["--port", device_port])
                
            # Change to app directory
            cwd = os.getcwd()
            os.chdir(app_dir)
            
            try:
                # Run uFBT launch
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                if result.returncode == 0:
                    return True, "Application deployed successfully"
                else:
                    return False, f"Deployment failed: {result.stderr}"
            finally:
                # Restore working directory
                os.chdir(cwd)
                
        except Exception as e:
            return False, f"Deployment error: {str(e)}"
            
    def install_app(self, fap_path: str, device_port: str = None) -> Tuple[bool, str]:
        """
        Install a FAP file to a Flipper Zero device.
        
        Args:
            fap_path: Path to the FAP file
            device_port: Serial port of the device (optional)
            
        Returns:
            tuple: (success, message)
        """
        try:
            # Prepare command
            cmd = [self.config.ufbt_path, "install"]
            
            if device_port:
                cmd.extend(["--port", device_port])
                
            cmd.append(fap_path)
            
            # Run uFBT install
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                return True, "Application installed successfully"
            else:
                return False, f"Installation failed: {result.stderr}"
                
        except Exception as e:
            return False, f"Installation error: {str(e)}"
            
    def detect_flipper_storage(self) -> Optional[str]:
        """
        Detect Flipper Zero storage mounted as a drive.
        
        Returns:
            str: Path to the Flipper Zero storage or None if not found
        """
        try:
            import platform
            system = platform.system()
            
            if system == "Windows":
                # On Windows, check all drives
                import win32api
                
                drives = win32api.GetLogicalDriveStrings().split('\000')[:-1]
                for drive in drives:
                    if os.path.exists(os.path.join(drive, "apps")):
                        return drive
                        
            elif system == "Darwin":  # macOS
                # Check /Volumes for Flipper
                volumes_dir = "/Volumes"
                for volume in os.listdir(volumes_dir):
                    volume_path = os.path.join(volumes_dir, volume)
                    if os.path.exists(os.path.join(volume_path, "apps")):
                        return volume_path
                        
            elif system == "Linux":
                # Check /media/<user> and /mnt
                import getpass
                user = getpass.getuser()
                
                # Check /media/<user>
                media_dir = f"/media/{user}"
                if os.path.exists(media_dir):
                    for volume in os.listdir(media_dir):
                        volume_path = os.path.join(media_dir, volume)
                        if os.path.exists(os.path.join(volume_path, "apps")):
                            return volume_path
                            
                # Check /mnt
                mnt_dir = "/mnt"
                if os.path.exists(mnt_dir):
                    for volume in os.listdir(mnt_dir):
                        volume_path = os.path.join(mnt_dir, volume)
                        if os.path.exists(os.path.join(volume_path, "apps")):
                            return volume_path
                            
        except Exception as e:
            logger.error(f"Error detecting Flipper storage: {e}")
            
        return None
        
    def copy_to_flipper(self, fap_path: str, storage_path: str = None) -> Tuple[bool, str]:
        """
        Copy a FAP file directly to a mounted Flipper Zero.
        
        Args:
            fap_path: Path to the FAP file
            storage_path: Path to the Flipper Zero storage (optional)
            
        Returns:
            tuple: (success, message)
        """
        try:
            # Find Flipper storage if not specified
            if not storage_path:
                storage_path = self.detect_flipper_storage()
                
            if not storage_path:
                return False, "Flipper Zero storage not found"
                
            # Check if the apps directory exists
            apps_dir = os.path.join(storage_path, "apps")
            if not os.path.exists(apps_dir):
                return False, f"Apps directory not found at {apps_dir}"
                
            # Copy the FAP file
            import shutil
            fap_filename = os.path.basename(fap_path)
            dest_path = os.path.join(apps_dir, fap_filename)
            
            shutil.copy(fap_path, dest_path)
            
            return True, f"Application copied to {dest_path}"
            
        except Exception as e:
            return False, f"Copy error: {str(e)}"