import React, { useRef, useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  CircularProgress,
  Alert,
  Snackbar,
} from '@mui/material';
import {
  PlayArrow,
  Stop,
  Fullscreen,
  Videocam,
  Error,
  CameraAlt,
} from '@mui/icons-material';
import './VideoPlayer.css';
import { useMutation } from '@tanstack/react-query';
import apiService from '../services/api';

// Declare global Janus types
declare global {
  interface Window {
    Janus: any;
    janusInitialized: boolean;
  }
}

interface VideoPlayerProps {
  deviceId: string;
  deviceName: string;
  webrtcUrl?: string;
  onStartStream?: () => void;
  onStopStream?: () => void;
}

export const VideoPlayer: React.FC<VideoPlayerProps> = ({
  deviceId,
  deviceName,
  webrtcUrl,
  onStartStream,
  onStopStream,
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [streamStatus, setStreamStatus] = useState<'idle' | 'connecting' | 'playing' | 'error'>('idle');
  const [janus, setJanus] = useState<any>(null);
  const [streaming, setStreaming] = useState<any>(null);
  const [snapshotSuccess, setSnapshotSuccess] = useState(false);
  const [snapshotError, setSnapshotError] = useState<string | null>(null);
  const [fps, setFps] = useState<number | null>(null);
  const fpsIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Snapshot capture mutation
  const captureSnapshotMutation = useMutation({
    mutationFn: (deviceId: string) => apiService.captureSnapshot(deviceId),
    onSuccess: () => {
      setSnapshotSuccess(true);
      setSnapshotError(null);
    },
    onError: (error: any) => {
      setSnapshotError(error.response?.data?.detail || 'Failed to capture snapshot');
      setSnapshotSuccess(false);
    },
  });

  // FPS monitoring function
  const getFPS = async (): Promise<number | null> => {
    if (!videoRef.current || !videoRef.current.srcObject) {
      return null;
    }

    try {
      const videoElement = videoRef.current;
      const stream = videoElement.srcObject as MediaStream;
      const videoTrack = stream.getVideoTracks()[0];
      
      if (!videoTrack) {
        return null;
      }

      // Use RTCPeerConnection to get stats
      const pc = new RTCPeerConnection();
      pc.addTrack(videoTrack, stream);
      
      const stats = await pc.getStats();
      let fpsValue: number | null = null;

      stats.forEach((report: any) => {
        if (report.type === 'inbound-rtp' && report.mediaType === 'video') {
          // Calculate FPS from frame rate
          if (report.framesPerSecond !== undefined) {
            fpsValue = Math.round(report.framesPerSecond);
          } else if (report.framesDecoded !== undefined && report.timestamp !== undefined) {
            // Fallback: calculate from frames decoded over time
            const currentTime = Date.now();
            const timeDiff = (currentTime - (report.timestamp || currentTime)) / 1000;
            if (timeDiff > 0) {
              fpsValue = Math.round(report.framesDecoded / timeDiff);
            }
          }
        }
      });

      pc.close();
      return fpsValue;
    } catch (error) {
      console.warn('Failed to get FPS stats:', error);
      return null;
    }
  };

  // Start FPS monitoring
  const startFPSMonitoring = () => {
    if (fpsIntervalRef.current) {
      clearInterval(fpsIntervalRef.current);
    }

    fpsIntervalRef.current = setInterval(async () => {
      const currentFPS = await getFPS();
      setFps(currentFPS);
    }, 1000); // Update every second
  };

  // Stop FPS monitoring
  const stopFPSMonitoring = () => {
    if (fpsIntervalRef.current) {
      clearInterval(fpsIntervalRef.current);
      fpsIntervalRef.current = null;
    }
    setFps(null);
  };

  // Cleanup effect for FPS monitoring
  useEffect(() => {
    return () => {
      if (fpsIntervalRef.current) {
        clearInterval(fpsIntervalRef.current);
      }
    };
  }, []);

  // Load Janus libraries
  useEffect(() => {
    const loadJanusLibraries = () => {
      if (typeof window.Janus !== 'undefined') {
        console.log('Janus library loaded');
        
        // Only initialize if not already initialized
        if (window.janusInitialized) {
          console.log('Janus already initialized, using existing instance');
          setJanus(window.Janus);
          return;
        }
        
        window.Janus.init({
          debug: "all",
          callback: function() {
            console.log("Janus initialized");
            // Mark as initialized globally
            window.janusInitialized = true;
            // Store the Janus constructor, not the initialized object
            setJanus(window.Janus);
          },
          error: function(error: any) {
            console.error("Janus initialization error:", error);
            setError("Failed to initialize Janus: " + error);
          }
        });
      } else {
        console.log('Janus library not loaded yet, retrying...');
        setTimeout(loadJanusLibraries, 1000);
      }
    };

    loadJanusLibraries();
  }, []);

  const handleStartStream = async () => {
    if (!janus) {
      setError("Janus not initialized");
      return;
    }

    setIsLoading(true);
    setStreamStatus('connecting');
    setError(null);

    try {
      // First, call the backend API to start the stream
      if (onStartStream) {
        await onStartStream();
      }

      // Get the mountpoint ID from device ID mapping
      const mountpointId = deviceId === '05a9a734-f76d-4f45-9b0e-1e9c89b43e2c' ? 1 : 2;

      // Connect to Janus WebSocket
      const janusInstance = new window.Janus({
        server: 'ws://10.30.250.245:8188',
        success: function() {
          console.log("Connected to Janus WebSocket");
          
          // Attach to streaming plugin
          let currentPluginHandle: any = null;
          janusInstance.attach({
            plugin: "janus.plugin.streaming",
            success: function(pluginHandle: any) {
              console.log(`Attached to streaming plugin for ${deviceName}`);
              currentPluginHandle = pluginHandle;
              setStreaming(pluginHandle);
              
              // Watch the stream
              pluginHandle.send({
                message: { request: "watch", id: mountpointId },
                success: function(result: any) {
                  console.log(`Watch request successful for ${deviceName}:`, result);
                  setStreamStatus('connecting');
                },
                error: function(error: any) {
                  console.error(`Watch request failed for ${deviceName}:`, error);
                  setError(`Failed to watch ${deviceName}: ` + JSON.stringify(error));
                  setStreamStatus('error');
                }
              });
            },
            error: function(error: any) {
              console.error(`Plugin attach failed for ${deviceName}:`, error);
              setError(`Plugin attach failed for ${deviceName}: ` + error);
              setStreamStatus('error');
            },
            onmessage: function(msg: any, jsep: any) {
              console.log(`Message from ${deviceName}:`, msg);
              
              if (jsep) {
                console.log(`SDP offer received for ${deviceName}:`, jsep);
                setStreamStatus('connecting');
                
                // Use the pluginHandle from the attach success callback
                const handle = currentPluginHandle;
                if (handle) {
                  handle.createAnswer({
                    jsep: jsep,
                    success: function(jsep: any) {
                      console.log(`SDP answer created for ${deviceName}:`, jsep);
                      handle.send({ 
                        message: { request: "start" }, 
                        jsep: jsep,
                        success: function() {
                          console.log(`Stream started for ${deviceName}`);
                          setStreamStatus('playing');
                          setIsPlaying(true);
                        }
                      });
                    },
                    error: function(error: any) {
                      console.error(`Answer creation failed for ${deviceName}:`, error);
                      setError(`Video setup failed for ${deviceName}: ` + error);
                      setStreamStatus('error');
                    }
                  });
                }
              }
            },
            onremotetrack: function(track: any, mid: any, added: any) {
              console.log(`Remote track event for ${deviceName}:`, { track, mid, added });
              
              if (added && track.kind === 'video') {
                console.log(`Adding video track for ${deviceName}`);
                const stream = new MediaStream([track]);
                if (videoRef.current) {
                  videoRef.current.srcObject = stream;
                  
                  // Debounce play attempts to avoid AbortError
                  if ((videoRef.current as any).playTimeout) {
                    clearTimeout((videoRef.current as any).playTimeout);
                  }
                  (videoRef.current as any).playTimeout = setTimeout(() => {
                    if (videoRef.current && videoRef.current.srcObject) {
                      videoRef.current.play().then(() => {
                        console.log(`Video playing for ${deviceName}!`);
                        setStreamStatus('playing');
                        setIsPlaying(true);
                        // Start FPS monitoring when video starts playing
                        startFPSMonitoring();
                      }).catch((error: any) => {
                        if (error.name !== 'AbortError') {
                          console.error(`Video play failed for ${deviceName}:`, error);
                          setError(`Video play failed for ${deviceName}: ` + error);
                          setStreamStatus('error');
                        }
                      });
                    }
                  }, 100);
                }
              }
            },
            oncleanup: function() {
              console.log(`Cleanup for ${deviceName}`);
              if (videoRef.current) {
                videoRef.current.srcObject = null;
              }
              setStreamStatus('idle');
              setIsPlaying(false);
              // Stop FPS monitoring when stream stops
              stopFPSMonitoring();
            }
          });
        },
        error: function(error: any) {
          console.error("Janus connection error:", error);
          setError("Failed to connect to Janus: " + error);
          setStreamStatus('error');
        },
        destroyed: function() {
          console.log("Janus destroyed");
          setStreamStatus('idle');
          setIsPlaying(false);
          // Stop FPS monitoring when Janus is destroyed
          stopFPSMonitoring();
        }
      });
    } catch (error) {
      console.error('Failed to start stream:', error);
      setError('Failed to start stream: ' + error);
      setStreamStatus('error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleStopStream = () => {
    if (streaming) {
      streaming.send({ message: { request: "stop" } });
      streaming.detach();
      setStreaming(null);
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setIsPlaying(false);
    setStreamStatus('idle');
    setError(null);
    // Stop FPS monitoring when stream stops
    stopFPSMonitoring();
    if (onStopStream) onStopStream();
  };

  const handleFullscreen = () => {
    if (videoRef.current) {
      if (document.fullscreenElement) {
        document.exitFullscreen();
      } else {
        videoRef.current.requestFullscreen();
      }
    }
  };

  const handleTakeSnapshot = () => {
    captureSnapshotMutation.mutate(deviceId);
  };

  const getStatusColor = () => {
    switch (streamStatus) {
      case 'playing':
        return 'success';
      case 'connecting':
        return 'warning';
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusIcon = () => {
    switch (streamStatus) {
      case 'playing':
        return <Videocam />;
      case 'connecting':
        return <CircularProgress size={16} />;
      case 'error':
        return <Error />;
      default:
        return <Videocam />;
    }
  };

  return (
    <Card className="video-player-card">
      <CardContent className="video-player-content">
        <Box className="video-player-header">
          <Typography variant="h6" noWrap className="video-player-title">
            {deviceName}
          </Typography>
          <Box display="flex" alignItems="center" gap={1}>
            <Chip
              icon={getStatusIcon()}
              label={streamStatus}
              color={getStatusColor() as any}
              size="small"
              sx={{ fontSize: '0.75rem' }}
            />
            {fps !== null && (
              <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
                {fps} fps
              </Typography>
            )}
          </Box>
        </Box>

        {/* Video Container */}
        <Box className="video-player-video-container">
          {isLoading && (
            <Box className="video-player-placeholder">
              <CircularProgress />
              <Typography variant="body2" color="white">
                Connecting...
              </Typography>
            </Box>
          )}

          {error && (
            <Box className="video-player-placeholder">
              <Error sx={{ color: 'error.main', fontSize: 48 }} />
              <Typography variant="body2" color="error.main">
                {error}
              </Typography>
            </Box>
          )}

          {!isLoading && !error && streamStatus === 'idle' && (
            <Box className="video-player-placeholder">
              <Videocam sx={{ color: 'grey.500', fontSize: 48 }} />
              <Typography variant="body2" color="grey.500">
                Click Start to begin streaming
              </Typography>
            </Box>
          )}

          <video
            ref={videoRef}
            className="video-player-video"
            style={{
              display: isPlaying ? 'block' : 'none',
            }}
            autoPlay
            muted
            playsInline
          />
        </Box>

        {/* Controls */}
        <Box className="video-player-controls">
          {!isPlaying ? (
            <Button
              variant="contained"
              startIcon={<PlayArrow />}
              onClick={handleStartStream}
              disabled={isLoading}
              className="video-player-button video-player-button-primary"
            >
              Start Stream
            </Button>
          ) : (
            <>
              <Button
                variant="outlined"
                startIcon={<Stop />}
                onClick={handleStopStream}
                disabled={isLoading}
                className="video-player-button video-player-button-secondary"
              >
                Stop Stream
              </Button>

              <Button
                variant="outlined"
                startIcon={<Fullscreen />}
                onClick={handleFullscreen}
                className="video-player-button video-player-button-secondary"
              >
                Fullscreen
              </Button>

              <Button
                variant="outlined"
                startIcon={captureSnapshotMutation.isPending ? <CircularProgress size={16} /> : <CameraAlt />}
                onClick={handleTakeSnapshot}
                disabled={captureSnapshotMutation.isPending}
                className="video-player-button video-player-button-snapshot"
              >
                {captureSnapshotMutation.isPending ? 'Capturing...' : 'Snapshot'}
              </Button>
            </>
          )}
        </Box>

        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}

        {/* Snapshot Success/Error Messages */}
        <Snackbar
          open={snapshotSuccess}
          autoHideDuration={3000}
          onClose={() => setSnapshotSuccess(false)}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        >
          <Alert severity="success" onClose={() => setSnapshotSuccess(false)}>
            Snapshot captured successfully!
          </Alert>
        </Snackbar>

        <Snackbar
          open={!!snapshotError}
          autoHideDuration={5000}
          onClose={() => setSnapshotError(null)}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        >
          <Alert severity="error" onClose={() => setSnapshotError(null)}>
            {snapshotError}
          </Alert>
        </Snackbar>

      </CardContent>
    </Card>
  );
}; 