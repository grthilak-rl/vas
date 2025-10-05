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

  // Calculate timeline bounds
  const timelineStart = timeline && timeline.time_range?.start ? 
    dateFns.parseISO(timeline.time_range.start) : 
    dateFns.subHours(new Date(), timelineHours);
  const timelineEnd = useMemo(() => 
    timeline && timeline.time_range?.end ? 
      dateFns.parseISO(timeline.time_range.end) : 
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
      if (!segment.start_timestamp || !segment.end_timestamp) return false;
      const segmentStart = dateFns.parseISO(segment.start_timestamp);
      const segmentEnd = dateFns.parseISO(segment.end_timestamp);
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
      if (!segment.start_timestamp || !segment.end_timestamp) return false;
      const segmentStart = dateFns.parseISO(segment.start_timestamp);
      const segmentEnd = dateFns.parseISO(segment.end_timestamp);
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
    if (!timeline?.segments) return null;

    return timeline.segments.map((segment, index) => {
      if (!segment.start_timestamp || !segment.end_timestamp) return null;
      
      const segmentStart = dateFns.parseISO(segment.start_timestamp);
      const segmentEnd = dateFns.parseISO(segment.end_timestamp);
      const segmentStartPercent = ((segmentStart.getTime() - timelineStart.getTime()) / timelineDuration) * 100;
      const segmentDurationPercent = ((segmentEnd.getTime() - segmentStart.getTime()) / timelineDuration) * 100;

      return (
        <div
          key={segment.id}
          className="timeline-segment"
          style={{
            left: `${segmentStartPercent}%`,
            width: `${segmentDurationPercent}%`,
          }}
          title={`${dateFns.format(segmentStart, 'HH:mm:ss')} - ${dateFns.format(segmentEnd, 'HH:mm:ss')}`}
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
          <IconButton onClick={() => handleSkip('prev')} disabled={isLive}>
            <SkipPrevious />
          </IconButton>
        </Tooltip>
        
        <Tooltip title={isLive ? "Switch to Live" : isPlaying ? "Pause" : "Play"}>
          <IconButton onClick={handlePlayPause} color="primary">
            {isLive ? <LiveTv /> : isPlaying ? <Pause /> : <PlayArrow />}
          </IconButton>
        </Tooltip>
        
        <Tooltip title="Skip Forward">
          <IconButton onClick={() => handleSkip('next')} disabled={isLive}>
            <SkipNext />
          </IconButton>
        </Tooltip>

        {/* Current Time Display */}
        <Typography variant="body2" className="timeline-time-display">
          {currentPosition && currentPosition.timestamp ? 
            dateFns.format(dateFns.parseISO(currentPosition.timestamp), 'HH:mm:ss') : 
            '--:--:--'}
        </Typography>

        {/* Segment Info */}
        {selectedSegment && selectedSegment.start_timestamp && (
          <Chip
            label={`Segment: ${dateFns.format(dateFns.parseISO(selectedSegment.start_timestamp), 'HH:mm:ss')}`}
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
