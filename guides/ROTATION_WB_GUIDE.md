# 🔄 Rotation & White Balance Guide

## New Features Added

### ✅ Camera Rotation Correction
- Correct for camera mounting angles
- Support for any angle (0-359°)
- Quick presets: 0°, 90°, 180°, 270°
- Live preview in video feed

### ✅ White Balance Control
- Auto mode (default)
- Manual mode with temperature control
- Presets: Tungsten, Fluorescent, Daylight, Cloudy
- Lock white balance during competition

### ✅ Fixed Issues
- Calibration page now works properly
- Zoom controls functional on all pages
- Video feed stable during calibration
- No more errors with camera switching

---

## 🔄 Rotation Correction

### When to Use

**Camera mounted at angle:**
- Sideways: Use 90° or 270°
- Upside down: Use 180°
- Slightly off: Use custom angle

**Why it matters:**
- Ensures target rings appear circular
- Correct scoring calculations
- Proper calibration alignment

### How to Set Rotation

#### Via Settings Page

1. Navigate to `http://pi-ip:5000/settings`
2. Select your camera from dropdown
3. Click rotation preset (0°, 90°, 180°, 270°)
4. Or enter custom angle and click "Set Custom"
5. Check live video feed to verify

#### Via API

```bash
# Set to 90° (portrait mode)
curl http://pi-ip:5000/set_rotation/0/90

# Set custom angle (45°)
curl http://pi-ip:5000/set_rotation/0/45

# Get current rotation
curl http://pi-ip:5000/get_rotation/0
```

### Common Rotation Scenarios

```
Camera Mounted:          Use Rotation:
─────────────────────────────────────
Normal (upright)         0°
Left side down           90°
Upside down              180°
Right side down          270°
Slight tilt left         -5° (or 355°)
Slight tilt right        5°
```

### Testing Rotation

1. Point camera at target
2. Set rotation angle
3. Check video feed:
   - Target should appear upright
   - Bull's eye at center
   - Rings circular (not oval)
4. Adjust if needed
5. Recalibrate after setting rotation

---

## 🎨 White Balance Control

### Why White Balance Matters

**Problem:** Auto white balance can shift during competition
- Changes color temperature
- Affects grey mark detection
- Causes inconsistent baselines
- Impacts frame differencing

**Solution:** Lock white balance before competition

### White Balance Modes

#### Auto Mode (Default)
```bash
curl http://pi-ip:5000/unlock_white_balance/0
```
- Camera adjusts automatically
- Good for testing
- **Don't use during competition!**

#### Manual Mode (Recommended)
```bash
curl http://pi-ip:5000/lock_white_balance/0
```
- Fixed color temperature
- Consistent colors
- Stable detection
- **Use during competition!**

### Color Temperature Presets

```bash
# Tungsten / Incandescent (warm/yellow light)
curl http://pi-ip:5000/set_white_balance/0/2800

# Fluorescent (cool white light)
curl http://pi-ip:5000/set_white_balance/0/4000

# Daylight (natural light)
curl http://pi-ip:5000/set_white_balance/0/5500

# Cloudy / Shade (cool/blue light)
curl http://pi-ip:5000/set_white_balance/0/6500
```

### How to Choose Temperature

1. **Look at your lighting:**
   - Yellow/warm bulbs → 2800K (Tungsten)
   - White LED/fluorescent → 4000K
   - Natural window light → 5500K
   - Overcast day → 6500K

2. **Test each preset:**
   - Set temperature
   - Look at video feed
   - White target should appear white (not blue or yellow)
   - Choose most neutral appearance

3. **Lock before competition**

### Via Settings Page

1. Go to `/settings`
2. Select camera
3. White Balance section:
   - Click "Manual"
   - Click preset button (Tungsten, Fluorescent, etc.)
   - OR click "Auto" to re-enable auto mode

---

## 📋 Pre-Competition Checklist

Use this checklist before each competition:

### Camera Setup
- [ ] Mount camera perpendicular to target
- [ ] Set rotation if camera at angle
- [ ] Verify target appears upright in feed
- [ ] Set zoom to frame target properly

### White Balance
- [ ] Switch to Manual mode
- [ ] Select lighting preset
- [ ] Verify white target looks white
- [ ] Lock white balance

### Exposure
- [ ] Lock exposure
- [ ] Verify no brightness drift
- [ ] Test 30 seconds without changes

### Calibration
- [ ] Mark center, bull, outer ring
- [ ] Check quality >0.75
- [ ] Verify zoom/rotation don't affect calibration

### Final Test
- [ ] Fire 1 test shot
- [ ] Verify detection works
- [ ] Check score accuracy
- [ ] Ready for competition!

---

## 🔧 API Reference

### Rotation Endpoints

```bash
# Set rotation angle
GET /set_rotation/{cam_id}/{angle}
→ {"camera": 0, "rotation": 90}

# Get current rotation
GET /get_rotation/{cam_id}
→ {"camera": 0, "rotation": 90}
```

### White Balance Endpoints

```bash
# Lock white balance (manual mode)
GET /lock_white_balance/{cam_id}
→ {"locked": true, "camera": 0}

# Unlock white balance (auto mode)
GET /unlock_white_balance/{cam_id}
→ {"locked": false, "camera": 0}

# Set temperature (2800-6500K)
GET /set_white_balance/{cam_id}/{temperature}
→ {"camera": 0, "temperature": 4000}
```

### Camera Info (includes rotation & WB)

```bash
GET /camera_info/{cam_id}
→ {
  "rotation": 90,
  "white_balance": 4000,
  "white_balance_locked": true,
  "zoom": 2.0,
  "exposure_locked": true,
  ...
}
```

---

## 🐛 Troubleshooting

### Rotation Issues

**Problem:** Target appears sideways/upside down

**Solution:**
```bash
# Try each rotation preset
curl http://pi-ip:5000/set_rotation/0/0
curl http://pi-ip:5000/set_rotation/0/90
curl http://pi-ip:5000/set_rotation/0/180
curl http://pi-ip:5000/set_rotation/0/270
```

**Problem:** Calibration fails after rotation

**Solution:**
1. Set rotation first
2. Then recalibrate
3. Rotation must be set before calibration

**Problem:** Detection inaccurate after rotation

**Solution:**
1. Reset calibration
2. Apply rotation
3. Recalibrate with rotation applied

### White Balance Issues

**Problem:** Colors look wrong (too blue/yellow)

**Solution:**
1. Try different temperature presets
2. Match to your lighting type
3. Use custom temperature if needed

**Problem:** White balance keeps changing

**Solution:**
1. Verify lock_white_balance was called
2. Check camera_info shows "white_balance_locked": true
3. Some cameras don't support manual WB

**Problem:** Detection worse after WB lock

**Solution:**
1. Unlock WB temporarily
2. Let camera auto-adjust
3. Lock again
4. Reset baseline (stop/start detection)

### Calibration Page Errors (Fixed!)

**Previous problems - now fixed:**
- ✅ Video feed no longer freezes
- ✅ Calibration doesn't crash
- ✅ Zoom works during calibration
- ✅ Rotation preserved during calibration

**If still having issues:**
1. Clear browser cache
2. Reload page (Ctrl+Shift+R)
3. Check browser console for errors
4. Verify Python dependencies installed

---

## 💡 Best Practices

### Rotation
1. **Set once per camera**
   - Measure camera angle during mount
   - Set rotation in config
   - Don't change during competition

2. **Recalibrate after rotation**
   - Rotation affects image geometry
   - Always recalibrate
   - Test with known shots

3. **Use presets when possible**
   - 90° increments most common
   - Custom angles for fine-tuning
   - Avoid unnecessary custom angles

### White Balance
1. **Lock before competition**
   - Set during setup
   - Test for 5 minutes
   - Verify stability

2. **Match your lighting**
   - Indoor: 2800-4000K
   - Mixed: 4000-5500K
   - Outdoor: 5500-6500K

3. **Don't change mid-round**
   - Breaks baseline
   - Causes detection issues
   - Restart if must change

### Combined
1. **Order matters:**
   - Set rotation first
   - Set white balance second
   - Lock exposure third
   - Calibrate fourth
   - Start detection last

2. **Document your settings:**
   - Save camera settings
   - Note rotation angles
   - Record WB temperature
   - Can restore if needed

3. **Test thoroughly:**
   - 5 test shots minimum
   - Verify all detected correctly
   - Check score accuracy
   - Ready for competition

---

## 📊 Settings Examples

### Indoor Range (Fluorescent)
```json
{
  "rotation": 0,
  "white_balance": 4000,
  "exposure_locked": true,
  "zoom": 1.5
}
```

### Outdoor Range (Daylight)
```json
{
  "rotation": 0,
  "white_balance": 5500,
  "exposure_locked": true,
  "zoom": 2.0
}
```

### Camera Mounted Sideways
```json
{
  "rotation": 90,
  "white_balance": 4000,
  "exposure_locked": true,
  "zoom": 1.0
}
```

---

## 🎯 Quick Commands

### Setup Camera 0 for Competition

```bash
# Set rotation (if needed)
curl http://pi-ip:5000/set_rotation/0/0

# Set white balance for fluorescent lighting
curl http://pi-ip:5000/lock_white_balance/0
curl http://pi-ip:5000/set_white_balance/0/4000

# Set zoom
curl http://pi-ip:5000/set_zoom/0/1.5

# Lock exposure
curl http://pi-ip:5000/lock_exposure/0

# Verify settings
curl http://pi-ip:5000/camera_info/0
```

### Reset All Camera Settings

```bash
# Reset rotation
curl http://pi-ip:5000/set_rotation/0/0

# Reset zoom
curl http://pi-ip:5000/set_zoom/0/1.0

# Unlock WB (auto)
curl http://pi-ip:5000/unlock_white_balance/0

# Unlock exposure
curl http://pi-ip:5000/unlock_exposure/0
```

---

**All fixed and ready to use! 🎯**
