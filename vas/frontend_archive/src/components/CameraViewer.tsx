import React, { useState, useEffect, useRef } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Button,
  Chip,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Videocam as CameraIcon,
  Fullscreen as FullscreenIcon,
} from '@mui/icons-material';

interface Camera {
  id: number;
  name: string;
  status: 'offline' | 'online' | 'streaming';
  location: string;
  streamUrl: string;
}

const CameraViewer: React.FC = () => {
  const [cameras, setCameras] = useState<Camera[]>([
    { id: 1, name: 'Camera 1', status: 'offline', location: 'Office', streamUrl: 'http://localhost/streams/1' },
    { id: 2, name: 'Camera 2', status: 'offline', location: 'Lobby', streamUrl: 'http://localhost/streams/2' },
    { id: 3, name: 'Camera 3', status: 'offline', location: 'Entrance', streamUrl: 'http://localhost/streams/3' },
    { id: 4, name: 'Camera 4', status: 'offline', location: 'Parking', streamUrl: 'http://localhost/streams/4' },
    { id: 5, name: 'Camera 5', status: 'offline', location: 'Storage', streamUrl: 'http://localhost/streams/5' },
    { id: 6, name: 'Camera 6', status: 'offline', location: 'Workshop', streamUrl: 'http://localhost/streams/6' },
  ]);

  const [selectedCamera, setSelectedCamera] = useState<Camera | null>(null);
  const [fullscreenOpen, setFullscreenOpen] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'streaming': return 'success';
      case 'online': return 'info';
      case 'offline': return 'default';
      default: return 'default';
    }
  };

  const handleStartStream = (camera: Camera) => {
    setCameras(prev => prev.map(c => 
      c.id === camera.id ? { ...c, status: 'streaming' as const } : c
    ));
    
    // In a real implementation, this would connect to Janus WebRTC
    console.log(`Starting stream for ${camera.name}`);
  };

  const handleStopStream = (camera: Camera) => {
    setCameras(prev => prev.map(c => 
      c.id === camera.id ? { ...c, status: 'offline' as const } : c
    ));
    
    // In a real implementation, this would stop the WebRTC stream
    console.log(`Stopping stream for ${camera.name}`);
  };

  const handleViewFullscreen = (camera: Camera) => {
    setSelectedCamera(camera);
    setFullscreenOpen(true);
  };

  const handleCloseFullscreen = () => {
    setFullscreenOpen(false);
    setSelectedCamera(null);
  };

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Camera Viewer
      </Typography>
      
      <Alert severity="info" sx={{ mb: 3 }}>
        This is a demonstration of the camera viewer interface. In the full implementation, 
        this would connect to Janus WebRTC Gateway for real-time streaming.
      </Alert>

      <Grid container spacing={3}>
        {cameras.map((camera) => (
          <Grid item xs={12} sm={6} md={4} key={camera.id}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={2}>
                  <CameraIcon color="primary" sx={{ mr: 1 }} />
                  <Typography variant="h6">{camera.name}</Typography>
                </Box>
                
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Location: {camera.location}
                </Typography>
                
                <Box mb={2}>
                  <Chip 
                    label={camera.status} 
                    color={getStatusColor(camera.status)} 
                    size="small" 
                  />
                </Box>

                <Box display="flex" gap={1} flexWrap="wrap">
                  {camera.status === 'streaming' ? (
                    <Button
                      variant="contained"
                      color="error"
                      size="small"
                      startIcon={<StopIcon />}
                      onClick={() => handleStopStream(camera)}
                    >
                      Stop
                    </Button>
                  ) : (
                    <Button
                      variant="contained"
                      color="primary"
                      size="small"
                      startIcon={<PlayIcon />}
                      onClick={() => handleStartStream(camera)}
                    >
                      Start
                    </Button>
                  )}
                  
                  <Button
                    variant="outlined"
                    size="small"
                    startIcon={<FullscreenIcon />}
                    onClick={() => handleViewFullscreen(camera)}
                  >
                    Fullscreen
                  </Button>
                </Box>

                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                  Stream URL: {camera.streamUrl}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Fullscreen Dialog */}
      <Dialog
        open={fullscreenOpen}
        onClose={handleCloseFullscreen}
        maxWidth={false}
        fullWidth
        PaperProps={{
          sx: {
            width: '90vw',
            height: '90vh',
            maxWidth: 'none',
            maxHeight: 'none',
          }
        }}
      >
        <DialogTitle>
          {selectedCamera?.name} - {selectedCamera?.location}
        </DialogTitle>
        <DialogContent>
          <Box
            sx={{
              width: '100%',
              height: '70vh',
              backgroundColor: '#000',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              borderRadius: 1,
            }}
          >
            <Typography variant="h6" color="white">
              Video Stream Placeholder
            </Typography>
            <Typography variant="body2" color="white" sx={{ ml: 2 }}>
              (WebRTC stream would appear here)
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseFullscreen}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default CameraViewer;
