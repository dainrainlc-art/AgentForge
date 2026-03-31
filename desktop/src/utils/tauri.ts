import { invoke } from '@tauri-apps/api/tauri';
import { listen } from '@tauri-apps/api/event';
import { appWindow } from '@tauri-apps/api/window';
import { notification } from '@tauri-apps/api';
import { clipboard } from '@tauri-apps/api';
import { open } from '@tauri-apps/api/shell';
import { save, open as openDialog } from '@tauri-apps/api/dialog';
import { readTextFile, writeTextFile } from '@tauri-apps/api/fs';

export interface SystemInfo {
  os: string;
  version: string;
  arch: string;
  hostname: string;
}

export interface UpdateInfo {
  version: string;
  date: string;
  notes?: string;
}

export class TauriAPI {
  static isTauri(): boolean {
    return typeof window !== 'undefined' && '__TAURI__' in window;
  }

  static async greet(name: string): Promise<string> {
    if (!this.isTauri()) return `Hello, ${name}! (Web mode)`;
    return await invoke<string>('greet', { name });
  }

  static async checkBackendConnection(): Promise<boolean> {
    if (!this.isTauri()) {
      try {
        const response = await fetch('http://localhost:8000/health');
        return response.ok;
      } catch {
        return false;
      }
    }
    return await invoke<boolean>('check_backend_connection');
  }

  static async getSystemInfo(): Promise<SystemInfo> {
    if (!this.isTauri()) {
      return {
        os: navigator.platform,
        version: 'Web',
        arch: 'Unknown',
        hostname: 'Web Browser',
      };
    }
    return await invoke<SystemInfo>('get_system_info');
  }

  static async openExternal(url: string): Promise<void> {
    if (!this.isTauri()) {
      window.open(url, '_blank');
      return;
    }
    await invoke('open_external', { url });
  }

  static async showNotification(title: string, body: string): Promise<void> {
    if (!this.isTauri()) {
      if ('Notification' in window && Notification.permission === 'granted') {
        new Notification(title, { body });
      } else if ('Notification' in window && Notification.permission !== 'denied') {
        const permission = await Notification.requestPermission();
        if (permission === 'granted') {
          new Notification(title, { body });
        }
      }
      return;
    }
    await invoke('show_notification', { title, body });
  }

  static async getClipboard(): Promise<string> {
    if (!this.isTauri()) {
      return await navigator.clipboard.readText();
    }
    return await invoke<string>('get_clipboard');
  }

  static async setClipboard(text: string): Promise<void> {
    if (!this.isTauri()) {
      await navigator.clipboard.writeText(text);
      return;
    }
    await invoke('set_clipboard', { text });
  }

  static async readFile(path: string): Promise<string> {
    if (!this.isTauri()) {
      throw new Error('File system not available in web mode');
    }
    return await invoke<string>('read_file', { path });
  }

  static async writeFile(path: string, content: string): Promise<void> {
    if (!this.isTauri()) {
      throw new Error('File system not available in web mode');
    }
    await invoke('write_file', { path, content });
  }

  static async selectFile(filters?: { name: string; extensions: string[] }[]): Promise<string | null> {
    if (!this.isTauri()) {
      const input = document.createElement('input');
      input.type = 'file';
      input.accept = filters?.flatMap(f => f.extensions.map(e => `.${e}`)).join(',') || '';
      
      return new Promise((resolve) => {
        input.onchange = () => {
          if (input.files && input.files.length > 0) {
            resolve(input.files[0].name);
          } else {
            resolve(null);
          }
        };
        input.click();
      });
    }
    
    const selected = await openDialog({
      multiple: false,
      filters: filters,
    });
    
    return selected as string | null;
  }

  static async selectFolder(): Promise<string | null> {
    if (!this.isTauri()) {
      return null;
    }
    
    const selected = await openDialog({
      directory: true,
    });
    
    return selected as string | null;
  }

  static async saveFile(defaultName?: string, filters?: { name: string; extensions: string[] }[]): Promise<string | null> {
    if (!this.isTauri()) {
      return null;
    }
    
    const selected = await save({
      defaultPath: defaultName,
      filters: filters,
    });
    
    return selected as string | null;
  }

  static async minimizeWindow(): Promise<void> {
    if (!this.isTauri()) return;
    await appWindow.minimize();
  }

  static async maximizeWindow(): Promise<void> {
    if (!this.isTauri()) return;
    await appWindow.maximize();
  }

  static async unmaximizeWindow(): Promise<void> {
    if (!this.isTauri()) return;
    await appWindow.unmaximize();
  }

  static async closeWindow(): Promise<void> {
    if (!this.isTauri()) {
      window.close();
      return;
    }
    await appWindow.close();
  }

  static async hideWindow(): Promise<void> {
    if (!this.isTauri()) return;
    await appWindow.hide();
  }

  static async showWindow(): Promise<void> {
    if (!this.isTauri()) return;
    await appWindow.show();
    await appWindow.setFocus();
  }

  static onUpdateAvailable(callback: (version: string) => void): () => void {
    if (!this.isTauri()) return () => {};
    
    let unlisten: (() => void) | null = null;
    
    listen<string>('update-available', (event) => {
      callback(event.payload);
    }).then((fn) => {
      unlisten = fn;
    });
    
    return () => {
      if (unlisten) unlisten();
    };
  }

  static onUpdateProgress(callback: (progress: number) => void): () => void {
    if (!this.isTauri()) return () => {};
    
    let unlisten: (() => void) | null = null;
    
    listen<number>('update-progress', (event) => {
      callback(event.payload);
    }).then((fn) => {
      unlisten = fn;
    });
    
    return () => {
      if (unlisten) unlisten();
    };
  }

  static onUpdateDownloaded(callback: () => void): () => void {
    if (!this.isTauri()) return () => {};
    
    let unlisten: (() => void) | null = null;
    
    listen('update-downloaded', () => {
      callback();
    }).then((fn) => {
      unlisten = fn;
    });
    
    return () => {
      if (unlisten) unlisten();
    };
  }

  static onNavigate(callback: (path: string) => void): () => void {
    if (!this.isTauri()) return () => {};
    
    let unlisten: (() => void) | null = null;
    
    listen<string>('navigate', (event) => {
      callback(event.payload);
    }).then((fn) => {
      unlisten = fn;
    });
    
    return () => {
      if (unlisten) unlisten();
    };
  }

  static onBackendRestarted(callback: () => void): () => void {
    if (!this.isTauri()) return () => {};
    
    let unlisten: (() => void) | null = null;
    
    listen('backend-restarted', () => {
      callback();
    }).then((fn) => {
      unlisten = fn;
    });
    
    return () => {
      if (unlisten) unlisten();
    };
  }

  static async sendNotification(title: string, body: string): Promise<void> {
    if (!this.isTauri()) {
      await this.showNotification(title, body);
      return;
    }
    await invoke('send_notification', { title, body });
  }

  static async sendOrderNotification(orderId: string, customer: string): Promise<void> {
    if (!this.isTauri()) return;
    await invoke('send_order_notification', { orderId, customer });
  }

  static async sendTaskNotification(taskName: string, status: string): Promise<void> {
    if (!this.isTauri()) return;
    await invoke('send_task_notification', { taskName, status });
  }

  static async toggleWindow(): Promise<boolean> {
    if (!this.isTauri()) return false;
    return await invoke<boolean>('toggle_window');
  }

  static async isBackgroundMode(): Promise<boolean> {
    if (!this.isTauri()) return false;
    return await invoke<boolean>('is_background_mode');
  }

  static async getNotificationCount(): Promise<number> {
    if (!this.isTauri()) return 0;
    return await invoke<number>('get_notification_count');
  }

  static async incrementNotificationCount(): Promise<number> {
    if (!this.isTauri()) return 0;
    return await invoke<number>('increment_notification_count');
  }

  static async clearNotificationCount(): Promise<void> {
    if (!this.isTauri()) return;
    await invoke('clear_notification_count');
  }

  static async enableAutoLaunch(): Promise<void> {
    if (!this.isTauri()) return;
    await invoke('enable_auto_launch');
  }

  static async disableAutoLaunch(): Promise<void> {
    if (!this.isTauri()) return;
    await invoke('disable_auto_launch');
  }

  static async isAutoLaunchEnabled(): Promise<boolean> {
    if (!this.isTauri()) return false;
    return await invoke<boolean>('is_auto_launch_enabled');
  }

  static onNotificationSent(callback: (data: { title: string; body: string; timestamp: string }) => void): () => void {
    if (!this.isTauri()) return () => {};
    
    let unlisten: (() => void) | null = null;
    
    listen('notification-sent', (event) => {
      callback(event.payload as { title: string; body: string; timestamp: string });
    }).then((fn) => {
      unlisten = fn;
    });
    
    return () => {
      if (unlisten) unlisten();
    };
  }

  static onCacheCleared(callback: () => void): () => void {
    if (!this.isTauri()) return () => {};
    
    let unlisten: (() => void) | null = null;
    
    listen('cache-cleared', () => {
      callback();
    }).then((fn) => {
      unlisten = fn;
    });
    
    return () => {
      if (unlisten) unlisten();
    };
  }
}

export default TauriAPI;
