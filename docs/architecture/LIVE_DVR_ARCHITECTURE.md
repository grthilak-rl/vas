# Live DVR Architecture Documentation

## Overview

The Live DVR (Digital Video Recorder) feature enables users to view live camera feeds with the ability to seek back in time to review recent events. This provides a seamless experience similar to professional surveillance systems like Genetec, where users can navigate through recent recordings without switching modes.

## Core Concept

The Live DVR system continuously records camera feeds in small segments while simultaneously streaming live content via WebRTC. Users can seamlessly navigate between live and recorded content using a timeline scrubber, providing immediate access to recent events without interrupting the live monitoring experience.

## Technical Architecture

### 1. Recording Service Layer

#### Live DVR Recording Service
- **Purpose**: Continuously records RTSP streams in small segments
- **Segment Duration**: 30 seconds per segment
- **Retention Period**: 48 hours (configurable)
- **Format**: MP4 (H.264) for web compatibility
- **Storage**: Local filesystem with metadata in database

#### Segment Management
- **Naming Convention**: `{device_id}_{timestamp}_{segment_index}.mp4`
- **Overlap**: 2-3 seconds between segments for seamless playback
- **Cleanup**: Automatic deletion of expired segments
- **Indexing**: Database metadata for quick segment lookup

### 2. Database Schema

#### Recording Segments Table
```sql
CREATE TABLE recording_segments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID NOT NULL REFERENCES devices(id),
    segment_file_path VARCHAR(500) NOT NULL,
    start_timestamp TIMESTAMP NOT NULL,
    end_timestamp TIMESTAMP NOT NULL,
    duration_seconds INTEGER NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_device_timestamp (device_id, start_timestamp),
    INDEX idx_timestamp_range (start_timestamp, end_timestamp)
);
```

#### Recording Status Table
```sql
CREATE TABLE recording_status (
    device_id UUID PRIMARY KEY REFERENCES devices(id),
    is_recording BOOLEAN DEFAULT FALSE,
    last_segment_timestamp TIMESTAMP,
    total_segments INTEGER DEFAULT 0,
    total_size_bytes BIGINT DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3. Backend Components

#### Live DVR Service
- **File**: `backend/app/services/live_dvr_service.py`
- **Responsibilities**:
  - Start/stop continuous recording for devices
  - Manage segment creation and cleanup
  - Handle FFmpeg processes
  - Monitor recording health

#### Recording API Endpoints
- **File**: `backend/app/api/recordings.py`
- **Endpoints**:
  - `GET /recordings/{device_id}/segments` - List available segments
  - `GET /recordings/{device_id}/segment/{timestamp}` - Get specific segment
  - `GET /recordings/{device_id}/timeline` - Get timeline data
  - `POST /recordings/{device_id}/start` - Start recording
  - `POST /recordings/{device_id}/stop` - Stop recording

#### FFmpeg Integration
- **Process Management**: Spawn and monitor FFmpeg processes
- **Error Handling**: Restart failed recordings
- **Resource Management**: Monitor CPU/memory usage
- **Quality Settings**: Configurable bitrate and resolution

### 4. Frontend Components

#### Enhanced Video Player
- **File**: `frontend/src/components/LiveDVRPlayer.tsx`
- **Features**:
  - Unified player for live and recorded content
  - Timeline scrubber for time navigation
  - Live indicator and current time display
  - Seamless switching between live and recorded modes

#### Timeline Scrubber Component
- **File**: `frontend/src/components/TimelineScrubber.tsx`
- **Features**:
  - Visual timeline showing available segments
  - Live indicator showing current time
  - Seek controls for time navigation
  - Segment availability indicators

#### Recording Status Component
- **File**: `frontend/src/components/RecordingStatus.tsx`
- **Features**:
  - Recording indicator for each camera
  - Storage usage display
  - Recording health status
  - Manual start/stop controls

### 5. Data Flow

#### Recording Flow
1. **Device Online**: Recording service detects device status
2. **FFmpeg Process**: Spawns FFmpeg process for RTSP recording
3. **Segment Creation**: Creates 30-second MP4 segments
4. **Metadata Storage**: Stores segment information in database
5. **Cleanup**: Removes expired segments automatically

#### Playback Flow
1. **User Seeks**: User clicks on timeline scrubber
2. **Segment Lookup**: Frontend requests segment for specific time
3. **Video Source**: Changes video source to recorded segment
4. **Seamless Playback**: HTML5 video player handles MP4 playback
5. **Return to Live**: User can return to live feed anytime

### 6. Storage Management

#### Segment Storage
- **Directory Structure**: `/recordings/{device_id}/{date}/`
- **File Naming**: `{timestamp}_{segment_index}.mp4`
- **Compression**: H.264 with optimized settings
- **Size Estimation**: ~2-3MB per 30-second segment

#### Cleanup Strategy
- **Automatic Cleanup**: Removes segments older than retention period
- **Storage Monitoring**: Tracks disk usage and alerts when full
- **Graceful Degradation**: Reduces retention if storage is low
- **Manual Cleanup**: Admin interface for manual segment management

### 7. Performance Considerations

#### Resource Usage
- **CPU Impact**: +5-10% per camera for recording
- **Memory Usage**: +50-100MB for segment buffering
- **Disk I/O**: Continuous write operations for segments
- **Network**: No additional network load (uses existing RTSP)

#### Optimization Strategies
- **Segment Overlap**: Minimizes gaps in playback
- **Efficient Encoding**: Optimized FFmpeg settings
- **Background Processing**: Non-blocking recording operations
- **Resource Monitoring**: Real-time performance tracking

### 8. Error Handling

#### Recording Failures
- **FFmpeg Errors**: Automatic restart of failed processes
- **Storage Issues**: Graceful degradation and alerts
- **Network Problems**: Retry logic for RTSP connection issues
- **Resource Exhaustion**: Automatic cleanup and quality reduction

#### Playback Issues
- **Missing Segments**: Graceful handling of gaps
- **Corrupted Files**: Automatic detection and replacement
- **Network Timeouts**: Retry logic for segment requests
- **Browser Compatibility**: Fallback for unsupported features

### 9. Configuration

#### Recording Settings
```yaml
live_dvr:
  segment_duration: 30  # seconds
  retention_hours: 48   # hours
  overlap_seconds: 3    # seconds
  quality:
    bitrate: "1M"       # 1 Mbps
    resolution: "1920x1080"
    framerate: 30
  storage:
    max_disk_usage: "80%"  # percentage
    cleanup_threshold: "75%"  # percentage
```

#### Device-Specific Settings
- **Per-Camera Configuration**: Different settings per device
- **Quality Profiles**: High/Medium/Low quality options
- **Retention Policies**: Custom retention per camera
- **Recording Schedules**: Time-based recording control

### 10. Security Considerations

#### Access Control
- **User Permissions**: Recording access based on user roles
- **Device Access**: Only authorized devices can be recorded
- **Segment Access**: Authentication required for segment playback
- **Admin Controls**: Restricted recording management functions

#### Data Protection
- **Encryption**: Optional encryption for stored segments
- **Access Logging**: Audit trail for recording access
- **Secure Storage**: Segments stored in protected directories
- **Data Retention**: Compliance with data retention policies

## Implementation Phases

### Phase 1: Core Recording Service
- Implement Live DVR recording service
- Add database schema for segments
- Create basic recording API endpoints
- Add FFmpeg integration and process management

### Phase 2: Frontend Integration
- Enhance VideoPlayer component with timeline scrubber
- Implement seamless live/recorded switching
- Add recording status indicators
- Create timeline navigation UI

### Phase 3: Advanced Features
- Add recording quality controls
- Implement storage management
- Add performance monitoring
- Create admin interface for recording management

### Phase 4: Optimization and Polish
- Performance optimization
- Error handling improvements
- User experience enhancements
- Documentation and testing

## Dependencies

### Backend Dependencies
- **FFmpeg**: Video recording and processing
- **SQLAlchemy**: Database operations
- **FastAPI**: API endpoints
- **asyncio**: Asynchronous processing
- **psutil**: System resource monitoring

### Frontend Dependencies
- **React**: Component framework
- **Material-UI**: UI components
- **React Query**: Data fetching and caching
- **Date-fns**: Date/time manipulation
- **React Player**: Video playback (if needed)

## Testing Strategy

### Unit Tests
- Recording service functionality
- Segment management logic
- API endpoint validation
- Database operations

### Integration Tests
- End-to-end recording workflow
- Frontend-backend integration
- FFmpeg process management
- Storage and cleanup operations

### Performance Tests
- Resource usage monitoring
- Concurrent recording tests
- Storage capacity tests
- Playback performance validation

## Monitoring and Alerting

### Key Metrics
- **Recording Success Rate**: Percentage of successful recordings
- **Storage Usage**: Disk space utilization
- **CPU/Memory Usage**: Resource consumption
- **Segment Availability**: Percentage of available segments
- **Playback Performance**: Video loading times

### Alerting Rules
- **Recording Failures**: Alert on consecutive failures
- **Storage Full**: Alert when storage exceeds threshold
- **Resource Exhaustion**: Alert on high CPU/memory usage
- **Segment Gaps**: Alert on missing segments

## Future Enhancements

### Advanced Features
- **Motion Detection**: Record only when motion detected
- **Event-Based Recording**: Record around specific events
- **Cloud Storage**: Optional cloud backup of segments
- **Advanced Analytics**: Recording usage analytics

### Scalability Improvements
- **Distributed Recording**: Multiple recording servers
- **Load Balancing**: Distribute recording load
- **Caching Layer**: Redis caching for segment metadata
- **CDN Integration**: Content delivery for segments

## Conclusion

The Live DVR architecture provides a robust foundation for implementing time-shifted video playback while maintaining the existing live streaming functionality. The modular design ensures minimal impact on current operations while providing a professional-grade surveillance experience.

The implementation follows industry best practices for video recording systems and provides a scalable foundation for future enhancements. The phased approach allows for incremental development and testing, reducing implementation risks and ensuring system stability.
