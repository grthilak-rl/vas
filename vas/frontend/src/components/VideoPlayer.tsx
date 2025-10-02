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
} from '@mui/material';
import {
  PlayArrow,
  Stop,
  Fullscreen,
  Videocam,
  Error,
} from '@mui/icons-material';

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
    <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <CardContent sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6" noWrap>
            {deviceName}
          </Typography>
          <Chip
            icon={getStatusIcon()}
            label={streamStatus}
            color={getStatusColor() as any}
            size="small"
          />
        </Box>

        {/* Video Container */}
        <Box
          sx={{
            flex: 1,
            backgroundColor: '#000',
            borderRadius: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            position: 'relative',
            minHeight: 200,
          }}
        >
          {isLoading && (
            <Box display="flex" flexDirection="column" alignItems="center">
              <CircularProgress />
              <Typography variant="body2" color="white" mt={1}>
                Connecting...
              </Typography>
            </Box>
          )}

          {error && (
            <Box display="flex" flexDirection="column" alignItems="center">
              <Error sx={{ color: 'error.main', fontSize: 48 }} />
              <Typography variant="body2" color="error.main" mt={1}>
                {error}
              </Typography>
            </Box>
          )}

          {!isLoading && !error && streamStatus === 'idle' && (
            <Box display="flex" flexDirection="column" alignItems="center">
              <Videocam sx={{ color: 'grey.500', fontSize: 48 }} />
              <Typography variant="body2" color="grey.500" mt={1}>
                Click Start to begin streaming
              </Typography>
            </Box>
          )}

          <video
            ref={videoRef}
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'contain',
              display: isPlaying ? 'block' : 'none',
            }}
            autoPlay
            muted
            playsInline
          />
        </Box>

        {/* Controls */}
        <Box display="flex" justifyContent="center" gap={1} mt={2}>
          {!isPlaying ? (
            <Button
              variant="contained"
              startIcon={<PlayArrow />}
              onClick={handleStartStream}
              disabled={isLoading}
            >
              {webrtcUrl ? 'Start Stream' : 'Start Stream'}
            </Button>
          ) : (
            <Button
              variant="outlined"
              startIcon={<Stop />}
              onClick={handleStopStream}
              disabled={isLoading}
            >
              Stop Stream
            </Button>
          )}

          {isPlaying && (
            <Button
              variant="outlined"
              startIcon={<Fullscreen />}
              onClick={handleFullscreen}
            >
              Fullscreen
            </Button>
          )}
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