/**
 * Frontend configuration
 * Values can be overridden via environment variables (VITE_ prefix)
 */

// API URL - defaults to localhost for development, can be overridden for Docker
const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const wsProtocol = apiUrl.startsWith('https') ? 'wss' : 'ws';
const wsUrl = apiUrl.replace(/^https?/, wsProtocol);

export const config = {
  /**
   * Backend API URL
   * Default: http://localhost:8000 (development)
   * In Docker: Use VITE_API_URL to point to backend service
   */
  apiUrl,

  /**
   * WebSocket URL (derived from API URL)
   */
  wsUrl,

  /**
   * UI refresh interval in milliseconds
   * How often the dashboard updates when tasks are in progress
   * Default: 3000ms (3 seconds)
   */
  uiRefreshIntervalMs: Number(import.meta.env.VITE_UI_REFRESH_INTERVAL_MS) || 3000,
} as const;
