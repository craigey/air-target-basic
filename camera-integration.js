/**
 * Camera Integration Helper for Bell Target Pro Scoring System
 * 
 * This script connects your existing scoring HTML with the Flask detection system.
 * Add this to your targets22-shooters-Gemini.html file.
 */

// ============ CONFIGURATION ============
const DETECTION_API_BASE = "http://192.168.1.100:5000";  // ⚠️ CHANGE TO YOUR PI IP
const POLL_INTERVAL_MS = 2000;  // Poll for new hits every 2 seconds
const AUTO_CONFIGURE_CAMERAS = true;  // Auto-detect cameras from API

// ============ GLOBAL STATE ============
let detectionAPI = {
    baseUrl: DETECTION_API_BASE,
    cameras: [],
    pollingActive: false,
    intervalId: null
};

// ============ INITIALIZATION ============

/**
 * Call this function when your page loads
 */
async function initDetectionSystem() {
    console.log("🎯 Initializing detection system integration...");
    
    try {
        // Load camera configuration from detection API
        const cameras = await loadCameraConfiguration();
        
        if (cameras.length === 0) {
            console.warn("No cameras detected from API. Using manual configuration.");
            return false;
        }
        
        console.log(`✅ Detected ${cameras.length} cameras`);
        detectionAPI.cameras = cameras;
        
        // Update your targets array with camera URLs
        if (AUTO_CONFIGURE_CAMERAS) {
            updateTargetsWithCameraURLs(cameras);
        }
        
        return true;
    } catch (err) {
        console.error("❌ Failed to initialize detection system:", err);
        return false;
    }
}

/**
 * Load camera configuration from Flask API
 */
async function loadCameraConfiguration() {
    const url = `${detectionAPI.baseUrl}/camera_urls`;
    
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        return data.cameras;
        
    } catch (err) {
        console.error("Failed to load camera config:", err);
        return [];
    }
}

/**
 * Update your existing targets array with camera stream URLs
 */
function updateTargetsWithCameraURLs(cameras) {
    // This assumes you have a global 'targets' array in your HTML
    // Adjust the property names to match your structure
    
    cameras.forEach(cam => {
        const targetIdx = cam.lane - 1;  // Lane 1 -> index 0
        
        if (window.targets && window.targets[targetIdx]) {
            // Update existing target with camera URLs
            window.targets[targetIdx].cameraUrl = cam.stream_url;
            window.targets[targetIdx].rawCameraUrl = cam.raw_stream_url;
            window.targets[targetIdx].hitsUrl = cam.hits_url;
            window.targets[targetIdx].cameraId = cam.camera_id;
            
            console.log(`📹 Lane ${cam.lane} -> Camera ${cam.camera_id}`);
            
            // Update the video feed element if it exists
            updateVideoFeed(cam.lane, cam.stream_url);
        }
    });
}

/**
 * Update video feed in your HTML
 */
function updateVideoFeed(laneNumber, streamUrl) {
    // Find the video/image element for this lane
    // Adjust selector to match your HTML structure
    const laneId = `target-${laneNumber}`;
    const videoElement = document.querySelector(`#${laneId} .cam-feed`);
    
    if (videoElement) {
        videoElement.src = streamUrl;
        console.log(`📺 Updated video feed for Lane ${laneNumber}`);
    }
}

// ============ SCORE POLLING ============

/**
 * Start polling for score updates
 */
function startScorePolling() {
    if (detectionAPI.pollingActive) {
        console.log("⚠️ Polling already active");
        return;
    }
    
    console.log("▶️ Starting score polling...");
    detectionAPI.pollingActive = true;
    
    // Poll immediately
    pollAllCameras();
    
    // Then poll at interval
    detectionAPI.intervalId = setInterval(pollAllCameras, POLL_INTERVAL_MS);
}

/**
 * Stop polling for score updates
 */
function stopScorePolling() {
    if (!detectionAPI.pollingActive) return;
    
    console.log("⏸️ Stopping score polling");
    detectionAPI.pollingActive = false;
    
    if (detectionAPI.intervalId) {
        clearInterval(detectionAPI.intervalId);
        detectionAPI.intervalId = null;
    }
}

/**
 * Poll all cameras for new hits
 */
async function pollAllCameras() {
    const promises = detectionAPI.cameras.map(cam => 
        pollCameraHits(cam.camera_id, cam.lane)
    );
    
    await Promise.all(promises);
}

/**
 * Poll a specific camera for hits
 */
async function pollCameraHits(cameraId, lane) {
    try {
        const response = await fetch(`${detectionAPI.baseUrl}/hits/${cameraId}`);
        if (!response.ok) return;
        
        const hits = await response.json();
        
        // Update your UI with the hits
        updateLaneScores(lane, hits);
        
    } catch (err) {
        console.error(`Error polling camera ${cameraId}:`, err);
    }
}

/**
 * Update scores in your HTML for a specific lane
 */
function updateLaneScores(lane, hits) {
    if (!hits || hits.length === 0) return;
    
    // This is where you integrate with your existing scoring logic
    // Adjust to match your HTML structure and functions
    
    // Example: Update player scores
    const player = getPlayerForLane(lane);
    if (!player) return;
    
    // Update shots array
    const currentRound = getCurrentRound();
    if (!player.rounds[currentRound]) return;
    
    hits.forEach((hit, idx) => {
        // Only update if shot doesn't exist yet
        if (!player.rounds[currentRound].shots[idx]) {
            player.rounds[currentRound].shots[idx] = hit.score;
            
            // Trigger visual update (adjust function name to match yours)
            if (typeof updateScoreDisplay === 'function') {
                updateScoreDisplay(player, currentRound);
            }
            
            console.log(`📊 Lane ${lane}, Shot ${idx + 1}: ${hit.score}`);
        }
    });
}

// ============ CAMERA CONTROL ============

/**
 * Lock exposure on all cameras (recommended before competition)
 */
async function lockAllCameraExposures() {
    console.log("🔒 Locking camera exposures...");
    
    const promises = detectionAPI.cameras.map(cam => 
        fetch(`${detectionAPI.baseUrl}/lock_exposure/${cam.camera_id}`)
    );
    
    await Promise.all(promises);
    console.log("✅ All camera exposures locked");
}

/**
 * Get scoring configuration (4-ring vs 3-ring, bull hole bonus)
 */
async function getScoringConfig() {
    try {
        const response = await fetch(`${detectionAPI.baseUrl}/get_scoring_config`);
        const config = await response.json();
        
        console.log("Scoring config:", config);
        return config;
        
    } catch (err) {
        console.error("Failed to get scoring config:", err);
        return null;
    }
}

/**
 * Set zoom for a specific camera
 */
async function setCameraZoom(cameraId, zoomLevel) {
    try {
        const response = await fetch(
            `${detectionAPI.baseUrl}/set_zoom/${cameraId}/${zoomLevel}`
        );
        const result = await response.json();
        
        console.log(`🔍 Camera ${cameraId} zoom: ${result.zoom}x`);
        return result.zoom;
        
    } catch (err) {
        console.error(`Failed to set zoom for camera ${cameraId}:`, err);
        return null;
    }
}

// ============ HELPER FUNCTIONS ============

/**
 * Get player assigned to a specific lane
 * (Adjust this to match your player/target assignment logic)
 */
function getPlayerForLane(lane) {
    // Example implementation - adjust to your structure
    if (!window.players) return null;
    
    const currentRound = getCurrentRound();
    return window.players.find(p => 
        p.assignments && p.assignments[currentRound] === lane
    );
}

/**
 * Get current round number
 * (Adjust to match your round tracking)
 */
function getCurrentRound() {
    // Example - adjust to your structure
    return window.currentRound || 0;
}

// ============ EXAMPLE USAGE ============

/*
Add this to your HTML file's <script> section:

// On page load
window.addEventListener('load', async function() {
    // Initialize detection system
    const success = await initDetectionSystem();
    
    if (success) {
        console.log("✅ Detection system ready");
        
        // Lock exposures before starting
        await lockAllCameraExposures();
        
        // Start polling for scores
        startScorePolling();
        
        // Optional: Set zoom for each camera
        // await setCameraZoom(0, 2.0);  // Lane 1: 2x zoom
        // await setCameraZoom(1, 1.5);  // Lane 2: 1.5x zoom
    } else {
        console.warn("⚠️ Detection system not available - using manual mode");
    }
});

// When competition starts
function onCompetitionStart() {
    startScorePolling();
}

// When competition ends
function onCompetitionEnd() {
    stopScorePolling();
}

// Manual camera control buttons (add to your UI)
document.getElementById('btnLockExposures').addEventListener('click', () => {
    lockAllCameraExposures();
});

document.getElementById('btnZoomIn').addEventListener('click', async () => {
    const currentCam = getSelectedCamera();  // Your function
    await setCameraZoom(currentCam, 2.0);
});

*/

// ============ EXPORT ============

// Make functions available globally
window.detectionAPI = detectionAPI;
window.initDetectionSystem = initDetectionSystem;
window.startScorePolling = startScorePolling;
window.stopScorePolling = stopScorePolling;
window.lockAllCameraExposures = lockAllCameraExposures;
window.getScoringConfig = getScoringConfig;
window.setCameraZoom = setCameraZoom;

console.log("📦 Detection API integration loaded");
