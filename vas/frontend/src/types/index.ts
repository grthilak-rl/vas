// API Response Types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  status: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// Authentication Types
export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface User {
  username: string;
  role: string;
  full_name: string;
}

// Device Types
export interface Device {
  id: string;
  name: string;
  device_type: string;
  manufacturer: string;
  model: string;
  ip_address: string;
  port: number;
  rtsp_url: string;
  username: string;
  password: string;
  location: string;
  description: string;
  tags: string[];
  device_metadata: Record<string, any>;
  hostname: string;
  vendor: string;
  resolution: string;
  codec: string;
  fps: number;
  last_seen: string;
  status: DeviceStatus;
  credentials_secure: boolean;
  encrypted_credentials: string;
  created_at: string;
  updated_at: string;
}

export type DeviceStatus = 'ONLINE' | 'OFFLINE' | 'UNREACHABLE';

export interface CreateDeviceRequest {
  name: string;
  device_type: string;
  manufacturer: string;
  model: string;
  ip_address: string;
  port: number;
  rtsp_url: string;
  username: string;
  password: string;
  location: string;
  description: string;
  tags: string[];
  metadata: Record<string, any>;
}

export interface UpdateDeviceRequest {
  name?: string;
  device_type?: string;
  manufacturer?: string;
  model?: string;
  ip_address?: string;
  port?: number;
  rtsp_url?: string;
  username?: string;
  password?: string;
  location?: string;
  description?: string;
  tags?: string[];
  metadata?: Record<string, any>;
}

// Discovery Types
export interface DiscoveryRequest {
  subnets: string[];
}

export interface DiscoveryTask {
  task_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  subnets: string[];
  results?: Record<string, DiscoveryResult[]>;
  created_at: string;
  completed_at?: string;
}

export interface DiscoveryResult {
  ip_address: string;
  hostname: string;
  vendor: string;
  rtsp_url: string;
  rtsp_ports: number[];
  discovered_at: number;
}

// Stream Types
export interface Stream {
  id: string;
  device_id: string;
  device_name: string;
  status: StreamStatus;
  mountpoint_id: number;
  webrtc_url: string;
  created_at: string;
  updated_at: string;
}

export type StreamStatus = 'active' | 'inactive' | 'error';

export interface StreamResponse {
  id: string;
  device_id: string;
  device_name: string;
  status: StreamStatus;
  mountpoint_id: number;
  webrtc_url: string;
  created_at: string;
  updated_at: string;
}

// Health Types
export interface HealthStatus {
  status: 'healthy' | 'unhealthy';
  timestamp: string;
  services: {
    database: ServiceHealth;
    redis: ServiceHealth;
    janus: ServiceHealth;
  };
}

export interface ServiceHealth {
  status: 'healthy' | 'unhealthy';
  response_time: number;
  error?: string;
}

// WebRTC Types
export interface WebRTCConfig {
  janus_url: string;
  mountpoint_id: number;
  session_id?: string;
  handle_id?: string;
}

// Snapshot Types
export interface Snapshot {
  id: string;
  device_id: string;
  image_format: string;
  width?: number;
  height?: number;
  file_size?: number;
  captured_at?: string;
  created_at: string;
  updated_at: string;
}

export interface SnapshotListResponse {
  snapshots: Snapshot[];
  total: number;
  page: number;
  per_page: number;
}

// UI Types
export interface TableColumn {
  field: string;
  headerName: string;
  width?: number;
  flex?: number;
  sortable?: boolean;
  filterable?: boolean;
  renderCell?: (params: any) => React.ReactNode;
}

export interface FilterOptions {
  status?: DeviceStatus[];
  device_type?: string[];
  manufacturer?: string[];
  tags?: string[];
}

export interface SortOptions {
  field: string;
  direction: 'asc' | 'desc';
} 