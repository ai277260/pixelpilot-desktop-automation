import { app, BrowserWindow, ipcMain, dialog } from 'electron';
import { spawn, ChildProcessWithoutNullStreams } from 'node:child_process';
import path from 'node:path';
import readline from 'node:readline';
import fs from 'node:fs/promises';

let windowRef: BrowserWindow | null = null;
let backend: ChildProcessWithoutNullStreams | null = null;
const send = (message: unknown) => windowRef?.webContents.send('backend:event', message);

function startBackend() {
  if (backend && !backend.killed) return;
  const script = path.join(app.getAppPath(), 'python', 'backend.py');
  backend = spawn(process.env.PYTHON ?? 'python', [script], { cwd: app.getAppPath(), stdio: ['pipe', 'pipe', 'pipe'], windowsHide: true });
  const lines = readline.createInterface({ input: backend.stdout });
  lines.on('line', (line) => { try { send(JSON.parse(line)); } catch { send({ type: 'log', message: line }); } });
  backend.stderr.on('data', (chunk: Buffer) => send({ type: 'log', message: chunk.toString().trim() }));
  backend.on('exit', (code) => { send({ type: 'status', status: 'stopped', detail: `Python 服务已退出 (${code ?? 'unknown'})` }); backend = null; });
}

ipcMain.handle('backend:command', (_event, command: Record<string, unknown>) => {
  if (!backend) startBackend();
  backend?.stdin.write(`${JSON.stringify(command)}\n`);
  return { ok: true };
});
ipcMain.handle('dialog:template', async () => {
  const options = { title: '选择模板图片', properties: ['openFile'] as ('openFile')[], filters: [{ name: '图片', extensions: ['png', 'jpg', 'jpeg', 'bmp', 'webp'] }] };
  const result = windowRef ? await dialog.showOpenDialog(windowRef, options) : await dialog.showOpenDialog(options);
  return result.canceled ? null : result.filePaths[0];
});
ipcMain.handle('config:load', async () => {
  const file = path.join(app.getPath('userData'), 'task-config.json');
  try { return JSON.parse(await fs.readFile(file, 'utf8')); } catch { return null; }
});
ipcMain.handle('config:save', async (_event, config: unknown) => {
  const file = path.join(app.getPath('userData'), 'task-config.json');
  await fs.mkdir(path.dirname(file), { recursive: true });
  await fs.writeFile(file, JSON.stringify(config, null, 2), 'utf8');
  return { ok: true };
});

function createWindow() {
  windowRef = new BrowserWindow({ width: 1440, height: 940, minWidth: 1050, minHeight: 700, backgroundColor: '#111315', title: 'Game Automator', webPreferences: { preload: path.join(__dirname, 'preload.js'), contextIsolation: true, nodeIntegration: false } });
  if (process.env.VITE_DEV_SERVER_URL) void windowRef.loadURL(process.env.VITE_DEV_SERVER_URL);
  else void windowRef.loadFile(path.join(app.getAppPath(), 'renderer-dist', 'index.html'));
  windowRef.on('closed', () => { windowRef = null; if (backend) { backend.kill(); backend = null; } });
}
app.whenReady().then(createWindow);
app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit(); });

