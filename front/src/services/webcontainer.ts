import { WebContainer, FileSystemTree } from '@webcontainer/api';
import { API_URL } from './api';

let webcontainerInstance: WebContainer | null = null;
let templateInstalled = false; // Track if template dependencies are installed
let cachedNodeModules: FileSystemTree | null = null; // Cache of installed node_modules

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
  console.log('[Screenshot Helper] Initializing...');

  // Listen for screenshot requests from parent
  window.addEventListener('message', async (event) => {
    if (event.data.type === 'capture-screenshot') {
      console.log('[Screenshot Helper] Received capture request');

      try {
        // Dynamically import html2canvas
        if (!window.html2canvas) {
          console.log('[Screenshot Helper] Loading html2canvas...');
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

        console.log('[Screenshot Helper] Capturing DOM with html2canvas...');
        const canvas = await window.html2canvas(document.body, {
          allowTaint: true,
          useCORS: true,
          logging: false,
          width: window.innerWidth,
          height: window.innerHeight,
          windowWidth: 1280,
          windowHeight: 720,
        });

        const dataUrl = canvas.toDataURL('image/png');
        console.log('[Screenshot Helper] Capture successful, sending to parent');

        // Send screenshot back to parent
        window.parent.postMessage({
          type: 'screenshot-captured',
          data: dataUrl
        }, '*');
      } catch (error) {
        console.error('[Screenshot Helper] Capture failed:', error);
        window.parent.postMessage({
          type: 'screenshot-error',
          error: error.message
        }, '*');
      }
    }
  });

  console.log('[Screenshot Helper] Ready');
})();
`;

/**
 * Lightweight Visual Editor script (minimal version)
 */
const VISUAL_EDITOR_SCRIPT = `
(function(){console.log('[VisualEditor] Init');let m=false,s=null,h=null;const style=document.createElement('style');style.textContent='.visual-editor-mode{cursor:crosshair!important}.visual-editor-hover{outline:2px dashed #3b82f6!important;z-index:9999!important}.visual-editor-selected{outline:2px solid #3b82f6!important;z-index:9999!important}';document.head.appendChild(style);window.addEventListener('message',e=>{const{type,enabled,property,value}=e.data;if(type==='visual-editor:toggle-mode'){m=enabled;m?document.body.classList.add('visual-editor-mode'):(document.body.classList.remove('visual-editor-mode'),s&&s.classList.remove('visual-editor-selected'),h&&h.classList.remove('visual-editor-hover'),s=h=null)}else if(type==='visual-editor:update-style'&&s)s.style[property]=value});document.addEventListener('mouseover',e=>{if(!m)return;h&&h!==s&&h.classList.remove('visual-editor-hover');h=e.target;h!==s&&h.classList.add('visual-editor-hover')},true);document.addEventListener('mouseout',e=>{m&&e.target.classList.remove('visual-editor-hover')},true);document.addEventListener('click',e=>{if(!m)return;e.preventDefault();e.stopPropagation();s&&s.classList.remove('visual-editor-selected');s=e.target;s.classList.add('visual-editor-selected');s.classList.remove('visual-editor-hover');const getSelector=el=>{if(el.id)return'#'+el.id;let path=[],cur=el;while(cur&&cur!==document.body){let sel=cur.tagName.toLowerCase();if(cur.id){sel+='#'+cur.id;path.unshift(sel);break}else{let nth=1,sib=cur;while(sib=sib.previousElementSibling)sib.tagName.toLowerCase()===sel&&nth++;nth!==1&&(sel+=':nth-of-type('+nth+')')}path.unshift(sel);cur=cur.parentElement}return path.join(' > ')};window.parent.postMessage({type:'visual-editor:selected',elementId:s.id||'',tagName:s.tagName.toLowerCase(),className:s.className,selector:getSelector(s),innerText:s.innerText.substring(0,100)},'*')},true)})();
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
      fetch(`${API_URL}/projects/${projectId}/bundle`)
    ]);

    if (!response.ok) {
      throw new Error(`Failed to fetch project: ${response.status} ${response.statusText}`);
    }

    const { files } = await response.json();
    log(`[WebContainer] Received ${Object.keys(files).length} files`);

    // INJECT SCREENSHOT HELPER: Always inject to enable screenshot capture
    files['screenshot-helper.js'] = SCREENSHOT_HELPER_SCRIPT;
    if (files['index.html'] && !files['index.html'].includes('screenshot-helper.js')) {
      files['index.html'] = files['index.html'].replace(
        '</body>',
        '<script src="./screenshot-helper.js"></script></body>'
      );
      log('[WebContainer] Screenshot helper injected');
    }

    // OPTIMIZATION 2: Lazy load visual editor (only add if needed, skip for now)
    // files['visual-editor-helper.js'] = VISUAL_EDITOR_SCRIPT;

    // OPTIMIZATION 4: Fast file tree conversion (already optimized)
    log('[WebContainer] Preparing files...');
    const fileTree = convertToWebContainerFiles(files);

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
    if (onLog) onLog(msg);
  };

  try {
    if (!webcontainerInstance) {
      throw new Error('WebContainer not initialized. Call loadProject first.');
    }

    log('[WebContainer] Fetching updated files...');
    const response = await fetch(`${API_URL}/projects/${projectId}/bundle`);

    if (!response.ok) {
      throw new Error(`Failed to fetch project: ${response.status} ${response.statusText}`);
    }

    const { files } = await response.json();
    log(`[WebContainer] Updating ${Object.keys(files).length} files...`);

    // Batch file writes for better performance
    const writePromises = Object.entries(files).map(([filepath, content]) =>
      webcontainerInstance!.fs.writeFile(filepath, content as string)
    );

    await Promise.all(writePromises);

    log('[WebContainer] Files updated (HMR active)');
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
    templateInstalled = false;
    cachedNodeModules = null;
  }
}

/**
 * Force reinstall dependencies on next load
 */
export function clearTemplateCache(): void {
  templateInstalled = false;
  cachedNodeModules = null;
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
