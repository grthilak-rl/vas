import React, { useRef, useState } from 'react';
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

  const handleStartStream = async () => {
    if (onStartStream) {
      setIsLoading(true);
      try {
        await onStartStream();
        // After starting stream, the parent component should refresh data
        // and provide the webrtcUrl if stream creation was successful
      } catch (error) {
        console.error('Failed to start stream:', error);
      } finally {
        setIsLoading(false);
      }
    }
  };

  const handleStopStream = () => {
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