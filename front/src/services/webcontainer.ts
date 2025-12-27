import { WebContainer } from '@webcontainer/api';

let webcontainerInstance: WebContainer | null = null;

export interface WebContainerFiles {
  [path: string]: {
    file?: {
      contents: string;
    };
    directory?: {
      [path: string]: any;
    };
  };
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
function convertToWebContainerFiles(files: Record<string, string>): WebContainerFiles {
  const tree: WebContainerFiles = {};

  Object.entries(files).forEach(([path, content]) => {
    const parts = path.split('/');
    let current = tree;

    // Navigate/create directory structure
    for (let i = 0; i < parts.length - 1; i++) {
      const part = parts[i];
      if (!current[part]) {
        current[part] = { directory: {} };
      }
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

    log('[WebContainer] Converting file structure...');
    const fileTree = convertToWebContainerFiles(files);

    log('[WebContainer] Mounting files...');
    await container.mount(fileTree);
    log('[WebContainer] Files mounted successfully');

    log('[WebContainer] Installing dependencies...');
    const installProcess = await container.spawn('npm', ['install']);

    // Stream install output
    installProcess.output.pipeTo(
      new WritableStream({
        write(data) {
          log(`[npm] ${data}`);
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
          log(`[dev] ${data}`);
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
        console.log(`[dev] ${data}`);
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
 * Clean up WebContainer instance
 */
export async function teardown(): Promise<void> {
  if (webcontainerInstance) {
    await webcontainerInstance.teardown();
    webcontainerInstance = null;
  }
}
