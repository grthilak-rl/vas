/**
 * VAS Integration Example
 * Shows how VAS frontend can integrate with the Janus FastAPI service
 */

class VASJanusClient {
    constructor(janusApiUrl) {
        this.apiUrl = janusApiUrl; // e.g., 'http://localhost:3000'
        this.activeSessions = new Map();
    }

    /**
     * Add a new camera to the streaming service
     */
    async addCamera(cameraConfig) {
        try {
            const response = await fetch(`${this.apiUrl}/cameras`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(cameraConfig)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            console.log('Camera added successfully:', result);
            return result;
        } catch (error) {
            console.error('Failed to add camera:', error);
            throw error;
        }
    }

    /**
     * Get all cameras from the service
     */
    async getCameras() {
        try {
            const response = await fetch(`${this.apiUrl}/cameras`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Failed to get cameras:', error);
            throw error;
        }
    }

    /**
     * Get WebRTC stream information for a camera
     */
    async getStreamInfo(cameraId) {
        try {
            const response = await fetch(`${this.apiUrl}/cameras/${cameraId}/stream`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Failed to get stream info:', error);
            throw error;
        }
    }

    /**
     * Create a WebRTC connection for a camera stream
     */
    async startCameraStream(cameraId, videoElement) {
        try {
            // Get stream information from our API
            const streamInfo = await this.getStreamInfo(cameraId);
            
            // Initialize Janus if not already done
            if (!window.Janus) {
                throw new Error('Janus library not loaded');
            }

            return new Promise((resolve, reject) => {
                // Create Janus session
                const janus = new Janus({
                    server: streamInfo.janus_url,
                    iceServers: [
                        {urls: "stun:stun.l.google.com:19302"}
                    ],
                    success: () => {
                        console.log('Connected to Janus server');
                        
                        // Attach to streaming plugin
                        janus.attach({
                            plugin: "janus.plugin.streaming",
                            success: (pluginHandle) => {
                                console.log('Successfully attached to streaming plugin');
                                
                                // Start watching the stream
                                pluginHandle.send({
                                    message: { 
                                        request: "watch", 
                                        id: streamInfo.stream_id 
                                    }
                                });
                                
                                // Store session for cleanup
                                this.activeSessions.set(cameraId, {
                                    janus: janus,
                                    handle: pluginHandle
                                });
                                
                                resolve(pluginHandle);
                            },
                            error: (error) => {
                                console.error('Error attaching to streaming plugin:', error);
                                reject(error);
                            },
                            onmessage: (msg, jsep) => {
                                console.log('Message from plugin:', msg);
                                
                                if (jsep) {
                                    console.log('Handling remote JSEP:', jsep.type);
                                    pluginHandle.createAnswer({
                                        jsep: jsep,
                                        media: { 
                                            audioSend: false, 
                                            videoSend: false, 
                                            audioRecv: true, 
                                            videoRecv: true 
                                        },
                                        success: (answer) => {
                                            console.log('Created answer successfully');
                                            pluginHandle.send({
                                                message: { request: "start" },
                                                jsep: answer
                                            });
                                        },
                                        error: (error) => {
                                            console.error('WebRTC error:', error);
                                            reject(error);
                                        }
                                    });
                                }
                                
                                if (msg.result && msg.result.status === "playing") {
                                    console.log('Stream is now playing!');
                                }
                            },
                            onremotetrack: (track, mid, added, metadata) => {
                                console.log('Remote track event:', track.kind, 'added:', added);
                                
                                if (added && track.kind === 'video') {
                                    console.log('Adding video track to video element');
                                    const stream = new MediaStream([track]);
                                    videoElement.srcObject = stream;
                                }
                            },
                            oncleanup: () => {
                                console.log('Plugin cleanup');
                                videoElement.srcObject = null;
                            }
                        });
                    },
                    error: (error) => {
                        console.error('Error connecting to Janus:', error);
                        reject(error);
                    }
                });
            });
            
        } catch (error) {
            console.error('Failed to start camera stream:', error);
            throw error;
        }
    }

    /**
     * Stop a camera stream
     */
    async stopCameraStream(cameraId) {
        const session = this.activeSessions.get(cameraId);
        if (session) {
            try {
                if (session.handle) {
                    session.handle.hangup();
                }
                if (session.janus) {
                    session.janus.destroy();
                }
                this.activeSessions.delete(cameraId);
                console.log(`Stopped stream for camera ${cameraId}`);
            } catch (error) {
                console.error('Error stopping stream:', error);
            }
        }
    }

    /**
     * Remove a camera from the service
     */
    async removeCamera(cameraId) {
        try {
            // Stop stream first
            await this.stopCameraStream(cameraId);
            
            // Remove from service
            const response = await fetch(`${this.apiUrl}/cameras/${cameraId}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            console.log('Camera removed successfully:', result);
            return result;
        } catch (error) {
            console.error('Failed to remove camera:', error);
            throw error;
        }
    }

    /**
     * Restart a camera stream
     */
    async restartCamera(cameraId) {
        try {
            const response = await fetch(`${this.apiUrl}/cameras/${cameraId}/restart`, {
                method: 'POST'
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            console.log('Camera restarted successfully:', result);
            return result;
        } catch (error) {
            console.error('Failed to restart camera:', error);
            throw error;
        }
    }

    /**
     * Check service health
     */
    async checkHealth() {
        try {
            const response = await fetch(`${this.apiUrl}/health`);
            return await response.json();
        } catch (error) {
            console.error('Health check failed:', error);
            return { status: 'unhealthy', error: error.message };
        }
    }
}

// Usage example for VAS developers
class VASCameraManager {
    constructor() {
        this.janusClient = new VASJanusClient('http://localhost:3000');
        this.cameraGrid = document.getElementById('camera-grid');
    }

    async initializeVAS() {
        try {
            // Check if Janus service is healthy
            const health = await this.janusClient.checkHealth();
            console.log('Janus service health:', health);

            // Load existing cameras
            await this.loadCameras();
        } catch (error) {
            console.error('Failed to initialize VAS:', error);
        }
    }

    async loadCameras() {
        try {
            const cameras = await this.janusClient.getCameras();
            this.renderCameraGrid(cameras);
        } catch (error) {
            console.error('Failed to load cameras:', error);
        }
    }

    renderCameraGrid(cameras) {
        this.cameraGrid.innerHTML = '';
        
        cameras.forEach(camera => {
            const cameraDiv = document.createElement('div');
            cameraDiv.className = 'camera-card';
            cameraDiv.innerHTML = `
                <div class="camera-header">
                    <h3>${camera.name}</h3>
                    <span class="status ${camera.status}">${camera.status}</span>
                </div>
                <video id="video-${camera.camera_id}" 
                       autoplay playsinline muted 
                       style="width: 100%; background: #000;">
                </video>
                <div class="camera-controls">
                    <button onclick="vasManager.startStream('${camera.camera_id}')">Start</button>
                    <button onclick="vasManager.stopStream('${camera.camera_id}')">Stop</button>
                    <button onclick="vasManager.restartCamera('${camera.camera_id}')">Restart</button>
                </div>
            `;
            this.cameraGrid.appendChild(cameraDiv);
        });
    }

    async startStream(cameraId) {
        try {
            const videoElement = document.getElementById(`video-${cameraId}`);
            await this.janusClient.startCameraStream(cameraId, videoElement);
            console.log(`Started stream for camera ${cameraId}`);
        } catch (error) {
            console.error('Failed to start stream:', error);
            alert(`Failed to start stream: ${error.message}`);
        }
    }

    async stopStream(cameraId) {
        try {
            await this.janusClient.stopCameraStream(cameraId);
            console.log(`Stopped stream for camera ${cameraId}`);
        } catch (error) {
            console.error('Failed to stop stream:', error);
        }
    }

    async restartCamera(cameraId) {
        try {
            await this.janusClient.restartCamera(cameraId);
            console.log(`Restarted camera ${cameraId}`);
        } catch (error) {
            console.error('Failed to restart camera:', error);
            alert(`Failed to restart camera: ${error.message}`);
        }
    }

    async addNewCamera(cameraConfig) {
        try {
            await this.janusClient.addCamera(cameraConfig);
            await this.loadCameras(); // Refresh the grid
        } catch (error) {
            console.error('Failed to add camera:', error);
            alert(`Failed to add camera: ${error.message}`);
        }
    }
}

// Initialize VAS when DOM is ready
let vasManager;
document.addEventListener('DOMContentLoaded', () => {
    vasManager = new VASCameraManager();
    vasManager.initializeVAS();
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { VASJanusClient, VASCameraManager };
}