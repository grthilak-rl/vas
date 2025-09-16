import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Chip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  IconButton,
  Menu,
  MenuItem,
} from '@mui/material';
import {
  Add,
  MoreVert,
  Edit,
  Delete,
  Videocam,
  CheckCircle,
  Error,
  Warning,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiService from '../services/api';
import { Device, DeviceStatus } from '../types';

export const Devices: React.FC = () => {
  const [openDialog, setOpenDialog] = useState(false);
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedDeviceForMenu, setSelectedDeviceForMenu] = useState<Device | null>(null);
  
  const queryClient = useQueryClient();

  const { data: devicesData, isLoading } = useQuery({
    queryKey: ['devices'],
    queryFn: () => apiService.getDevices(1, 1000),
  });

  const deleteDeviceMutation = useMutation({
    mutationFn: (deviceId: string) => apiService.deleteDevice(deviceId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['devices'] });
    },
  });

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, device: Device) => {
    setAnchorEl(event.currentTarget);
    setSelectedDeviceForMenu(device);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedDeviceForMenu(null);
  };

  const handleEdit = (device: Device) => {
    setSelectedDevice(device);
    setOpenDialog(true);
    handleMenuClose();
  };

  const handleDelete = (deviceId: string) => {
    if (window.confirm('Are you sure you want to delete this device?')) {
      deleteDeviceMutation.mutate(deviceId);
    }
    handleMenuClose();
  };

  const getStatusColor = (status: DeviceStatus) => {
    switch (status) {
      case 'ONLINE':
        return 'success';
      case 'OFFLINE':
        return 'warning';
      case 'UNREACHABLE':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status: DeviceStatus) => {
    switch (status) {
      case 'ONLINE':
        return <CheckCircle fontSize="small" />;
      case 'OFFLINE':
        return <Warning fontSize="small" />;
      case 'UNREACHABLE':
        return <Error fontSize="small" />;
      default:
        return <Videocam fontSize="small" />;
    }
  };

  if (isLoading) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>
          Devices
        </Typography>
        <Typography>Loading devices...</Typography>
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" gutterBottom>
          Devices ({devicesData?.total || 0})
        </Typography>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => {
            setSelectedDevice(null);
            setOpenDialog(true);
          }}
        >
          Add Device
        </Button>
      </Box>

      <Grid container spacing={3}>
        {devicesData?.devices?.map((device: Device) => (
          <Grid item xs={12} sm={6} md={4} key={device.id}>
            <Card>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="flex-start">
                  <Box flex={1}>
                    <Typography variant="h6" gutterBottom>
                      {device.name}
                    </Typography>
                    <Typography variant="body2" color="textSecondary" gutterBottom>
                      {device.manufacturer} {device.model}
                    </Typography>
                    <Typography variant="body2" color="textSecondary" gutterBottom>
                      {device.ip_address}:{device.port}
                    </Typography>
                    <Typography variant="body2" color="textSecondary" gutterBottom>
                      {device.location}
                    </Typography>
                  </Box>
                  <IconButton
                    size="small"
                    onClick={(e) => handleMenuOpen(e, device)}
                  >
                    <MoreVert />
                  </IconButton>
                </Box>
                
                <Box display="flex" justifyContent="space-between" alignItems="center" mt={2}>
                  <Chip
                    icon={getStatusIcon(device.status)}
                    label={device.status}
                    color={getStatusColor(device.status) as any}
                    size="small"
                  />
                  <Typography variant="caption" color="textSecondary">
                    {device.resolution} • {device.fps}fps
                  </Typography>
                </Box>

                {device.tags && device.tags.length > 0 && (
                  <Box mt={1}>
                    {device.tags.slice(0, 3).map((tag: string, index: number) => (
                      <Chip
                        key={index}
                        label={tag}
                        size="small"
                        variant="outlined"
                        sx={{ mr: 0.5, mb: 0.5 }}
                      />
                    ))}
                    {device.tags.length > 3 && (
                      <Chip
                        label={`+${device.tags.length - 3}`}
                        size="small"
                        variant="outlined"
                      />
                    )}
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Device Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={() => selectedDeviceForMenu && handleEdit(selectedDeviceForMenu)}>
          <Edit fontSize="small" sx={{ mr: 1 }} />
          Edit
        </MenuItem>
        <MenuItem 
          onClick={() => selectedDeviceForMenu && handleDelete(selectedDeviceForMenu.id)}
          sx={{ color: 'error.main' }}
        >
          <Delete fontSize="small" sx={{ mr: 1 }} />
          Delete
        </MenuItem>
      </Menu>

      {/* Add/Edit Device Dialog */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {selectedDevice ? 'Edit Device' : 'Add New Device'}
        </DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="textSecondary">
            Device management functionality coming soon...
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          <Button variant="contained" disabled>
            {selectedDevice ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}; 