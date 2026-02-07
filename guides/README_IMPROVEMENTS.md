# Air Target Scoring System - IMPROVED VERSION

## 🎯 What's New in This Version

### Major Improvements

#### 1. **Color-Based Detection for Grey Marks**
- Detects grey pellet marks on white TiO2 paint using HSV color space
- Analyzes both brightness (Value) and saturation changes
- Can be enabled/disabled via `config.json`

#### 2. **Auto-Exposure Locking**
- Locks camera exposure after initialization to prevent drift
- Critical for consistent frame differencing
- Can be toggled via API endpoints

#### 3. **Enhanced Accuracy**
- Fixed scoring calculation bug (now uses correct scale factor)
- Added Gaussian blur for noise reduction
- Adaptive/OTSU thresholding instead of fixed threshold
- Sub-pixel centroid accuracy

#### 4. **Real AI Classifier**
- Circularity-based pellet hole detection
- Rejects irregular shapes and noise
- Aspect ratio and contrast validation

#### 5. **Better Calibration**
- Uses both bull and outer ring for scale calculation
- RANSAC homography for robustness
- Reprojection error calculation
- Weighted scale averaging

#### 6. **Improved Baseline Management**
- Selective baseline update (avoids hit locations)
- Prevents "drift" problem
- Configurable update modes

#### 7. **Spatial Duplicate Detection**
- Prevents detecting the same hole multiple times
- Checks if new detection is too close to recent hits

---

## 📦 Installation

```bash
# Install dependencies
sudo apt-get update
sudo apt-get install python3-opencv python3-flask python3-numpy

# Or use pip
pip3 install opencv-python flask numpy

# Clone/copy files to your Raspberry Pi
cd /home/pi/air-target
```

---

## ⚙️ Configuration

Edit `config.json` to customize behavior:

```json
{
  "cameras": [0],                    // Camera device IDs
  "min_area": 40,                    // Min contour area (pixels)
  "max_area": 400,                   // Max contour area (pixels)
  
  // Target dimensions (millimeters)
  "bull_mm": 9.525,                  // Bull's eye diameter
  "rings_mm": [25.4, 50.8, 76.2, 101.6],
  "pellet_mm": 4.5,                  // Pellet diameter
  
  // Detection algorithm
  "adaptive_threshold": true,         // Use adaptive thresholding
  "color_detection": true,            // Enable color-based detection
  "grey_threshold": 15,               // Grey mark detection sensitivity
  "min_confidence": 0.6,              // Minimum AI confidence
  
  // Baseline management
  "baseline_update_mode": "selective", // "selective", "always", or "never"
  
  // Shot detection
  "shot_cooldown_frames": 15,        // Frames to wait between shots
  
  // Camera settings
  "auto_lock_exposure": true,         // Lock exposure on startup
  "exposure_stabilization_frames": 30,
  "optimize_camera_on_start": true
}
```

---

## 🚀 Usage

### 1. Start the Server

```bash
python3 app.py
```

Access web interface at `http://raspberry-pi-ip:5000`

### 2. Calibration (IMPORTANT!)

1. Navigate to `/calibrate` page
2. Click to mark:
   - Target center
   - Bull's eye edge
   - Outer ring edge
3. Optionally mark 4 corners for perspective correction
4. Click "Save Calibration"

**Tip:** For best results, mark points on opposite sides (N/S or E/W) for better circle fitting.

### 3. Lock Exposure (CRITICAL!)

Before starting detection, make sure exposure is locked:

```bash
# Via API
curl http://raspberry-pi-ip:5000/lock_exposure/0

# Or it happens automatically if "auto_lock_exposure": true in config
```

**Why?** Auto-exposure causes brightness changes that break frame differencing!

### 4. Start Detection

Click "Start Detection" button or:

```bash
curl http://raspberry-pi-ip:5000/toggle
```

### 5. Shoot!

Fire at the target. System will:
- Detect new marks using color + shape analysis
- Apply homography correction
- Calculate score
- Display on overlay

---

## 🔧 API Endpoints

### Core Functionality
- `GET /` - Main interface
- `GET /video/<cam>` - Video stream
- `GET /toggle` - Toggle detection on/off
- `GET /hits` - Get all detected hits (JSON)
- `GET /reset` - Clear all hits

### Calibration
- `GET /calibrate` - Calibration interface
- `POST /set_calibration` - Save calibration data

### Camera Control
- `GET /lock_exposure/<cam>` - Lock exposure
- `GET /unlock_exposure/<cam>` - Unlock exposure
- `GET /camera_info/<cam>` - Get camera settings
- `GET /optimize_camera/<cam>` - Optimize camera

### Visualization
- `GET /toggle_heatmap` - Toggle heatmap
- `GET /reset_heatmap` - Clear heatmap
- `GET /spectator` - Spectator view

---

## 🎨 Color Detection Explained

The system detects grey pellet marks on white paint using HSV color space:

1. **Value (Brightness) Channel**
   - Grey marks are darker than white background
   - Threshold: >15 points darker (configurable)

2. **Saturation Channel**
   - Grey has low saturation (desaturated)
   - White paint also has low saturation
   - Validates that mark isn't just a shadow

3. **Combined Detection**
   - Must be both darker AND low saturation
   - Reduces false positives from lighting changes

**Tuning:** Adjust `grey_threshold` in config.json:
- Lower (10-12): More sensitive, may get false positives
- Higher (20-25): Less sensitive, may miss faint marks
- Default (15): Good balance for most lighting

---

## 🎯 Calibration Tips

### For Best Accuracy:

1. **Use Multiple Points**
   - Mark at least 3 rings (bull, middle, outer)
   - Mark 4 corners for homography

2. **Consistent Lighting**
   - Use steady lighting (not fluorescent)
   - Avoid shadows or glare on target
   - Lock exposure before calibration

3. **Camera Position**
   - Mount camera perpendicular to target
   - Minimize angle/perspective distortion
   - Use homography correction if angled

4. **Validation**
   - After calibration, check reported quality
   - Quality < 0.75 means recalibrate
   - Test with known positions

---

## 🔍 Troubleshooting

### False Positives (Detecting non-shots)

**Causes:**
- Camera noise
- Lighting changes
- Movement/vibration

**Solutions:**
1. Lock exposure: `auto_lock_exposure: true`
2. Increase `min_confidence` (try 0.7)
3. Increase `min_area` (try 60-80)
4. Enable `color_detection` if not already

### Missing Real Shots

**Causes:**
- Exposure locked at wrong brightness
- Detection threshold too high
- Marks too faint

**Solutions:**
1. Unlock exposure, let adjust, then relock
2. Lower `grey_threshold` (try 10-12)
3. Lower `min_confidence` (try 0.5)
4. Check camera focus

### Inaccurate Scores

**Causes:**
- Poor calibration
- Perspective distortion
- Camera moved after calibration

**Solutions:**
1. Recalibrate with more points
2. Use homography (mark 4 corners)
3. Mount camera more securely
4. Check scale factor in logs

### Multiple Detections Per Shot

**Causes:**
- Shot cooldown too short
- Pellet bouncing/debris

**Solutions:**
1. Increase `shot_cooldown_frames` (try 20-30)
2. System already has spatial duplicate check
3. Increase `min_confidence` to reduce noise

---

## 📊 Performance Optimization

### Camera Settings

The system auto-optimizes on startup, but you can tune:

- **Brightness**: Lower (110-128) if white target is overexposed
- **Contrast**: Higher (150-180) makes marks more visible
- **Focus**: Lock to target distance
- **Resolution**: 1280x720 is good balance of speed/quality

### Detection Speed

Typical: 25-30 FPS on Raspberry Pi 4

To improve:
- Lower resolution (640x480)
- Disable `color_detection` if not needed
- Reduce morphological operations
- Use faster threshold mode

---

## 🧪 Testing & Validation

### Create Test Dataset

1. Shoot 10 pellets at known positions
2. Manually measure actual positions
3. Compare detected vs. actual
4. Calculate average error

**Target Accuracy:** <2mm for bull's eye, <3mm for outer rings

### Lighting Test

1. Test at different times of day
2. Test with artificial lights on/off
3. Verify exposure lock prevents drift

### Multi-Shot Test

Fire 5 rapid shots:
- Should detect all 5
- Should not double-count
- Cooldown should reset properly

---

## 🔬 Advanced Features

### Future Enhancements (TODO)

1. **Machine Learning Classifier**
   - Collect 100-200 pellet hole images
   - Train small CNN (see `ai_classifier.py`)
   - Better than rule-based approach

2. **Multi-Camera Fusion**
   - Average results from 2+ cameras
   - Triangulation for 3D position

3. **Shot Sound Detection**
   - Use microphone to trigger detection
   - More reliable than IR break-beam

4. **Auto-Calibration**
   - Use `target_detection.py` to find rings automatically
   - HoughCircles for bulls-eye detection

---

## 📝 Code Structure

```
detection.py        - Main detection logic with color analysis
ai_classifier.py    - Circularity-based hole validation
calibration.py      - Scale calculation + homography
scoring.py          - Distance-based scoring with confidence
camera_manager.py   - Camera control + exposure locking
app.py              - Flask web server + API
config.json         - Configuration parameters
```

---

## 🆘 Support

Check these in order:

1. **Camera not detected?**
   - `v4l2-ctl --list-devices`
   - Check camera_id in config.json

2. **Exposure not locking?**
   - Check `/camera_info/0` endpoint
   - Some cameras don't support manual exposure

3. **Poor detection?**
   - Verify lighting is consistent
   - Check calibration quality (should be >0.75)
   - Review logs for warnings

4. **Scoring seems wrong?**
   - Recalibrate using both bull and outer ring
   - Verify `pellet_mm` setting matches your pellet size
   - Check scale factor in startup logs

---

## 📜 License

Free to use and modify for personal or commercial use.

---

## 🙏 Credits

Original concept with improvements for:
- Color-based detection
- Exposure locking
- Enhanced calibration
- Better accuracy

**Enjoy your automated target scoring! 🎯**
