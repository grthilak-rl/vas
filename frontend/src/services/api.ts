import axios, { AxiosInstance, AxiosResponse } from 'axios';
import {
  LoginRequest,
  LoginResponse,
  Device,
  CreateDeviceRequest,
  UpdateDeviceRequest,
  DiscoveryRequest,
  DiscoveryTask,
  Stream,
  StreamResponse,
  HealthStatus,
  Snapshot,
  SnapshotListResponse,
  RecordingTimeline,
  RecordingSegment,
  RecordingStatus
} from '../types';

class ApiService {
  private api: AxiosInstance;
  private baseURL: string;

  constructor() {
    // Use full URL to backend for development, relative URL for production
    const devApiUrl = process.env.REACT_APP_SERVER_IP 
      ? `http://${process.env.REACT_APP_SERVER_IP}:8000/api`
      : `http://${window.location.hostname}:8000/api`;
    
    this.baseURL = process.env.NODE_ENV === 'development' 
      ? devApiUrl
      : (process.env.REACT_APP_API_URL || '/api');
    this.api = axios.create({
      baseURL: this.baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add request interceptor to include auth token
    this.api.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Add response interceptor to handle auth errors
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('access_token');
          localStorage.removeItem('user');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Authentication
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response: AxiosResponse<LoginResponse> = await this.api.post('/auth/login-json', credentials);
    return response.data;
  }

  async logout(): Promise<void> {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
  }

  // Health Check
  async getHealth(): Promise<HealthStatus> {
    const response: AxiosResponse<HealthStatus> = await this.api.get('/health');
    return response.data;
  }

  // Devices
  async getDevices(
    page: number = 1,
    size: number = 20,
    filters?: Record<string, any>
  ): Promise<any> {
    // Convert page/size to skip/limit for backend
    const skip = (page - 1) * size;
    const limit = size;
    
    const params = new URLSearchParams({
      skip: skip.toString(),
      limit: limit.toString(),
      ...filters,
    });
    
    const response: AxiosResponse<any> = await this.api.get(`/devices/?${params}`);
    return response.data;
  }

  async getDevice(id: string): Promise<Device> {
    const response: AxiosResponse<Device> = await this.api.get(`/devices/${id}`);
    return response.data;
  }

  async createDevice(device: CreateDeviceRequest): Promise<Device> {
    const response: AxiosResponse<Device> = await this.api.post('/devices', device);
    return response.data;
  }

  async updateDevice(id: string, device: UpdateDeviceRequest): Promise<Device> {
    const response: AxiosResponse<Device> = await this.api.patch(`/devices/${id}`, device);
    return response.data;
  }

  async deleteDevice(id: string): Promise<void> {
    await this.api.delete(`/devices/${id}`);
  }

  async validateDevice(rtspUrl: string, username: string = '', password: string = ''): Promise<any> {
    const response: AxiosResponse = await this.api.post('/devices/validate', {
      rtsp_url: rtspUrl,
      username,
      password,
    });
    return response.data;
  }

  async getDeviceStatus(id: string): Promise<any> {
    const response: AxiosResponse = await this.api.get(`/devices/${id}/status`);
    return response.data;
  }

  // Discovery
  async startDiscovery(request: DiscoveryRequest): Promise<DiscoveryTask> {
    const response: AxiosResponse<DiscoveryTask> = await this.api.post('/discover', request);
    return response.data;
  }

  async getDiscoveryTask(taskId: string): Promise<DiscoveryTask> {
    const response: AxiosResponse<DiscoveryTask> = await this.api.get(`/discover/${taskId}`);
    return response.data;
  }

  async getDiscoveryTasks(): Promise<DiscoveryTask[]> {
    const response: AxiosResponse<DiscoveryTask[]> = await this.api.get('/discover');
    return response.data;
  }

  // Streams
  async getStreams(): Promise<Stream[]> {
    const response: AxiosResponse<Stream[]> = await this.api.get('/streams');
    return response.data;
  }

  async startStream(deviceId: string): Promise<StreamResponse> {
    const response: AxiosResponse<StreamResponse> = await this.api.post(`/streams/${deviceId}/start`);
    return response.data;
  }

  async stopStream(deviceId: string): Promise<void> {
    await this.api.post(`/streams/${deviceId}/stop`);
  }

  async getStreamStatus(deviceId: string): Promise<StreamResponse> {
    const response: AxiosResponse<StreamResponse> = await this.api.get(`/streams/${deviceId}/status`);
    return response.data;
  }

  async getStreamHealth(): Promise<any> {
    const response: AxiosResponse = await this.api.get('/streams/health/streams');
    return response.data;
  }

  // Janus Health
  async getJanusHealth(): Promise<any> {
    const response: AxiosResponse = await this.api.get('/streams/janus/health');
    return response.data;
  }

  // Metrics
  async getMetrics(): Promise<any> {
    const response: AxiosResponse = await this.api.get('/metrics');
    return response.data;
  }

  // Snapshots
  async captureSnapshot(deviceId: string): Promise<Snapshot> {
    const response: AxiosResponse<Snapshot> = await this.api.post(`/snapshots/capture/${deviceId}`);
    return response.data;
  }

  async getSnapshots(deviceId?: string, page: number = 1, perPage: number = 10): Promise<SnapshotListResponse> {
    const params: any = { page, per_page: perPage };
    if (deviceId) {
      params.device_id = deviceId;
    }
    
    const response: AxiosResponse<SnapshotListResponse> = await this.api.get(`/snapshots`, {
      params
    });
    return response.data;
  }

  async getLatestSnapshot(deviceId: string): Promise<Snapshot> {
    const response: AxiosResponse<Snapshot> = await this.api.get(`/snapshots/device/${deviceId}/latest`);
    return response.data;
  }

  async deleteSnapshot(snapshotId: string): Promise<void> {
    await this.api.delete(`/snapshots/${snapshotId}`);
  }

  getSnapshotImageUrl(snapshotId: string): string {
    return `${this.baseURL}/snapshots/${snapshotId}/binary`;
  }

  async getSnapshotImageBinary(snapshotId: string): Promise<Blob> {
    const response: AxiosResponse<Blob> = await this.api.get(`/snapshots/${snapshotId}/binary`, {
      responseType: 'blob' // Important for binary data
    });
    return response.data;
  }

  // Recording API methods
  async getRecordingTimeline(deviceId: string, hours: number = 24): Promise<RecordingTimeline> {
    const response: AxiosResponse<RecordingTimeline> = await this.api.get(`/recordings/${deviceId}/timeline`, {
      params: { hours }
    });
    return response.data;
  }

  async getRecordingSegments(deviceId: string, startTime?: string, endTime?: string, limit: number = 100): Promise<RecordingSegment[]> {
    const response: AxiosResponse<{ segments: RecordingSegment[] }> = await this.api.get(`/recordings/${deviceId}/segments`, {
      params: { start_time: startTime, end_time: endTime, limit }
    });
    return response.data.segments;
  }

  async getRecordingStatus(deviceId: string): Promise<RecordingStatus> {
    const response: AxiosResponse<RecordingStatus> = await this.api.get(`/recordings/${deviceId}/status`);
    return response.data;
  }

  async startRecording(deviceId: string): Promise<void> {
    await this.api.post(`/recordings/${deviceId}/start`);
  }

  async stopRecording(deviceId: string): Promise<void> {
    await this.api.post(`/recordings/${deviceId}/stop`);
  }

  getRecordingSegmentUrl(deviceId: string, segmentId: string): string {
    return `${this.baseURL}/recordings/${deviceId}/segment/${segmentId}/play`;
  }
}

export const apiService = new ApiService();
export default apiService; 