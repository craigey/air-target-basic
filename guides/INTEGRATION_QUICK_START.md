# 🔗 External Scoring System Integration

## Quick Integration Steps

Your `targets22-shooters-Gemini.html` file can connect to the detection system in **3 easy steps**:

---

## Step 1: Add Integration Script

Add this script tag to your HTML (just before `</body>`):

```html
<script src="http://YOUR-PI-IP:5000/static/camera-integration.js"></script>
```

Or copy the contents of `camera-integration.js` directly into your HTML.

---

## Step 2: Configure API Base URL

At the top of your script section, set the Pi's IP address:

```javascript
const DETECTION_API_BASE = "http://192.168.1.100:5000";  // ⚠️ Change this!
```

---

## Step 3: Initialize on Page Load

Add this to your existing window.onload or init function:

```javascript
window.addEventListener('load', async function() {
    // ... your existing initialization code ...
    
    // Initialize detection system
    const success = await initDetectionSystem();
    
    if (success) {
        console.log("✅ Detection system connected");
        
        // Lock camera exposures before competition
        await lockAllCameraExposures();
        
        // Start polling for scores
        startScorePolling();
    } else {
        console.warn("⚠️ Using manual scoring mode");
    }
});
```

**That's it!** Your scoring system now receives automatic scores from the cameras.

---

## What This Does

### Automatic Camera Discovery
```javascript
await initDetectionSystem();
```
- Contacts Flask API at `/camera_urls`
- Gets all connected cameras automatically
- Updates your `targets` array with stream URLs

### Live Video Feeds
Each target viewport will show the live camera stream:
```html
<img class="cam-feed" src="http://pi-ip:5000/video/0" />
```

### Automatic Score Updates
```javascript
startScorePolling();
```
- Polls `/hits/{camera_id}` every 2 seconds
- Updates player scores automatically
- Displays shots as they're detected

### Camera Control
```javascript
// Lock exposures before competition
await lockAllCameraExposures();

// Adjust zoom for specific lane
await setCameraZoom(0, 2.0);  // Lane 1: 2x zoom
```

---

## Integration Points in Your HTML

### 1. Camera Feeds

**Find this in your HTML:**
```html
<img class="cam-feed" src="" ... />
```

**Will auto-update to:**
```html
<img class="cam-feed" src="http://pi-ip:5000/video/0" />
```

### 2. Score Updates

When a shot is detected, your existing scoring functions are called:
```javascript
// Detected: Lane 1, Shot 3, Score 5
→ Calls your updateScoreDisplay(player, round)
→ Your UI updates automatically
```

### 3. Target Assignment

If you're using round-robin or custom assignments, the integration respects this:
```javascript
// Round 1: Player "John" assigned to Lane 2
// Detection system sends scores to Lane 2
// Integration maps Lane 2 → Player "John"
// Scores update for John automatically
```

---

## Advanced Configuration

### Manual Camera Assignment

If you don't want auto-detection:

```javascript
const AUTO_CONFIGURE_CAMERAS = false;  // At top of integration script

// Then manually set:
window.targets = [
    {
        id: 1,
        name: "Target 1",
        cameraUrl: "http://192.168.1.100:5000/video/0",
        hitsUrl: "http://192.168.1.100:5000/hits/0"
    },
    // ... etc
];
```

### Custom Polling Interval

Change how often scores are checked:

```javascript
const POLL_INTERVAL_MS = 1000;  // Poll every 1 second (faster)
// or
const POLL_INTERVAL_MS = 5000;  // Poll every 5 seconds (slower)
```

### Selective Polling

Only poll during active rounds:

```javascript
// When round starts
function onRoundStart() {
    startScorePolling();
}

// When round ends
function onRoundEnd() {
    stopScorePolling();
}
```

---

## API Reference

### Available Functions

```javascript
// Initialization
await initDetectionSystem()

// Polling control
startScorePolling()
stopScorePolling()

// Camera control
await lockAllCameraExposures()
await setCameraZoom(cameraId, zoomLevel)

// Configuration
await getScoringConfig()
```

### Available Endpoints

```bash
# Camera info
GET /camera_urls
GET /camera_info/{cam_id}

# Video streams
GET /video/{cam_id}           # With detection overlay
GET /raw_video/{cam_id}       # Raw feed

# Scores
GET /hits/{cam_id}            # Hits for specific camera
GET /round_summary            # All cameras summary

# Control
GET /lock_exposure/{cam_id}
GET /set_zoom/{cam_id}/{zoom}
```

---

## Workflow Example

### Pre-Competition Setup

1. **Start detection system on Pi**
   ```bash
   python3 app.py
   ```

2. **Open your scoring HTML**
   ```
   http://your-laptop-ip/targets22-shooters-Gemini.html
   ```

3. **Auto-connection happens**
   - Script contacts Pi
   - Loads camera URLs
   - Updates video feeds
   - Ready for scoring

### During Competition

1. **Assign players to lanes** (your existing UI)
2. **Click "Start Round"** (your existing button)
3. **Shooters fire 6 shots**
4. **Scores appear automatically** in your UI
5. **Click "Next Round"** (your existing button)
6. Repeat!

### Post-Competition

1. **Export results** (your existing export function)
2. **View recordings** on Pi: `http://pi-ip:5000/rounds`
3. **Review disputes** using stack/unstack feature

---

## Troubleshooting

### Video feeds not showing

**Check:**
```javascript
console.log(window.detectionAPI.cameras);
```

Should show:
```javascript
[
  {camera_id: 0, lane: 1, stream_url: "http://..."}, 
  ...
]
```

**Fix:**
- Verify Pi IP address is correct
- Check `config.json` has cameras: [0, 1, 2, 3]
- Ensure Flask app running

### Scores not updating

**Check browser console:**
```
📊 Lane 1, Shot 1: 5
📊 Lane 1, Shot 2: 4
```

**If nothing appearing:**
- Verify `startScorePolling()` was called
- Check network tab for `/hits/` requests
- Ensure cameras calibrated
- Check detection is active on Pi

### CORS errors

If your HTML is on different domain:

**Add to Pi's app.py:**
```python
from flask_cors import CORS
CORS(app)
```

**Install:**
```bash
pip3 install flask-cors
```

---

## Testing the Integration

### 1. Test API Connection

Open browser console:
```javascript
await initDetectionSystem()
// Should log: "✅ Detected X cameras"
```

### 2. Test Video Streams

Navigate to:
```
http://pi-ip:5000/video/0
```
Should show live camera feed.

### 3. Test Score Polling

```javascript
startScorePolling()
// Fire a shot at target
// Wait 2 seconds
// Check console for: "📊 Lane 1, Shot 1: 5"
```

### 4. Manual Score Injection

For testing without shooting:
```javascript
// Manually update a score
updateLaneScores(1, [{
    score: 5,
    x: 320,
    y: 240,
    confidence: 0.95
}]);
```

---

## Benefits of Integration

### ✅ Automatic Scoring
- No manual input needed
- Instant score updates
- Reduced human error

### ✅ Video Verification
- Live camera feeds in your interface
- Can review disputed shots
- Stack/unstack feature for verification

### ✅ Flexible Control
- Control zoom from your interface
- Lock exposures remotely
- Configure scoring rules (4-ring/3-ring)

### ✅ Competition Ready
- Handles 1-4 lanes simultaneously
- Real-time spectator view available
- Export with verified scores

---

## Next Steps

1. ✅ Copy `camera-integration.js` to your project
2. ✅ Add script tag to your HTML
3. ✅ Set `DETECTION_API_BASE` to your Pi IP
4. ✅ Add `initDetectionSystem()` to page load
5. ✅ Test with one camera first
6. ✅ Expand to multiple cameras
7. ✅ Run test competition

**Questions?** See `MULTI_CAMERA_GUIDE.md` for more details!
