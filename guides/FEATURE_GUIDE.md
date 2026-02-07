# 🎯 NARPA Air Target System - Complete Feature Guide

## 🆕 New Features Summary

### 1. **4-Ring Scoring (Default)**
- Bull (1"): 5 points
- Ring 1 (2"): 4 points
- Ring 2 (3"): 3 points
- Ring 3 (4"): 2 points
- **Ring 4 (5"): 1 point** ← NEW!
- Outside: 0 points

### 2. **Configurable Scoring via UI**
- Toggle between 4-ring and 3-ring scoring
- Enable/disable bull hole bonus (5.1 points)
- Changes apply immediately, no restart needed
- Access via `/settings` page

### 3. **Camera Digital Zoom**
- Zoom range: 1.0x to 4.0x
- Helps narrow down target area
- Controlled via buttons or slider
- Useful for multi-target setups

### 4. **Shot Image Recording**
- Records every shot with metadata
- Saves cropped image (200px default)
- Includes timestamp, score, confidence

### 5. **Stack/Unstack Viewer**
- View target state at any point
- Stack: Show accumulated marks
- Unstack: Show state before specific shot
- Perfect for verification and replay

### 6. **Round Management**
- Auto-creates new round on start
- Lists all recorded rounds
- View/replay previous rounds
- Delete old rounds
- Export round summary image

---

## 📦 Installation

```bash
# On Raspberry Pi
cd /home/pi/air-target

# Copy all files
cp [downloaded]/*.py .
cp [downloaded]/config.json .
cp -r [downloaded]/templates .

# Create shots directory
mkdir -p /home/pi/air-target/shots

# Install dependencies (if not already installed)
pip3 install opencv-python flask numpy
```

---

## ⚙️ Configuration (config.json)

### Scoring Settings
```json
{
  "use_4_ring_scoring": true,          // Default: 4-ring
  "enable_bull_hole_bonus": false,      // Default: disabled
  "bull_hole_score": 5.1,
  "shots_per_round": 6
}
```

### Camera Settings
```json
{
  "auto_lock_exposure": true,           // Lock on startup
  "default_zoom": 1.0,                  // No zoom by default
  "zoom_step": 0.1,                     // Zoom increment
  "min_zoom": 1.0,
  "max_zoom": 4.0
}
```

### Recording Settings
```json
{
  "record_shots": true,                 // Enable recording
  "shot_images_dir": "/home/pi/air-target/shots",
  "record_full_frame": false,           // Just crop around hit
  "record_crop_size": 200               // 200x200 pixel crop
}
```

---

## 🚀 Using the New Features

### Settings Page

Navigate to `http://pi-ip:5000/settings`

**Features:**
1. **Scoring Configuration**
   - Check/uncheck 4-ring scoring
   - Enable bull hole bonus
   - Click "Save Scoring Settings"

2. **Camera Zoom Control**
   - Use +/- buttons for quick adjust
   - Use slider for precise control
   - Reset to 1.0x anytime
   - Zoom applies to all views

3. **Camera Settings**
   - Lock/unlock exposure
   - Optimize camera automatically
   - View current camera info

4. **Recording Settings**
   - Enable/disable shot recording
   - Changes apply immediately

### Main Shooting Interface

1. **Start Detection**
   - Automatically creates new round
   - Saves baseline image
   - Begins recording shots

2. **During Round**
   - Each shot displays score on video
   - Green = Bull (5), Red = Scoring (1-4), Blue = Miss (0)
   - Shot count shown: "Shot 3/6"
   - Running total displayed

3. **End Detection**
   - Shows final score and percentage
   - Round saved automatically
   - Images available for review

### Rounds Viewer

Navigate to `http://pi-ip:5000/rounds`

**Features:**

1. **Round Selection**
   - Lists all recorded rounds (newest first)
   - Shows timestamp
   - Click to open round

2. **Round Summary**
   - Total score: 26/30 (86.7%)
   - Average: 4.33
   - Shot count: 6

3. **Stack Controls**
   - **Clean Target:** Before any shots
   - **All Shots Stacked:** Final state
   - **Custom Stack:** Click any shot to see state before it
   - **Download Summary:** Get grid of all shots

4. **Individual Shots**
   - Grid view of all shots
   - Click to highlight and unstack
   - Shows score and confidence

---

## 🔍 API Endpoints Reference

### Scoring Configuration
```bash
# Get current config
GET /get_scoring_config
→ {"use_4_ring": true, "enable_bull_hole_bonus": false}

# Set config
POST /set_scoring_config
Body: {"use_4_ring": true, "enable_bull_hole_bonus": true}
→ Updates and saves to config.json
```

### Camera Zoom
```bash
# Set zoom level
GET /set_zoom/0/2.0
→ {"camera": 0, "zoom": 2.0}

# Adjust zoom
GET /adjust_zoom/0/0.1       # Zoom in
GET /adjust_zoom/0/-0.1      # Zoom out

# Get current zoom
GET /get_zoom/0
→ {"camera": 0, "zoom": 1.5}
```

### Shot Recording
```bash
# Get recording stats
GET /recording_stats
→ {"recording_enabled": true, "shots_recorded": 6, ...}

# Get shot image
GET /get_shot_image/3
→ Returns JPEG image

# Get shot metadata
GET /get_shot_metadata/3
→ {"score": 5, "x": 320, "y": 240, ...}

# Stack shots
GET /stack_shots              # All shots
GET /stack_shots/3            # First 3 shots
→ Returns composite JPEG

# Unstack (show before)
GET /unstack_shot/4
→ Returns target state before shot 4

# List rounds
GET /list_rounds
→ {"rounds": ["round_20260202_143022", ...]}

# Load round
GET /load_round/round_20260202_143022
→ {"shots": [...], "round": "..."}

# Delete round
DELETE /delete_round/round_20260202_143022
→ {"status": "OK"}
```

### Round Summary
```bash
# Get current round summary
GET /round_summary
→ {
  "total_shots": 6,
  "total_score": 26,
  "average": 4.33,
  "percentage": 86.7,
  "complete": true
}

# Get summary image
GET /round_summary_image
→ Returns grid JPEG with all shots
```

---

## 🎨 How Shot Recording Works

### On Start Detection:
1. Creates directory: `/shots/round_YYYYMMDD_HHMMSS/`
2. Saves `baseline.jpg` (clean target)
3. Ready to record shots

### On Each Shot:
1. Detects pellet mark
2. Crops 200x200px around hit
3. Saves as `shot_01_score_5.jpg`
4. Saves metadata `shot_01_score_5.json`

### Metadata Example:
```json
{
  "shot_number": 1,
  "score": 5,
  "x": 320.5,
  "y": 240.8,
  "confidence": 0.92,
  "ai_prob": 0.87,
  "area": 65,
  "timestamp": "2026-02-02T14:30:22.123456",
  "filepath": "/home/pi/air-target/shots/round_20260202_143022/shot_01_score_5.jpg"
}
```

### Directory Structure:
```
/home/pi/air-target/shots/
├── round_20260202_143022/
│   ├── baseline.jpg
│   ├── shot_01_score_5.jpg
│   ├── shot_01_score_5.json
│   ├── shot_02_score_4.jpg
│   ├── shot_02_score_4.json
│   └── ...
│   └── round_summary.jpg
└── round_20260202_150530/
    └── ...
```

---

## 📸 Stacking & Unstacking

### Stack (Accumulation View)

**Purpose:** See how marks accumulate on target

**How it works:**
- Loads shot images in order
- Blends them together (70% existing + 30% new)
- Creates composite showing all marks

**Use cases:**
- Verify final target state
- See shot grouping
- Confirm all shots recorded

**Example:**
```python
# Show target after 3 shots
GET /stack_shots/3
```

### Unstack (Before View)

**Purpose:** See target state BEFORE specific shot

**How it works:**
- Stacks all shots up to (but not including) target shot
- Shows what shooter saw before that shot

**Use cases:**
- Verify shot wasn't already there
- Check for clear target before shot
- Dispute resolution

**Example:**
```python
# Show target before shot 4
GET /unstack_shot/4
→ Returns stack of shots 1, 2, 3 only
```

---

## 🎯 Scoring Configuration Examples

### Example 1: Standard 4-Ring (Default)
```json
{
  "use_4_ring_scoring": true,
  "enable_bull_hole_bonus": false
}
```
**Scoring:** Bull=5, 2"=4, 3"=3, 4"=2, 5"=1, Outside=0

### Example 2: 3-Ring (No Outer Ring)
```json
{
  "use_4_ring_scoring": false,
  "enable_bull_hole_bonus": false
}
```
**Scoring:** Bull=5, 2"=4, 3"=3, 4"=2, Outside=0

### Example 3: 4-Ring with Bull Hole Bonus
```json
{
  "use_4_ring_scoring": true,
  "enable_bull_hole_bonus": true,
  "bull_hole_score": 5.1
}
```
**Scoring:** Bull=5, 2"=4, 3"=3, 4"=2, 5"=1, Bull Hole=5.1

---

## 🔧 Camera Zoom Usage

### When to Use Zoom:

1. **Target Too Small in Frame**
   - Zoom in to 2.0x-3.0x
   - Focuses on target area
   - Improves detection accuracy

2. **Multiple Targets Visible**
   - Zoom to isolate single target
   - Prevents detecting neighbor's shots
   - Better for multi-lane setups

3. **Fine-Tuning Calibration**
   - Zoom in for precise point marking
   - More accurate ring edge detection

### Zoom Limitations:

- **Digital zoom only** (crops and scales)
- **Reduces field of view** (may miss edge shots)
- **Does not improve resolution**
- **Best: 1.5x to 2.5x range**

### Zoom Tips:

```bash
# Start wide
Set zoom to 1.0x

# Shoot 1 test round
Check if all shots detected

# If target small
Increase to 1.5x or 2.0x

# Recalibrate after zoom change
Go to /calibrate and remark points
```

---

## 📊 Typical Workflow

### Competition Day Setup:

1. **Mount Camera**
   - Position perpendicular to target
   - Center on bull
   - Secure mount

2. **Configure System** (`/settings`)
   - Set 4-ring or 3-ring scoring
   - Enable bull hole bonus if needed
   - Adjust zoom to frame target
   - Lock exposure

3. **Calibrate** (`/calibrate`)
   - Mark center, bull edge, outer edge
   - Check quality >0.75

4. **Test Round**
   - Fire 6 test shots
   - Verify detection accuracy
   - Check scores vs manual

5. **Competition Rounds**
   - Start detection
   - Shoot 6 shots
   - Stop detection
   - Review in `/rounds`
   - Reset for next round

---

## 🐛 Troubleshooting New Features

### Zoom Not Working
- Check camera supports digital zoom
- Try smaller zoom increments
- Reset to 1.0x and retry
- Recalibrate after zoom change

### Shots Not Recording
- Check `record_shots: true` in config
- Verify shots directory exists
- Check disk space
- Enable via `/settings`

### Can't View Rounds
- Check rounds directory: `/home/pi/air-target/shots`
- Verify images exist in round folders
- Check file permissions

### Scoring Config Not Saving
- Verify config.json is writable
- Check for JSON syntax errors
- Reload page after changing

### Stack/Unstack Shows Wrong State
- Verify shot images saved correctly
- Check shot numbers in metadata
- Ensure shots saved in order

---

## 💾 Disk Space Management

Each shot image: ~15-30KB (cropped)
Full frame: ~100-150KB

**Capacity estimates:**
- 1GB = ~35,000 cropped shots = ~5,800 rounds
- 8GB SD card = ~40,000+ rounds

**Cleanup:**
```bash
# Delete old rounds via UI
Go to /rounds → Select round → Delete

# Or manually
rm -rf /home/pi/air-target/shots/round_20260101_*
```

---

## 🎓 Advanced Features

### Custom Scoring Rules

Edit `scoring.py` to implement:
- Custom ring diameters
- Different point values
- Penalty zones
- Bonus multipliers

### Multi-Camera Verification

**Future Feature:** (Currently not implemented)
- Two cameras per lane
- Each scores independently
- System compares results
- Flags discrepancies

**To implement:**
- Add camera_ids: [0, 1] to config
- Modify detection.py for multi-cam
- Compare results in app.py

---

## 📝 Files Changed Summary

**New Files:**
- `shot_recorder.py` - Shot recording and stacking
- `templates/settings.html` - Settings UI
- `templates/rounds.html` - Rounds viewer UI

**Modified Files:**
- `config.json` - Added zoom, recording settings
- `scoring.py` - Runtime config, 4-ring support
- `detection.py` - Recording integration
- `camera_manager.py` - Digital zoom support
- `app.py` - New endpoints for all features

---

## 🚀 Quick Start Commands

```bash
# Start system
python3 app.py

# Open browser
http://pi-ip:5000/

# Configure settings
http://pi-ip:5000/settings

# View past rounds
http://pi-ip:5000/rounds

# Calibrate
http://pi-ip:5000/calibrate

# API examples
curl http://pi-ip:5000/set_zoom/0/2.0
curl http://pi-ip:5000/get_scoring_config
curl http://pi-ip:5000/list_rounds
```

---

## ✅ Feature Checklist

Use this to verify all features working:

- [ ] 4-ring scoring enabled by default
- [ ] Can toggle to 3-ring via settings
- [ ] Bull hole bonus configurable
- [ ] Settings page loads and saves
- [ ] Zoom controls work (1.0x - 4.0x)
- [ ] Exposure locks on startup
- [ ] Shots record to /shots directory
- [ ] Rounds viewer shows all rounds
- [ ] Stack shows accumulated marks
- [ ] Unstack shows state before shot
- [ ] Summary image downloads
- [ ] Can delete old rounds
- [ ] Round statistics accurate
- [ ] Score colors display on video

---

**Enjoy your enhanced NARPA target system! 🎯**

Questions? Check the other README files or API docs above.
