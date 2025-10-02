import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  Grid,
} from '@mui/material';
import {
  Devices,
  Videocam,
  CheckCircle,
  Error,
  Warning,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import apiService from '../services/api';

export const Dashboard: React.FC = () => {
  const { data: devices } = useQuery({
    queryKey: ['devices'],
    queryFn: () => apiService.getDevices(1, 1000),
  });

  const { data: streams } = useQuery({
    queryKey: ['streams'],
    queryFn: () => apiService.getStreams(),
  });

  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: () => apiService.getHealth(),
  });

  const deviceStats = {
    total: devices?.total || 0,
    online: devices?.devices?.filter((d: any) => d.status === 'ONLINE').length || 0,
    offline: devices?.devices?.filter((d: any) => d.status === 'OFFLINE').length || 0,
    unreachable: devices?.devices?.filter((d: any) => d.status === 'UNREACHABLE').length || 0,
  };

  const streamStats = {
    total: streams?.length || 0,
    active: streams?.filter(s => s.status === 'active').length || 0,
    inactive: streams?.filter(s => s.status === 'inactive').length || 0,
    error: streams?.filter(s => s.status === 'error').length || 0,
  };

  const StatCard = ({ 
    title, 
    value, 
    icon, 
    color = 'primary',
    subtitle = ''
  }: {
    title: string;
    value: number | string;
    icon: React.ReactNode;
    color?: 'primary' | 'success' | 'error' | 'warning';
    subtitle?: string;
  }) => (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box>
            <Typography color="textSecondary" gutterBottom variant="h6">
              {title}
            </Typography>
            <Typography variant="h4" component="div">
              {value}
            </Typography>
            {subtitle && (
              <Typography variant="body2" color="textSecondary">
                {subtitle}
              </Typography>
            )}
          </Box>
          <Box 
            sx={{ 
              color: `${color}.main`,
              backgroundColor: `${color}.light`,
              borderRadius: '50%',
              p: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            {icon}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      
      <Grid container spacing={3}>
        {/* Device Statistics */}
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Devices"
            value={deviceStats.total}
            icon={<Devices />}
            color="primary"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Online Devices"
            value={deviceStats.online}
            icon={<CheckCircle />}
            color="success"
            subtitle={`${deviceStats.total > 0 ? Math.round((deviceStats.online / deviceStats.total) * 100) : 0}% of total`}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Offline Devices"
            value={deviceStats.offline}
            icon={<Warning />}
            color="warning"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Unreachable"
            value={deviceStats.unreachable}
            icon={<Error />}
            color="error"
          />
        </Grid>

        {/* Stream Statistics */}
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Active Streams"
            value={streamStats.active}
            icon={<Videocam />}
            color="success"
            subtitle={`${streamStats.total > 0 ? Math.round((streamStats.active / streamStats.total) * 100) : 0}% of total`}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Streams"
            value={streamStats.total}
            icon={<Videocam />}
            color="primary"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Inactive Streams"
            value={streamStats.inactive}
            icon={<Videocam />}
            color="warning"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Stream Errors"
            value={streamStats.error}
            icon={<Error />}
            color="error"
          />
        </Grid>

        {/* System Health Status */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System Health
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={4}>
                  <Box display="flex" alignItems="center">
                    <Chip 
                      label={health?.status === 'healthy' ? 'Healthy' : 'Unhealthy'}
                      color={health?.status === 'healthy' ? 'success' : 'error'}
                      size="small"
                    />
                    <Typography variant="body2" ml={1}>
                      Overall Status
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={12} sm={4}>
                  <Box display="flex" alignItems="center">
                    <Chip 
                      label={health?.services?.database?.status === 'healthy' ? 'OK' : 'Error'}
                      color={health?.services?.database?.status === 'healthy' ? 'success' : 'error'}
                      size="small"
                    />
                    <Typography variant="body2" ml={1}>
                      Database
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={12} sm={4}>
                  <Box display="flex" alignItems="center">
                    <Chip 
                      label={health?.services?.janus?.status === 'healthy' ? 'OK' : 'Error'}
                      color={health?.services?.janus?.status === 'healthy' ? 'success' : 'error'}
                      size="small"
                    />
                    <Typography variant="body2" ml={1}>
                      Janus Gateway
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}; 