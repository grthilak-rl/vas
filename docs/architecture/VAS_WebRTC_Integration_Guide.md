# VAS WebRTC Integration Guide for Third-Party Developers

## Overview

This guide provides step-by-step instructions for integrating VAS (Video Analytics System) WebRTC video feeds into third-party applications. The VAS system exposes WebRTC streaming endpoints that allow external applications to consume live camera feeds.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Authentication](#authentication)
3. [API Endpoints](#api-endpoints)
4. [WebRTC Integration](#webrtc-integration)
5. [Complete Example](#complete-example)
6. [Troubleshooting](#troubleshooting)
7. [Best Practices](#best-practices)

## Prerequisites

### Required Libraries
- **Janus WebRTC JavaScript Library**: For WebRTC communication
- **WebRTC Adapter**: For cross-browser compatibility
- **HTTP Client**: For API communication (fetch, axios, etc.)

### Browser Support
- Chrome/Chromium 80+
- Firefox 75+
- Safari 13+
- Edge 80+

### Network Requirements
- WebSocket connection to VAS server (port 8188)
- HTTP/HTTPS access to VAS API (port 8000)

## Authentication

### 1. Obtain Authentication Token

```javascript
async function authenticate(username, password) {
    const response = await fetch('http://YOUR_VAS_SERVER:8000/api/auth/login-json', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            username: username,
            password: password
        })
    });
    
    if (!response.ok) {
        throw new Error('Authentication failed');
    }
    
    const data = await response.json();
    return data.access_token;
}

// Usage
const token = await authenticate('admin', 'admin123');
```

### 2. Include Token in API Requests

```javascript
const headers = {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
};
```

## API Endpoints

### 1. Discover Available Streams

```javascript
async function getAvailableStreams(token) {
    const response = await fetch('http://YOUR_VAS_SERVER:8000/api/streams/webrtc/streams', {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
    
    const data = await response.json();
    return data.streams;
}

// Example response
[
    {
        "stream_id": "1",
        "name": "Live Camera 1 - Office",
        "type": "rtsp",
        "status": "active",
        "metadata": "VAS Live Camera 1 - Direct RTSP",
        "enabled": true,
        "webrtc_endpoint": "/api/streams/webrtc/streams/1/config"
    },
    {
        "stream_id": "2", 
        "name": "Live Camera 2 - Lobby",
        "type": "rtsp",
        "status": "active",
        "metadata": "VAS Live Camera 2 - Direct RTSP",
        "enabled": true,
        "webrtc_endpoint": "/api/streams/webrtc/streams/2/config"
    }
]
```

### 2. Get WebRTC Configuration

```javascript
async function getWebRTCConfig(token, streamId) {
    const response = await fetch(`http://YOUR_VAS_SERVER:8000/api/streams/webrtc/streams/${streamId}/config`, {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
    
    const data = await response.json();
    return data;
}

// Example response
{
    "stream_id": "1",
    "janus_ws_url": "ws://YOUR_VAS_SERVER:8188",
    "janus_http_url": "http://YOUR_VAS_SERVER:8088",
    "plugin_name": "janus.plugin.streaming",
    "mountpoint_id": 1,
    "stream_name": "Live Camera 1 - Office"
}
```

### 3. Check Stream Status

```javascript
async function getStreamStatus(token, streamId) {
    const response = await fetch(`http://YOUR_VAS_SERVER:8000/api/streams/webrtc/streams/${streamId}/status`, {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
    
    const data = await response.json();
    return data;
}
```

## WebRTC Integration

### 1. Include Required Libraries

```html
<!-- WebRTC Adapter (must be loaded first) -->
<script src="https://webrtc.github.io/adapter/adapter-latest.js"></script>
<!-- Janus WebRTC Library -->
<script src="https://janus.conf.meetecho.com/janus.js"></script>
```

### 2. Initialize Janus

```javascript
function initJanus() {
    return new Promise((resolve, reject) => {
        Janus.init({
            debug: "all", // Set to false for production
            callback: function() {
                console.log('Janus initialized successfully');
                resolve();
            }
        });
    });
}
```

### 3. Connect to Janus and Start Stream

```javascript
async function startStream(token, streamId, videoElement) {
    // Get WebRTC configuration
    const config = await getWebRTCConfig(token, streamId);
    
    // Initialize Janus
    await initJanus();
    
    // Create Janus session
    const janus = new Janus({
        server: config.janus_ws_url,
        success: function() {
            console.log('Connected to Janus');
            
            // Attach to streaming plugin
            janus.attach({
                plugin: config.plugin_name,
                success: function(pluginHandle) {
                    console.log('Attached to streaming plugin');
                    
                    // Send watch request
                    pluginHandle.send({
                        message: { request: "watch", id: config.mountpoint_id }
                    });
                    
                    // Handle plugin messages
                    pluginHandle.onmessage = function(msg, jsep) {
                        console.log('Received message:', msg);
                        
                        if (jsep) {
                            // Handle SDP offer
                            pluginHandle.createAnswer({
                                jsep: jsep,
                                success: function(jsep) {
                                    pluginHandle.send({
                                        message: { request: "start" },
                                        jsep: jsep
                                    });
                                },
                                error: function(error) {
                                    console.error('Error creating answer:', error);
                                }
                            });
                        }
                    };
                    
                    // Handle remote track (CRITICAL for video display)
                    pluginHandle.onremotetrack = function(track, mid, on) {
                        console.log(`Remote track: ${track.kind} (${on ? 'on' : 'off'})`);
                        
                        if (track.kind === 'video' && on) {
                            // Create MediaStream from track
                            const stream = new MediaStream([track]);
                            
                            // Set video element source
                            videoElement.srcObject = stream;
                            
                            // Play video
                            videoElement.play().catch(e => {
                                console.error('Video play failed:', e);
                            });
                        }
                    };
                    
                    // Handle remote stream (alternative method)
                    pluginHandle.onremotestream = function(stream) {
                        console.log('Received remote stream');
                        videoElement.srcObject = stream;
                        videoElement.play().catch(e => {
                            console.error('Video play failed:', e);
                        });
                    };
                },
                error: function(error) {
                    console.error('Failed to attach to plugin:', error);
                }
            });
        },
        error: function(error) {
            console.error('Failed to connect to Janus:', error);
        }
    });
}
```

## Complete Example

### HTML

```html
<!DOCTYPE html>
<html>
<head>
    <title>VAS WebRTC Integration</title>
    <script src="https://webrtc.github.io/adapter/adapter-latest.js"></script>
    <script src="https://janus.conf.meetecho.com/janus.js"></script>
</head>
<body>
    <div>
        <h2>VAS Camera Feeds</h2>
        <div id="streams-container"></div>
    </div>
    
    <script>
        // Your JavaScript code here
    </script>
</body>
</html>
```

### JavaScript

```javascript
class VASWebRTCClient {
    constructor(serverUrl, username, password) {
        this.serverUrl = serverUrl;
        this.username = username;
        this.password = password;
        this.token = null;
        this.activeStreams = new Map();
    }
    
    async initialize() {
        // Authenticate
        this.token = await this.authenticate();
        console.log('Authentication successful');
        
        // Initialize Janus
        await this.initJanus();
        console.log('Janus initialized');
    }
    
    async authenticate() {
        const response = await fetch(`${this.serverUrl}/api/auth/login-json`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username: this.username,
                password: this.password
            })
        });
        
        if (!response.ok) {
            throw new Error('Authentication failed');
        }
        
        const data = await response.json();
        return data.access_token;
    }
    
    async initJanus() {
        return new Promise((resolve, reject) => {
            Janus.init({
                debug: "all",
                callback: resolve
            });
        });
    }
    
    async getAvailableStreams() {
        const response = await fetch(`${this.serverUrl}/api/streams/webrtc/streams`, {
            headers: { 'Authorization': `Bearer ${this.token}` }
        });
        
        const data = await response.json();
        return data.streams;
    }
    
    async getWebRTCConfig(streamId) {
        const response = await fetch(`${this.serverUrl}/api/streams/webrtc/streams/${streamId}/config`, {
            headers: { 'Authorization': `Bearer ${this.token}` }
        });
        
        return await response.json();
    }
    
    async startStream(streamId, videoElement) {
        const config = await this.getWebRTCConfig(streamId);
        
        const janus = new Janus({
            server: config.janus_ws_url,
            success: () => {
                janus.attach({
                    plugin: config.plugin_name,
                    success: (pluginHandle) => {
                        pluginHandle.send({
                            message: { request: "watch", id: config.mountpoint_id }
                        });
                        
                        pluginHandle.onmessage = (msg, jsep) => {
                            if (jsep) {
                                pluginHandle.createAnswer({
                                    jsep: jsep,
                                    success: (jsep) => {
                                        pluginHandle.send({
                                            message: { request: "start" },
                                            jsep: jsep
                                        });
                                    }
                                });
                            }
                        };
                        
                        pluginHandle.onremotetrack = (track, mid, on) => {
                            if (track.kind === 'video' && on) {
                                const stream = new MediaStream([track]);
                                videoElement.srcObject = stream;
                                videoElement.play().catch(console.error);
                            }
                        };
                        
                        this.activeStreams.set(streamId, { janus, plugin: pluginHandle });
                    }
                });
            }
        });
    }
    
    stopStream(streamId) {
        const stream = this.activeStreams.get(streamId);
        if (stream) {
            stream.plugin.detach();
            stream.janus.destroy();
            this.activeStreams.delete(streamId);
        }
    }
}

// Usage
async function main() {
    const client = new VASWebRTCClient('http://YOUR_VAS_SERVER:8000', 'admin', 'admin123');
    
    try {
        await client.initialize();
        
        // Get available streams
        const streams = await client.getAvailableStreams();
        console.log('Available streams:', streams);
        
        // Create video elements and start streams
        streams.forEach(stream => {
            const videoElement = document.createElement('video');
            videoElement.autoplay = true;
            videoElement.muted = true;
            videoElement.controls = true;
            
            document.getElementById('streams-container').appendChild(videoElement);
            
            client.startStream(stream.stream_id, videoElement);
        });
        
    } catch (error) {
        console.error('Error:', error);
    }
}

// Start the application
main();
```

## Troubleshooting

### Common Issues

1. **No Video Display**
   - Ensure `onremotetrack` handler is implemented
   - Check if video element has `autoplay` and `muted` attributes
   - Verify WebRTC connection is established

2. **Authentication Errors**
   - Verify username/password are correct
   - Check if token is included in API requests
   - Ensure VAS server is accessible

3. **WebSocket Connection Failed**
   - Check firewall settings
   - Verify Janus WebSocket port (8188) is accessible
   - Check browser console for CORS errors

4. **No Streams Available**
   - Verify cameras are active in VAS
   - Check Janus configuration
   - Ensure RTSP streams are working

### Debug Steps

1. **Enable Janus Debug Mode**
   ```javascript
   Janus.init({
       debug: "all", // Enable all debug messages
       callback: function() { ... }
   });
   ```

2. **Check Browser Console**
   - Look for WebRTC connection errors
   - Monitor Janus plugin messages
   - Check for CORS issues

3. **Verify Network Connectivity**
   ```bash
   # Test API access
   curl -H "Authorization: Bearer YOUR_TOKEN" \
        http://YOUR_VAS_SERVER:8000/api/streams/webrtc/streams
   
   # Test WebSocket connection
   wscat -c ws://YOUR_VAS_SERVER:8188
   ```

## Best Practices

### 1. Error Handling
- Always handle authentication failures
- Implement retry logic for network issues
- Provide user-friendly error messages

### 2. Resource Management
- Stop streams when not needed
- Clean up Janus sessions
- Monitor memory usage

### 3. Performance
- Use appropriate video quality settings
- Implement connection pooling
- Monitor bandwidth usage

### 4. Security
- Use HTTPS in production
- Implement token refresh
- Validate all inputs

### 5. User Experience
- Show loading states
- Provide stream status indicators
- Handle network interruptions gracefully

## API Reference

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login-json` | Authenticate user |

### WebRTC Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/streams/webrtc/streams` | List available streams |
| GET | `/api/streams/webrtc/streams/{id}/config` | Get stream configuration |
| GET | `/api/streams/webrtc/streams/{id}/status` | Get stream status |

### WebSocket Endpoints

| Endpoint | Description |
|----------|-------------|
| `ws://YOUR_VAS_SERVER:8188` | Janus WebRTC Gateway |

## Support

For technical support or questions about VAS WebRTC integration:

1. Check the troubleshooting section above
2. Review browser console logs
3. Verify network connectivity
4. Contact VAS system administrator

---

**Note**: Replace `YOUR_VAS_SERVER` with the actual IP address or hostname of your VAS server. Current VAS server IP address is 10.30.250.245
