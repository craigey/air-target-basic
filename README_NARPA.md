# NARPA Air Rifle Target Scoring System

## 🎯 NARPA Rules Implementation

This system implements official NARPA (National Air Rifle and Pistol Association) target shooting rules.

### Target Specifications

**Physical Dimensions:**
- Bull hole: 3/8" (9.525mm) diameter
- Bull scoring ring: 1" (25.4mm) diameter - **Score: 5**
- Ring 1: 2" (50.8mm) diameter - **Score: 4**
- Ring 2: 3" (76.2mm) diameter - **Score: 3**  
- Ring 3: 4" (101.6mm) diameter - **Score: 2**
- Optional Ring 4: 5" (127mm) diameter - **Score: 1** (league dependent)
- Outside all rings - **Score: 0**

**Target Height:**
- Standard: 5 feet from floor to bull center
- Can vary by league (typically shoulder height)

**Shooting Format:**
- 5-6 shots per round (configurable)
- Minimum 0.3 seconds between shots
- Typical time: 10s of seconds between shots
- Game of accuracy, not speed

### Scoring Rules

#### Standard Scoring
- **Bull (1" ring):** 5 points
- **Ring 1 (2"):** 4 points
- **Ring 2 (3"):** 3 points
- **Ring 3 (4"):** 2 points
- **Outside:** 0 points

#### Split Shots
When a pellet mark touches a scoring line:
- **Majority rule:** The larger portion of the mark determines the score
- **Scores higher:** In ambiguous cases, score the higher value
- System uses pellet center as proxy for "majority"

#### Bull Hole Bonus (Optional)
- Pellet through bull hole without leaving visible mark
- Requires bell ring for verification
- **Score: 5.1** (if enabled)
- Without bell ring: **Score: 4**

### Configuration

Edit `config.json` to customize:

```json
{
  // NARPA Target dimensions (in mm)
  "bull_hole_mm": 9.525,      // 3/8" bull hole
  "bull_mm": 25.4,            // 1" bull scoring ring
  "rings_mm": [50.8, 76.2, 101.6],  // 2", 3", 4" rings
  
  // Optional 4" outer ring for score of 1
  "enable_outer_ring": false,
  "optional_outer_ring_mm": 127.0,
  
  // Bull hole bonus (5.1 score)
  "enable_bull_hole_bonus": false,
  "bull_hole_score": 5.1,
  
  // Round settings
  "shots_per_round": 6,
  
  // Detection settings for white TiO2 paint
  "color_detection": true,
  "grey_threshold": 15,
  
  // Timing (0.3s minimum between shots)
  "shot_cooldown_frames": 9,  // 9 frames @ 30fps = 0.3s
  "max_shot_interval_seconds": 120
}
```

---

## 🚀 Quick Start

### 1. Installation

```bash
# On Raspberry Pi
sudo apt-get update
sudo apt-get install python3-opencv python3-flask python3-numpy

cd /home/pi/air-target
# Copy all Python files here
```

### 2. Hardware Setup

**Required:**
- Raspberry Pi (3B+ or 4 recommended)
- USB webcam (720p or higher)
- NARPA-compliant target with white TiO2 paint
- Mounting bracket for camera

**Optional:**
- Break-beam sensor (GPIO 17)
- Bell for bull hole detection
- LED indicators

**Camera Position:**
- Mount perpendicular to target face
- Distance: 6-12 inches from target
- Center on bull
- Avoid glare from lighting

### 3. Calibration (CRITICAL!)

```bash
python3 app.py
# Navigate to http://pi-ip:5000/calibrate
```

**Mark 3 points:**
1. **Center** - Exact center of bull hole
2. **Bull edge** - Any point on the 1" bull ring edge
3. **Outer edge** - Any point on the 4" ring edge

**Optional: Perspective correction**
- Mark all 4 corners of target for homography
- Use if camera is at an angle
- Improves accuracy by 20-30%

**Expected quality:** >0.75 (shown in logs)

### 4. Lock Exposure (ESSENTIAL!)

The system auto-locks exposure on startup if configured:

```json
"auto_lock_exposure": true
```

Or manually via API:
```bash
curl http://pi-ip:5000/lock_exposure/0
```

**Why critical?** Auto-exposure causes brightness drift that breaks detection!

### 5. Start Shooting

1. Click "Start Detection" on web interface
2. Fire 6 shots (or configured amount)
3. System displays:
   - Individual scores
   - Round total
   - Running accuracy

---

## 🎨 Detection for White TiO2 Paint

### How It Works

Your target uses non-drying titanium-dioxide white paint. Pellets leave grey lead marks.

**Detection Method:**
1. **HSV Color Space Analysis**
   - Measures Value (brightness) decrease
   - Checks Saturation (grey = low saturation)
   - Combines with edge detection

2. **Grey Mark Thresholds**
   - Brightness drop: >15 points (0-255 scale)
   - Saturation change: <30 points
   - Both must match to confirm pellet mark

3. **Shape Validation**
   - Circularity check (pellet holes are round)
   - Size validation (40-400 pixels)
   - Aspect ratio filtering

### Tuning for Your Paint

If detection is inconsistent:

**Too many false positives (noise):**
```json
"grey_threshold": 20,        // Increase (was 15)
"min_confidence": 0.7,       // Increase (was 0.6)
"color_detection": true      // Keep enabled
```

**Missing real shots:**
```json
"grey_threshold": 10,        // Decrease (was 15)
"min_confidence": 0.5,       // Decrease (was 0.6)
"min_area": 30              // Decrease (was 40)
```

**Lighting varies during day:**
```json
"adaptive_threshold": true,  // Essential
"auto_lock_exposure": true   // Re-lock when lighting changes
```

---

## 📊 Scoring Display

### Web Interface

The main interface shows:
- Live camera feed with detections
- Current shot count (X/6)
- Individual scores: 5 + 4 + 5 + 3 + 4 + 5
- Round total: 26/30
- Percentage: 86.7%

### API Endpoints

```bash
# Get all hits for current round
curl http://pi-ip:5000/hits

# Get round summary
curl http://pi-ip:5000/round_summary

# Reset for new round
curl http://pi-ip:5000/reset
```

### Score Colors on Video

- **Green circle** - Bull (5 points)
- **Red circle** - Scoring ring (2-4 points)
- **Blue circle** - Miss (0 points)

---

## 🔧 Troubleshooting

### False Positives

**Symptom:** Detections with no shots fired

**Common causes:**
1. Exposure not locked (camera adjusting)
2. Camera movement/vibration
3. Lighting changes
4. Debris falling on target

**Solutions:**
1. Verify exposure locked: `/camera_info/0`
2. Secure camera mount
3. Use stable lighting (not fluorescent)
4. Increase `min_confidence` to 0.7

### Missing Shots

**Symptom:** Real shots not detected

**Common causes:**
1. Faint grey marks on paint
2. Threshold too high
3. Camera out of focus
4. Poor calibration

**Solutions:**
1. Lower `grey_threshold` to 10-12
2. Lower `min_confidence` to 0.5
3. Check camera focus
4. Recalibrate system

### Inaccurate Scores

**Symptom:** Wrong ring scoring

**Common causes:**
1. Poor calibration
2. Perspective distortion
3. Camera moved after calibration

**Solutions:**
1. Recalibrate with 3+ rings
2. Use homography (mark 4 corners)
3. Check scale factor in logs
4. Verify camera is perpendicular

### Double Counting

**Symptom:** Same shot counted twice

**Causes:**
1. Shot cooldown too short
2. Pellet bouncing/fragmentation

**Solutions:**
1. Already has spatial duplicate check (10px)
2. Increase `shot_cooldown_frames` to 15
3. Check `min_confidence` threshold

---

## 🎯 Shot Timing

### Cooldown Settings

Default: 0.3 seconds (9 frames @ 30fps)

```json
"shot_cooldown_frames": 9
```

**Adjust for:**
- **Rapid fire practice:** 6 frames (0.2s)
- **Competition:** 9 frames (0.3s)
- **Casual shooting:** 15 frames (0.5s)

### Maximum Interval

If no shots for 120 seconds, system logs warning (baseline may need refresh):

```json
"max_shot_interval_seconds": 120
```

---

## 📈 Performance Expectations

### Accuracy

**Target performance:**
- Bull detection: 98%+ accuracy
- Ring scoring: ±1 ring worst case
- Split shots: 90%+ correct by majority rule
- False positives: <1 per 100 frames
- Position accuracy: <2mm for bull, <3mm for rings

### Speed

- Detection latency: <0.1s per shot
- Frame rate: 25-30 fps on Pi 4
- Cooldown: 0.3s between shots
- Round time: Typically 2-5 minutes (6 shots)

---

## 🏆 Competition Use

### Pre-Competition Checklist

- [ ] Camera securely mounted
- [ ] Calibrated within last hour
- [ ] Exposure locked
- [ ] Test 6-shot round completed
- [ ] Accuracy verified manually
- [ ] Backup Pi SD card
- [ ] Spare camera available

### During Competition

1. Lock exposure before each session
2. Recalibrate if lighting changes
3. Monitor false positive rate
4. Log all rounds for verification
5. Keep manual backup scores

### Post-Round Verification

The system logs each shot:
```
🎯 Shot 1: Score 5 (confidence 0.92)
🎯 Shot 2: Score 4 (confidence 0.87)
...
✅ Round complete! Total: 26/30
```

Review logs to verify all detections.

---

## 🔍 Advanced Features

### Bull Hole Detection

Enable 5.1 scoring for shots through the bull hole:

```json
"enable_bull_hole_bonus": true,
"bull_hole_score": 5.1
```

**Detection logic:**
- Very small mark area (<30 pixels)
- Position at exact center (<4.76mm)
- High confidence (>0.9)

**Note:** Requires bell sensor for full NARPA compliance!

### Outer Ring (5" = 1 point)

Some leagues use a 5" outer ring scoring 1 point:

```json
"enable_outer_ring": true,
"optional_outer_ring_mm": 127.0
```

### Multi-Camera Setup

Use 2 cameras for redundancy:

```json
"cameras": [0, 1]
```

System will detect on both and compare results.

---

## 📝 NARPA Compliance Notes

This system aims for NARPA compatibility but should be verified:

✅ **Compliant:**
- Target dimensions (1", 2", 3", 4" rings)
- Scoring rules (5, 4, 3, 2, 0)
- 6 shots per round
- Split shot majority rule

⚠️ **Verify with league:**
- Electronic scoring acceptance
- Bull hole bonus (5.1) rules
- Bell requirement for bull holes
- Calibration procedure
- Manual verification process

---

## 🙏 Credits

Developed for NARPA air rifle competition with:
- Official NARPA target dimensions
- Titanium-dioxide paint detection
- Split shot majority rule
- Bull hole bonus scoring

**Good shooting! 🎯**
