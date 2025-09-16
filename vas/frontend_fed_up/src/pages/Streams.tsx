import React, { useState } from 'react';
import {
  Box,
  Typography,
  Grid,
  Button,
  Chip,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  Refresh,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiService from '../services/api';
import { VideoPlayer } from '../components/VideoPlayer';
import { Device, Stream } from '../types';

export const Streams: React.FC = () => {
  const [activeStreams, setActiveStreams] = useState<Set<string>>(new Set());
  const queryClient = useQueryClient();

  const { data: devicesData, isLoading: devicesLoading } = useQuery({
    queryKey: ['devices'],
    queryFn: () => apiService.getDevices(1, 1000),
  });

  const { data: streamsData, isLoading: streamsLoading, refetch: refetchStreams } = useQuery({
    queryKey: ['streams'],
    queryFn: () => apiService.getStreams(),
  });

  const startStreamMutation = useMutation({
    mutationFn: (deviceId: string) => apiService.startStream(deviceId),
    onSuccess: (data, deviceId) => {
      setActiveStreams(prev => new Set(prev).add(deviceId));
      queryClient.invalidateQueries({ queryKey: ['streams'] });
    },
  });

  const stopStreamMutation = useMutation({
    mutationFn: (deviceId: string) => apiService.stopStream(deviceId),
    onSuccess: (data, deviceId) => {
      setActiveStreams(prev => {
        const newSet = new Set(prev);
        newSet.delete(deviceId);
        return newSet;
      });
      queryClient.invalidateQueries({ queryKey: ['streams'] });
    },
  });

  const handleStartStream = async (deviceId: string) => {
    try {
      await startStreamMutation.mutateAsync(deviceId);
      // Refresh streams data to get updated webrtc_url
      await refetchStreams();
    } catch (error) {
      console.error('Failed to start stream:', error);
    }
  };

  const handleStopStream = async (deviceId: string) => {
    try {
      await stopStreamMutation.mutateAsync(deviceId);
      // Refresh streams data after stopping
      await refetchStreams();
    } catch (error) {
      console.error('Failed to stop stream:', error);
    }
  };

  const getStreamForDevice = (deviceId: string): Stream | undefined => {
    return streamsData?.find(stream => stream.device_id === deviceId);
  };

  const getStreamStatus = (deviceId: string) => {
    const stream = getStreamForDevice(deviceId);
    if (activeStreams.has(deviceId)) {
      return 'active';
    }
    return stream?.status || 'inactive';
  };

  const isLoading = devicesLoading || streamsLoading;

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  const onlineDevices = devicesData?.devices?.filter((device: Device) => device.status === 'ONLINE') || [];

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" gutterBottom>
            Video Streams
          </Typography>
          <Typography variant="body2" color="textSecondary">
            {onlineDevices.length} online devices available for streaming
          </Typography>
        </Box>
        <Button
          variant="outlined"
          startIcon={<Refresh />}
          onClick={() => {
            queryClient.invalidateQueries({ queryKey: ['devices'] });
            queryClient.invalidateQueries({ queryKey: ['streams'] });
          }}
        >
          Refresh
        </Button>
      </Box>

      {onlineDevices.length === 0 ? (
        <Alert severity="info">
          No online devices found. Please check device status or add new devices.
        </Alert>
      ) : (
        <Grid container spacing={3}>
          {onlineDevices.map((device: Device) => {
            const stream = getStreamForDevice(device.id);
            const streamStatus = getStreamStatus(device.id);
            const isStreamActive = streamStatus === 'active';
            const webrtcUrl = stream?.webrtc_url;

            return (
              <Grid item xs={12} sm={6} md={4} key={device.id}>
                <VideoPlayer
                  deviceId={device.id}
                  deviceName={device.name}
                  webrtcUrl={webrtcUrl}
                  onStartStream={() => handleStartStream(device.id)}
                  onStopStream={() => handleStopStream(device.id)}
                />
                
                <Box mt={1} display="flex" justifyContent="space-between" alignItems="center">
                  <Chip
                    label={streamStatus}
                    color={isStreamActive ? 'success' : 'default'}
                    size="small"
                  />
                  <Typography variant="caption" color="textSecondary">
                    {device.resolution} • {device.fps}fps
                  </Typography>
                </Box>
              </Grid>
            );
          })}
        </Grid>
      )}

      {/* Error handling */}
      {(startStreamMutation.isError || stopStreamMutation.isError) && (
        <Alert severity="error" sx={{ mt: 2 }}>
          Failed to manage stream. Please try again.
        </Alert>
      )}
    </Box>
  );
}; 