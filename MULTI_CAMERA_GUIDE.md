# 🎥 Multi-Camera Setup Guide

## Overview

The system now supports **multiple cameras** for multi-lane scoring. Each camera can monitor a separate target lane.

---

## 🔧 Configuration

### 1. Set Up Cameras in config.json

```json
{
  "cameras": [0, 1, 2, 3],  // Up to 4 cameras
  ...
}
```

**Camera IDs:**
- `0` = First USB camera (Lane 1)
- `1` = Second USB camera (Lane 2)
- `2` = Third USB camera (Lane 3)
- `3` = Fourth USB camera (Lane 4)

### 2. Verify Cameras Connected

```bash
# On Raspberry Pi
ls /dev/video*

# Should show:
# /dev/video0
# /dev/video1
# /dev/video2
# /dev/video3
```

---

## 🌐 Camera Stream URLs

### Get All Camera URLs

```bash
curl http://pi-ip:5000/camera_urls
```

**Response:**
```json
{
  "base_url": "http://192.168.1.100:5000",
  "total_cameras": 4,
  "cameras": [
    {
      "camera_id": 0,
      "lane": 1,
      "stream_url": "http://192.168.1.100:5000/video/0",
      "raw_stream_url": "http://192.168.1.100:5000/raw_video/0",
      "hits_url": "http://192.168.1.100:5000/hits/0",
      "status_url": "http://192.168.1.100:5000/camera_info/0"
    },
    {
      "camera_id": 1,
      "lane": 2,
      "stream_url": "http://192.168.1.100:5000/video/1",
      ...
    },
    ...
  ]
}
```

---

## 📺 Spectator Modes

### Mode 1: Built-in Multi-Camera Spectator

**URL:** `http://pi-ip:5000/spectator_fullscreen`

**Features:**
- Automatic grid layout (1-4 cameras)
- Real-time score updates
- Keyboard shortcuts:
  - `1` = Single camera view
  - `2` = 2x2 grid
  - `3` = 3 camera layout
  - `4` = 4 camera grid
  - `F` = Fullscreen toggle

**Best for:**
- Competition spectators
- Live match viewing
- Big screen displays

### Mode 2: External Scoring System Integration

Your existing `targets22-shooters-Gemini.html` can integrate using the camera URLs.

**Integration steps below** ↓

---

## 🔗 Integrating with External Scoring System

Your HTML scoring system expects camera URLs. Here's how to connect it:

### Option A: Manual Configuration

Edit your HTML file and add camera URLs:

```javascript
const targets = [
    {
        id: 1,
        name: "Target 1",
        cameraUrl: "http://192.168.1.100:5000/video/0",
        hitsUrl: "http://192.168.1.100:5000/hits/0"
    },
    {
        id: 2,
        name: "Target 2",
        cameraUrl: "http://192.168.1.100:5000/video/1",
        hitsUrl: "http://192.168.1.100:5000/hits/1"
    },
    // ... etc
];
```

### Option B: Dynamic Configuration (Recommended)

Add this JavaScript to your HTML to auto-detect cameras:

```javascript
// At page load
async function loadCameraConfig() {
    const API_BASE = "http://192.168.1.100:5000";  // Your Pi IP
    
    try {
        const response = await fetch(`${API_BASE}/camera_urls`);
        const data = await response.json();
        
        // Initialize targets array
        window.targets = data.cameras.map(cam => ({
            id: cam.lane,
            name: `Lane ${cam.lane}`,
            cameraUrl: cam.stream_url,
            hitsUrl: cam.hits_url,
            statusUrl: cam.status_url,
            cameraId: cam.camera_id
        }));
        
        console.log(`Loaded ${window.targets.length} cameras`);
        
        // Now render your targets
        renderTargets();
        
    } catch (err) {
        console.error("Failed to load camera config:", err);
        // Fall back to manual configuration
    }
}

// Call on page load
window.addEventListener('load', loadCameraConfig);
```

### Option C: Embed Detection System

Save your HTML as `templates/scoring.html` and access via:

```
http://pi-ip:5000/scoring
```

This allows your scoring system to run on the same Flask server.

---

## 📡 API Endpoints for External Systems

### Camera Streams

```bash
# Processed video (with detection overlays)
GET /video/{cam_id}

# Raw video (no overlays)
GET /raw_video/{cam_id}
```

### Score Data

```bash
# All hits for specific camera
GET /hits/{cam_id}

# Current round summary
GET /round_summary

# Scoring configuration
GET /get_scoring_config
```

### Camera Control

```bash
# Get camera info
GET /camera_info/{cam_id}

# Lock/unlock exposure
GET /lock_exposure/{cam_id}
GET /unlock_exposure/{cam_id}

# Zoom control
GET /set_zoom/{cam_id}/{zoom_level}
```

---

## 🎯 Multi-Lane Workflow

### Setup (One-time per session)

1. **Connect all cameras**
   ```bash
   # Verify cameras
   ls /dev/video*
   ```

2. **Update config.json**
   ```json
   {"cameras": [0, 1, 2, 3]}
   ```

3. **Start system**
   ```bash
   python3 app.py
   ```

4. **Calibrate each camera**
   - Navigate to `/calibrate` for camera 0
   - Mark center, bull, outer ring
   - Repeat for cameras 1, 2, 3

5. **Lock all exposures**
   ```bash
   for i in 0 1 2 3; do
       curl http://pi-ip:5000/lock_exposure/$i
   done
   ```

### During Competition

1. **Open spectator view**
   ```
   http://pi-ip:5000/spectator_fullscreen
   ```

2. **Start detection on all lanes**
   ```bash
   curl http://pi-ip:5000/toggle
   ```

3. **Shooters fire their rounds**
   - System detects all 4 lanes simultaneously
   - Scores update in real-time

4. **View results**
   - Spectator screen shows live scores
   - Individual lane views available
   - Export data via `/round_summary`

---

## 🔍 Per-Camera Features

Each camera operates independently:

### Individual Zoom
```bash
# Zoom camera 0 to 2x
curl http://pi-ip:5000/set_zoom/0/2.0

# Zoom camera 1 to 1.5x
curl http://pi-ip:5000/set_zoom/1/1.5
```

### Individual Calibration
- Each camera has its own calibration
- Stored separately per camera ID
- Allows different target positions/angles

### Individual Recording
- Each shot tagged with camera ID
- Separate image storage per lane
- Can review lane-by-lane

---

## 📊 Typical 4-Lane Setup

```
┌─────────────────────────────────────┐
│  Raspberry Pi 4 (Main Controller)   │
│  - 4x USB Camera Inputs             │
│  - Detection on all 4 lanes         │
│  - Web server on port 5000          │
└─────────────────────────────────────┘
          │
          │ Network (Ethernet/WiFi)
          │
    ┌─────┴─────┬─────────┬─────────┐
    │           │         │         │
┌───▼───┐ ┌───▼───┐ ┌───▼───┐ ┌───▼───┐
│Cam 0  │ │Cam 1  │ │Cam 2  │ │Cam 3  │
│Lane 1 │ │Lane 2 │ │Lane 3 │ │Lane 4 │
└───────┘ └───────┘ └───────┘ └───────┘
   │         │         │         │
   ▼         ▼         ▼         ▼
 Target   Target   Target   Target
   #1       #2       #3       #4
```

---

## ⚙️ Performance Considerations

### CPU Usage (Raspberry Pi 4)

- **1 camera:** ~25-30% CPU
- **2 cameras:** ~50-60% CPU
- **3 cameras:** ~75-85% CPU
- **4 cameras:** ~95-100% CPU

**Optimization tips:**
- Lower resolution to 640x480 for 4 cameras
- Disable color detection if not needed
- Reduce frame rate to 20 FPS
- Use Pi 4 with 4GB+ RAM

### Network Bandwidth

- **Per camera stream:** ~2-5 Mbps
- **4 cameras total:** ~10-20 Mbps
- Use wired Ethernet for best performance

---

## 🐛 Troubleshooting Multi-Camera

### Camera Not Detected

```bash
# List cameras
v4l2-ctl --list-devices

# Test specific camera
v4l2-ctl -d /dev/video1 --all
```

### Video Stream Lag

**Solutions:**
1. Lower resolution in `camera_manager.py`:
   ```python
   cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
   cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
   ```

2. Reduce frame rate:
   ```python
   cap.set(cv2.CAP_PROP_FPS, 20)
   ```

3. Use wired Ethernet connection

### Cameras Swapping IDs

If cameras swap IDs on reboot:

```bash
# Create udev rule
sudo nano /etc/udev/rules.d/99-camera.rules

# Add (adjust for your cameras):
SUBSYSTEM=="video4linux", ATTRS{serial}=="ABC123", SYMLINK+="camera0"
SUBSYSTEM=="video4linux", ATTRS{serial}=="DEF456", SYMLINK+="camera1"
```

### Detection Interference

Cameras may detect neighbor's shots if fields overlap.

**Solutions:**
- Use digital zoom to narrow field of view
- Add physical barriers between lanes
- Adjust camera angles
- Use tighter calibration

---

## 📝 External System Integration Checklist

For integrating with your scoring HTML:

- [ ] Flask server running on Pi
- [ ] All cameras connected and detected
- [ ] Config.json updated with camera IDs
- [ ] Each camera calibrated individually
- [ ] Exposure locked on all cameras
- [ ] `/camera_urls` endpoint returns all cameras
- [ ] Video streams accessible from browser
- [ ] Scoring HTML updated with camera URLs
- [ ] Network allows cross-origin requests if needed
- [ ] Test all 4 streams simultaneously

---

## 🔐 CORS Configuration (If Needed)

If your external HTML is on a different domain:

```python
# Add to app.py
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
```

---

## 💡 Advanced: Camera Verification

Some leagues may want dual-camera verification per lane.

**Setup:**
```json
{
  "cameras": [0, 1, 2, 3, 4, 5],
  "camera_pairs": {
    "lane1": [0, 1],  // Lane 1 has cameras 0 and 1
    "lane2": [2, 3],  // Lane 2 has cameras 2 and 3
    "lane3": [4, 5]   // Lane 3 has cameras 4 and 5
  }
}
```

This would require custom logic to compare scores from both cameras.

---

## 📖 Summary

### Single Camera (Current)
- Simple setup
- Lower CPU usage
- One target per system

### Multi-Camera (New)
- Up to 4 cameras/lanes
- Simultaneous detection
- Shared web interface
- Individual camera control
- Perfect for competitions

Choose based on your needs!
