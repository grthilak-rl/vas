import React, { useEffect, useRef, useState } from 'react';
import {
  Card,
  CardContent,
  Button,
  Typography,
  Box,
  Alert,
  CircularProgress,
} from '@mui/material';
import { PlayArrow, Stop, Videocam, Error } from '@mui/icons-material';

declare global {
  interface Window {
    Janus: any;
    adapter: any;
  }
}

interface SimpleVideoPlayerProps {
  deviceId: string;
  deviceName: string;
  janusStreamId: number; // Direct Janus stream ID (1 or 2)
}

export const SimpleVideoPlayer: React.FC<SimpleVideoPlayerProps> = ({
  deviceId,
  deviceName,
  janusStreamId,
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [janus, setJanus] = useState<any>(null);
  const [streaming, setStreaming] = useState<any>(null);
  const [status, setStatus] = useState<'idle' | 'connecting' | 'connected' | 'streaming' | 'error'>('idle');
  const [error, setError] = useState<string | null>(null);
  const [isJanusReady, setIsJanusReady] = useState(false);

  // Initialize Janus on component mount
  useEffect(() => {
    const initJanus = async () => {
      try {
        await loadJanusScripts();
        
        if (!window.Janus) {
          throw new (Error as any)('Janus library not loaded');
        }

        setStatus('connecting');

        window.Janus.init({
          debug: true,
          callback: () => {
            console.log('Janus initialized for', deviceName);
            
            const janusInstance = new window.Janus({
              server: process.env.REACT_APP_JANUS_WS_URL || 'ws://localhost:8188/janus',
              success: () => {
                console.log('✅ Connected to Janus WebSocket for', deviceName);
                setJanus(janusInstance);
                setStatus('connected');
                setIsJanusReady(true);
              },
              error: (error: any) => {
                console.error('❌ Janus connection error for', deviceName, ':', error);
                setError(`Failed to connect to video service: ${error}`);
                setStatus('error');
              },
              destroyed: () => {
                console.log('Janus destroyed for', deviceName);
                setJanus(null);
                setIsJanusReady(false);
                setStatus('idle');
              }
            });
          },
          error: (error: any) => {
            console.error('❌ Janus initialization error for', deviceName, ':', error);
            setError(`Failed to initialize video service: ${error}`);
            setStatus('error');
          }
        });
      } catch (error) {
        console.error('Failed to load Janus for', deviceName, ':', error);
        setError('Failed to load video service');
        setStatus('error');
      }
    };

    initJanus();

    // Cleanup
    return () => {
      if (streaming) {
        streaming.hangup();
      }
      if (janus) {
        janus.destroy();
      }
    };
  }, [deviceName]);

  // Load Janus scripts
  const loadJanusScripts = (): Promise<void> => {
    return new Promise((resolve, reject) => {
      if (window.Janus) {
        resolve();
        return;
      }

      const adapterScript = document.createElement('script');
      adapterScript.src = '/js/adapter.min.js';
      adapterScript.onload = () => {
        const janusScript = document.createElement('script');
        janusScript.src = '/js/janus.js';
        janusScript.onload = () => resolve();
        janusScript.onerror = () => reject(new (Error as any)('Failed to load janus.js'));
        document.head.appendChild(janusScript);
      };
      adapterScript.onerror = () => reject(new (Error as any)('Failed to load adapter.js'));
      document.head.appendChild(adapterScript);
    });
  };

  // Start streaming - exact same logic as working test page
  const startStream = () => {
    if (!janus || !isJanusReady) {
      setError('Video service not ready');
      return;
    }

    if (!videoRef.current) {
      setError('Video element not ready');
      return;
    }

    setStatus('connecting');
    setError(null);

    let pluginHandle: any = null;

    const attachConfig = {
      plugin: "janus.plugin.streaming",
      success: function(handle: any) {
        pluginHandle = handle;
        setStreaming(handle);
        console.log(`✅ Attached to streaming plugin for ${deviceName}`);
        
        // Add direct PeerConnection event listener with retry
        const addPeerConnectionListener = () => {
          if (handle.webrtcStuff && handle.webrtcStuff.pc) {
            console.log(`🔗 Adding direct PeerConnection track listener for ${deviceName}`);
            handle.webrtcStuff.pc.addEventListener('track', function(event: RTCTrackEvent) {
              console.log(`🎥 DIRECT PC track event for ${deviceName}:`, event);
              const track = event.track;
              if (track.kind === 'video' && videoRef.current) {
                console.log(`🎬 DIRECT PC - Adding video track for ${deviceName}`);
                const stream = new MediaStream([track]);
                videoRef.current.srcObject = stream;
                
                // Wait a bit for the video to be ready
                setTimeout(() => {
                  if (videoRef.current && !videoRef.current.paused) return; // Already playing
                  
                  videoRef.current?.play().then(() => {
                    console.log(`🎉 DIRECT PC - Video playing for ${deviceName}!`);
                    setStatus('streaming');
                  }).catch((e) => {
                    // Ignore AbortError as it's just timing related
                    if (e.name !== 'AbortError') {
                      console.error(`❌ DIRECT PC - Video play failed for ${deviceName}:`, e);
                    }
                  });
                }, 100);
              }
            });
            return true;
          }
          return false;
        };
        
        // Try immediately, then retry after delay
        if (!addPeerConnectionListener()) {
          console.log(`⏳ PeerConnection not ready, retrying in 1s for ${deviceName}`);
          setTimeout(() => {
            if (!addPeerConnectionListener()) {
              console.log(`⏳ PeerConnection still not ready, retrying in 3s for ${deviceName}`);
              setTimeout(addPeerConnectionListener, 3000);
            }
          }, 1000);
        }
        
        // Watch the stream - EXACT same as working test page
        handle.send({
          message: { request: "watch", id: janusStreamId },
          success: function(result: any) {
            console.log(`✅ Watch request successful for ${deviceName}:`, result);
            setStatus('streaming');
          },
          error: function(error: any) {
            console.error(`❌ Watch request failed for ${deviceName}:`, error);
            setError(`Failed to watch stream: ${JSON.stringify(error)}`);
            setStatus('error');
          }
        });
      },
      error: function(error: any) {
        console.error(`❌ Plugin attach failed for ${deviceName}:`, error);
        setError(`Plugin attach failed: ${error}`);
        setStatus('error');
      },
      onmessage: function(msg: any, jsep: any) {
        console.log(`📨 Message from ${deviceName}:`, msg);
        
        if (jsep && pluginHandle) {
          console.log(`🎬 SDP offer received for ${deviceName}:`, jsep);
          
          pluginHandle.createAnswer({
            jsep: jsep,
            media: { audioSend: false, videoSend: false, audioRecv: false, videoRecv: true },
            success: function(answerJsep: any) {
              console.log(`✅ SDP answer created for ${deviceName}:`, answerJsep);
              pluginHandle.send({ 
                message: { request: "start" }, 
                jsep: answerJsep,
                success: function() {
                  console.log(`🚀 Stream started for ${deviceName}`);
                }
              });
            },
            error: function(error: any) {
              console.error(`❌ Answer creation failed for ${deviceName}:`, error);
              setError(`Failed to create answer: ${error}`);
              setStatus('error');
            }
          });
        }
      },
      onremotestream: function(stream: MediaStream) {
        console.log(`🎥 LEGACY onremotestream for ${deviceName}:`, stream);
        
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          console.log(`🎬 Set srcObject from onremotestream for ${deviceName}`);
          
          // Avoid multiple play attempts
          setTimeout(() => {
            if (videoRef.current && videoRef.current.paused) {
              videoRef.current.play().then(() => {
                console.log(`🎉 Video playing for ${deviceName}!`);
                setStatus('streaming');
              }).catch((e) => {
                if (e.name !== 'AbortError') {
                  console.error(`❌ Video play failed for ${deviceName}:`, e);
                  setError(`Video play failed: ${e}`);
                }
              });
            }
          }, 150);
        }
      },
      onremotetrack: function(track: MediaStreamTrack, mid: string, added: boolean) {
        console.log(`🎵 Remote track event for ${deviceName}:`, track, mid, added);
        console.log(`🎬 Track kind: ${track.kind}, added: ${added}, videoRef exists: ${!!videoRef.current}`);
        
        if (added && track.kind === 'video') {
          console.log(`🎬 Adding video track for ${deviceName}`);
          const stream = new MediaStream([track]);
          console.log(`🎬 Created MediaStream:`, stream);
          
          if (videoRef.current) {
            videoRef.current.srcObject = stream;
            console.log(`🎬 Set srcObject on video element for ${deviceName}`);
            
            // Debounce play attempts to avoid AbortError
            if ((videoRef.current as any).playTimeout) {
              clearTimeout((videoRef.current as any).playTimeout);
            }
            (videoRef.current as any).playTimeout = setTimeout(() => {
              if (videoRef.current && videoRef.current.srcObject) {
                videoRef.current.play().then(() => {
                  console.log(`🎉 Video playing for ${deviceName}!`);
                  setStatus('streaming');
                }).catch((e) => {
                  if (e.name !== 'AbortError') {
                    console.error(`❌ Video play failed for ${deviceName}:`, e);
                    setError(`Video play failed: ${e}`);
                  }
                });
              }
            }, 100);
          } else {
            console.error(`❌ Video ref is null for ${deviceName}!`);
          }
        } else if (track.kind === 'audio') {
          console.log(`🎵 Audio track detected but we're video-only`);
        }
      },
      oncleanup: () => {
        console.log(`🧹 Cleanup for ${deviceName}`);
        if (videoRef.current) {
          videoRef.current.srcObject = null;
        }
        setStatus('connected');
      }
    };

    janus.attach(attachConfig);
  };

  // Stop streaming
  const stopStream = () => {
    if (streaming) {
      streaming.send({ message: { request: "stop" } });
      streaming.hangup();
      setStreaming(null);
    }
    
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    
    setStatus('connected');
  };

  const getStatusColor = () => {
    switch (status) {
      case 'streaming': return 'success';
      case 'connecting': return 'warning';
      case 'error': return 'error';
      case 'connected': return 'info';
      default: return 'default';
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'idle': return 'Initializing...';
      case 'connecting': return 'Connecting...';
      case 'connected': return 'Ready';
      case 'streaming': return 'Live';
      case 'error': return 'Error';
      default: return 'Unknown';
    }
  };

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          {deviceName}
        </Typography>
        
        <Box
          sx={{
            position: 'relative',
            backgroundColor: '#000',
            borderRadius: 1,
            overflow: 'hidden',
            aspectRatio: '16/9',
            mb: 2,
          }}
        >
          {status !== 'streaming' && (
            <Box
              sx={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexDirection: 'column',
                color: 'white',
                zIndex: 1,
              }}
            >
              {status === 'connecting' ? (
                <CircularProgress sx={{ color: 'grey.500', mb: 1 }} />
              ) : status === 'error' ? (
                <Error sx={{ color: 'error.main', fontSize: 48, mb: 1 }} />
              ) : (
                <Videocam sx={{ color: 'grey.500', fontSize: 48, mb: 1 }} />
              )}
              <Typography variant="body2" color="inherit">
                {status === 'idle' ? 'Initializing video service...' :
                 status === 'connecting' ? 'Connecting to stream...' :
                 status === 'connected' ? 'Ready to stream' :
                 status === 'error' ? (error || 'Video service error') :
                 'Click Start to begin streaming'}
              </Typography>
            </Box>
          )}

          <video
            ref={videoRef}
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'contain',
              display: status === 'streaming' ? 'block' : 'none',
            }}
            autoPlay
            muted
            playsInline
          />
        </Box>

        {/* Controls */}
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Box display="flex" gap={1}>
            {status !== 'streaming' ? (
              <Button
                variant="contained"
                startIcon={<PlayArrow />}
                onClick={startStream}
                disabled={!isJanusReady || status === 'connecting' || status === 'error'}
              >
                Start Video
              </Button>
            ) : (
              <Button
                variant="outlined"
                startIcon={<Stop />}
                onClick={stopStream}
              >
                Stop Stream
              </Button>
            )}
          </Box>
          
          <Box
            sx={{
              px: 1,
              py: 0.5,
              borderRadius: 1,
              backgroundColor: getStatusColor() === 'success' ? 'success.light' :
                             getStatusColor() === 'warning' ? 'warning.light' :
                             getStatusColor() === 'error' ? 'error.light' :
                             getStatusColor() === 'info' ? 'info.light' : 'grey.200',
              color: getStatusColor() === 'success' ? 'success.dark' :
                     getStatusColor() === 'warning' ? 'warning.dark' :
                     getStatusColor() === 'error' ? 'error.dark' :
                     getStatusColor() === 'info' ? 'info.dark' : 'grey.600',
            }}
          >
            <Typography variant="caption" fontWeight="bold">
              {getStatusText()}
            </Typography>
          </Box>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}
      </CardContent>
    </Card>
  );
};