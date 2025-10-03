# Snapshot Feature Implementation Plan

## 🎯 **Safe Implementation Strategy**

This document outlines how to implement the snapshot feature without affecting the existing working VAS system.

## 📋 **Implementation Steps**

### **Step 1: Database Schema (New Table)**
- Create `snapshots` table with foreign key to `devices`
- Use Alembic migration for safe database updates
- No changes to existing `devices` table

### **Step 2: New Models and Schemas**
- Add `Snapshot` model in `app/models.py`
- Add snapshot schemas in `app/schemas.py`
- Keep existing models unchanged

### **Step 3: Snapshot Service**
- Create `app/services/snapshot_service.py`
- Use FFmpeg to capture frames from RTSP streams
- Handle image storage and retrieval

### **Step 4: New API Endpoints**
- Create `app/api/snapshots.py` router
- Add to main app router
- Keep existing API endpoints unchanged

### **Step 5: Frontend Integration**
- Add snapshot functionality to React frontend
- New components for snapshot capture and display
- Keep existing video player unchanged

## 🔧 **Technical Implementation**

### **Database Schema**
```sql
CREATE TABLE snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    image_data BYTEA NOT NULL,
    image_format VARCHAR(10) NOT NULL DEFAULT 'jpeg',
    width INTEGER,
    height INTEGER,
    file_size INTEGER,
    captured_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_snapshots_device_id ON snapshots(device_id);
CREATE INDEX idx_snapshots_captured_at ON snapshots(captured_at);
```

### **API Endpoints**
```
POST /api/snapshots/capture/{device_id}  - Capture snapshot
GET  /api/snapshots/{snapshot_id}        - Get snapshot image
GET  /api/snapshots/device/{device_id}   - List device snapshots
DELETE /api/snapshots/{snapshot_id}      - Delete snapshot
```

### **Snapshot Capture Process**
1. Validate device exists and is online
2. Use FFmpeg to capture frame from RTSP stream
3. Convert to JPEG format
4. Store in database
5. Return snapshot metadata

## 🚨 **Safety Measures**

### **Non-Destructive Changes**
- All new code in separate files
- No modifications to existing models
- No changes to existing API endpoints
- No changes to Janus configuration

### **Testing Strategy**
- Test snapshot feature independently
- Verify existing functionality still works
- Use regression test script before deployment

### **Rollback Plan**
- Database migration can be rolled back
- New API endpoints can be disabled
- No impact on existing video streaming

## 📁 **File Structure**

```
vas/backend/
├── app/
│   ├── models.py              # Add Snapshot model
│   ├── schemas.py             # Add snapshot schemas
│   ├── api/
│   │   └── snapshots.py       # New snapshot API
│   ├── services/
│   │   └── snapshot_service.py # New snapshot service
│   └── main.py                # Add snapshot router
├── migrations/
│   └── versions/
│       └── 003_add_snapshots_table.py  # New migration
└── requirements.txt           # Add FFmpeg dependency
```

## 🔄 **Development Workflow**

### **Phase 1: Database & Models**
1. Create migration for snapshots table
2. Add Snapshot model
3. Add snapshot schemas
4. Test database changes

### **Phase 2: Backend Service**
1. Implement snapshot service
2. Create snapshot API endpoints
3. Test API functionality
4. Run regression tests

### **Phase 3: Frontend Integration**
1. Add snapshot components
2. Integrate with existing UI
3. Test end-to-end functionality
4. Final regression testing

## ✅ **Success Criteria**

- [ ] Snapshot capture works for both live cameras
- [ ] Snapshots stored in database successfully
- [ ] API endpoints return correct data
- [ ] Frontend can display snapshots
- [ ] Existing video streaming still works
- [ ] No performance impact on live streams
- [ ] All regression tests pass

## 🚀 **Next Steps**

1. **Backup current system**: `./backup-config.sh`
2. **Create snapshot branch**: `git checkout -b feature/snapshots`
3. **Implement database changes**
4. **Add snapshot service**
5. **Create API endpoints**
6. **Test thoroughly**
7. **Integrate with frontend**
8. **Run regression tests**
9. **Deploy to main branch**

This approach ensures we can add the snapshot feature without risking the existing working system.
