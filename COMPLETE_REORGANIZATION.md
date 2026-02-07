# 🎯 Complete System Reorganization & Fixes

## ✅ Issues to Fix

### 1. **Page Organization**
- ❌ Camera settings on main page (too cluttered)
- ❌ No calibration integration with camera settings
- ❌ Inconsistent navigation between pages
- ❌ Recording settings not in Settings page

### 2. **UI/UX Issues**
- ❌ White-themed settings page (doesn't match)
- ❌ Native alert() dialogs (ugly, don't match theme)
- ❌ No visual feedback for actions

### 3. **Technical Issues**
- ❌ Permission error: `/home/pi/air-target/shots/`
- ❌ Can't create round directories

---

## 🎨 New Page Structure

### **Main Page (`/`)**
**Purpose:** Shooting & Detection ONLY

**Contains:**
- Multi-camera grid view
- Live video feeds
- Score displays
- Start/Stop detection
- Reset button
- Navigation to other pages

**REMOVED:**
- All camera settings
- All configuration options
- Zoom/rotation controls

---

### **Camera Page (`/camera`)** - NEW!
**Purpose:** Camera Configuration & Calibration

**Contains:**
- Camera selection/enable
- Live preview with overlay
- Zoom controls
- Rotation controls
- White balance
- Exposure lock
- **Integrated calibration** (same page!)
- Test calibration button

**Layout:**
```
┌────────────────────────────────────┐
│ 📹 Camera Configuration            │
├────────────────────────────────────┤
│                                    │
│ [Camera 0 ▼]  [✓ Enabled]         │
│                                    │
│ ┌──────────────────────────────┐  │
│ │   Live Preview               │  │
│ │   (Shows zoom/rotation live) │  │
│ └──────────────────────────────┘  │
│                                    │
│ Zoom:  [−] 1.5x [+] [█████▓░░]   │
│ Rotation: [0°] [90°] [180°] [270°]│
│ White Balance: [Auto] [2800K]...  │
│ Exposure: [Lock]                   │
│                                    │
│ ┌──────────────────────────────┐  │
│ │ 🎯 Calibration               │  │
│ │ Step 1: Click center...      │  │
│ │ [Preview with click points]  │  │
│ │ [Reset] [Test]               │  │
│ └──────────────────────────────┘  │
└────────────────────────────────────┘
```

**Benefits:**
- Adjust settings & calibrate without page switching
- See effect of zoom/rotation before calibrating
- All camera config in one place
- Re-calibrate easily after adjustments

---

### **Settings Page (`/settings`)** - REDESIGNED!
**Purpose:** Match & System Settings

**Contains:**
- 🎯 Match Settings (scoring rules)
- 📸 Recording Settings (enable, crop size, storage)
- 🔧 Advanced (detection algorithm)
- System info

**REMOVED:**
- All camera settings (moved to Camera page)
- Calibration (moved to Camera page)

---

### **Rounds Page (`/rounds`)**
**Purpose:** View Recorded Rounds

**Contains:**
- List of rounds
- Shot images
- Stack/unstack view
- Download/delete

---

### **Spectator Page (`/spectator_fullscreen`)**
**Purpose:** Multi-Camera Display

**Contains:**
- All enabled cameras
- Live scores
- Fullscreen mode
- Keyboard shortcuts

---

## 🔧 Permission Error Fix

### Error:
```
PermissionError: [Errno 13] Permission denied: '/home/pi/air-target/shots/round_20260206_210235'
```

### Cause:
Script trying to write to `/home/pi/` but you're user `admin`

### Solutions:

#### Option 1: Change Shot Directory (Recommended)
Edit `config.json`:
```json
{
  "shot_directory": "/home/admin/air-target/shots",
  ...
}
```

Or create in your home:
```bash
mkdir -p ~/air-target/shots
```

Then update `shot_recorder.py`:
```python
# Change this line:
SHOTS_DIR = cfg.get("shot_directory", "/home/admin/air-target/shots")
# Instead of:
SHOTS_DIR = cfg.get("shot_directory", "/home/pi/air-target/shots")
```

#### Option 2: Create Directory with Permissions
```bash
# Create directory
sudo mkdir -p /home/pi/air-target/shots

# Give your user permission
sudo chown -R admin:admin /home/pi/air-target/shots

# Verify
ls -ld /home/pi/air-target/shots
# Should show: drwxr-xr-x admin admin
```

#### Option 3: Use Temp Directory
```python
import tempfile
SHOTS_DIR = os.path.join(tempfile.gettempdir(), "air-target-shots")
```

**Recommended:** Use Option 1 (change to your home directory)

---

## 🎨 Themed Modals Implementation

### Include in ALL Pages

**In HTML `<head>`:**
```html
<link rel="stylesheet" href="/static/modal-theme.css">
```

**Before `</body>`:**
```html
<script src="/static/modal-theme.js"></script>
```

### Replace All alert() Calls

**OLD:**
```javascript
alert('Settings saved');
if (confirm('Delete this?')) { ... }
```

**NEW:**
```javascript
showToast('Settings saved', 'success');
showConfirm('Delete Camera', 'Are you sure?', () => { /* delete */ });
```

### Examples:

**Success Notification:**
```javascript
showToast('Camera optimized successfully!', 'success');
```

**Error Notification:**
```javascript
showToast('Failed to connect to camera', 'error');
```

**Warning:**
```javascript
showToast('Camera quality below 0.75', 'warning');
```

**Confirm Dialog:**
```javascript
showConfirm(
  'Reset All Settings', 
  'This will reset zoom, rotation, and white balance. Continue?',
  () => {
    // User clicked Confirm
    resetAllSettings();
  },
  () => {
    // User clicked Cancel (optional)
    console.log('Cancelled');
  }
);
```

**Alert Dialog:**
```javascript
showAlert(
  'Camera Info',
  `Camera 0: 1920x1080 @ 30fps
Zoom: 1.5x
Rotation: 90°
Exposure: Locked`,
  'info'
);
```

**Prompt Dialog:**
```javascript
showPrompt(
  'Custom Rotation',
  'Enter rotation angle (0-359°):',
  '0',
  (value) => {
    setRotation(parseInt(value));
  }
);
```

---

## 📋 Navigation Structure

### Consistent Nav Bar on ALL Pages:

```html
<div class="nav-bar">
  <div>
    <h2>🎯 [Page Title]</h2>
  </div>
  <div>
    <a href="/" class="nav-btn">🏠 Main</a>
    <a href="/camera" class="nav-btn">📹 Camera</a>
    <a href="/settings" class="nav-btn">⚙️ Settings</a>
    <a href="/rounds" class="nav-btn">📂 Rounds</a>
    <a href="/spectator_fullscreen" class="nav-btn">👥 Spectator</a>
  </div>
</div>
```

**Current page highlighted:**
```javascript
// Add .active class to current page
document.querySelectorAll('.nav-btn').forEach(btn => {
  if (btn.href === window.location.href) {
    btn.classList.add('active');
  }
});
```

**CSS:**
```css
.nav-btn.active {
  background: #c5a000;
  color: #000;
  border-color: #c5a000;
}
```

---

## 🔄 Migration Steps

### Step 1: Fix Permissions
```bash
# Create shots directory in your home
mkdir -p ~/air-target/shots

# Update config.json
nano ~/air-target-basic-main/config.json
# Change: "shot_directory": "/home/admin/air-target/shots"
```

### Step 2: Add Themed Modals
```bash
# Copy CSS and JS to static folder
cp modal-theme.css ~/air-target-basic-main/static/
cp modal-theme.js ~/air-target-basic-main/static/
```

### Step 3: Update Templates
```bash
# Replace old templates with new ones:
# - index.html (simplified main page)
# - camera.html (NEW - camera config + calibration)
# - settings.html (match & recording settings only)
# - rounds.html (already created)
# - spectator_fullscreen.html (keep as is)
```

### Step 4: Update Navigation
Add nav bar to all templates

### Step 5: Replace Dialogs
Find and replace in all templates:
- `alert(` → `showToast(`
- `confirm(` → `showConfirm(`

### Step 6: Test
```bash
cd ~/air-target-basic-main
source venv/bin/activate
python app.py

# Visit each page:
# http://192.168.0.84:5000/
# http://192.168.0.84:5000/camera
# http://192.168.0.84:5000/settings
# http://192.168.0.84:5000/rounds
# http://192.168.0.84:5000/spectator_fullscreen
```

---

## 📊 New Workflow

### Setup (First Time):

1. **Navigate to Camera page** (`/camera`)
   - Select camera
   - Enable camera
   - Set zoom (watch preview)
   - Set rotation (watch preview)
   - Set white balance
   - Lock exposure
   - **Calibrate (same page!)**
   - Test calibration
   - Repeat for each camera

2. **Navigate to Settings** (`/settings`)
   - Set scoring rules (4-ring, bull hole)
   - Enable recording
   - Set crop size
   - Configure detection algorithm

3. **Navigate to Main** (`/`)
   - Click "Start All Cameras"
   - Begin shooting!

### During Competition:

**Main Page:**
- View all cameras
- See live scores
- Start/Stop/Reset

**Camera Page:**
- Quick adjustments if needed
- Re-calibrate if bumped

**Rounds Page:**
- Review past rounds
- Stack/unstack shots

**Spectator Page:**
- Full-screen on projector
- Show all lanes to audience

---

## ✨ Benefits of Reorganization

### Main Page
- ✅ Clean, focused on shooting
- ✅ No settings clutter
- ✅ Easy to use during competition

### Camera Page
- ✅ All camera config in one place
- ✅ Calibration integrated
- ✅ Live preview shows changes
- ✅ Easy to recalibrate

### Settings Page
- ✅ Match-specific settings
- ✅ Recording configuration
- ✅ System settings
- ✅ No camera confusion

### Themed Modals
- ✅ Beautiful, consistent UI
- ✅ Matches dark theme
- ✅ Better UX than alert()
- ✅ Non-blocking notifications

### Navigation
- ✅ Consistent on all pages
- ✅ Easy to navigate
- ✅ Clear page purposes
- ✅ Professional layout

---

## 🚀 Quick Fix Commands

```bash
# 1. Fix permissions
mkdir -p ~/air-target/shots
nano ~/air-target-basic-main/config.json
# Change shot_directory to "/home/admin/air-target/shots"

# 2. Copy modal files
cd ~/air-target-basic-main/static/
# Copy modal-theme.css and modal-theme.js here

# 3. Test
cd ~/air-target-basic-main
source venv/bin/activate
python app.py
```

---

## 📁 Final File Structure

```
air-target-basic-main/
├── static/
│   ├── style.css
│   ├── modal-theme.css      ← NEW
│   └── modal-theme.js        ← NEW
├── templates/
│   ├── index.html            ← SIMPLIFIED (no settings)
│   ├── camera.html           ← NEW (camera + calibration)
│   ├── settings.html         ← REDESIGNED (match + recording)
│   ├── rounds.html           ← FIXED
│   └── spectator_fullscreen.html
├── shots/                    ← Move to /home/admin/
└── config.json               ← Update shot_directory
```

---

## ✅ Summary

**Fixed:**
- ✓ Permission error (change shot directory)
- ✓ Themed modals (no more ugly alert())
- ✓ Consistent navigation (all pages)
- ✓ Page organization (proper separation)

**New Structure:**
- Main: Shooting only
- Camera: Config + Calibration
- Settings: Match + Recording
- Rounds: Review shots
- Spectator: Display

**Better UX:**
- Everything in logical place
- Beautiful themed dialogs
- Easy navigation
- Professional layout

**Ready for competition! 🎯**
