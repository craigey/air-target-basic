# Migration Guide - Upgrading to Improved Version

## 🔄 Quick Upgrade Steps

### 1. Backup Your Current System

```bash
cd /home/pi/air-target
cp -r . ../air-target-backup
```

### 2. Replace Files

Copy these updated files (overwrites old versions):

**Core Files (MUST replace):**
- `detection.py` - Major changes for color detection
- `ai_classifier.py` - Now has real logic
- `calibration.py` - Fixed scale calculation bug
- `scoring.py` - Fixed scale usage
- `camera_manager.py` - Added exposure locking
- `app.py` - New API endpoints
- `config.json` - New parameters

**Keep Your Files:**
- `templates/` - No changes needed
- `static/` - No changes needed
- Other files unchanged

### 3. Update Config

Your old config.json will work, but add these new parameters for best results:

```json
{
  // ... keep your existing settings ...
  
  // ADD THESE:
  "adaptive_threshold": true,
  "color_detection": true,
  "grey_threshold": 15,
  "min_confidence": 0.6,
  "baseline_update_mode": "selective",
  "shot_cooldown_frames": 15,
  "auto_lock_exposure": true,
  "exposure_stabilization_frames": 30,
  "optimize_camera_on_start": true
}
```

### 4. Test Changes

```bash
# Start server
python3 app.py

# Watch startup logs for:
# ✅ Calibration: scale=X mm/px
# ✅ Camera optimized
# ✅ Exposure locked at X
```

### 5. Recalibrate

The improved calibration is more accurate, so **you MUST recalibrate** after upgrading:

1. Go to `/calibrate`
2. Mark center, bull edge, outer edge
3. Save and verify quality >0.75

---

## 🐛 Breaking Changes

### 1. Scoring Calculation

**Old:** Used incorrect scale calculation  
**New:** Uses proper calibrated scale

**Impact:** Scores may be slightly different  
**Action:** Recalibrate system

### 2. AI Classifier Return Value

**Old:** Always returned 0.85  
**New:** Returns actual confidence (0.35-0.95)

**Impact:** May filter differently  
**Action:** Tune `min_confidence` if needed

### 3. Baseline Update

**Old:** Updated every frame  
**New:** Selective update (configurable)

**Impact:** Better long-term stability  
**Action:** None, but can change via config

---

## 🎯 Testing Checklist

After upgrade, test these scenarios:

- [ ] Single shot detection works
- [ ] Scoring accuracy within 2mm
- [ ] No false positives in 30 seconds
- [ ] 5 rapid shots all detected
- [ ] Exposure stays locked
- [ ] Grey marks detected (if using TiO2 paint)
- [ ] Calibration quality >0.75
- [ ] No duplicate detections per shot

---

## 🔧 Rollback Plan

If something doesn't work:

```bash
cd /home/pi
rm -rf air-target
mv air-target-backup air-target
cd air-target
python3 app.py
```

---

## 📊 Expected Improvements

You should see:

1. **Fewer false positives** (noise rejection)
2. **Better detection rate** (color + shape analysis)
3. **More accurate scores** (fixed calculation)
4. **Stable over time** (exposure lock + selective baseline)
5. **Better calibration** (RANSAC + dual-scale)

---

## ❓ Common Issues After Migration

### Issue: "No detections at all"

**Cause:** Confidence threshold too high  
**Fix:** Lower `min_confidence` to 0.5 in config

### Issue: "Too many false positives"

**Cause:** Noise or lighting changes  
**Fix:** 
1. Verify exposure is locked
2. Increase `min_confidence` to 0.7
3. Enable `color_detection`

### Issue: "Scores seem wrong"

**Cause:** Need to recalibrate with new system  
**Fix:** Recalibrate using /calibrate page

### Issue: "Camera won't lock exposure"

**Cause:** Camera doesn't support manual exposure  
**Fix:** Set `auto_lock_exposure: false` in config

---

## 🚀 Next Steps

After successful migration:

1. Run 20-30 test shots
2. Measure accuracy vs. manual scoring
3. Tune config parameters if needed
4. Consider adding ML classifier (see README)
5. Test different lighting conditions

---

## 📞 Need Help?

Check these files:
- `README_IMPROVEMENTS.md` - Full documentation
- Startup logs - Look for ⚠️ warnings
- `/camera_info/0` - Check camera status

Good luck with your upgrade! 🎯
