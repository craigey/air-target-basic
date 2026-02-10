# 🎥 Logitech 925e Camera Controls - Complete Setup

## ✅ Your Camera: Logitech 925e
The Logitech 925e supports advanced V4L2 controls including:
- ✅ Brightness
- ✅ Contrast
- ✅ Saturation
- ✅ Sharpness
- ✅ Gain (ISO)
- ✅ Auto/Manual Focus
- ✅ Backlight Compensation
- ✅ Power Line Frequency (50Hz/60Hz flicker reduction)
- ✅ White Balance
- ✅ Exposure

---

## 🔧 Installation

### Step 1: Install v4l-utils
```bash
sudo apt update
sudo apt install v4l-utils
```

### Step 2: Verify Installation
```bash
v4l2-ctl --version
# Should show: v4l2-ctl 1.x.x
```

### Step 3: Check Camera Support
```bash
# List your camera
v4l2-ctl --list-devices

# Should show something like:
# Logi C925e (usb-...):
#     /dev/video0
#     /dev/video1

# List all controls for camera 0
v4l2-ctl -d /dev/video0 -L

# You should see output like:
#                brightness 0x00980900 (int)    : min=-64 max=64 step=1 default=0 value=0
#                  contrast 0x00980901 (int)    : min=0 max=64 step=1 default=32 value=32
#                saturation 0x00980902 (int)    : min=0 max=128 step=1 default=64 value=64
#                 sharpness 0x0098090b (int)    : min=0 max=255 step=1 default=128 value=128
#                      gain 0x00980913 (int)    : min=0 max=255 step=1 default=0 value=0
# ... and many more
```

---

## 🧪 Testing Controls Manually

### Test Brightness
```bash
# Get current value
v4l2-ctl -d /dev/video0 -C brightness

# Set brightness to 20
v4l2-ctl -d /dev/video0 -c brightness=20

# Reset to default (0)
v4l2-ctl -d /dev/video0 -c brightness=0
```

### Test Contrast
```bash
v4l2-ctl -d /dev/video0 -c contrast=40
```

### Test Saturation
```bash
# 0 = grayscale, 128 = max color
v4l2-ctl -d /dev/video0 -c saturation=100
```

### Test Sharpness
```bash
v4l2-ctl -d /dev/video0 -c sharpness=200
```

### Test Focus
```bash
# Disable auto-focus
v4l2-ctl -d /dev/video0 -c focus_auto=0

# Set manual focus
v4l2-ctl -d /dev/video0 -c focus_absolute=50

# Re-enable auto-focus
v4l2-ctl -d /dev/video0 -c focus_auto=1
```

### Test Backlight Compensation
```bash
# Enable backlight compensation (useful if target is lit from behind)
v4l2-ctl -d /dev/video0 -c backlight_compensation=1

# Disable
v4l2-ctl -d /dev/video0 -c backlight_compensation=0
```

### Test Power Line Frequency
```bash
# Disable (0)
v4l2-ctl -d /dev/video0 -c power_line_frequency=0

# 50 Hz (Europe, Asia, Africa, Australia)
v4l2-ctl -d /dev/video0 -c power_line_frequency=1

# 60 Hz (North America, South America)
v4l2-ctl -d /dev/video0 -c power_line_frequency=2
```

---

## 📋 Deploy to Your System

### Step 1: Copy Files
```bash
cd ~/air-target-basic-main

# Copy the V4L2 control functions
# Add contents of v4l2_controls.py to app.py

# Copy the updated camera page
cp camera-v4l2.html templates/camera.html
```

### Step 2: Verify v4l-utils in Python
```bash
# Test from Python
python3 << 'EOF'
import subprocess
result = subprocess.run(["v4l2-ctl", "--version"], capture_output=True, text=True)
print(result.stdout)
EOF
```

### Step 3: Restart Application
```bash
cd ~/air-target-basic-main
source venv/bin/activate
python app.py
```

---

## 🎛️ Available Controls on Logitech 925e

### Basic Controls:
| Control | Range | Default | Description |
|---------|-------|---------|-------------|
| Brightness | -64 to 64 | 0 | Overall image brightness |
| Contrast | 0 to 64 | 32 | Difference between light/dark |
| Saturation | 0 to 128 | 64 | Color intensity (0=grayscale) |
| Sharpness | 0 to 255 | 128 | Edge definition |
| Gain | 0 to 255 | 0 | ISO sensitivity (higher=brighter+noisier) |

### Focus Controls:
| Control | Range | Default | Description |
|---------|-------|---------|-------------|
| Focus Auto | 0 or 1 | 1 | Auto-focus on/off |
| Focus Absolute | 0 to 255 | varies | Manual focus position |

### Advanced Controls:
| Control | Options | Default | Description |
|---------|---------|---------|-------------|
| Backlight Compensation | 0 or 1 | 0 | Compensate for backlighting |
| Power Line Frequency | 0/1/2 | 2 | Flicker reduction (0=off, 1=50Hz, 2=60Hz) |
| Exposure Auto | 1/3 | 3 | Auto exposure mode |
| White Balance Auto | 0 or 1 | 1 | Auto white balance |

---

## 🔍 Troubleshooting

### Issue: "v4l2-ctl: command not found"
**Solution:**
```bash
sudo apt install v4l-utils
```

### Issue: "Cannot open device /dev/video0"
**Solution:**
```bash
# Check permissions
ls -l /dev/video0
# Should show: crw-rw---- 1 root video

# Add user to video group
sudo usermod -a -G video $USER

# Logout and login again
```

### Issue: Controls don't work
**Solution:**
```bash
# Check if camera supports the control
v4l2-ctl -d /dev/video0 -L | grep brightness

# If not listed, camera doesn't support it
# The Logitech 925e DOES support all these controls
```

### Issue: Changes don't appear in video
**Reason:** Some controls require time to take effect
**Solution:** Wait 1-2 seconds after adjusting

### Issue: Python subprocess error
**Solution:**
```bash
# Make sure v4l-utils is installed
which v4l2-ctl

# Test manually first
v4l2-ctl -d /dev/video0 -c brightness=10
```

---

## 🎯 Optimal Settings for Target Shooting

### Recommended Starting Point:
```bash
# For well-lit indoor range
v4l2-ctl -d /dev/video0 -c brightness=0
v4l2-ctl -d /dev/video0 -c contrast=40
v4l2-ctl -d /dev/video0 -c saturation=80
v4l2-ctl -d /dev/video0 -c sharpness=200
v4l2-ctl -d /dev/video0 -c gain=0
v4l2-ctl -d /dev/video0 -c power_line_frequency=2  # 60Hz for USA
v4l2-ctl -d /dev/video0 -c backlight_compensation=0

# Disable auto-focus (important for target shooting!)
v4l2-ctl -d /dev/video0 -c focus_auto=0
v4l2-ctl -d /dev/video0 -c focus_absolute=50
# Adjust focus_absolute while watching preview until target is sharp
```

### For Low Light:
```bash
# Increase gain (but expect more noise)
v4l2-ctl -d /dev/video0 -c gain=100

# Increase brightness
v4l2-ctl -d /dev/video0 -c brightness=20
```

### For Backlit Target:
```bash
# Enable backlight compensation
v4l2-ctl -d /dev/video0 -c backlight_compensation=1
```

---

## 🌐 Web Interface Usage

After deployment, you can:

1. **Go to Camera page** (`/camera`)
2. **See all sliders** with live values from camera
3. **Adjust any control** - changes apply immediately
4. **Click "Refresh Values"** to reload current settings from camera
5. **Click "Reset to Defaults"** to reset all controls
6. **Focus:**
   - Click "Auto Focus" button to toggle auto/manual
   - When manual, slider appears for precise focus control
7. **Power Line Frequency:**
   - Set to 50 Hz if in Europe/Asia/Africa/Australia
   - Set to 60 Hz if in North/South America
   - Reduces LED flicker in video

---

## 📊 Control Ranges by Camera

Different Logitech models have different ranges:

### Logitech C925e (Your Camera):
- Brightness: -64 to 64
- Contrast: 0 to 64
- Saturation: 0 to 128
- Sharpness: 0 to 255
- Gain: 0 to 255
- Focus: 0 to 255

### Other Models (for reference):
**C920:**
- Similar ranges to C925e

**C930e:**
- Same as C925e plus extended FOV options

---

## ✅ Verification Checklist

After setup:
- [ ] v4l-utils installed (`v4l2-ctl --version`)
- [ ] Can list camera controls (`v4l2-ctl -d /dev/video0 -L`)
- [ ] Can manually set brightness (`v4l2-ctl -d /dev/video0 -c brightness=20`)
- [ ] Python subprocess works (test in script)
- [ ] Web interface shows sliders on Camera page
- [ ] Moving sliders changes camera image
- [ ] "Refresh Values" button loads current settings
- [ ] "Reset to Defaults" works
- [ ] Focus controls work (auto/manual)
- [ ] Power line frequency reduces flicker

---

## 💡 Pro Tips

### 1. **Disable Auto-Focus for Target Shooting**
Auto-focus can hunt during shooting. Set manual focus once, lock it.

### 2. **Use Power Line Frequency**
Set to your region's frequency (50Hz or 60Hz) to eliminate LED flicker.

### 3. **Increase Sharpness**
Higher sharpness (180-220) helps detect small pellet holes.

### 4. **Low Gain in Good Light**
Keep gain at 0 for clean image. Only increase in dim lighting.

### 5. **Moderate Saturation**
Too much saturation makes detection harder. Keep around 60-80.

### 6. **Save Your Settings**
Once you find good values, note them down for quick setup next time.

---

## 🚀 Quick Start

```bash
# Install
sudo apt install v4l-utils

# Test
v4l2-ctl -d /dev/video0 -L

# Add code to app.py
# Copy camera-v4l2.html to templates/

# Restart
python app.py

# Visit: http://192.168.0.84:5000/camera
# Adjust sliders and see immediate results!
```

---

## 📝 Summary

**Your Logitech 925e fully supports:**
- ✅ Brightness, Contrast, Saturation, Sharpness
- ✅ Gain (ISO sensitivity)
- ✅ Auto/Manual Focus
- ✅ Backlight Compensation
- ✅ Power Line Frequency (flicker reduction)
- ✅ All adjustable via web interface!

**Ready to use! Perfect for target scoring! 🎯**
