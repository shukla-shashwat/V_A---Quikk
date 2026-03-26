# tools/network_tools.py
"""
WiFi and Bluetooth control tools for Windows.
"""

import subprocess
import re
from typing import Tuple, List, Dict, Optional


def _run_netsh(args: List[str]) -> Tuple[bool, str]:
    """Run a netsh command."""
    try:
        result = subprocess.run(
            ["netsh"] + args,
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0, result.stdout.strip()
    except Exception as e:
        return False, str(e)


# ==================== WiFi Functions ====================

def get_wifi_status() -> Dict:
    """Get current WiFi status."""
    success, output = _run_netsh(["wlan", "show", "interfaces"])
    
    if not success:
        return {"enabled": False, "error": "Could not get WiFi status"}
    
    status = {
        "enabled": True,
        "connected": False,
        "ssid": None,
        "signal": None,
        "state": None
    }
    
    for line in output.split("\n"):
        line = line.strip()
        if "State" in line and ":" in line:
            state = line.split(":")[1].strip()
            status["state"] = state
            status["connected"] = "connected" in state.lower()
        elif "SSID" in line and "BSSID" not in line and ":" in line:
            status["ssid"] = line.split(":")[1].strip()
        elif "Signal" in line and ":" in line:
            status["signal"] = line.split(":")[1].strip()
    
    return status


def enable_wifi() -> Tuple[bool, str]:
    """Enable WiFi adapter - requires admin privileges."""
    return False, "⚠️ WiFi enable/disable requires admin privileges.\n💡 Tip: Use Windows Settings (Win+I > Network) or Action Center (Win+A) to toggle WiFi."


def disable_wifi() -> Tuple[bool, str]:
    """Disable WiFi adapter - requires admin privileges."""
    return False, "⚠️ WiFi enable/disable requires admin privileges.\n💡 Tip: Use Windows Settings (Win+I > Network) or Action Center (Win+A) to toggle WiFi."


def toggle_wifi() -> Tuple[bool, str]:
    """Toggle WiFi on/off."""
    status = get_wifi_status()
    
    if status.get("enabled") and status.get("connected"):
        return disable_wifi()
    else:
        return enable_wifi()


def list_wifi_networks() -> Tuple[bool, str]:
    """List available WiFi networks."""
    success, output = _run_netsh(["wlan", "show", "networks"])
    
    if not success:
        return False, "Could not scan WiFi networks"
    
    networks = []
    current_network = {}
    
    for line in output.split("\n"):
        line = line.strip()
        if line.startswith("SSID") and "BSSID" not in line:
            if current_network:
                networks.append(current_network)
            ssid = line.split(":")[1].strip() if ":" in line else ""
            current_network = {"ssid": ssid}
        elif "Signal" in line and ":" in line:
            current_network["signal"] = line.split(":")[1].strip()
        elif "Authentication" in line and ":" in line:
            current_network["security"] = line.split(":")[1].strip()
    
    if current_network:
        networks.append(current_network)
    
    # Filter out empty SSIDs
    networks = [n for n in networks if n.get("ssid")]
    
    if not networks:
        return True, "No WiFi networks found"
    
    lines = ["📶 Available WiFi Networks:"]
    for n in networks[:10]:  # Limit to 10
        signal = n.get("signal", "?")
        security = n.get("security", "")
        lock = "🔒" if "WPA" in security or "WEP" in security else "🔓"
        lines.append(f"  {lock} {n['ssid']} ({signal})")
    
    return True, "\n".join(lines)


def connect_wifi(ssid: str, password: str = None) -> Tuple[bool, str]:
    """Connect to a WiFi network."""
    try:
        if password:
            # Create a temporary profile
            profile_xml = f'''<?xml version="1.0"?>
<WLANProfile xmlns="http://www.microsoft.com/networking/WLAN/profile/v1">
    <name>{ssid}</name>
    <SSIDConfig>
        <SSID>
            <name>{ssid}</name>
        </SSID>
    </SSIDConfig>
    <connectionType>ESS</connectionType>
    <connectionMode>auto</connectionMode>
    <MSM>
        <security>
            <authEncryption>
                <authentication>WPA2PSK</authentication>
                <encryption>AES</encryption>
                <useOneX>false</useOneX>
            </authEncryption>
            <sharedKey>
                <keyType>passPhrase</keyType>
                <protected>false</protected>
                <keyMaterial>{password}</keyMaterial>
            </sharedKey>
        </security>
    </MSM>
</WLANProfile>'''
            
            import tempfile
            import os
            
            # Write profile to temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
                f.write(profile_xml)
                profile_path = f.name
            
            try:
                # Add profile
                subprocess.run(
                    ["netsh", "wlan", "add", "profile", f"filename={profile_path}"],
                    capture_output=True,
                    timeout=10
                )
            finally:
                os.unlink(profile_path)
        
        # Connect to the network
        result = subprocess.run(
            ["netsh", "wlan", "connect", f"name={ssid}"],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if result.returncode == 0:
            return True, f"📶 Connected to {ssid}"
        else:
            return False, f"Failed to connect to {ssid}"
            
    except Exception as e:
        return False, f"Error connecting: {e}"


def disconnect_wifi() -> Tuple[bool, str]:
    """Disconnect from current WiFi network."""
    try:
        result = subprocess.run(
            ["netsh", "wlan", "disconnect"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            return True, "📴 Disconnected from WiFi"
        else:
            return False, "Failed to disconnect"
            
    except Exception as e:
        return False, f"Error disconnecting: {e}"


# ==================== Bluetooth Functions ====================

def get_bluetooth_status() -> Dict:
    """Get Bluetooth status using PowerShell."""
    try:
        # Use PowerShell to check Bluetooth status
        result = subprocess.run(
            ["powershell", "-Command", 
             "Get-PnpDevice | Where-Object {$_.Class -eq 'Bluetooth'} | Select-Object Status, FriendlyName | ConvertTo-Json"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0 and result.stdout.strip():
            import json
            devices = json.loads(result.stdout)
            if not isinstance(devices, list):
                devices = [devices]
            
            enabled = any(d.get("Status") == "OK" for d in devices)
            return {
                "available": True,
                "enabled": enabled,
                "devices": devices
            }
        
        return {"available": False, "enabled": False}
        
    except Exception as e:
        return {"available": False, "enabled": False, "error": str(e)}


def enable_bluetooth() -> Tuple[bool, str]:
    """Enable Bluetooth - requires admin privileges."""
    return False, "⚠️ Bluetooth enable/disable requires admin privileges.\n💡 Tip: Use Windows Settings (Win+I > Bluetooth) or Action Center (Win+A) to toggle Bluetooth."


def disable_bluetooth() -> Tuple[bool, str]:
    """Disable Bluetooth - requires admin privileges."""
    return False, "⚠️ Bluetooth enable/disable requires admin privileges.\n💡 Tip: Use Windows Settings (Win+I > Bluetooth) or Action Center (Win+A) to toggle Bluetooth."


def toggle_bluetooth() -> Tuple[bool, str]:
    """Toggle Bluetooth on/off."""
    status = get_bluetooth_status()
    
    if status.get("enabled"):
        return disable_bluetooth()
    else:
        return enable_bluetooth()


def list_bluetooth_devices() -> Tuple[bool, str]:
    """List paired Bluetooth devices."""
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             "Get-PnpDevice | Where-Object {$_.Class -eq 'Bluetooth'} | Select-Object FriendlyName, Status | ConvertTo-Json"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0 and result.stdout.strip():
            import json
            devices = json.loads(result.stdout)
            if not isinstance(devices, list):
                devices = [devices]
            
            lines = ["🔵 Bluetooth Devices:"]
            for d in devices:
                status = "✓" if d.get("Status") == "OK" else "✗"
                lines.append(f"  {status} {d.get('FriendlyName', 'Unknown')}")
            
            return True, "\n".join(lines)
        
        return True, "No Bluetooth devices found"
        
    except Exception as e:
        return False, f"Error listing devices: {e}"


# ==================== Convenience Functions ====================

def wifi_on() -> Tuple[bool, str]:
    """Turn WiFi on."""
    return enable_wifi()


def wifi_off() -> Tuple[bool, str]:
    """Turn WiFi off."""
    return disable_wifi()


def bluetooth_on() -> Tuple[bool, str]:
    """Turn Bluetooth on."""
    return enable_bluetooth()


def bluetooth_off() -> Tuple[bool, str]:
    """Turn Bluetooth off."""
    return disable_bluetooth()


def network_status() -> str:
    """Get status of WiFi and Bluetooth."""
    wifi = get_wifi_status()
    bt = get_bluetooth_status()
    
    lines = ["📡 Network Status:"]
    
    # WiFi status
    if wifi.get("connected"):
        lines.append(f"  📶 WiFi: Connected to {wifi.get('ssid', 'Unknown')} ({wifi.get('signal', '?')})")
    elif wifi.get("enabled"):
        lines.append("  📶 WiFi: On (not connected)")
    else:
        lines.append("  📴 WiFi: Off")
    
    # Bluetooth status
    if bt.get("enabled"):
        lines.append("  🔵 Bluetooth: On")
    elif bt.get("available"):
        lines.append("  ⚫ Bluetooth: Off")
    else:
        lines.append("  ⚪ Bluetooth: Not available")
    
    return "\n".join(lines)
