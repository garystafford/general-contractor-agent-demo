/**
 * Frontend configuration
 * Values can be overridden via environment variables (VITE_ prefix)
 */

export const config = {
  /**
   * UI refresh interval in milliseconds
   * How often the dashboard updates when tasks are in progress
   * Default: 3000ms (3 seconds)
   */
  uiRefreshIntervalMs: Number(import.meta.env.VITE_UI_REFRESH_INTERVAL_MS) || 3000,
} as const;
