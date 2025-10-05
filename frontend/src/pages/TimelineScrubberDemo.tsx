import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  Alert,
  Chip,
} from '@mui/material';
import { TimelineScrubber } from '../components/TimelineScrubber';
import { TimelinePosition } from '../types';

const TimelineScrubberDemo: React.FC = () => {
  const [currentPosition, setCurrentPosition] = useState<TimelinePosition | undefined>();
  const [isLive, setIsLive] = useState(false);

  const handleSeek = (position: TimelinePosition) => {
    setCurrentPosition(position);
    console.log('Seek to:', position);
  };

  const handleToggleLive = () => {
    setIsLive(!isLive);
    if (!isLive) {
      // Switch to live mode
      const livePosition: TimelinePosition = {
        timestamp: new Date().toISOString(),
        isLive: true,
      };
      setCurrentPosition(livePosition);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Timeline Scrubber Demo
      </Typography>
      
      <Alert severity="info" sx={{ mb: 3 }}>
        This is a demo of the TimelineScrubber component. It shows how the timeline scrubber
        integrates with recording data and provides seek functionality.
      </Alert>

      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recording Timeline
              </Typography>
              
              <TimelineScrubber
                deviceId="05a9a734-f76d-4f45-9b0e-1e9c89b43e2c"
                deviceName="Camera-172.16.16.122"
                onSeek={handleSeek}
                currentPosition={currentPosition}
                isLive={isLive}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Controls
              </Typography>
              
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Button
                  variant={isLive ? "contained" : "outlined"}
                  color={isLive ? "error" : "primary"}
                  onClick={handleToggleLive}
                  fullWidth
                >
                  {isLive ? "Exit Live Mode" : "Switch to Live"}
                </Button>
                
                <Button
                  variant="outlined"
                  onClick={() => setCurrentPosition(undefined)}
                  fullWidth
                >
                  Clear Position
                </Button>
              </Box>

              <Box sx={{ mt: 3 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Current Position:
                </Typography>
                
                {currentPosition ? (
                  <Box>
                    <Chip
                      label={currentPosition.isLive ? "LIVE" : "RECORDED"}
                      color={currentPosition.isLive ? "error" : "primary"}
                      size="small"
                      sx={{ mb: 1 }}
                    />
                    <Typography variant="body2" color="textSecondary">
                      Time: {new Date(currentPosition.timestamp).toLocaleString()}
                    </Typography>
                    {currentPosition.segment && (
                      <Typography variant="body2" color="textSecondary">
                        Segment: {currentPosition.segment.id}
                      </Typography>
                    )}
                  </Box>
                ) : (
                  <Typography variant="body2" color="textSecondary">
                    No position selected
                  </Typography>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Box sx={{ mt: 3 }}>
        <Typography variant="h6" gutterBottom>
          Features Demonstrated:
        </Typography>
        <Box component="ul" sx={{ pl: 2 }}>
          <li>Visual timeline with recording segments</li>
          <li>Interactive scrubbing and seeking</li>
          <li>Live mode switching</li>
          <li>Time markers and navigation</li>
          <li>Playback controls (play/pause/skip)</li>
          <li>Responsive design</li>
          <li>Real-time data fetching</li>
        </Box>
      </Box>
    </Box>
  );
};

export default TimelineScrubberDemo;
