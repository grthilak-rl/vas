import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  CardMedia,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Chip,
  CircularProgress,
  Alert,
  Pagination,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tooltip,
  TextField,
  Collapse,
  Paper,
  Divider,
} from '@mui/material';
import {
  Refresh,
  Delete,
  Download,
  ZoomIn,
  PhotoCamera,
  FilterList,
  Search,
  Clear,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiService from '../services/api';
import { Device, Snapshot } from '../types';

// Component to handle image loading with authentication
const AuthenticatedImage: React.FC<{ 
  snapshotId: string; 
  alt: string; 
  onClick: () => void; 
  height: number;
  style?: React.CSSProperties;
}> = ({ snapshotId, alt, onClick, height, style }) => {
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let objectUrl: string | null = null;
    const fetchImage = async () => {
      setLoading(true);
      setError(null);
      try {
        const blob = await apiService.getSnapshotImageBinary(snapshotId);
        objectUrl = URL.createObjectURL(blob);
        setImageUrl(objectUrl);
      } catch (err: any) {
        console.error(`Failed to load image for snapshot ${snapshotId}:`, err);
        setError('Failed to load image');
      } finally {
        setLoading(false);
      }
    };

    fetchImage();

    return () => {
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
      }
    };
  }, [snapshotId]);

  if (loading) {
    return (
      <Box 
        display="flex" 
        justifyContent="center" 
        alignItems="center" 
        height={height} 
        sx={{ bgcolor: 'grey.200' }}
        style={style}
      >
        <CircularProgress size={24} />
      </Box>
    );
  }

  if (error || !imageUrl) {
    return (
      <Box 
        display="flex" 
        justifyContent="center" 
        alignItems="center" 
        height={height} 
        sx={{ bgcolor: 'grey.300' }}
        style={style}
      >
        <Alert severity="error" sx={{ p: 1 }}>{error || 'No image'}</Alert>
      </Box>
    );
  }

  return (
    <CardMedia
      component="img"
      height={height}
      image={imageUrl}
      alt={alt}
      sx={{ cursor: 'pointer' }}
      onClick={onClick}
      style={style}
    />
  );
};

export const Snapshots: React.FC = () => {
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>('');
  const [page, setPage] = useState(1);
  const [selectedSnapshot, setSelectedSnapshot] = useState<Snapshot | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [snapshotToDelete, setSnapshotToDelete] = useState<Snapshot | null>(null);
  const [selectedSnapshots, setSelectedSnapshots] = useState<Set<string>>(new Set());
  const [batchMode, setBatchMode] = useState(false);
  const [bulkDeleteDialogOpen, setBulkDeleteDialogOpen] = useState(false);
  
  // Search and filter state
  const [searchQuery, setSearchQuery] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [filteredSnapshots, setFilteredSnapshots] = useState<Snapshot[]>([]);
  
  const queryClient = useQueryClient();

  const { data: devicesData, isLoading: devicesLoading } = useQuery({
    queryKey: ['devices'],
    queryFn: () => apiService.getDevices(1, 1000),
  });

  const { data: snapshotsData, isLoading: snapshotsLoading, refetch: refetchSnapshots } = useQuery({
    queryKey: ['snapshots', selectedDeviceId, page],
    queryFn: () => apiService.getSnapshots(selectedDeviceId || undefined, page, 12),
  });

  const deleteSnapshotMutation = useMutation({
    mutationFn: (snapshotId: string) => apiService.deleteSnapshot(snapshotId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['snapshots'] });
      setDeleteDialogOpen(false);
      setSnapshotToDelete(null);
    },
  });

  const handleDeviceChange = (deviceId: string) => {
    setSelectedDeviceId(deviceId);
    setPage(1); // Reset to first page when device changes
  };

  const handlePageChange = (event: React.ChangeEvent<unknown>, value: number) => {
    setPage(value);
  };

  const handleViewSnapshot = (snapshot: Snapshot) => {
    setSelectedSnapshot(snapshot);
  };

  const handleCloseViewer = () => {
    setSelectedSnapshot(null);
  };

  const handleDeleteClick = (snapshot: Snapshot) => {
    setSnapshotToDelete(snapshot);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = () => {
    if (snapshotToDelete) {
      deleteSnapshotMutation.mutate(snapshotToDelete.id);
    }
  };

  const handleDeleteCancel = () => {
    setDeleteDialogOpen(false);
    setSnapshotToDelete(null);
  };

  // Batch operation handlers
  const handleToggleBatchMode = () => {
    setBatchMode(!batchMode);
    setSelectedSnapshots(new Set());
  };

  const handleSelectSnapshot = (snapshotId: string) => {
    const newSelected = new Set(selectedSnapshots);
    if (newSelected.has(snapshotId)) {
      newSelected.delete(snapshotId);
    } else {
      newSelected.add(snapshotId);
    }
    setSelectedSnapshots(newSelected);
  };

  const handleSelectAll = () => {
    if (selectedSnapshots.size === filteredSnapshots.length) {
      setSelectedSnapshots(new Set());
    } else {
      const allIds = new Set(filteredSnapshots.map((s: Snapshot) => s.id));
      setSelectedSnapshots(allIds);
    }
  };

  const handleDownload = useCallback(async (snapshot: Snapshot) => {
    try {
      const blob = await apiService.getSnapshotImageBinary(snapshot.id);
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `snapshot_${snapshot.id}_${snapshot.captured_at || 'unknown'}.${snapshot.image_format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (error: any) {
      console.error('Failed to download snapshot:', error);
      // You could add a toast notification here
    }
  }, []);

  const handleBulkDownload = useCallback(async () => {
    if (selectedSnapshots.size === 0) return;
    
    try {
      // Convert Set to Array for iteration
      const snapshotIds = Array.from(selectedSnapshots);
      for (const snapshotId of snapshotIds) {
        const snapshot = snapshotsData?.snapshots.find((s: Snapshot) => s.id === snapshotId);
        if (snapshot) {
          await handleDownload(snapshot);
          // Small delay between downloads to avoid overwhelming the browser
          await new Promise(resolve => setTimeout(resolve, 100));
        }
      }
    } catch (error) {
      console.error('Failed to download snapshots:', error);
    }
  }, [selectedSnapshots, snapshotsData, handleDownload]);

  const handleBulkDelete = () => {
    setBulkDeleteDialogOpen(true);
  };

  const handleBulkDeleteConfirm = () => {
    if (selectedSnapshots.size === 0) return;
    
    // Delete all selected snapshots
    selectedSnapshots.forEach(snapshotId => {
      deleteSnapshotMutation.mutate(snapshotId);
    });
    
    setBulkDeleteDialogOpen(false);
    setSelectedSnapshots(new Set());
    setBatchMode(false);
  };

  const handleBulkDeleteCancel = () => {
    setBulkDeleteDialogOpen(false);
  };

  // Search and filter handlers
  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(event.target.value);
  };

  const handleDateFromChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setDateFrom(event.target.value);
  };

  const handleDateToChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setDateTo(event.target.value);
  };

  const handleClearFilters = () => {
    setSearchQuery('');
    setDateFrom('');
    setDateTo('');
    setSelectedDeviceId(''); // Reset to "All Devices"
    setFilteredSnapshots([]);
  };

  const handleToggleFilters = () => {
    setShowFilters(!showFilters);
  };

  // Filter snapshots based on search criteria
  const applyFilters = useCallback((snapshots: Snapshot[]) => {
    let filtered = [...snapshots];

    // Search query filter (search in ID, device ID, format)
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(snapshot => 
        snapshot.id.toLowerCase().includes(query) ||
        snapshot.device_id.toLowerCase().includes(query) ||
        snapshot.image_format.toLowerCase().includes(query)
      );
    }

    // Date range filter
    if (dateFrom) {
      const fromDate = new Date(dateFrom);
      filtered = filtered.filter(snapshot => {
        if (!snapshot.captured_at) return false;
        return new Date(snapshot.captured_at) >= fromDate;
      });
    }

    if (dateTo) {
      const toDate = new Date(dateTo);
      toDate.setHours(23, 59, 59, 999); // End of day
      filtered = filtered.filter(snapshot => {
        if (!snapshot.captured_at) return false;
        return new Date(snapshot.captured_at) <= toDate;
      });
    }

    return filtered;
  }, [searchQuery, dateFrom, dateTo]);

  // Apply filters when snapshots data changes
  useEffect(() => {
    if (snapshotsData?.snapshots) {
      const filtered = applyFilters(snapshotsData.snapshots);
      setFilteredSnapshots(filtered);
    }
  }, [snapshotsData?.snapshots, applyFilters]);

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Unknown';
    return new Date(dateString).toLocaleString();
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return 'Unknown';
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  const onlineDevices = devicesData?.devices?.filter((device: Device) => device.status === 'ONLINE') || [];

  if (devicesLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" gutterBottom>
            Snapshots
          </Typography>
          <Typography variant="body2" color="textSecondary">
            View and manage camera snapshots
          </Typography>
        </Box>
        <Box display="flex" gap={1}>
          <Button
            variant={showFilters ? "contained" : "outlined"}
            startIcon={<FilterList />}
            onClick={handleToggleFilters}
          >
            Filters
          </Button>
          <Button
            variant={batchMode ? "contained" : "outlined"}
            startIcon={<PhotoCamera />}
            onClick={handleToggleBatchMode}
          >
            {batchMode ? 'Exit Batch' : 'Batch Mode'}
          </Button>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={() => {
              queryClient.invalidateQueries({ queryKey: ['devices'] });
              queryClient.invalidateQueries({ queryKey: ['snapshots'] });
            }}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {/* Search and Filter Panel */}
      <Collapse in={showFilters}>
        <Paper sx={{ p: 2, mb: 3 }}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">Search & Filters</Typography>
            <Button
              size="small"
              startIcon={<Clear />}
              onClick={handleClearFilters}
              disabled={!searchQuery && !dateFrom && !dateTo && !selectedDeviceId}
            >
              Clear All
            </Button>
          </Box>
          
          <Grid container spacing={2}>
            {/* Search Query */}
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Search"
                placeholder="Search by ID, device, or format..."
                value={searchQuery}
                onChange={handleSearchChange}
                InputProps={{
                  startAdornment: <Search sx={{ mr: 1, color: 'text.secondary' }} />
                }}
              />
            </Grid>

            {/* Date From */}
            <Grid item xs={12} md={2}>
              <TextField
                fullWidth
                label="From Date"
                type="date"
                value={dateFrom}
                onChange={handleDateFromChange}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>

            {/* Date To */}
            <Grid item xs={12} md={2}>
              <TextField
                fullWidth
                label="To Date"
                type="date"
                value={dateTo}
                onChange={handleDateToChange}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>

            {/* Device Selection */}
            <Grid item xs={12} md={4}>
              <FormControl fullWidth>
                <InputLabel>Select Device</InputLabel>
                <Select
                  value={selectedDeviceId}
                  label="Select Device"
                  onChange={(e) => handleDeviceChange(e.target.value)}
                >
                  <MenuItem value="">
                    <em>All Devices</em>
                  </MenuItem>
                  {onlineDevices.map((device: Device) => (
                    <MenuItem key={device.id} value={device.id}>
                      {device.name} ({device.ip_address})
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          </Grid>

          {/* Active Filters Summary */}
          {(searchQuery || dateFrom || dateTo || selectedDeviceId) && (
            <>
              <Divider sx={{ my: 2 }} />
              <Box>
                <Typography variant="body2" color="textSecondary" mb={1}>
                  Active Filters:
                </Typography>
                <Box display="flex" flexWrap="wrap" gap={1}>
                  {searchQuery && (
                    <Chip
                      label={`Search: "${searchQuery}"`}
                      size="small"
                      onDelete={() => setSearchQuery('')}
                    />
                  )}
                  {dateFrom && (
                    <Chip
                      label={`From: ${dateFrom}`}
                      size="small"
                      onDelete={() => setDateFrom('')}
                    />
                  )}
                  {dateTo && (
                    <Chip
                      label={`To: ${dateTo}`}
                      size="small"
                      onDelete={() => setDateTo('')}
                    />
                  )}
                  {selectedDeviceId && (
                    <Chip
                      label={`Device: ${onlineDevices.find((d: Device) => d.id === selectedDeviceId)?.name || selectedDeviceId}`}
                      size="small"
                      onDelete={() => setSelectedDeviceId('')}
                    />
                  )}
                </Box>
              </Box>
            </>
          )}
        </Paper>
      </Collapse>

      {snapshotsLoading ? (
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress />
        </Box>
      ) : !snapshotsData?.snapshots?.length ? (
        <Alert severity="info">
          No snapshots found. Take a snapshot from the Streams page.
        </Alert>
      ) : (
        <>
          {/* Batch Operations Bar */}
          {batchMode && (
            <Box 
              display="flex" 
              justifyContent="space-between" 
              alignItems="center" 
              p={2} 
              mb={2}
              sx={{ 
                bgcolor: 'primary.light', 
                borderRadius: 1,
                color: 'primary.contrastText'
              }}
            >
              <Box display="flex" alignItems="center" gap={2}>
                <Typography variant="body2">
                  {selectedSnapshots.size} of {filteredSnapshots.length} selected
                </Typography>
                <Button
                  size="small"
                  variant="outlined"
                  onClick={handleSelectAll}
                  sx={{ color: 'inherit', borderColor: 'currentColor' }}
                >
                  {selectedSnapshots.size === filteredSnapshots.length ? 'Deselect All' : 'Select All'}
                </Button>
              </Box>
              <Box display="flex" gap={1}>
                <Button
                  size="small"
                  variant="contained"
                  startIcon={<Download />}
                  onClick={handleBulkDownload}
                  disabled={selectedSnapshots.size === 0}
                  sx={{ bgcolor: 'success.main' }}
                >
                  Download ({selectedSnapshots.size})
                </Button>
                <Button
                  size="small"
                  variant="contained"
                  startIcon={<Delete />}
                  onClick={handleBulkDelete}
                  disabled={selectedSnapshots.size === 0}
                  sx={{ bgcolor: 'error.main' }}
                >
                  Delete ({selectedSnapshots.size})
                </Button>
              </Box>
            </Box>
          )}

          {/* Snapshots Grid */}
          <Grid container spacing={2} mb={3}>
            {filteredSnapshots.map((snapshot: Snapshot) => (
              <Grid item xs={12} sm={6} md={4} lg={3} key={snapshot.id}>
                <Card 
                  sx={{ 
                    height: '100%', 
                    display: 'flex', 
                    flexDirection: 'column',
                    position: 'relative',
                    border: batchMode && selectedSnapshots.has(snapshot.id) ? '2px solid' : '1px solid',
                    borderColor: batchMode && selectedSnapshots.has(snapshot.id) ? 'primary.main' : 'divider'
                  }}
                >
                  {batchMode && (
                    <Box
                      sx={{
                        position: 'absolute',
                        top: 8,
                        left: 8,
                        zIndex: 1,
                        bgcolor: 'background.paper',
                        borderRadius: '50%',
                        p: 0.5
                      }}
                    >
                      <input
                        type="checkbox"
                        checked={selectedSnapshots.has(snapshot.id)}
                        onChange={() => handleSelectSnapshot(snapshot.id)}
                        style={{ width: 20, height: 20 }}
                      />
                    </Box>
                  )}
                  <AuthenticatedImage
                    snapshotId={snapshot.id}
                    alt={`Snapshot ${snapshot.id}`}
                    onClick={() => batchMode ? handleSelectSnapshot(snapshot.id) : handleViewSnapshot(snapshot)}
                    height={200}
                    style={{ objectFit: 'cover' }}
                  />
                  <CardContent sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
                    <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                      <Chip
                        label={snapshot.image_format.toUpperCase()}
                        size="small"
                        color="primary"
                        variant="outlined"
                      />
                      <Typography variant="caption" color="textSecondary">
                        {formatFileSize(snapshot.file_size)}
                      </Typography>
                    </Box>
                    
                    <Typography variant="body2" color="textSecondary" mb={2}>
                      {formatDate(snapshot.captured_at)}
                    </Typography>

                    {snapshot.width && snapshot.height && (
                      <Typography variant="caption" color="textSecondary" mb={2}>
                        {snapshot.width} × {snapshot.height}
                      </Typography>
                    )}

                    <Box display="flex" gap={1} mt="auto">
                      <Tooltip title="View Full Size">
                        <IconButton
                          size="small"
                          onClick={() => handleViewSnapshot(snapshot)}
                        >
                          <ZoomIn />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Download">
                        <IconButton
                          size="small"
                          onClick={() => handleDownload(snapshot)}
                        >
                          <Download />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Delete">
                        <IconButton
                          size="small"
                          onClick={() => handleDeleteClick(snapshot)}
                          color="error"
                        >
                          <Delete />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>

          {/* Pagination */}
          {snapshotsData.total > 12 && (
            <Box display="flex" justifyContent="center" mt={3}>
              <Pagination
                count={Math.ceil(snapshotsData.total / 12)}
                page={page}
                onChange={handlePageChange}
                color="primary"
              />
            </Box>
          )}

          {/* Summary */}
          <Box mt={2}>
            <Typography variant="body2" color="textSecondary">
              Showing {filteredSnapshots.length} of {snapshotsData.total} snapshots
              {(searchQuery || dateFrom || dateTo || selectedDeviceId) && (
                <span> (filtered from {snapshotsData.snapshots.length} total)</span>
              )}
            </Typography>
          </Box>
        </>
      )}

      {/* Snapshot Viewer Dialog */}
      <Dialog
        open={!!selectedSnapshot}
        onClose={handleCloseViewer}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          Snapshot Details
          {selectedSnapshot && (
            <Typography variant="body2" color="textSecondary">
              {formatDate(selectedSnapshot.captured_at)}
            </Typography>
          )}
        </DialogTitle>
        <DialogContent>
          {selectedSnapshot && (
            <Box>
              <Box display="flex" justifyContent="center" mb={2}>
                <AuthenticatedImage
                  snapshotId={selectedSnapshot.id}
                  alt={`Snapshot ${selectedSnapshot.id}`}
                  onClick={() => {}}
                  height={400}
                  style={{
                    maxWidth: '100%',
                    maxHeight: '70vh',
                    objectFit: 'contain',
                  }}
                />
              </Box>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    Format: {selectedSnapshot.image_format.toUpperCase()}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    Size: {formatFileSize(selectedSnapshot.file_size)}
                  </Typography>
                </Grid>
                {selectedSnapshot.width && selectedSnapshot.height && (
                  <Grid item xs={6}>
                    <Typography variant="body2" color="textSecondary">
                      Dimensions: {selectedSnapshot.width} × {selectedSnapshot.height}
                    </Typography>
                  </Grid>
                )}
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    ID: {selectedSnapshot.id}
                  </Typography>
                </Grid>
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          {selectedSnapshot && (
            <Button
              startIcon={<Download />}
              onClick={() => handleDownload(selectedSnapshot)}
            >
              Download
            </Button>
          )}
          <Button onClick={handleCloseViewer}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={handleDeleteCancel}
      >
        <DialogTitle>Delete Snapshot</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete this snapshot? This action cannot be undone.
          </Typography>
          {snapshotToDelete && (
            <Typography variant="body2" color="textSecondary" mt={1}>
              Snapshot taken on {formatDate(snapshotToDelete.captured_at)}
            </Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDeleteCancel}>Cancel</Button>
          <Button
            onClick={handleDeleteConfirm}
            color="error"
            disabled={deleteSnapshotMutation.isPending}
          >
            {deleteSnapshotMutation.isPending ? <CircularProgress size={20} /> : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Bulk Delete Confirmation Dialog */}
      <Dialog
        open={bulkDeleteDialogOpen}
        onClose={handleBulkDeleteCancel}
      >
        <DialogTitle>Delete Multiple Snapshots</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete {selectedSnapshots.size} snapshots? This action cannot be undone.
          </Typography>
          <Typography variant="body2" color="textSecondary" mt={1}>
            This will permanently remove all selected snapshots from the system.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleBulkDeleteCancel}>Cancel</Button>
          <Button
            onClick={handleBulkDeleteConfirm}
            color="error"
            disabled={deleteSnapshotMutation.isPending}
          >
            {deleteSnapshotMutation.isPending ? <CircularProgress size={20} /> : `Delete ${selectedSnapshots.size} Snapshots`}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Error handling */}
      {deleteSnapshotMutation.isError && (
        <Alert severity="error" sx={{ mt: 2 }}>
          Failed to delete snapshot. Please try again.
        </Alert>
      )}
    </Box>
  );
};
