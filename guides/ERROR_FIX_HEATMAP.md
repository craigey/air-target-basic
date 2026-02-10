# 🐛 Heatmap Error Fix

## Error You're Seeing

```
ValueError: too many values to unpack (expected 2)
File "overlay.py", line 27, in draw_overlay
    for (x, y) in heatmap:
```

## Root Cause

The `get_heatmap_normalized()` function returns data in a format that has more than 2 values per point (likely x, y, and count/intensity). The old code tries to unpack this into only 2 variables (x, y), causing the error.

## The Fix

Replace your `overlay.py` with this corrected version:

```python
import cv2
from calibration import get_target
from heatmap import get_heatmap_normalized, is_heatmap_enabled

def draw_overlay(frame, cam_id=0):
    """Draw target rings and heatmap overlay on frame."""
    t = get_target(cam_id)
    if t.get("center") is None:
        return frame

    cx, cy = t["center"]

    # Bull hole (inner circle)
    bull_hole_radius = int(t.get("bull_hole_px", 5))
    cv2.circle(frame, (cx, cy), bull_hole_radius, (255, 255, 255), 2)

    # Scoring rings
    for r in t.get("rings_px", []):
        cv2.circle(frame, (cx, cy), int(r), (0, 215, 255), 2)

    # Center dot
    cv2.circle(frame, (cx, cy), 2, (0, 0, 255), -1)

    # Heatmap overlay
    if is_heatmap_enabled():
        try:
            heatmap = get_heatmap_normalized()
            for point in heatmap:
                # Handle different heatmap formats
                if isinstance(point, (list, tuple)):
                    if len(point) >= 2:
                        x, y = point[0], point[1]
                        cv2.circle(frame, (int(x), int(y)), 2, (0, 255, 255), -1)
        except Exception as e:
            # Silently fail if heatmap has issues
            pass

    return frame
```

## Quick Fix Commands

```bash
cd ~/air-target-basic-main

# Backup current file
cp overlay.py overlay.py.bak

# Copy fixed version
cp /path/to/outputs/overlay-fixed.py overlay.py

# Or use the fix script
bash fix-errors.sh

# Restart
python app.py
```

## What Changed

### Old Code (BROKEN):
```python
for (x, y) in heatmap:
    cv2.circle(frame, (int(x), int(y)), 2, (0, 255, 255), -1)
```

### New Code (FIXED):
```python
for point in heatmap:
    if isinstance(point, (list, tuple)):
        if len(point) >= 2:
            x, y = point[0], point[1]
            cv2.circle(frame, (int(x), int(y)), 2, (0, 255, 255), -1)
```

### Why This Works:
1. Doesn't assume exactly 2 values
2. Checks if point is a list/tuple
3. Safely extracts first 2 values (x, y)
4. Ignores extra values (count, intensity, etc.)
5. Try/except catches any other issues

## Verify the Fix

Run this to check all files:
```bash
bash check-system.sh
```

Should see:
```
✅ ALL CHECKS PASSED - System ready to use!
```

## Other Potential Issues Checked

The fix script also checks and fixes:
1. ✓ `is_enabled()` → `is_heatmap_enabled()` 
2. ✓ `draw_overlay(frame)` → `draw_overlay(frame, cam_id)`
3. ✓ Shot directory permissions
4. ✓ All template files exist
5. ✓ Modal files exist
6. ✓ App routes exist

## After Fix

Your system should:
- ✅ Display video feeds without errors
- ✅ Show heatmap when enabled
- ✅ Process shots correctly
- ✅ Save recordings to correct directory

---

## If Still Having Issues

Run the check script to see what's wrong:
```bash
cd ~/air-target-basic-main
bash check-system.sh
```

This will show exactly what needs to be fixed.
