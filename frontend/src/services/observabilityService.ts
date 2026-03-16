/**
 * 可观测性 API 服务
 */

import axios from 'axios';

const API_BASE = '/api/v1';

/**
 * 获取系统健康状态
 */
export const fetchHealthStatus = async () => {
  const response = await axios.get(`${API_BASE}/observability/health`);
  return response.data;
};

/**
 * 获取系统指标
 */
export const fetchObservabilityMetrics = async (windowSeconds = 300) => {
  const response = await axios.get(`${API_BASE}/observability/metrics`, {
    params: { window_seconds: windowSeconds },
  });
  return response.data;
};

/**
 * 获取延迟指标
 */
export const fetchLatencyMetrics = async (windowSeconds = 300) => {
  const response = await axios.get(`${API_BASE}/observability/metrics/latency`, {
    params: { window_seconds: windowSeconds },
  });
  return response.data;
};

/**
 * 获取业务指标
 */
export const fetchBusinessMetrics = async () => {
  const response = await axios.get(`${API_BASE}/observability/metrics/business`);
  return response.data;
};
