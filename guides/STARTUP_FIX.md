# 🚀 Startup Guide - Fixing Camera & GPIO Errors

## ❌ Errors You're Seeing

### Error 1: GPIO RuntimeError
```
RuntimeError: Please set pin numbering mode using GPIO.setmode(GPIO.BOARD) or GPIO.setmode(GPIO.BCM)
```
**Cause:** Break-beam module trying to use GPIO before initialization  
**Fix:** Updated breakbeam.py to call setup_gpio() first

### Error 2: Camera Access Error
```
WARN: VIDEOIO(V4L2:/dev/video0): can't open camera by index
RuntimeError: ❌ Cannot open camera 0
```
**Cause:** Running with `sudo` blocks camera access for your user  
**Fix:** Add user to video group and run WITHOUT sudo

---

## ✅ Complete Fix

### Step 1: Add User to Video Group
```bash
# Add your user to video group (allows camera access)
sudo usermod -a -G video $USER

# Add to GPIO group (allows GPIO access without sudo)
sudo usermod -a -G gpio $USER

# Verify groups
groups $USER
# Should see: ... video gpio ...
```

### Step 2: LOGOUT and LOGIN Again
**IMPORTANT:** Groups only take effect after logout/login
```bash
# Logout
exit

# SSH back in
ssh admin@raspberrypi
```

### Step 3: Update breakbeam.py
Replace the file with the fixed version:
```bash
cp /path/to/fixed/breakbeam.py ~/air-target-basic-main/
```

### Step 4: Run WITHOUT sudo
```bash
cd ~/air-target-basic-main
source venv/bin/activate
python app.py  # NO sudo!
```

---

## 🔧 Alternative: Disable Break-Beam Temporarily

If you don't have a break-beam sensor connected, you can disable it:

### Option A: Comment Out Break-Beam in app.py
```python
# In app.py, find this line:
from breakbeam import watch_breakbeam
import threading
# threading.Thread(target=watch_breakbeam, daemon=True).start()  # Comment this out
```

### Option B: Modify config.json
```json
{
  "enable_breakbeam": false,
  ...
}
```

Then check in app.py:
```python
# Add this check
if cfg.get("enable_breakbeam", True):
    threading.Thread(target=watch_breakbeam, daemon=True).start()
```

---

## 🎯 Quick Fix Commands

Run these in order:

```bash
# 1. Add user to groups
sudo usermod -a -G video,gpio $USER

# 2. Check current permissions
ls -l /dev/video0
# Should show: crw-rw---- 1 root video ...

# 3. Verify video group exists
getent group video
# Should show: video:x:44:admin (or your username)

# 4. LOGOUT and back in
exit
# ... SSH back in ...

# 5. Test camera access (should work now)
v4l2-ctl --list-devices

# 6. Run app WITHOUT sudo
cd ~/air-target-basic-main
source venv/bin/activate
python app.py
```

---

## 🐛 Troubleshooting

### Camera Still Not Working?

**Check camera is detected:**
```bash
ls /dev/video*
# Should see: /dev/video0 /dev/video1 ...
```

**Check permissions:**
```bash
ls -l /dev/video0
# Should show: crw-rw---- 1 root video
```

**Test camera directly:**
```bash
# Install if needed
sudo apt-get install v4l-utils

# List cameras
v4l2-ctl --list-devices

# Test capture
ffmpeg -f v4l2 -i /dev/video0 -frames:v 1 test.jpg
```

**If still fails, set permissions manually (temporary):**
```bash
sudo chmod 666 /dev/video0
```

### GPIO Still Not Working?

**Check GPIO group exists:**
```bash
getent group gpio
# Should show: gpio:x:997:admin
```

**If gpio group doesn't exist:**
```bash
sudo groupadd -f --system gpio
sudo usermod -a -G gpio $USER
```

**Check udev rules:**
```bash
ls -l /etc/udev/rules.d/*gpio*
```

**Create GPIO udev rule if missing:**
```bash
sudo nano /etc/udev/rules.d/99-gpio.rules
```

Add:
```
SUBSYSTEM=="gpio", GROUP="gpio", MODE="0660"
SUBSYSTEM=="gpio*", PROGRAM="/bin/sh -c 'chown -R root:gpio /sys/class/gpio && chmod -R 770 /sys/class/gpio; chown -R root:gpio /sys/devices/virtual/gpio && chmod -R 770 /sys/devices/virtual/gpio'"
```

Reload:
```bash
sudo udevadm control --reload-rules
sudo udevadm trigger
```

---

## 📋 Correct Startup Procedure

### Every Time You Run:

```bash
# 1. Activate venv
cd ~/air-target-basic-main
source venv/bin/activate

# 2. Run WITHOUT sudo
python app.py

# 3. Open browser
# Navigate to: http://192.168.0.84:5000
```

### DO NOT:
- ❌ Run with `sudo python app.py`
- ❌ Use `sudo` at all (unless installing packages)
- ❌ Run as root user

### WHY:
- Camera devices (/dev/video*) are owned by `video` group
- Your user needs to be in `video` group
- Running with `sudo` switches to root user (not in video group)
- GPIO access needs `gpio` group membership

---

## ✅ Verification

After fixes, you should see:

```bash
$ python app.py

✅ Shot recorder initialized: /home/pi/air-target/shots
✅ Break-beam GPIO initialized
👁️ Break-beam watcher running
✅ Initialized camera 0
✅ All cameras ready: [0]
⚙️ Optimizing camera 0 settings...
✅ Camera 0 optimized
📸 Stabilizing exposure for camera 0...
✅ Exposure locked at 250.0
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://192.168.0.84:5000
```

**No errors! 🎉**

---

## 🔐 File Permissions Summary

### Camera Devices
```bash
# Should be:
crw-rw---- 1 root video /dev/video0

# Your user must be in 'video' group
groups $USER | grep video  # Should find it
```

### GPIO Devices
```bash
# Should be:
drwxrwx--- 2 root gpio /sys/class/gpio

# Your user must be in 'gpio' group
groups $USER | grep gpio  # Should find it
```

### Application Files
```bash
# Should be owned by you, not root
ls -l ~/air-target-basic-main/
# Should show: drwxr-xr-x admin admin ...
```

---

## 🆘 If Nothing Works

### Nuclear Option - Run in User Camera Mode
Modify camera_manager.py:

```python
# Add at top of init_cameras()
import os
os.environ['OPENCV_VIDEOIO_PRIORITY_V4L2'] = '0'
```

### Or Use GStreamer Backend
```python
# In camera_manager.py, init_cameras()
cap = cv2.VideoCapture(cam_id, cv2.CAP_GSTREAMER)
```

### Or Use PyCamera2 (Raspberry Pi specific)
```bash
pip install picamera2
```

Then modify to use picamera2 instead of OpenCV.

---

## 📞 Support Checklist

If you need help, provide:

```bash
# 1. User groups
groups

# 2. Camera devices
ls -l /dev/video*

# 3. Camera detection
v4l2-ctl --list-devices

# 4. Python/OpenCV version
python --version
python -c "import cv2; print(cv2.__version__)"

# 5. OS version
cat /etc/os-release

# 6. Full error output
python app.py 2>&1 | tee error.log
```

---

## ✨ Summary

**The Fix:**
1. Add user to `video` and `gpio` groups
2. Logout and back in
3. Use fixed breakbeam.py
4. Run WITHOUT sudo

**Why It Happened:**
- Camera requires `video` group membership
- GPIO requires `gpio` group membership  
- `sudo` runs as root (not in those groups)
- Break-beam wasn't initializing GPIO mode

**Result:**
- Camera works ✓
- GPIO works ✓
- No sudo needed ✓
- Clean startup ✓
