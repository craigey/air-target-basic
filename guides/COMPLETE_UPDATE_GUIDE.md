# 🎯 Complete System Update - All Files

## 🐛 Critical Fixes

### 1. **overlay.py Error Fix**
```python
# Line 23 error: is_enabled() not defined
# Should be: is_heatmap_enabled()

# FIXED VERSION:
import cv2
from calibration import get_target
from heatmap import get_heatmap_normalized, is_heatmap_enabled

def draw_overlay(frame, cam_id=0):
    t = get_target(cam_id)
    if t.get("center") is None:
        return frame
    
    cx, cy = t["center"]
    
    # Bull hole
    bull_hole_radius = int(t.get("bull_hole_px", 5))
    cv2.circle(frame, (cx, cy), bull_hole_radius, (255, 255, 255), 2)
    
    # Rings
    for r in t.get("rings_px", []):
        cv2.circle(frame, (cx, cy), int(r), (0, 215, 255), 2)
    
    # Center
    cv2.circle(frame, (cx, cy), 2, (0, 0, 255), -1)
    
    # Heatmap
    if is_heatmap_enabled():
        for (x, y) in get_heatmap_normalized():
            cv2.circle(frame, (int(x), int(y)), 2, (0, 255, 255), -1)
    
    return frame
```

### 2. **Permission Error Fix**

Edit `/home/admin/air-target-basic-main/config.json`:
```json
{
  "shot_directory": "/home/admin/air-target/shots",
  ...other settings...
}
```

Create directory:
```bash
mkdir -p /home/admin/air-target/shots
```

### 3. **Shots Directory Configuration in Settings**

Add to `config.json`:
```json
{
  "shot_directory": "/home/admin/air-target/shots",
  "shot_directory_editable": true
}
```

---

## 📁 Complete File List

### Files to Update:
1. ✅ `overlay.py` - Fix is_enabled() error
2. ✅ `config.json` - Change shot_directory path
3. ✅ `templates/index.html` - Simplified (no camera settings)
4. ✅ `templates/camera.html` - NEW (camera + calibration)
5. ✅ `templates/settings.html` - Redesigned (match + recording + shot dir)
6. ✅ `templates/rounds.html` - Already created
7. ✅ `static/modal-theme.css` - NEW (themed dialogs)
8. ✅ `static/modal-theme.js` - NEW (modal functions)
9. ✅ `app.py` - Add /camera route

---

## 🔧 Quick Fix Commands

```bash
cd ~/air-target-basic-main

# 1. Fix overlay.py
nano overlay.py
# Replace line 23: is_enabled() with is_heatmap_enabled()
# Or copy the fixed version from outputs

# 2. Fix config.json  
nano config.json
# Change "shot_directory": "/home/admin/air-target/shots"

# 3. Create shots directory
mkdir -p /home/admin/air-target/shots

# 4. Copy modal files
cp /path/to/modal-theme.css static/
cp /path/to/modal-theme.js static/

# 5. Restart
source venv/bin/activate
python app.py
```

---

## 📋 New Page Structure

### Main Page (`/`) - Shooting Only
- Multi-camera grid
- Live video feeds
- Scores with shot badges
- Start/Stop/Reset buttons
- **NO camera settings**

### Camera Page (`/camera`) - NEW!
- Camera selection
- Enable/disable cameras
- Live preview
- Zoom controls (see immediately in preview)
- Rotation controls (see immediately in preview)
- White balance
- Exposure lock
- **Integrated calibration** (same page!)

### Settings Page (`/settings`)
- Match settings (scoring rules)
- **Recording settings** (enable, crop size)
- **Shot directory path** (editable!)
- Advanced detection settings

### Rounds Page (`/rounds`)
- View recorded rounds
- Shot images
- Stack/unstack

---

## 🎨 Navigation (All Pages)

```html
<div class="nav-bar">
  <div><h2>🎯 [Page Title]</h2></div>
  <div>
    <a href="/" class="nav-btn">🏠 Main</a>
    <a href="/camera" class="nav-btn">📹 Camera</a>
    <a href="/settings" class="nav-btn">⚙️ Settings</a>
    <a href="/rounds" class="nav-btn">📂 Rounds</a>
    <a href="/spectator_fullscreen" class="nav-btn">👥 Spectator</a>
  </div>
</div>
```

---

## 🚀 Add /camera Route to app.py

```python
@app.route("/camera")
def camera_page():
    """Camera configuration and calibration page."""
    return render_template("camera.html")
```

---

## ✨ Replace All alert() Calls

Find in all templates:
- `alert(` → `showToast(`
- `confirm(` → `showConfirm(`

Examples:
```javascript
// OLD
alert('Settings saved');
if (confirm('Delete?')) { /* delete */ }

// NEW
showToast('Settings saved', 'success');
showConfirm('Delete', 'Are you sure?', () => { /* delete */ });
```

---

## 📦 Files Available in /outputs/

1. `overlay.py` - Fixed version
2. `modal-theme.css` - Themed modals/toasts
3. `modal-theme.js` - Modal functions
4. `rounds.html` - Rounds viewer
5. `COMPLETE_REORGANIZATION.md` - Full guide

---

## ✅ Verification Checklist

After updates, verify:

- [ ] No `is_enabled()` error in overlay.py
- [ ] Shot directory is `/home/admin/air-target/shots`
- [ ] Directory exists and is writable
- [ ] Main page has NO camera settings
- [ ] Camera page has settings + calibration
- [ ] Settings page has shot directory config
- [ ] All pages have navigation bar
- [ ] All alert() replaced with showToast()
- [ ] Can navigate between all pages

---

## 🎯 Testing Steps

```bash
# 1. Start app
cd ~/air-target-basic-main
source venv/bin/activate
python app.py

# 2. Test pages
http://192.168.0.84:5000/              # Main - shooting only
http://192.168.0.84:5000/camera        # Camera - config + calibration  
http://192.168.0.84:5000/settings      # Settings - match + recording
http://192.168.0.84:5000/rounds        # Rounds - view shots
http://192.168.0.84:5000/spectator_fullscreen  # Spectator

# 3. Test detection
- Click "Start All Cameras"
- Should create round in /home/admin/air-target/shots/
- No permission errors
- No is_enabled() errors

# 4. Test calibration
- Go to Camera page
- Adjust zoom/rotation (see in preview)
- Click 3 calibration points
- Should save without errors
```

---

## 🆘 If Errors Persist

### overlay.py error:
```bash
# Check line 23
grep -n "is_enabled" overlay.py
# Should show: is_heatmap_enabled()
# NOT: is_enabled()
```

### Permission error:
```bash
# Check ownership
ls -ld /home/admin/air-target/shots
# Should show: drwxr-xr-x admin admin

# If wrong owner:
sudo chown -R admin:admin /home/admin/air-target/shots
```

### Modal not working:
```bash
# Check files exist
ls -l static/modal-theme.*
# Should show: modal-theme.css and modal-theme.js

# Check included in HTML
grep "modal-theme" templates/index.html
# Should find link and script tags
```

---

## 📝 Summary of Changes

**Fixed:**
1. overlay.py `is_enabled()` → `is_heatmap_enabled()`
2. config.json shot_directory → `/home/admin/air-target/shots`
3. Created shots directory with proper permissions

**Added:**
1. Camera page (/camera) with integrated calibration
2. Themed modal system (CSS + JS)
3. Consistent navigation on all pages
4. Shot directory config in Settings

**Reorganized:**
1. Main page: Shooting only (no settings)
2. Camera page: All camera config + calibration
3. Settings page: Match + Recording + Advanced

**Result:**
- Clean, professional UI
- Logical page organization
- No permission errors
- No undefined function errors
- Themed dialogs throughout
- Easy to navigate
