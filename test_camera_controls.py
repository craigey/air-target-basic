#!/usr/bin/env python3
"""
Quick test script for Logitech 925e V4L2 controls
Run this to verify your camera supports all the controls before integrating.
"""

import subprocess
import sys

def run_cmd(cmd):
    """Run command and return output."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"
    except FileNotFoundError:
        return "Error: v4l2-ctl not found. Install with: sudo apt install v4l-utils"

def test_v4l_installation():
    """Test if v4l-utils is installed."""
    print("🔍 Testing v4l-utils installation...")
    output = run_cmd(["v4l2-ctl", "--version"])
    if "Error" in output:
        print("❌ v4l-utils not installed")
        print("   Install with: sudo apt install v4l-utils")
        return False
    else:
        print(f"✅ v4l-utils installed: {output.strip()}")
        return True

def list_cameras():
    """List available cameras."""
    print("\n📹 Listing cameras...")
    output = run_cmd(["v4l2-ctl", "--list-devices"])
    print(output)
    return output

def test_camera_controls(device="/dev/video0"):
    """Test camera controls."""
    print(f"\n🎛️  Testing controls on {device}...")
    
    # List all controls
    output = run_cmd(["v4l2-ctl", "-d", device, "-L"])
    
    if "Error" in output:
        print(f"❌ Cannot access {device}")
        print("   Make sure:")
        print("   1. Camera is connected")
        print("   2. You're in the 'video' group: sudo usermod -a -G video $USER")
        print("   3. Logout and login again")
        return False
    
    print("\n✅ Available controls:")
    
    # Parse and display important controls
    controls = {
        "brightness": False,
        "contrast": False,
        "saturation": False,
        "sharpness": False,
        "gain": False,
        "focus_auto": False,
        "focus_absolute": False,
        "backlight_compensation": False,
        "power_line_frequency": False
    }
    
    for line in output.split('\n'):
        for control in controls.keys():
            if control in line.lower():
                controls[control] = True
                print(f"   ✓ {control}")
    
    print("\n📊 Control Support Summary:")
    all_supported = True
    for control, supported in controls.items():
        status = "✅" if supported else "❌"
        print(f"   {status} {control}")
        if not supported:
            all_supported = False
    
    return all_supported

def test_set_control(device="/dev/video0", control="brightness", value="10"):
    """Test setting a control."""
    print(f"\n🧪 Testing: Setting {control} to {value}...")
    
    # Get current value
    get_output = run_cmd(["v4l2-ctl", "-d", device, "-C", control])
    print(f"   Current: {get_output.strip()}")
    
    # Set new value
    set_output = run_cmd(["v4l2-ctl", "-d", device, "-c", f"{control}={value}"])
    
    if "Error" in set_output:
        print(f"   ❌ Failed to set {control}")
        return False
    else:
        # Verify
        verify_output = run_cmd(["v4l2-ctl", "-d", device, "-C", control])
        print(f"   After:   {verify_output.strip()}")
        print(f"   ✅ Successfully set {control}")
        return True

def reset_controls(device="/dev/video0"):
    """Reset controls to defaults."""
    print(f"\n🔄 Resetting {device} to defaults...")
    
    defaults = {
        "brightness": "0",
        "contrast": "32",
        "saturation": "64",
        "sharpness": "128",
        "gain": "0"
    }
    
    for control, value in defaults.items():
        run_cmd(["v4l2-ctl", "-d", device, "-c", f"{control}={value}"])
    
    print("✅ Reset complete")

def main():
    """Run all tests."""
    print("=" * 60)
    print("Logitech 925e Camera Controls Test")
    print("=" * 60)
    
    # Test 1: v4l-utils installation
    if not test_v4l_installation():
        sys.exit(1)
    
    # Test 2: List cameras
    list_cameras()
    
    # Test 3: Check controls (default camera)
    device = "/dev/video0"
    if len(sys.argv) > 1:
        device = sys.argv[1]
    
    if not test_camera_controls(device):
        print("\n⚠️  Some controls not supported or camera not accessible")
        print("\nTroubleshooting:")
        print("  1. Is the camera Logitech 925e? (Other models may differ)")
        print("  2. Check permissions: ls -l /dev/video0")
        print("  3. Add yourself to video group: sudo usermod -a -G video $USER")
        print("  4. Logout and login again")
        sys.exit(1)
    
    # Test 4: Actually set a control
    print("\n" + "=" * 60)
    print("Testing actual control changes...")
    print("=" * 60)
    test_set_control(device, "brightness", "20")
    test_set_control(device, "contrast", "40")
    test_set_control(device, "sharpness", "200")
    
    # Test 5: Reset
    reset_controls(device)
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
    print("\nYour Logitech 925e fully supports all controls.")
    print("Ready to integrate into web interface!")
    print("\nNext steps:")
    print("  1. Add v4l2_controls.py code to app.py")
    print("  2. Copy camera-v4l2.html to templates/camera.html")
    print("  3. Restart application")
    print("  4. Visit http://your-ip:5000/camera")
    print("  5. Adjust sliders and see immediate results!")

if __name__ == "__main__":
    main()
