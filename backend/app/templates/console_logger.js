/**
 * Browser Console Logger for WebContainer
 *
 * This script intercepts console methods and sends logs to the parent window
 * via postMessage for the AI agent to analyze.
 */
(function() {
  'use strict';

  // Store original console methods
  const originalConsole = {
    log: console.log,
    error: console.error,
    warn: console.warn,
    info: console.info
  };

  /**
   * Send log to parent window via postMessage
   */
  function sendLogToParent(type, args) {
    try {
      const message = args.map(arg => {
        if (arg instanceof Error) {
          return `${arg.message}\n${arg.stack}`;
        }
        if (typeof arg === 'object') {
          try {
            return JSON.stringify(arg, null, 2);
          } catch {
            return String(arg);
          }
        }
        return String(arg);
      }).join(' ');

      const stack = args[0] instanceof Error ? args[0].stack : undefined;

      window.parent.postMessage({
        type: 'console-log',
        logType: type,
        message: message,
        stack: stack,
        timestamp: new Date().toISOString()
      }, '*');
    } catch (error) {
      // Silently fail to avoid infinite loops
    }
  }

  // Intercept console.log
  console.log = function(...args) {
    sendLogToParent('log', args);
    originalConsole.log.apply(console, args);
  };

  // Intercept console.error
  console.error = function(...args) {
    sendLogToParent('error', args);
    originalConsole.error.apply(console, args);
  };

  // Intercept console.warn
  console.warn = function(...args) {
    sendLogToParent('warning', args);
    originalConsole.warn.apply(console, args);
  };

  // Intercept console.info
  console.info = function(...args) {
    sendLogToParent('info', args);
    originalConsole.info.apply(console, args);
  };

  // Capture unhandled errors
  window.addEventListener('error', function(event) {
    sendLogToParent('error', [event.error || event.message]);
  });

  // Capture unhandled promise rejections
  window.addEventListener('unhandledrejection', function(event) {
    sendLogToParent('error', [`Unhandled Promise Rejection: ${event.reason}`]);
  });

  console.log('[ConsoleLogger] Browser console logging initialized');
})();
