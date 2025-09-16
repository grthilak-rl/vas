import React, { useState, useEffect } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  LinearProgress,
  Alert,
} from '@mui/material';
import {
  Videocam as CameraIcon,
  Memory as MemoryIcon,
  Storage as StorageIcon,
  Speed as SpeedIcon,
} from '@mui/icons-material';
import axios from 'axios';

interface SystemStatus {
  status: string;
  uptime: string;
  memory: {
    used: number;
    total: number;
  };
  cpu: {
    usage: number;
    cores: number;
  };
  cameras: {
    total: number;
    active: number;
  };
}

const Dashboard: React.FC = () => {
  const [systemStatus, setSystemStatus] = useState<SystemStatus>({
    status: 'loading',
    uptime: '0s',
    memory: { used: 0, total: 0 },
    cpu: { usage: 0, cores: 8 },
    cameras: { total: 6, active: 0 },
  });

  const [apiStatus, setApiStatus] = useState<string>('checking');
  const [janusStatus, setJanusStatus] = useState<string>('checking');

  useEffect(() => {
    // Check API status
    const checkApiStatus = async () => {
      try {
        const response = await axios.get('http://localhost:8000/docs');
        setApiStatus('online');
      } catch (error) {
        setApiStatus('offline');
      }
    };

    // Check Janus status
    const checkJanusStatus = async () => {
      try {
        const response = await axios.get('http://localhost:8088/janus/info');
        setJanusStatus('online');
      } catch (error) {
        setJanusStatus('offline');
      }
    };

    checkApiStatus();
    checkJanusStatus();

    // Simulate system metrics (in real implementation, these would come from the backend)
    const interval = setInterval(() => {
      setSystemStatus(prev => ({
        ...prev,
        status: 'online',
        uptime: `${Math.floor(Date.now() / 1000)}s`,
        memory: {
          used: Math.floor(Math.random() * 8) + 4,
          total: 16,
        },
        cpu: {
          usage: Math.floor(Math.random() * 30) + 10,
          cores: 8,
        },
        cameras: {
          total: 6,
          active: Math.floor(Math.random() * 3),
        },
      }));
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online': return 'success';
      case 'offline': return 'error';
      case 'loading': return 'default';
      default: return 'default';
    }
  };

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        VAS Edge Dashboard
      </Typography>
      
      <Grid container spacing={3}>
        {/* System Status Card */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <SpeedIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">System Status</Typography>
              </Box>
              <Box mb={2}>
                <Typography variant="body2" color="text.secondary">
                  Status: <Chip label={systemStatus.status} color={getStatusColor(systemStatus.status)} size="small" />
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Uptime: {systemStatus.uptime}
                </Typography>
              </Box>
              <Box mb={2}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  CPU Usage: {systemStatus.cpu.usage}%
                </Typography>
                <LinearProgress variant="determinate" value={systemStatus.cpu.usage} />
              </Box>
              <Box>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Memory: {systemStatus.memory.used}GB / {systemStatus.memory.total}GB
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={(systemStatus.memory.used / systemStatus.memory.total) * 100} 
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Camera Status Card */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <CameraIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">Camera Status</Typography>
              </Box>
              <Typography variant="h3" color="primary">
                {systemStatus.cameras.active}/{systemStatus.cameras.total}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Active Cameras
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Service Status Cards */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Backend API</Typography>
              <Chip 
                label={apiStatus} 
                color={getStatusColor(apiStatus)} 
                size="small" 
              />
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                http://localhost:8000
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Janus Gateway</Typography>
              <Chip 
                label={janusStatus} 
                color={getStatusColor(janusStatus)} 
                size="small" 
              />
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                http://localhost:8088
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Edge API</Typography>
              <Chip 
                label="online" 
                color="success" 
                size="small" 
              />
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                http://localhost:3001
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Quick Actions */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Quick Actions</Typography>
              <Alert severity="info">
                Use the navigation menu to access Camera Viewer and Device Management features.
                The system is ready for camera stream management and device configuration.
              </Alert>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;
