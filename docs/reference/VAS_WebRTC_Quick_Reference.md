# VAS WebRTC Quick Reference

## 🚀 Quick Start

### 1. Include Libraries
```html
<script src="https://webrtc.github.io/adapter/adapter-latest.js"></script>
<script src="https://janus.conf.meetecho.com/janus.js"></script>
```

### 2. Authenticate
```javascript
const token = await fetch('http://YOUR_VAS_SERVER:8000/api/auth/login-json', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: 'admin', password: 'admin123' })
}).then(r => r.json()).then(d => d.access_token);
```

### 3. Get Streams
```javascript
const streams = await fetch('http://YOUR_VAS_SERVER:8000/api/streams/webrtc/streams', {
    headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json()).then(d => d.streams);
```

### 4. Start Stream
```javascript
// Get config
const config = await fetch(`http://YOUR_VAS_SERVER:8000/api/streams/webrtc/streams/${streamId}/config`, {
    headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());

// Connect to Janus
const janus = new Janus({
    server: config.janus_ws_url,
    success: function() {
        janus.attach({
            plugin: config.plugin_name,
            success: function(pluginHandle) {
                // Watch stream
                pluginHandle.send({
                    message: { request: "watch", id: config.mountpoint_id }
                });
                
                // Handle SDP
                pluginHandle.onmessage = function(msg, jsep) {
                    if (jsep) {
                        pluginHandle.createAnswer({
                            jsep: jsep,
                            success: function(jsep) {
                                pluginHandle.send({
                                    message: { request: "start" },
                                    jsep: jsep
                                });
                            }
                        });
                    }
                };
                
                // CRITICAL: Handle video track
                pluginHandle.onremotetrack = function(track, mid, on) {
                    if (track.kind === 'video' && on) {
                        const stream = new MediaStream([track]);
                        videoElement.srcObject = stream;
                        videoElement.play();
                    }
                };
            }
        });
    }
});
```

## 🔧 Essential Configuration

### Video Element Setup
```html
<video autoplay muted playsInline controls></video>
```

### Janus Initialization
```javascript
Janus.init({
    debug: "all", // Set to false for production
    callback: function() {
        console.log('Janus ready');
    }
});
```

## 📡 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/auth/login-json` | POST | Authenticate |
| `/api/streams/webrtc/streams` | GET | List streams |
| `/api/streams/webrtc/streams/{id}/config` | GET | Get config |
| `/api/streams/webrtc/streams/{id}/status` | GET | Check status |

## 🔍 Troubleshooting

### No Video?
- ✅ Check `onremotetrack` handler
- ✅ Verify `autoplay` and `muted` on video element
- ✅ Ensure WebRTC connection established

### Authentication Failed?
- ✅ Verify username/password
- ✅ Check server accessibility
- ✅ Include token in headers

### Connection Issues?
- ✅ Check WebSocket port 8188
- ✅ Verify firewall settings
- ✅ Check browser console for errors

## 🎯 Key Points

1. **Always use `onremotetrack`** - `onremotestream` may not fire
2. **Video element must be `muted`** - Browser autoplay policy
3. **Handle errors gracefully** - Network issues are common
4. **Clean up resources** - Stop streams when done

## 📝 Complete Working Example

```html
<!DOCTYPE html>
<html>
<head>
    <title>VAS WebRTC Test</title>
    <script src="https://webrtc.github.io/adapter/adapter-latest.js"></script>
    <script src="https://janus.conf.meetecho.com/janus.js"></script>
</head>
<body>
    <video id="video" autoplay muted playsInline controls></video>
    
    <script>
        async function startVASStream() {
            // 1. Authenticate
            const token = await fetch('http://YOUR_VAS_SERVER:8000/api/auth/login-json', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: 'admin', password: 'admin123' })
            }).then(r => r.json()).then(d => d.access_token);
            
            // 2. Get stream config
            const config = await fetch('http://YOUR_VAS_SERVER:8000/api/streams/webrtc/streams/1/config', {
                headers: { 'Authorization': `Bearer ${token}` }
            }).then(r => r.json());
            
            // 3. Initialize Janus
            await new Promise(resolve => Janus.init({ callback: resolve }));
            
            // 4. Connect and start stream
            const janus = new Janus({
                server: config.janus_ws_url,
                success: function() {
                    janus.attach({
                        plugin: config.plugin_name,
                        success: function(pluginHandle) {
                            pluginHandle.send({
                                message: { request: "watch", id: config.mountpoint_id }
                            });
                            
                            pluginHandle.onmessage = function(msg, jsep) {
                                if (jsep) {
                                    pluginHandle.createAnswer({
                                        jsep: jsep,
                                        success: function(jsep) {
                                            pluginHandle.send({
                                                message: { request: "start" },
                                                jsep: jsep
                                            });
                                        }
                                    });
                                }
                            };
                            
                            pluginHandle.onremotetrack = function(track, mid, on) {
                                if (track.kind === 'video' && on) {
                                    const stream = new MediaStream([track]);
                                    document.getElementById('video').srcObject = stream;
                                    document.getElementById('video').play();
                                }
                            };
                        }
                    });
                }
            });
        }
        
        // Start the stream
        startVASStream().catch(console.error);
    </script>
</body>
</html>
```

---

**Replace `YOUR_VAS_SERVER` with your actual VAS server IP/hostname**
