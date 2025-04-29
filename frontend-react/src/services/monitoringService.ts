import { apiClient } from '../utils/apiClient';

export interface SystemHealth {
  process: {
    memory_usage_mb: number;
    memory_percent: number;
    cpu_percent: number;
    threads: number;
    open_files: number;
    connections: number;
    uptime_seconds: number;
  };
  system: {
    cpu_count: number;
    memory_total_mb: number;
    memory_available_mb: number;
    memory_percent: number;
    disk_total_gb: number;
    disk_used_gb: number;
    disk_percent: number;
    load_1m: number | null;
    load_5m: number | null;
    load_15m: number | null;
  };
}

export interface EndpointMetric {
  count: number;
  errors: number;
  avg_time: number;
  median_time: number | null;
  p95_time: number | null;
  p99_time: number | null;
  min_time: number;
  max_time: number;
  error_rate: number;
}

export interface GlobalMetrics {
  uptime_seconds: number;
  total_requests: number;
  total_errors: number;
  error_rate: number;
  requests_per_minute: number;
  slow_requests_count: number;
}

export interface SystemMetrics {
  [endpoint: string]: EndpointMetric | GlobalMetrics;
  _global: GlobalMetrics;
}

export interface SlowRequest {
  endpoint: string;
  method: string;
  status_code: number;
  duration: number;
  timestamp: string;
}

// Obtener métricas detalladas del sistema
export const getSystemMetrics = async (): Promise<SystemMetrics> => {
  try {
    const response = await apiClient.get<SystemMetrics>('/monitoring/metrics');
    return response.data;
  } catch (error) {
    console.error('Error al obtener métricas del sistema:', error);
    throw error;
  }
};

// Obtener información de salud del sistema
export const getSystemHealth = async (): Promise<SystemHealth> => {
  try {
    const response = await apiClient.get<SystemHealth>('/monitoring/system-health');
    return response.data;
  } catch (error) {
    console.error('Error al obtener estado de salud del sistema:', error);
    throw error;
  }
};

// Obtener solicitudes lentas recientes
export const getSlowRequests = async (limit: number = 10): Promise<SlowRequest[]> => {
  try {
    const response = await apiClient.get<SlowRequest[]>(`/monitoring/metrics/slow?limit=${limit}`);
    return response.data;
  } catch (error) {
    console.error('Error al obtener solicitudes lentas:', error);
    return [];
  }
}; 