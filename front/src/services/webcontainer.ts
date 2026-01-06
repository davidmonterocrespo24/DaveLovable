import { WebContainer, FileSystemTree } from '@webcontainer/api';

let webcontainerInstance: WebContainer | null = null;

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
 * Load project into WebContainer and start dev server
 */
export async function loadProject(
  projectId: number,
  onLog?: (message: string) => void,
  onError?: (message: string) => void
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
    log('[WebContainer] Getting instance...');
    const container = await getWebContainer();

    log('[WebContainer] Fetching project files...');
    const response = await fetch(`http://localhost:8000/api/v1/projects/${projectId}/bundle`);

    if (!response.ok) {
      throw new Error(`Failed to fetch project: ${response.status} ${response.statusText}`);
    }

    const { files } = await response.json();
    log(`[WebContainer] Received ${Object.keys(files).length} files`);

    // Inject Visual Editor Helper Script
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
          const innerText = selectedElement.innerText.substring(0, 100);
          
          // Get useful attributes
          const attributes = {};
          ['src', 'href', 'placeholder', 'type', 'name', 'value', 'alt'].forEach(attr => {
             if (selectedElement.hasAttribute(attr)) {
               attributes[attr] = selectedElement.getAttribute(attr);
             }
          });
          
          console.log('[VisualEditor] Selected:', tagName, elementId, selector);
          
          // Send selection to parent
          window.parent.postMessage({
            type: 'visual-editor:selected',
            elementId,
            tagName,
            className,
            selector,
            innerText,
            attributes
          }, '*');
        }, true);
      })();
    `;

    // Add helper script to files
    files['visual-editor-helper.js'] = VISUAL_EDITOR_SCRIPT;

    // Inject script into index.html if it exists
    if (files['index.html']) {
      const indexHtml = files['index.html'];
      if (!indexHtml.includes('visual-editor-helper.js')) {
        files['index.html'] = indexHtml.replace(
          '</body>',
          '<script src="./visual-editor-helper.js"></script></body>'
        );
      }
    }

    log('[WebContainer] Converting file structure...');
    const fileTree = convertToWebContainerFiles(files);

    log('[WebContainer] Mounting files...');
    await container.mount(fileTree);
    log('[WebContainer] Files mounted successfully');

    log('[WebContainer] Installing dependencies...');
    const installProcess = await container.spawn('npm', ['install']);

    let lastLogWasSpinner = false;

    // Stream install output
    installProcess.output.pipeTo(
      new WritableStream({
        write(data) {
          const cleaned = stripAnsi(data);
          if (cleaned) {
            // Only log meaningful messages, skip spinner lines
            if (cleaned.length > 1 || !/^[\\|/\-]$/.test(cleaned)) {
              log(`[npm] ${cleaned}`);
              lastLogWasSpinner = false;
            } else if (!lastLogWasSpinner) {
              // Show one spinner indicator
              log(`[npm] Installing packages...`);
              lastLogWasSpinner = true;
            }
          }
        },
      })
    );

    const installExitCode = await installProcess.exit;
    if (installExitCode !== 0) {
      throw new Error(`npm install failed with exit code ${installExitCode}`);
    }

    log('[WebContainer] Dependencies installed successfully');
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

    // Wait for server to be ready
    log('[WebContainer] Waiting for dev server...');

    return new Promise((resolve, reject) => {
      let serverUrl = '';

      // Listen for server ready event
      container.on('server-ready', (port, url) => {
        log(`[WebContainer] Server ready at ${url}`);
        serverUrl = url;
        resolve({ url, logs });
      });

      // Timeout after 30 seconds
      setTimeout(() => {
        if (!serverUrl) {
          const msg = 'Dev server startup timeout';
          error(msg);
          reject(new Error(msg));
        }
      }, 30000);
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
 */
export async function reloadProjectFiles(
  projectId: number,
  onLog?: (message: string) => void
): Promise<void> {
  const log = (msg: string) => {
    if (onLog) onLog(msg);
  };

  try {
    if (!webcontainerInstance) {
      throw new Error('WebContainer not initialized. Call loadProject first.');
    }

    log('[WebContainer] Fetching updated project files...');
    const response = await fetch(`http://localhost:8000/api/v1/projects/${projectId}/bundle`);

    if (!response.ok) {
      throw new Error(`Failed to fetch project: ${response.status} ${response.statusText}`);
    }

    const { files } = await response.json();
    log(`[WebContainer] Received ${Object.keys(files).length} files`);

    // Write each file directly to the existing container
    log('[WebContainer] Updating files...');
    for (const [filepath, content] of Object.entries(files)) {
      await webcontainerInstance.fs.writeFile(filepath, content as string);
    }

    log('[WebContainer] Files updated successfully (HMR will auto-reload)');
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    if (onLog) onLog(`ERROR: Failed to reload files: ${message}`);
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
  }
}
