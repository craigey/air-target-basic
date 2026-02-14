# TROUBLESHOOTING GUIDE - Video Feed & Scoring Issues

## Quick Fix Checklist

If you can't see the video feed on the main page or scores aren't showing:

### 1️⃣ Add Missing Files (MOST LIKELY ISSUE)

Your `detection.py` needs two files that don't exist:

```bash
# Copy these files to your project directory:
cp diagnostic_fixes/overlay.py ./
cp diagnostic_fixes/ai_classifier.py ./
```

**Why?** Your `detection.py` imports:
- `from overlay import draw_overlay`
- `from ai_classifier import classify_hit`

Without these files, detection.py crashes on import, so video feed won't work!

---

### 2️⃣ Replace index.html (Has Duplicate Code)

Your current `index.html` has duplicate function definitions which causes JavaScript errors:

```bash
# Backup and replace:
cp templates/index.html templates/index.html.backup
cp diagnostic_fixes/index.html templates/
```

**What was wrong:** 
- `viewMode` variable declared twice
- `toggleViewMode()` function defined twice

---

### 3️⃣ Run Diagnostic Script

```bash
cd /path/to/your/project
python diagnostic_fixes/diagnose.py
```

This will tell you exactly what's missing!

---

## Detailed Troubleshooting Steps

### Problem: "No Video Feed on Main Page"

**Step 1: Check Flask Console for Errors**

When you start `app.py`, look for import errors:
```
ModuleNotFoundError: No module named 'overlay'
ModuleNotFoundError: No module named 'ai_classifier'
```

**If you see these errors:**
→ Copy `overlay.py` and `ai_classifier.py` from diagnostic_fixes/

**Step 2: Check Browser Console (F12)**

Open browser DevTools (F12), go to Console tab.

Look for errors like:
```
GET http://localhost:5000/video/0 404 Not Found
Failed to load resource
```

**If you see 404 errors on `/video/0`:**
→ detection.py is crashing, see Step 1

**Step 3: Test Video Endpoint Directly**

In browser, go to: `http://localhost:5000/raw_video/0`

- **If this works:** Problem is with `/video/0` endpoint (detection issue)
- **If this fails:** Problem is with camera access

**Step 4: Check Camera Access**

```bash
# List cameras:
ls -l /dev/video*

# Should show:
# crw-rw---- 1 root video ... /dev/video0

# Add your user to video group:
sudo usermod -a -G video $USER

# Set permissions (temporary fix):
sudo chmod 666 /dev/video0

# Then logout and login again for group changes to take effect
```

**Step 5: Test Camera with v4l2-ctl**

```bash
# List camera capabilities:
v4l2-ctl -d /dev/video0 --list-formats-ext

# Capture a test frame:
v4l2-ctl -d /dev/video0 --set-fmt-video=width=1280,height=720 --stream-mmap --stream-count=1 --stream-to=test.jpg

# If this fails, camera hardware issue
# If this works, Python OpenCV issue
```

---

### Problem: "Can't See Scores"

**Step 1: Check if Detection is Running**

On main page, click "Start All Cameras" button.

- Button should change to "Stop All Cameras"
- Detection indicator should turn green

**If button doesn't change:**
→ Check Flask console for errors when clicking button

**Step 2: Check /hits Endpoint**

In browser or curl:
```bash
curl http://localhost:5000/hits
```

Should return JSON array:
```json
[]  # Empty if no shots
[{"x": 123, "y": 456, "score": 5, ...}]  # With shots
```

**If you get error:**
→ detection.py issue, check imports

**Step 3: Check Camera Calibration**

Scores won't work without calibration!

1. Go to Camera page: `http://localhost:5000/camera`
2. Scroll to "Target Calibration" section
3. Click 3 points on target
4. Should say "Calibration complete"

**If calibration doesn't work:**
→ Check that `calibration.py` exists

**Step 4: Test Scoring Module**

```python
# Test in Python console:
python3
>>> from scoring import score_hit
>>> score_hit(100, 100)  # Should return (score, confidence)
```

**If import fails:**
→ Check `scoring.py` exists

---

## Complete File Checklist

### Core Python Files (Must Exist):
- ✅ app.py
- ✅ detection.py
- ✅ calibration.py
- ✅ scoring.py
- ✅ camera_manager.py
- ✅ heatmap.py
- ✅ shot_recorder.py
- ⚠️ **overlay.py** (NEW - add from diagnostic_fixes/)
- ⚠️ **ai_classifier.py** (NEW - add from diagnostic_fixes/)

### HTML Templates (in templates/ directory):
- ✅ index.html (replace with fixed version)
- ✅ camera.html
- ✅ settings.html
- ✅ help.html
- ✅ calibrate.html
- ✅ rounds.html
- ✅ spectator_fullscreen.html

### Configuration:
- ✅ config.json

---

## Common Error Messages & Fixes

### Error: "ModuleNotFoundError: No module named 'overlay'"
**Fix:** Copy `overlay.py` from diagnostic_fixes/

### Error: "ModuleNotFoundError: No module named 'ai_classifier'"
**Fix:** Copy `ai_classifier.py` from diagnostic_fixes/

### Error: "Cannot open camera"
**Fix:** 
```bash
sudo chmod 666 /dev/video0
sudo usermod -a -G video $USER
```

### Error: "Permission denied" (white_balance_temperature)
**Fix:** This is normal, ignore it. Other controls will work.

### Error: Video shows "Not Calibrated"
**Fix:** Go to Camera page and calibrate (click 3 points on target)

### Error: Scores always 0 or None
**Fix:** 
1. Check calibration is complete
2. Make sure detection is started ("Start All Cameras" button)
3. Check target is visible in frame

---

## Step-by-Step Setup from Scratch

1. **Copy Missing Files:**
```bash
cp diagnostic_fixes/overlay.py ./
cp diagnostic_fixes/ai_classifier.py ./
cp diagnostic_fixes/index.html templates/
```

2. **Fix Permissions:**
```bash
sudo usermod -a -G video $USER
sudo chmod 666 /dev/video*
# Then logout and login
```

3. **Install Dependencies:**
```bash
pip install flask opencv-python numpy
sudo apt install v4l-utils
```

4. **Run Diagnostic:**
```bash
python diagnostic_fixes/diagnose.py
```

5. **Start Application:**
```bash
python app.py
```

6. **Open Browser:**
```
http://localhost:5000
```

7. **Calibrate Camera:**
- Go to Camera page
- Click 3 points on target (center, bull edge, outer edge)
- Should say "Calibration complete"

8. **Test Detection:**
- Go to Main page
- Click "Start All Cameras"
- Should see video feed with target rings overlay
- Fire pellet at target
- Should see score appear

---

## If Still Not Working

### Enable Debug Mode

Edit `app.py`, at the bottom change:
```python
app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
```

This shows detailed errors in Flask console.

### Check Flask Console Output

When starting app, you should see:
```
✅ Initialized camera 0
✅ All cameras ready: [0]
✅ v4l-utils is available
 * Running on http://0.0.0.0:5000
```

**If you see errors here, that's the problem!**

### Check Browser Console (F12)

Press F12 in browser, go to Console tab.

Look for:
- JavaScript errors (red text)
- Network errors (404, 500)
- Failed requests

### Test Individual Endpoints

```bash
# Test camera list:
curl http://localhost:5000/camera_urls

# Test video feed (should stream MJPEG):
curl http://localhost:5000/raw_video/0

# Test detection toggle:
curl http://localhost:5000/toggle

# Test hits:
curl http://localhost:5000/hits
```

---

## Still Stuck?

Run the diagnostic script and send the output:
```bash
python diagnostic_fixes/diagnose.py > diagnostic_output.txt
```

The diagnostic will tell you exactly what's wrong!

---

## Quick Reference

| Issue | Most Likely Cause | Quick Fix |
|-------|------------------|-----------|
| No video on main page | Missing overlay.py | Copy from diagnostic_fixes/ |
| No scores | Not calibrated | Calibrate in Camera page |
| Camera error | Permissions | sudo chmod 666 /dev/video0 |
| Import errors | Missing files | Run diagnose.py |
| Duplicate code errors | Old index.html | Replace with fixed version |

---

Generated: February 13, 2026
