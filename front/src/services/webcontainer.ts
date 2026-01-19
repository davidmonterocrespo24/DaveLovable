import { WebContainer, FileSystemTree } from '@webcontainer/api';
import { API_URL } from './api';

let webcontainerInstance: WebContainer | null = null;
let templateInstalled = false; // Track if template dependencies are installed
let cachedNodeModules: FileSystemTree | null = null; // Cache of installed node_modules
let fileContentCache = new Map<string, string>(); // Cache of current files in WebContainer

/**
 * Strip ANSI escape codes from terminal output
 */
function stripAnsi(str: string): string {
  // eslint-disable-next-line no-control-regex
  return str.replace(/\u001b\[[0-9;]*[a-zA-Z]/g, '').replace(/\[[\d]+[GK]/g, '').trim();
}

/**
 * Get or create WebContainer instance (singleton)
 */
export async function getWebContainer(): Promise<WebContainer> {
  if (!webcontainerInstance) {
    console.log('[WebContainer] Booting...');
    webcontainerInstance = await WebContainer.boot();
    console.log('[WebContainer] Ready');
  }
  return webcontainerInstance;
}

/**
 * Convert flat files object to WebContainer tree structure
 */
function convertToWebContainerFiles(files: Record<string, string>): FileSystemTree {
  const tree: FileSystemTree = {};

  Object.entries(files).forEach(([path, content]) => {
    const parts = path.split('/');
    let current = tree;

    // Navigate/create directory structure
    for (let i = 0; i < parts.length - 1; i++) {
      const part = parts[i];
      if (!current[part]) {
        current[part] = { directory: {} };
      }
      // @ts-ignore
      current = current[part].directory!;
    }

    // Add file
    const fileName = parts[parts.length - 1];
    current[fileName] = {
      file: {
        contents: content,
      },
    };
  });

  return tree;
}

export interface LoadProjectResult {
  url: string;
  logs: string[];
}

/**
 * Screenshot Capture Helper Script
 * Injects html2canvas into the WebContainer to capture its own DOM
 */
const SCREENSHOT_HELPER_SCRIPT = `
(function() {
  // Silent logging - don't pollute user's console
  const DEBUG = false; // Set to true only for debugging
  const log = DEBUG ? console.log.bind(console) : () => {};

  log('[Screenshot Helper] Initializing...');

  // Wait for app to be fully rendered before allowing screenshots
  let isAppReady = false;

  // Check if app is ready (React root has content)
  const checkAppReady = () => {
    const root = document.querySelector('#root');
    if (root && root.children.length > 0) {
      // Check if there's actual content (not just loading spinner)
      const hasContent = root.textContent && root.textContent.trim().length > 100;
      if (hasContent) {
        isAppReady = true;
        log('[Screenshot Helper] App is ready for capture');
        return true;
      }
    }
    return false;
  };

  // Monitor for app ready state
  const observer = new MutationObserver(() => {
    if (!isAppReady) {
      checkAppReady();
    }
  });

  // Observe the root element for changes
  const root = document.querySelector('#root');
  if (root) {
    observer.observe(root, { childList: true, subtree: true });
  }

  // Check immediately
  setTimeout(() => checkAppReady(), 1000);

  // Listen for screenshot requests from parent
  window.addEventListener('message', async (event) => {
    if (event.data.type === 'capture-screenshot') {
      log('[Screenshot Helper] Received capture request');

      try {
        // Wait for app to be ready
        if (!isAppReady) {
          log('[Screenshot Helper] Waiting for app to be ready...');
          let attempts = 0;
          while (!isAppReady && attempts < 20) {
            await new Promise(resolve => setTimeout(resolve, 500));
            checkAppReady();
            attempts++;
          }
          if (!isAppReady) {
            throw new Error('App did not become ready in time');
          }
        }

        // Dynamically import html2canvas
        if (!window.html2canvas) {
          log('[Screenshot Helper] Loading html2canvas...');
          const script = document.createElement('script');
          script.src = 'https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js';
          document.head.appendChild(script);

          // Wait for script to load
          await new Promise((resolve, reject) => {
            script.onload = resolve;
            script.onerror = reject;
            setTimeout(reject, 5000); // 5s timeout
          });
        }

        log('[Screenshot Helper] Capturing DOM with html2canvas...');

        // Wait a bit more for any animations/renders to complete
        await new Promise(resolve => setTimeout(resolve, 1000));

        // Pre-process images: convert external images to data URLs to avoid CORS issues
        log('[Screenshot Helper] Pre-processing external images...');
        const externalImages = Array.from(document.querySelectorAll('img')).filter(img => {
          const src = img.getAttribute('src') || '';
          return src.startsWith('http') && !src.includes(window.location.hostname);
        });

        // Store original sources and convert to data URLs
        const imageCache = new Map();
        for (const img of externalImages) {
          const src = img.src;
          if (imageCache.has(src)) continue;

          try {
            // Try to load image through a canvas to convert to data URL
            const response = await fetch(src, { mode: 'cors' });
            const blob = await response.blob();
            const dataUrl = await new Promise((resolve) => {
              const reader = new FileReader();
              reader.onloadend = () => resolve(reader.result);
              reader.readAsDataURL(blob);
            });
            imageCache.set(src, dataUrl);
            log('[Screenshot Helper] Converted external image to data URL:', src);
          } catch (err) {
            log('[Screenshot Helper] Failed to convert image, will use placeholder:', src);
            imageCache.set(src, null); // Mark as failed
          }
        }

        // Capture the #root element (where React app lives)
        const targetElement = document.querySelector('#root') || document.body;

        const canvas = await window.html2canvas(targetElement, {
          allowTaint: false,  // CRITICAL: Must be false to export canvas
          useCORS: false,     // Don't rely on CORS, we've pre-processed images
          logging: false,     // Reduce console noise
          scale: 1,
          backgroundColor: '#ffffff',
          width: Math.max(window.innerWidth, 1280),
          height: Math.max(window.innerHeight, 720),
          windowWidth: 1280,
          windowHeight: 720,
          onclone: (clonedDoc) => {
            log('[Screenshot Helper] Document cloned, replacing external images...');

            // Replace external images with data URLs or placeholders
            const images = clonedDoc.querySelectorAll('img');
            let replacedCount = 0;
            let placeholderCount = 0;

            images.forEach(img => {
              const src = img.getAttribute('src') || '';
              if (src.startsWith('http') && !src.includes(window.location.hostname)) {
                const dataUrl = imageCache.get(src);
                if (dataUrl) {
                  // Replace with data URL
                  img.src = dataUrl;
                  replacedCount++;
                } else {
                  // Create a nice placeholder with the image dimensions
                  const width = img.width || 200;
                  const height = img.height || 150;
                  img.style.width = width + 'px';
                  img.style.height = height + 'px';
                  img.style.backgroundColor = '#f3f4f6';
                  img.style.border = '2px dashed #d1d5db';
                  img.style.display = 'flex';
                  img.style.alignItems = 'center';
                  img.style.justifyContent = 'center';
                  img.removeAttribute('src');
                  img.alt = '🖼️';
                  placeholderCount++;
                }
              }
            });

            log('[Screenshot Helper] Images replaced:', replacedCount, 'Placeholders:', placeholderCount);
          }
        });

        const dataUrl = canvas.toDataURL('image/png');

        // Validate canvas has content (not blank)
        if (canvas.width === 0 || canvas.height === 0) {
          throw new Error('Canvas has no dimensions');
        }

        log('[Screenshot Helper] Capture successful:', {
          width: canvas.width,
          height: canvas.height,
          dataLength: dataUrl.length
        });

        // Send screenshot back to parent
        window.parent.postMessage({
          type: 'screenshot-captured',
          data: dataUrl
        }, '*');
      } catch (error) {
        // Only log errors - these are important
        if (DEBUG) {
          console.error('[Screenshot Helper] Capture failed:', error);
        }
        window.parent.postMessage({
          type: 'screenshot-error',
          error: error instanceof Error ? error.message : String(error)
        }, '*');
      }
    }
  });

  log('[Screenshot Helper] Ready');
})();
`;

/**
 * Visual Editor Script - Injects into WebContainer for element selection
 */
const VISUAL_EDITOR_SCRIPT = `
(function() {
  console.log('[VisualEditor] Helper script initialized');
  let isVisualMode = false;
  let selectedElement = null;
  let hoveredElement = null;

  // Add styles for visual editor
  const style = document.createElement('style');
  style.textContent = \`
    .visual-editor-mode { cursor: crosshair !important; }
    .visual-editor-hover { outline: 2px dashed #3b82f6 !important; z-index: 9999 !important; }
    .visual-editor-selected { outline: 2px solid #3b82f6 !important; z-index: 9999 !important; }
  \`;
  document.head.appendChild(style);

  // Handle messages from parent
  window.addEventListener('message', (event) => {
    const { type, enabled, property, value } = event.data;

    if (type === 'visual-editor:toggle-mode') {
      isVisualMode = enabled;
      console.log('[VisualEditor] Mode toggled:', isVisualMode);
      if (isVisualMode) {
        document.body.classList.add('visual-editor-mode');
      } else {
        document.body.classList.remove('visual-editor-mode');
        clearSelection();
      }
    } else if (type === 'visual-editor:update-style') {
      if (selectedElement) {
        console.log('[VisualEditor] Updating style:', property, value);
        selectedElement.style[property] = value;
      }
    }
  });

  function clearSelection() {
    if (selectedElement) {
      selectedElement.classList.remove('visual-editor-selected');
      selectedElement = null;
    }
    if (hoveredElement) {
      hoveredElement.classList.remove('visual-editor-hover');
      hoveredElement = null;
    }
  }

  // Mouse interaction
  document.addEventListener('mouseover', (e) => {
    if (!isVisualMode) return;
    e.stopPropagation();

    if (hoveredElement && hoveredElement !== selectedElement) {
      hoveredElement.classList.remove('visual-editor-hover');
    }

    hoveredElement = e.target;
    if (hoveredElement !== selectedElement) {
      hoveredElement.classList.add('visual-editor-hover');
    }
  }, true);

  document.addEventListener('mouseout', (e) => {
    if (!isVisualMode) return;
    if (e.target.classList.contains('visual-editor-hover')) {
      e.target.classList.remove('visual-editor-hover');
    }
  }, true);

  document.addEventListener('click', (e) => {
    if (!isVisualMode) return;
    e.preventDefault();
    e.stopPropagation();

    if (selectedElement) {
      selectedElement.classList.remove('visual-editor-selected');
    }

    selectedElement = e.target;
    selectedElement.classList.add('visual-editor-selected');
    selectedElement.classList.remove('visual-editor-hover');

    // Generate a unique selector
    const getSelector = (el) => {
      if (el.id) return '#' + el.id;

      let path = [];
      let current = el;

      while (current && current !== document.body) {
        let selector = current.tagName.toLowerCase();

        if (current.id) {
          selector += '#' + current.id;
          path.unshift(selector);
          break;
        } else {
          let nth = 1;
          let sibling = current;
          while (sibling = sibling.previousElementSibling) {
            if (sibling.tagName.toLowerCase() === selector) nth++;
          }
          if (nth !== 1) selector += ':nth-of-type(' + nth + ')';
        }

        path.unshift(selector);
        current = current.parentElement;
      }

      return path.join(' > ');
    };

    const elementId = selectedElement.id || '';
    const tagName = selectedElement.tagName.toLowerCase();
    const className = selectedElement.className;
    const selector = getSelector(selectedElement);
    const innerText = selectedElement.innerText ? selectedElement.innerText.substring(0, 100) : '';

    // Get useful attributes
    const attributes = {};
    ['src', 'href', 'placeholder', 'type', 'name', 'value', 'alt'].forEach(attr => {
      if (selectedElement.hasAttribute(attr)) {
        attributes[attr] = selectedElement.getAttribute(attr);
      }
    });

    console.log('[VisualEditor] Selected:', tagName, elementId, selector);

    // Helper to find React Fiber
    const getReactFiber = (el) => {
      for (const key in el) {
        if (key.startsWith('__reactFiber$')) {
          return el[key];
        }
      }
      return null;
    };

    // Helper to get source from fiber
    const getSource = (el) => {
      let fiber = getReactFiber(el);
      while (fiber) {
        if (fiber._debugSource) {
          return fiber._debugSource;
        }
        fiber = fiber.return;
      }
      return null;
    };

    const source = getSource(selectedElement);
    console.log('[VisualEditor] Source:', source);

    // Send selection to parent
    window.parent.postMessage({
      type: 'visual-editor:selected',
      elementId,
      tagName,
      className,
      selector,
      innerText,
      attributes,
      source
    }, '*');
  }, true);
})();
`;


/**
 * Load project into WebContainer and start dev server
 * OPTIMIZED: Skip npm install if already done, faster mounting
 */
export async function loadProject(
  projectId: number,
  onLog?: (message: string) => void,
  onError?: (message: string) => void,
  forceReinstall = false
): Promise<LoadProjectResult> {
  const logs: string[] = [];

  const log = (msg: string) => {
    logs.push(msg);
    if (onLog) onLog(msg);
  };

  const error = (msg: string) => {
    logs.push(`ERROR: ${msg}`);
    if (onError) onError(msg);
  };

  try {
    // OPTIMIZATION 1: Parallel container boot + file fetch
    log('[WebContainer] Initializing...');
    const [container, response] = await Promise.all([
      getWebContainer(),
      fetch(`${API_URL}/projects/${projectId}/bundle?t=${Date.now()}`)
    ]);

    if (!response.ok) {
      throw new Error(`Failed to fetch project: ${response.status} ${response.statusText}`);
    }

    const { files } = await response.json();
    log(`[WebContainer] Received ${Object.keys(files).length} files`);

    // INJECT SCREENSHOT HELPER: Always inject to enable screenshot capture
    files['screenshot-helper.js'] = SCREENSHOT_HELPER_SCRIPT;

    // INJECT VISUAL EDITOR HELPER: Always inject to enable visual editing mode
    files['visual-editor-helper.js'] = VISUAL_EDITOR_SCRIPT;

    if (files['index.html']) {
      let htmlContent = files['index.html'];

      // Inject screenshot helper if not already present
      if (!htmlContent.includes('screenshot-helper.js')) {
        htmlContent = htmlContent.replace(
          '</body>',
          '<script src="./screenshot-helper.js"></script></body>'
        );
      }

      // Inject visual editor helper if not already present
      if (!htmlContent.includes('visual-editor-helper.js')) {
        htmlContent = htmlContent.replace(
          '</body>',
          '<script src="./visual-editor-helper.js"></script></body>'
        );
      }

      files['index.html'] = htmlContent;
      log('[WebContainer] Screenshot helper and Visual Editor injected');
    }

    // OPTIMIZATION 4: Fast file tree conversion (already optimized)
    log('[WebContainer] Preparing files...');
    const fileTree = convertToWebContainerFiles(files);

    // Initialize cache
    fileContentCache.clear();
    Object.entries(files).forEach(([path, content]) => {
      fileContentCache.set(path, content as string);
    });

    log('[WebContainer] Mounting files...');
    await container.mount(fileTree);
    log('[WebContainer] Mounted ⚡');

    // OPTIMIZATION 5: Use template cache if available
    if (!templateInstalled || forceReinstall) {
      log('[WebContainer] Installing dependencies...');
      // OPTIMIZATION 6: More aggressive npm flags
      const installProcess = await container.spawn('npm', [
        'install',
        '--prefer-offline',      // Use offline cache first
        '--no-audit',            // Skip security audit
        '--no-fund',             // Skip funding messages
        '--progress=false',      // Disable progress bar
        '--loglevel=error',      // Only show errors
        '--ignore-scripts'       // Skip postinstall scripts for speed
      ]);

      // Simplified output streaming
      installProcess.output.pipeTo(
        new WritableStream({
          write(data) {
            const cleaned = stripAnsi(data);
            if (cleaned && cleaned.length > 2) {
              log(`[npm] ${cleaned}`);
            }
          },
        })
      );

      const installExitCode = await installProcess.exit;
      if (installExitCode !== 0) {
        throw new Error(`npm install failed with exit code ${installExitCode}`);
      }

      templateInstalled = true;
      log('[WebContainer] Dependencies installed');
    } else {
      log('[WebContainer] Using cached dependencies (skip install)');
    }

    log('[WebContainer] Starting dev server...');

    const devProcess = await container.spawn('npm', ['run', 'dev']);

    // Stream dev server output
    devProcess.output.pipeTo(
      new WritableStream({
        write(data) {
          const cleaned = stripAnsi(data);
          if (cleaned) {
            log(`[dev] ${cleaned}`);
          }
        },
      })
    );

    // Wait for server to be ready with optimized timeout
    log('[WebContainer] Waiting for dev server...');

    return new Promise((resolve, reject) => {
      let serverUrl = '';
      let resolved = false;

      // Listen for server ready event
      container.on('server-ready', (port, url) => {
        if (!resolved) {
          resolved = true;
          log(`[WebContainer] Server ready at ${url}`);
          serverUrl = url;
          resolve({ url, logs });
        }
      });

      // Reduced timeout to 15 seconds (was 30)
      setTimeout(() => {
        if (!serverUrl && !resolved) {
          resolved = true;
          const msg = 'Dev server startup timeout (15s)';
          error(msg);
          reject(new Error(msg));
        }
      }, 15000);
    });

  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    error(`Failed to load project: ${message}`);
    throw err;
  }
}

/**
 * Update a file in the WebContainer
 */
export async function updateFile(filepath: string, content: string): Promise<void> {
  if (!webcontainerInstance) {
    throw new Error('WebContainer not initialized');
  }

  await webcontainerInstance.fs.writeFile(filepath, content);
}

/**
 * Restart the dev server
 */
export async function restartDevServer(): Promise<void> {
  if (!webcontainerInstance) {
    throw new Error('WebContainer not initialized');
  }

  // Kill existing dev server process
  // Note: This is a simplified version - you might want to track the process
  const devProcess = await webcontainerInstance.spawn('npm', ['run', 'dev']);

  devProcess.output.pipeTo(
    new WritableStream({
      write(data) {
        const cleaned = stripAnsi(data);
        if (cleaned) {
          console.log(`[dev] ${cleaned}`);
        }
      },
    })
  );
}

/**
 * Get file content from WebContainer
 */
export async function readFile(filepath: string): Promise<string> {
  if (!webcontainerInstance) {
    throw new Error('WebContainer not initialized');
  }

  const content = await webcontainerInstance.fs.readFile(filepath, 'utf-8');
  return content;
}

/**
 * Reload project files WITHOUT reinstalling dependencies or restarting server
 * This is much lighter than loadProject() - use this for incremental updates
 * OPTIMIZED: Batch file writes for better performance
 */
export async function reloadProjectFiles(
  projectId: number,
  onLog?: (message: string) => void
): Promise<void> {
  const log = (msg: string) => {
    console.log(msg); // Force log to console for debugging!
    if (onLog) onLog(msg);
  };

  try {
    if (!webcontainerInstance) {
      throw new Error('WebContainer not initialized. Call loadProject first.');
    }

    log('[WebContainer] Fetching updated files...');
    log('[WebContainer] Fetching updated files...');
    const response = await fetch(`${API_URL}/projects/${projectId}/bundle?t=${Date.now()}`);

    if (!response.ok) {
      throw new Error(`Failed to fetch project: ${response.status} ${response.statusText}`);
    }

    const { files } = await response.json();
    log(`[WebContainer] Syncing ${Object.keys(files).length} files...`);

    // Calculate Diff
    const toUpdate: Record<string, string> = {};
    const toDelete: string[] = [];
    const incomingPaths = new Set(Object.keys(files));

    // 1. Find updates/adds
    Object.entries(files).forEach(([filepath, content]) => {
      const currentContent = fileContentCache.get(filepath);
      if (currentContent !== content) {
        toUpdate[filepath] = content as string;
      }
    });

    // 2. Find deletions (in cache but not in new files)
    for (const cachedPath of fileContentCache.keys()) {
      if (!incomingPaths.has(cachedPath)) {
        toDelete.push(cachedPath);
      }
    }

    const updatesCount = Object.keys(toUpdate).length;
    const deletesCount = toDelete.length;

    if (updatesCount === 0 && deletesCount === 0) {
      log('[WebContainer] No changes detected, skipping writes.');
      return;
    }

    log(`[WebContainer] Applying changes: ${updatesCount} updates, ${deletesCount} deletions...`);

    // Apply Deletions
    if (toDelete.length > 0) {
      await Promise.all(
        toDelete.map(async (filepath) => {
          try {
            await webcontainerInstance!.fs.rm(filepath, { force: true });
            fileContentCache.delete(filepath);
          } catch (e) {
            console.warn(`[WebContainer] Failed to delete ${filepath}:`, e);
          }
        })
      );
    }

    // Apply Updates
    if (updatesCount > 0) {
      const writePromises = Object.entries(toUpdate).map(async ([filepath, content]) => {
        await webcontainerInstance!.fs.writeFile(filepath, content);
        fileContentCache.set(filepath, content);
      });
      await Promise.all(writePromises);
    }

    log('[WebContainer] Files synced ⚡');
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    if (onLog) onLog(`ERROR: Failed to reload files: ${message}`);
    throw err;
  }
}

/**
 * Update project files directly (Push model)
 */
export async function updateProjectFiles(
  files: Array<{ path: string, content: string }>,
  onLog?: (message: string) => void
): Promise<void> {
  if (!webcontainerInstance) {
    if (onLog) onLog('⚠️ WebContainer not initialized, skipping update');
    return;
  }

  const log = (msg: string) => {
    console.log(msg);
    if (onLog) onLog(msg);
  };

  try {
    // Execute writes sequentially to minimize HMR race conditions
    for (const file of files) {
      await webcontainerInstance!.fs.writeFile(file.path, file.content);
      fileContentCache.set(file.path, file.content);
    }

    log(`[WebContainer] Pushed ${files.length} file updates ⚡`);
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    if (onLog) onLog(`ERROR: Failed to push updates: ${message}`);
    throw err;
  }
}

/**
 * Clean up WebContainer instance
 */
export async function teardown(): Promise<void> {
  if (webcontainerInstance) {
    await webcontainerInstance.teardown();
    webcontainerInstance = null;
    templateInstalled = false;
    cachedNodeModules = null;
    fileContentCache.clear();
  }
}

/**
 * Force reinstall dependencies on next load
 */
export function clearTemplateCache(): void {
  templateInstalled = false;
  cachedNodeModules = null;
  fileContentCache.clear();
}

/**
 * Enable Visual Editor by injecting helper script
 * Call this only when visual editor mode is activated
 */
export async function enableVisualEditor(): Promise<void> {
  if (!webcontainerInstance) {
    throw new Error('WebContainer not initialized');
  }

  // Write visual editor helper script
  await webcontainerInstance.fs.writeFile('visual-editor-helper.js', VISUAL_EDITOR_SCRIPT);

  // Read and update index.html
  const indexHtml = await webcontainerInstance.fs.readFile('index.html', 'utf-8');

  if (!indexHtml.includes('visual-editor-helper.js')) {
    const updatedHtml = indexHtml.replace(
      '</body>',
      '<script src="./visual-editor-helper.js"></script></body>'
    );
    await webcontainerInstance.fs.writeFile('index.html', updatedHtml);
    console.log('[WebContainer] Visual Editor enabled');
  }
}
