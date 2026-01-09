/**
 * Service to capture browser console logs from the WebContainer preview iframe
 * and send them to the backend for the AI agent to analyze.
 *
 * Uses postMessage to communicate with the iframe due to cross-origin restrictions.
 */

import { API_URL } from './api';

export interface BrowserLog {
  type: 'log' | 'error' | 'warning' | 'info';
  message: string;
  timestamp: string;
  stack?: string;
}

const MAX_LOGS = 100; // Keep last 100 logs
const logs: BrowserLog[] = [];

/**
 * Initialize console log capture by listening to postMessage from iframe
 */
export function initializeLogCapture() {
  // Listen for log messages from the iframe via postMessage
  window.addEventListener('message', (event) => {
    // Security: verify the message is from our WebContainer
    if (event.data?.type === 'console-log') {
      const { logType, message, stack, timestamp } = event.data;
      captureLog(logType, message, stack, timestamp);
    }
  });

  console.log('[BrowserLogs] Log capture initialized (using postMessage)');
}

/**
 * Capture a log entry
 */
function captureLog(type: BrowserLog['type'], message: string, stack?: string, timestamp?: string) {
  const log: BrowserLog = {
    type,
    message,
    timestamp: timestamp || new Date().toISOString(),
    stack,
  };

  logs.push(log);

  // Keep only last MAX_LOGS
  if (logs.length > MAX_LOGS) {
    logs.shift();
  }

  console.log(`[BrowserLogs] Captured ${type}:`, message);
}

/**
 * Get all captured logs
 */
export function getAllLogs(): BrowserLog[] {
  return [...logs];
}

/**
 * Get logs of a specific type
 */
export function getLogsByType(type: BrowserLog['type']): BrowserLog[] {
  return logs.filter((log) => log.type === type);
}

/**
 * Clear all logs
 */
export function clearLogs() {
  logs.length = 0;
}

/**
 * Send logs to backend for the AI agent to analyze
 */
export async function sendLogsToBackend(projectId: number): Promise<void> {
  if (logs.length === 0) {
    console.log('[BrowserLogs] No logs to send');
    return;
  }

  try {
    const response = await fetch(`${API_URL}/projects/${projectId}/browser-logs`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ logs }),
    });

    if (!response.ok) {
      throw new Error(`Failed to send logs: ${response.status} ${response.statusText}`);
    }

    console.log(`[BrowserLogs] Sent ${logs.length} logs to backend`);
  } catch (error) {
    console.error('[BrowserLogs] Failed to send logs to backend:', error);
  }
}

/**
 * Auto-send logs every 10 seconds
 */
export function startAutoSync(projectId: number, intervalMs: number = 10000) {
  return setInterval(() => {
    sendLogsToBackend(projectId);
  }, intervalMs);
}
