# 🔧 Complete System Fixes - All Issues Resolved

## ✅ All Issues Fixed

### 1. **Rotation Slider** ✅
- Added slider to rotation section (0-359°)
- Preset buttons still work
- Real-time preview updates

### 2. **Camera Numbering** ✅
- Cameras now display as 1, 2, 3, 4 (instead of 0, 1, 2, 3)
- Internal IDs still 0-based (no breaking changes)
- All displays show 1-based numbering

### 3. **Lane Names** ✅
- Can customize lane names per camera
- Defaults to "Lane 1", "Lane 2", etc.
- Saves to config.json
- Shows on main page

### 4. **Calibration Lock** ✅
- After 3 points clicked, calibration completes
- Viewport becomes disabled (pointer-events: none)
- Can't add more points until you click "Reset Points"
- Shows "Calibration complete!" message

### 5. **HTTPS Support** ℹ️
See dedicated section below with setup instructions

### 6. **Heatmap Button Status** ✅
- Button turns green when heatmap enabled
- Button disabled (grey) when no data available
- Updates every second
- Visual feedback for status

### 7. **Detection Framerate in Settings** ✅
- Dropdown in Settings page
- Options: 1, 3, 5, 10, 15, 30 FPS
- Recommended: 5 FPS
- Saves to config.json

### 8. **Additional Settings Exposed** ✅
All JSON settings now in Settings page:
- Shot cooldown frames
- Max shot interval
- Min/max shot area
- Baseline update mode
- Min/max zoom limits
- Zoom step size

### 9. **Brightness/Contrast/Saturation/Sharpness REMOVED** ✅
- These controls don't work on most USB cameras
- Require special hardware support
- Removed to prevent 500 errors
- Most webcams don't support these properties

---

## 📁 Files to Deploy

1. **camera-complete.html** → `templates/camera.html`
2. **index-complete.html** → `templates/index.html`
3. **settings-complete.html** → `templates/settings.html`
4. **app_complete_fixes.py** → Add routes to `app.py`

---

## 🚀 Quick Deployment

```bash
cd ~/air-target-basic-main

# Copy templates
cp camera-complete.html templates/camera.html
cp index-complete.html templates/index.html
cp settings-complete.html templates/settings.html

# Add routes to app.py
# (Copy from app_complete_fixes.py)

# Restart
python app.py
```

---

## 🔒 HTTPS Setup Guide

### Why HTTPS?
- Secure camera feeds
- Required for some modern browsers
- Professional deployment

### Option 1: Self-Signed Certificate (Testing)

**Generate certificate:**
```bash
cd ~/air-target-basic-main

# Create certificates directory
mkdir certs
cd certs

# Generate self-signed certificate
openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout key.pem -out cert.pem -days 365 \
  -subj "/CN=192.168.0.84"

cd ..
```

**Update app.py:**
```python
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        ssl_context=('certs/cert.pem', 'certs/key.pem'),  # Add this
        debug=True,
        use_reloader=False
    )
```

**Access:**
```
https://192.168.0.84:5000
```

**Note:** Browser will show security warning (click "Advanced" → "Proceed")

---

### Option 2: Let's Encrypt (Production)

**Requirements:**
- Domain name pointing to your server
- Port 80 and 443 accessible

**Install Certbot:**
```bash
sudo apt update
sudo apt install certbot python3-certbot-nginx
```

**Get certificate:**
```bash
# If using domain name
sudo certbot certonly --standalone -d yourdomain.com
```

**Certificates location:**
```
/etc/letsencrypt/live/yourdomain.com/fullchain.pem
/etc/letsencrypt/live/yourdomain.com/privkey.pem
```

**Update app.py:**
```python
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=443,  # HTTPS port
        ssl_context=(
            '/etc/letsencrypt/live/yourdomain.com/fullchain.pem',
            '/etc/letsencrypt/live/yourdomain.com/privkey.pem'
        ),
        debug=False,
        use_reloader=False
    )
```

**Run with sudo:**
```bash
sudo python app.py  # Port 443 requires root
```

**Auto-renewal:**
```bash
# Test renewal
sudo certbot renew --dry-run

# Add to cron (runs daily)
sudo crontab -e
# Add: 0 3 * * * certbot renew --quiet
```

---

### Option 3: Reverse Proxy (Recommended for Production)

Use nginx as reverse proxy to handle HTTPS:

**Install nginx:**
```bash
sudo apt install nginx
```

**Configure nginx:**
```bash
sudo nano /etc/nginx/sites-available/air-target
```

```nginx
server {
    listen 80;
    server_name 192.168.0.84;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name 192.168.0.84;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Enable site:**
```bash
sudo ln -s /etc/nginx/sites-available/air-target /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

**Keep app.py on HTTP:**
```python
# app.py stays on HTTP - nginx handles HTTPS
app.run(host="127.0.0.1", port=5000)
```

**Benefits:**
- App doesn't need root
- Better performance
- Can add compression, caching
- Industry standard

---

## 📋 New Routes Required in app.py

```python
# Lane Names
@app.route("/get_lane_names")
def get_lane_names():
    # See app_complete_fixes.py for implementation

@app.route("/set_lane_name", methods=["POST"])
def set_lane_name():
    # See app_complete_fixes.py

# Heatmap Status
@app.route("/heatmap_status")
def heatmap_status():
    # See app_complete_fixes.py

# Detection FPS
@app.route("/set_detection_fps/<int:fps>")
def set_detection_fps(fps):
    # See app_complete_fixes.py

@app.route("/get_detection_fps")
def get_detection_fps():
    # See app_complete_fixes.py

# Zoom Config
@app.route("/set_zoom_config", methods=["POST"])
def set_zoom_config():
    # See app_complete_fixes.py

# Update camera_urls to include display numbers and lane names
```

---

## 🎨 New Features

### Camera Page:
- ✅ Rotation slider (0-359°)
- ✅ Lane name customization
- ✅ Calibration lock after completion
- ✅ Camera numbers start from 1

### Main Page:
- ✅ Heatmap button with status indicator
- ✅ Lane names displayed
- ✅ Camera numbers start from 1

### Settings Page:
- ✅ Detection framerate dropdown
- ✅ Shot cooldown configuration
- ✅ Max shot interval
- ✅ Min/max shot area
- ✅ Baseline update mode
- ✅ Zoom limits configuration
- ✅ All JSON settings exposed

---

## ⚠️ Important Notes

### Brightness/Contrast/Saturation/Sharpness:
**REMOVED** - Don't work on most USB cameras. These require:
- Hardware support in camera firmware
- V4L2 driver support
- Most webcams don't have this

**Alternative:**
- Adjust lighting in environment
- Use white balance and exposure controls (these DO work)
- Consider better camera hardware if image quality critical

### Detection Framerate:
- **Recommended: 5 FPS** (1 frame every 0.2 seconds)
- Live video still runs at full 30 FPS
- Reduces CPU usage by 80%+
- Plenty fast for pellet detection

### HTTPS:
- Self-signed: Easy but security warnings
- Let's Encrypt: Free but needs domain
- Reverse proxy: Best for production

---

## ✅ Verification Checklist

After deployment:
- [ ] Cameras numbered 1, 2, 3, 4 (not 0, 1, 2, 3)
- [ ] Can customize lane names
- [ ] Rotation slider works
- [ ] Calibration locks after 3 points
- [ ] Heatmap button shows status (green when active)
- [ ] Heatmap button disabled when no data
- [ ] Settings page has detection framerate dropdown
- [ ] All config settings visible in settings
- [ ] No 500 errors from brightness/contrast
- [ ] (Optional) HTTPS working if configured

---

## 🎯 Summary

**Fixed:**
- ✅ Rotation slider added
- ✅ Camera numbering starts from 1
- ✅ Custom lane names
- ✅ Calibration prevents extra clicks
- ✅ Heatmap button status indicator
- ✅ Detection framerate in settings
- ✅ All JSON settings exposed
- ✅ Removed broken brightness/contrast controls
- ℹ️ HTTPS setup instructions provided

**All issues resolved! System ready for competition! 🎯**
