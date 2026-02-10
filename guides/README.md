# 🎯 Complete System Update - README

## 📦 Files Provided

### Core Files:
1. **overlay.py** - Fixed `is_enabled()` → `is_heatmap_enabled()` error
2. **config.json** - Updated shot directory path
3. **app_routes.py** - New routes to add to app.py

### HTML Templates:
4. **index.html** - Simplified main page (shooting only)
5. **camera.html** - Camera configuration + calibration (NEW!)
6. **settings.html** - Match, recording & advanced settings (shot directory config)
7. **rounds.html** - Rounds viewer with dynamic path
8. **help.html** - System help & API documentation (NEW!)

### UI Components:
9. **modal-theme.css** - Themed modals/toasts
10. **modal-theme.js** - Modal JavaScript functions

---

## 🚀 Quick Deployment

### Option 1: Manual Copy (Recommended)

```bash
cd ~/air-target-basic-main

# 1. Backup
mkdir -p backups/$(date +%Y%m%d_%H%M%S)
cp overlay.py config.json templates/*.html backups/$(date +%Y%m%d_%H%M%S)/

# 2. Copy files
cp /path/to/outputs/overlay.py .
cp /path/to/outputs/config.json .
cp /path/to/outputs/*.html templates/
cp /path/to/outputs/modal-theme.* static/

# 3. Create shots directory
mkdir -p ~/air-target/shots

# 4. Add routes to app.py (see below)

# 5. Start
source venv/bin/activate
python app.py
```

---

## 📝 Adding Routes to app.py

Add these lines to your `app.py`:

```python
# After existing routes, add:

@app.route("/camera")
def camera_page():
    return render_template("camera.html")

@app.route("/help")
def help_page():
    return render_template("help.html")

@app.route("/get_config")
def get_config():
    with open('config.json', 'r') as f:
        config = json.load(f)
    return jsonify(config)

@app.route("/set_recording_config", methods=["POST"])
def set_recording_config():
    try:
        data = request.json
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        config['record_shots'] = data.get('record_shots', True)
        config['record_full_frame'] = data.get('record_full_frame', False)
        config['crop_size'] = data.get('crop_size', 200)
        
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/set_shot_directory", methods=["POST"])
def set_shot_directory():
    try:
        data = request.json
        directory = data.get('directory', '')
        os.makedirs(directory, exist_ok=True)
        
        with open('config.json', 'r') as f:
            config = json.load(f)
        config['shot_directory'] = directory
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        return jsonify({"success": True, "directory": directory})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/set_advanced_config", methods=["POST"])
def set_advanced_config():
    try:
        data = request.json
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        config['adaptive_threshold'] = data.get('adaptive_threshold', True)
        config['color_detection'] = data.get('color_detection', True)
        config['min_confidence'] = data.get('min_confidence', 0.6)
        config['shot_cooldown_frames'] = data.get('shot_cooldown_frames', 9)
        
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
```

Also add `import os` at the top if not already there.

---

## ✅ What's Fixed

1. ✅ **overlay.py error** - `is_enabled()` → `is_heatmap_enabled()`
2. ✅ **Permission error** - Shot directory now in `/home/admin/air-target/shots`
3. ✅ **Camera page** - New page with live feed + config + calibration
4. ✅ **Settings page** - Now includes shot directory configuration
5. ✅ **Rounds page** - Shows dynamic shot directory path
6. ✅ **Help page** - Complete API documentation
7. ✅ **Navigation** - Consistent nav bar on all pages
8. ✅ **Themed modals** - Beautiful dialogs instead of alert()

---

## 🎨 New Page Structure

### Main Page (`/`)
- Multi-camera grid
- Live video feeds
- Scores & shot badges
- Start/Stop/Reset buttons
- **NO camera settings**

### Camera Page (`/camera`) ⭐ NEW!
- Camera selection
- **Live preview** (see zoom/rotation changes immediately)
- Zoom controls
- Rotation controls
- White balance & exposure
- **Integrated calibration** (same page!)

### Settings Page (`/settings`)
- Match settings (scoring rules)
- Recording settings
- **Shot directory path** (editable!)
- Advanced detection settings

### Rounds Page (`/rounds`)
- View recorded rounds
- Dynamic shot directory display

### Help Page (`/help`) ⭐ NEW!
- All API endpoints
- Quick start guide
- Keyboard shortcuts

---

## 🔧 API Endpoints Reference

### Detection & Scoring
- `GET /toggle` - Start/stop all cameras
- `GET /reset` - Reset all cameras
- `GET /hits` - All hits from all cameras
- `GET /hits/{cam_id}` - Hits for specific camera

### Camera Control
- `GET /camera_urls` - List all cameras
- `GET /camera_info/{cam_id}` - Camera status
- `GET /video/{cam_id}` - Video with overlays
- `GET /raw_video/{cam_id}` - Raw video (no overlays)
- `GET /set_zoom/{cam_id}/{value}` - Set zoom
- `GET /adjust_zoom/{cam_id}/{delta}` - Adjust zoom
- `GET /set_rotation/{cam_id}/{angle}` - Set rotation
- `GET /lock_exposure/{cam_id}` - Lock exposure
- `GET /unlock_exposure/{cam_id}` - Unlock exposure

### Configuration
- `GET /get_config` - Get all config
- `POST /set_scoring_config` - Update scoring
- `POST /set_recording_config` - Update recording
- `POST /set_shot_directory` - Set shot directory
- `POST /set_advanced_config` - Update detection

### Calibration
- `POST /set_calibration` - Save calibration points

---

## 🎯 Typical Workflow

### First Time Setup:
1. Visit `/camera` page
2. Select camera
3. Adjust zoom (watch live preview)
4. Adjust rotation (watch live preview)
5. Click 3 calibration points on preview
6. Check quality badge (should be >0.75)
7. Visit `/settings` page
8. Configure match settings
9. Set recording options
10. Set shot directory path
11. Return to `/` main page
12. Click "Start All Cameras"
13. Begin shooting!

### During Competition:
- Main page shows all cameras
- Scores update in real-time
- Use Camera page for quick adjustments
- Use Spectator page for display

---

## 🆘 Troubleshooting

### "Camera button doesn't work"
**Fix:** Add `/camera` route to app.py (see above)

### "Permission denied" when saving shots
**Fix:** Check shot directory path in Settings page, make sure directory exists and is writable

### "is_enabled() not defined"
**Fix:** Replace overlay.py with provided version

### "Modal not styled correctly"
**Fix:** Ensure modal-theme.css and modal-theme.js are in static/ folder and linked in HTML

### "Rounds shows wrong path"
**Fix:** Replace rounds.html with provided version (dynamically loads path)

---

## 📋 Verification Checklist

After deployment:
- [ ] No errors on startup
- [ ] Can navigate to all 5 pages (Main, Camera, Settings, Rounds, Help)
- [ ] Camera page shows live preview
- [ ] Zoom/rotation changes visible in preview
- [ ] Calibration works (can click 3 points)
- [ ] Settings page shows shot directory config
- [ ] Can change shot directory and save
- [ ] Rounds page shows correct directory path
- [ ] Help page displays all endpoints
- [ ] Themed modals appear (not native alert boxes)
- [ ] Detection starts without permission errors

---

## ✨ Summary

**What Changed:**
- Fixed critical errors (overlay.py, permissions)
- Added Camera page (config + calibration integrated)
- Added Help page (API documentation)
- Updated Settings (shot directory config)
- Updated all pages with navigation
- Added themed modal system

**What's Better:**
- Clean main page (shooting only)
- All camera settings in one place
- Live preview shows changes immediately
- Calibration integrated with camera page
- Professional themed dialogs
- Complete system documentation

**Ready to Use! 🎯**
