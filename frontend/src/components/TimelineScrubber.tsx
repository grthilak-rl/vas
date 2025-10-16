import React, { useState, useRef, useCallback, useMemo } from 'react';
import {
  Box,
  Slider,
  Typography,
  IconButton,
  Tooltip,
  Chip,
  LinearProgress,
  Alert,
} from '@mui/material';
import {
  PlayArrow,
  Pause,
  SkipPrevious,
  SkipNext,
  LiveTv,
  Schedule,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import * as dateFns from 'date-fns';
import apiService from '../services/api';
import { TimelineScrubberProps, TimelinePosition, RecordingSegment } from '../types';
import './TimelineScrubber.css';

export const TimelineScrubber: React.FC<TimelineScrubberProps> = ({
  deviceId,
  deviceName,
  onSeek,
  currentPosition,
  isLive = false,
  className = '',
  compact = false,
}) => {
  const [timelineHours, setTimelineHours] = useState(24);
  const [isPlaying, setIsPlaying] = useState(false);
  const [selectedSegment, setSelectedSegment] = useState<RecordingSegment | null>(null);
  const timelineRef = useRef<HTMLDivElement>(null);

  // Fetch recording timeline data
  const { data: timeline, isLoading, error } = useQuery({
    queryKey: ['recording-timeline', deviceId, timelineHours],
    queryFn: () => apiService.getRecordingTimeline(deviceId, timelineHours),
    refetchInterval: isLive ? 30000 : false, // Refresh every 30 seconds if live
    enabled: !!deviceId,
  });

  // Debug logging
  console.log('TimelineScrubber Debug:', {
    deviceId,
    timelineHours,
    isLoading,
    error: error?.message,
    timeline: timeline ? {
      segmentsCount: timeline.segments?.length || 0,
      timeRange: timeline.time_range,
      deviceName: timeline.device_name
    } : null
  });

  // Calculate timeline bounds
  const timelineStart = timeline && timeline.time_range?.start_time ? 
    dateFns.parseISO(timeline.time_range.start_time) : 
    dateFns.subHours(new Date(), timelineHours);
  const timelineEnd = useMemo(() => 
    timeline && timeline.time_range?.end_time ? 
      dateFns.parseISO(timeline.time_range.end_time) : 
      new Date(), 
    [timeline]
  );
  const timelineDuration = timelineEnd.getTime() - timelineStart.getTime();

  // Calculate current position percentage
  const getCurrentPositionPercentage = useCallback(() => {
    if (!timeline || !currentPosition || !currentPosition.timestamp) return 0;
    
    const currentTimestamp = dateFns.parseISO(currentPosition.timestamp);
    const position = currentTimestamp.getTime() - timelineStart.getTime();
    return Math.max(0, Math.min(100, (position / timelineDuration) * 100));
  }, [timeline, currentPosition, timelineStart, timelineDuration]);

  // Handle timeline scrub
  const handleTimelineChange = useCallback((event: Event, newValue: number | number[]) => {
    const percentage = Array.isArray(newValue) ? newValue[0] : newValue;
    const targetTime = new Date(timelineStart.getTime() + (timelineDuration * percentage / 100));
    
    // Find the closest segment
    const closestSegment = timeline?.segments?.find(segment => {
      if (!segment.start_time || !segment.end_time) return false;
      const segmentStart = dateFns.parseISO(segment.start_time);
      const segmentEnd = dateFns.parseISO(segment.end_time);
      return dateFns.isAfter(targetTime, segmentStart) && dateFns.isBefore(targetTime, segmentEnd);
    });

    const position: TimelinePosition = {
      timestamp: targetTime.toISOString(),
      segment: closestSegment || undefined,
      isLive: false,
    };

    setSelectedSegment(closestSegment || null);
    onSeek(position);
  }, [timeline, timelineStart, timelineDuration, onSeek]);

  // Handle play/pause
  const handlePlayPause = useCallback(() => {
    if (isLive) {
      // Switch to live mode
      const livePosition: TimelinePosition = {
        timestamp: new Date().toISOString(),
        isLive: true,
      };
      onSeek(livePosition);
      setIsPlaying(false);
    } else {
      setIsPlaying(!isPlaying);
    }
  }, [isLive, isPlaying, onSeek]);

  // Handle skip buttons
  const handleSkip = useCallback((direction: 'prev' | 'next') => {
    if (!timeline) return;

    const skipMinutes = 5; // Skip 5 minutes
    const currentTimestamp = currentPosition && currentPosition.timestamp ? 
      dateFns.parseISO(currentPosition.timestamp) : 
      new Date();
    const newTime = new Date(
      currentTimestamp.getTime() + (direction === 'next' ? skipMinutes : -skipMinutes) * 60 * 1000
    );

    // Ensure we stay within timeline bounds
    const clampedTime = new Date(Math.max(timelineStart.getTime(), Math.min(timelineEnd.getTime(), newTime.getTime())));
    
    const closestSegment = timeline.segments?.find(segment => {
      if (!segment.start_time || !segment.end_time) return false;
      const segmentStart = dateFns.parseISO(segment.start_time);
      const segmentEnd = dateFns.parseISO(segment.end_time);
      return dateFns.isAfter(clampedTime, segmentStart) && dateFns.isBefore(clampedTime, segmentEnd);
    });

    const position: TimelinePosition = {
      timestamp: clampedTime.toISOString(),
      segment: closestSegment || undefined,
      isLive: false,
    };

    setSelectedSegment(closestSegment || null);
    onSeek(position);
  }, [timeline, currentPosition, timelineStart, timelineEnd, onSeek]);

  // Handle timeline hours change
  const handleTimelineHoursChange = useCallback((hours: number) => {
    setTimelineHours(hours);
  }, []);

  // Render timeline segments
  const renderTimelineSegments = () => {
    if (!timeline?.segments) {
      console.log('No timeline segments to render');
      return null;
    }

    console.log('Rendering timeline segments:', timeline.segments.length);
    return timeline.segments.map((segment, index) => {
      if (!segment.start_time || !segment.end_time) {
        console.log('Skipping segment with missing time data:', segment);
        return null;
      }
      
      const segmentStart = dateFns.parseISO(segment.start_time);
      const segmentEnd = dateFns.parseISO(segment.end_time);
      const segmentStartPercent = ((segmentStart.getTime() - timelineStart.getTime()) / timelineDuration) * 100;
      const segmentDurationPercent = ((segmentEnd.getTime() - segmentStart.getTime()) / timelineDuration) * 100;

      console.log(`Rendering segment ${index}:`, {
        id: segment.id,
        startTime: segment.start_time,
        endTime: segment.end_time,
        startPercent: segmentStartPercent,
        durationPercent: segmentDurationPercent
      });

      return (
        <div
          key={segment.id}
          className="timeline-segment"
          style={{
            left: `${segmentStartPercent}%`,
            width: `${segmentDurationPercent}%`,
            zIndex: 5,
            minWidth: '4px',
            minHeight: '20px'
          }}
          title={`${dateFns.format(segmentStart, 'HH:mm:ss')} - ${dateFns.format(segmentEnd, 'HH:mm:ss')}`}
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            console.log('Segment clicked:', segment);
            console.log('Segment click event:', e);
            const position: TimelinePosition = {
              timestamp: segmentStart.toISOString(),
              segment: segment,
              isLive: false
            };
            console.log('Calling onSeek with position:', position);
            onSeek(position);
          }}
        />
      );
    });
  };

  // Render time markers
  const renderTimeMarkers = () => {
    const markers = [];
    const markerInterval = timelineHours <= 6 ? 1 : timelineHours <= 24 ? 2 : 6; // hours between markers
    
    for (let i = 0; i <= timelineHours; i += markerInterval) {
      const markerTime = dateFns.addHours(timelineStart, i);
      const markerPercent = ((markerTime.getTime() - timelineStart.getTime()) / timelineDuration) * 100;
      
      markers.push(
        <div
          key={i}
          className="timeline-marker"
          style={{ left: `${markerPercent}%` }}
        >
          <Typography variant="caption" className="timeline-marker-text">
            {dateFns.format(markerTime, 'HH:mm')}
          </Typography>
        </div>
      );
    }
    
    return markers;
  };

  if (error) {
    return (
      <Alert severity="error" className={`timeline-scrubber ${className}`}>
        Failed to load recording timeline: {error.message}
      </Alert>
    );
  }

  // Compact mode for overlay
  if (compact) {
    return (
      <Box sx={{ width: '100%' }}>
        {/* Compact Header */}
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
          <Typography variant="caption" sx={{ color: 'white', fontWeight: 600 }}>
            {deviceName} - Recording
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <Chip
              icon={<Schedule />}
              label={`${timelineHours}h`}
              size="small"
              sx={{ height: 20, fontSize: '0.7rem' }}
              onClick={() => handleTimelineHoursChange(timelineHours === 24 ? 6 : timelineHours === 6 ? 48 : 24)}
            />
            {isLive && (
              <Chip
                icon={<LiveTv />}
                label="LIVE"
                color="error"
                size="small"
                sx={{ height: 20, fontSize: '0.7rem', cursor: 'pointer' }}
                onClick={() => {
                  console.log('LIVE button clicked');
                  const position: TimelinePosition = {
                    timestamp: new Date().toISOString(),
                    isLive: true
                  };
                  onSeek(position);
                }}
              />
            )}
          </Box>
        </Box>

        {/* Compact Timeline */}
        <Box sx={{ position: 'relative', height: 30, mb: 1 }}>
          <Box sx={{ 
            position: 'relative', 
            height: 20, 
            backgroundColor: 'rgba(255, 255, 255, 0.2)', 
            borderRadius: 10,
            overflow: 'hidden'
          }}>
            {/* Segments */}
            {renderTimelineSegments()}
            
            {/* Current Position Indicator */}
            {currentPosition && !isLive && (
              <Box
                sx={{
                  position: 'absolute',
                  top: 0,
                  height: '100%',
                  width: 2,
                  backgroundColor: '#f44336',
                  left: `${getCurrentPositionPercentage()}%`,
                  zIndex: 3
                }}
              />
            )}
          </Box>

          {/* Compact Slider */}
          <Slider
            value={getCurrentPositionPercentage()}
            onChange={handleTimelineChange}
            disabled={isLive}
            min={0}
            max={100}
            step={0.1}
            sx={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              height: 20,
              '& .MuiSlider-track': { display: 'none' },
              '& .MuiSlider-rail': { display: 'none' },
              '& .MuiSlider-thumb': {
                width: 16,
                height: 16,
                backgroundColor: '#f44336',
                border: '2px solid white',
                boxShadow: '0 2px 4px rgba(0, 0, 0, 0.3)'
              }
            }}
          />
        </Box>

        {/* Compact Controls */}
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1 }}>
          <Tooltip title="Skip Backward">
            <span>
              <IconButton 
                onClick={() => handleSkip('prev')} 
                disabled={isLive}
                size="small"
                sx={{ color: 'white', p: 0.5 }}
              >
                <SkipPrevious fontSize="small" />
              </IconButton>
            </span>
          </Tooltip>
          
          <Tooltip title={isLive ? "Switch to Live" : isPlaying ? "Pause" : "Play"}>
            <IconButton 
              onClick={handlePlayPause} 
              color="primary"
              size="small"
              sx={{ p: 0.5 }}
            >
              {isLive ? <LiveTv fontSize="small" /> : isPlaying ? <Pause fontSize="small" /> : <PlayArrow fontSize="small" />}
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Skip Forward">
            <span>
              <IconButton 
                onClick={() => handleSkip('next')} 
                disabled={isLive}
                size="small"
                sx={{ color: 'white', p: 0.5 }}
              >
                <SkipNext fontSize="small" />
              </IconButton>
            </span>
          </Tooltip>

          {/* Current Time Display */}
          <Typography variant="caption" sx={{ color: 'white', minWidth: 60, textAlign: 'center' }}>
            {currentPosition && currentPosition.timestamp ? 
              dateFns.format(dateFns.parseISO(currentPosition.timestamp), 'HH:mm:ss') : 
              '--:--:--'}
          </Typography>
        </Box>

        {/* Compact Info */}
        <Typography variant="caption" sx={{ color: 'rgba(255, 255, 255, 0.7)', textAlign: 'center', display: 'block', mt: 0.5 }}>
          {timeline?.segments?.length || 0} segments • {dateFns.format(timelineStart, 'MMM dd, HH:mm')} - {dateFns.format(timelineEnd, 'MMM dd, HH:mm')}
        </Typography>
      </Box>
    );
  }

  return (
    <Box className={`timeline-scrubber ${className}`}>
      {/* Timeline Header */}
      <Box className="timeline-header">
        <Typography variant="h6" className="timeline-title">
          {deviceName} - Recording Timeline
        </Typography>
        <Box className="timeline-controls">
          <Chip
            icon={<Schedule />}
            label={`${timelineHours}h`}
            size="small"
            onClick={() => handleTimelineHoursChange(timelineHours === 24 ? 6 : timelineHours === 6 ? 48 : 24)}
          />
          {isLive && (
            <Chip
              icon={<LiveTv />}
              label="LIVE"
              color="error"
              size="small"
              sx={{ cursor: 'pointer' }}
              onClick={() => {
                console.log('LIVE button clicked');
                const position: TimelinePosition = {
                  timestamp: new Date().toISOString(),
                  isLive: true
                };
                onSeek(position);
              }}
            />
          )}
        </Box>
      </Box>

      {/* Loading Indicator */}
      {isLoading && (
        <LinearProgress className="timeline-loading" />
      )}

      {/* Timeline Container */}
      <Box className="timeline-container" ref={timelineRef}>
        {/* Timeline Track */}
        <Box className="timeline-track">
          {/* Segments */}
          {renderTimelineSegments()}
          
          {/* Time Markers */}
          {renderTimeMarkers()}
          
          {/* Current Position Indicator */}
          {currentPosition && !isLive && (
            <Box
              className="timeline-current-position"
              style={{ left: `${getCurrentPositionPercentage()}%` }}
            />
          )}
        </Box>

        {/* Timeline Slider */}
        <Slider
          value={getCurrentPositionPercentage()}
          onChange={handleTimelineChange}
          className="timeline-slider"
          disabled={isLive}
          min={0}
          max={100}
          step={0.1}
        />
      </Box>

      {/* Playback Controls */}
      <Box className="timeline-controls">
        <Tooltip title="Skip Backward">
          <span>
            <IconButton onClick={() => handleSkip('prev')} disabled={isLive}>
              <SkipPrevious />
            </IconButton>
          </span>
        </Tooltip>
        
        <Tooltip title={isLive ? "Switch to Live" : isPlaying ? "Pause" : "Play"}>
          <IconButton onClick={handlePlayPause} color="primary">
            {isLive ? <LiveTv /> : isPlaying ? <Pause /> : <PlayArrow />}
          </IconButton>
        </Tooltip>
        
        <Tooltip title="Skip Forward">
          <span>
            <IconButton onClick={() => handleSkip('next')} disabled={isLive}>
              <SkipNext />
            </IconButton>
          </span>
        </Tooltip>

        {/* Current Time Display */}
        <Typography variant="body2" className="timeline-time-display">
          {currentPosition && currentPosition.timestamp ? 
            dateFns.format(dateFns.parseISO(currentPosition.timestamp), 'HH:mm:ss') : 
            '--:--:--'}
        </Typography>

        {/* Segment Info */}
        {selectedSegment && selectedSegment.start_time && (
          <Chip
            label={`Segment: ${dateFns.format(dateFns.parseISO(selectedSegment.start_time), 'HH:mm:ss')}`}
            size="small"
            variant="outlined"
          />
        )}
      </Box>

      {/* Timeline Info */}
      {timeline && (
        <Box className="timeline-info">
          <Typography variant="caption" color="textSecondary">
            {timeline.total_segments} segments available • 
            {dateFns.format(timelineStart, 'MMM dd, HH:mm')} - {dateFns.format(timelineEnd, 'MMM dd, HH:mm')}
            {timeline.is_recording && ' • Recording Active'}
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default TimelineScrubber;
