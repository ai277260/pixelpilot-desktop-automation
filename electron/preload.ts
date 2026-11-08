import { contextBridge, ipcRenderer } from 'electron';
contextBridge.exposeInMainWorld('automator', {
  command: (command: Record<string, unknown>) => ipcRenderer.invoke('backend:command', command),
  chooseTemplate: (): Promise<string | null> => ipcRenderer.invoke('dialog:template'),
  loadConfig: (): Promise<{steps?: unknown[]; loop?: boolean} | null> => ipcRenderer.invoke('config:load'),
  saveConfig: (config: unknown): Promise<{ok:boolean}> => ipcRenderer.invoke('config:save', config),
  onEvent: (callback: (event: Record<string, unknown>) => void) => {
    const listener = (_event: Electron.IpcRendererEvent, data: Record<string, unknown>) => callback(data);
    ipcRenderer.on('backend:event', listener);
    return () => ipcRenderer.removeListener('backend:event', listener);
  }
});

