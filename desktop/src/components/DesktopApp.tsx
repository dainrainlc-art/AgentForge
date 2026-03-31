import React, { useEffect, useState } from 'react';
import TauriAPI from '../utils/tauri';
import ChatPage from './ChatPage';
import SettingsPage from './SettingsPage';

interface TitleBarProps {
  title?: string;
}

export const TitleBar: React.FC<TitleBarProps> = ({ title = 'AgentForge' }) => {
  const [isMaximized, setIsMaximized] = useState(false);

  useEffect(() => {
    const checkMaximized = async () => {
      if (TauriAPI.isTauri()) {
        const maximized = await window.__TAURI__?.window.appWindow.isMaximized();
        setIsMaximized(maximized || false);
      }
    };
    checkMaximized();
  }, []);

  const handleMinimize = async () => {
    await TauriAPI.minimizeWindow();
  };

  const handleMaximize = async () => {
    if (isMaximized) {
      await TauriAPI.unmaximizeWindow();
    } else {
      await TauriAPI.maximizeWindow();
    }
    setIsMaximized(!isMaximized);
  };

  const handleClose = async () => {
    await TauriAPI.hideWindow();
    await TauriAPI.sendNotification('AgentForge Running', 'Application is running in the background');
  };

  if (!TauriAPI.isTauri()) {
    return null;
  }

  return (
    <div className="titlebar h-8 bg-gray-900 flex items-center justify-between px-2 select-none" data-tauri-drag-region>
      <div className="flex items-center gap-2">
        <img src="/icon.png" alt="AgentForge" className="w-4 h-4" />
        <span className="text-xs text-gray-300">{title}</span>
      </div>
      
      <div className="flex items-center">
        <button
          onClick={handleMinimize}
          className="w-8 h-8 flex items-center justify-center hover:bg-gray-700 text-gray-400 hover:text-white transition-colors"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
          </svg>
        </button>
        
        <button
          onClick={handleMaximize}
          className="w-8 h-8 flex items-center justify-center hover:bg-gray-700 text-gray-400 hover:text-white transition-colors"
        >
          {isMaximized ? (
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 4H6a2 2 0 00-2 2v2m0 8v2a2 2 0 002 2h2m8-16h2a2 2 0 012 2v2m0 8v2a2 2 0 01-2 2h-2" />
            </svg>
          ) : (
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
            </svg>
          )}
        </button>
        
        <button
          onClick={handleClose}
          className="w-8 h-8 flex items-center justify-center hover:bg-red-600 text-gray-400 hover:text-white transition-colors"
          title="Minimize to Tray"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
          </svg>
        </button>
      </div>
    </div>
  );
};

export const SystemTrayIndicator: React.FC = () => {
  const [connected, setConnected] = useState(false);
  const [notificationCount, setNotificationCount] = useState(0);
  const [isBackgroundMode, setIsBackgroundMode] = useState(false);

  useEffect(() => {
    const checkConnection = async () => {
      const isConnected = await TauriAPI.checkBackendConnection();
      setConnected(isConnected);
    };

    checkConnection();
    const interval = setInterval(checkConnection, 30000);

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const checkBackgroundMode = async () => {
      const isBg = await TauriAPI.isBackgroundMode();
      setIsBackgroundMode(isBg);
    };

    checkBackgroundMode();
    const interval = setInterval(checkBackgroundMode, 5000);

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const checkNotificationCount = async () => {
      const count = await TauriAPI.getNotificationCount();
      setNotificationCount(count);
    };

    checkNotificationCount();
    const interval = setInterval(checkNotificationCount, 10000);

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const unsubBackendRestart = TauriAPI.onBackendRestarted(() => {
      setConnected(true);
    });

    const unsubNotificationSent = TauriAPI.onNotificationSent(() => {
      setNotificationCount(prev => prev + 1);
    });

    return () => {
      unsubBackendRestart();
      unsubNotificationSent();
    };
  }, []);

  const handleIndicatorClick = async () => {
    if (isBackgroundMode) {
      await TauriAPI.showWindow();
      setIsBackgroundMode(false);
    }
  };

  return (
    <div 
      className="flex items-center gap-2 px-3 py-1 bg-gray-800 rounded-full text-xs cursor-pointer hover:bg-gray-700 transition-colors"
      onClick={handleIndicatorClick}
      title={isBackgroundMode ? 'Click to show window' : 'Running in foreground'}
    >
      <span className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`} />
      <span className="text-gray-300">{connected ? 'Connected' : 'Disconnected'}</span>
      {notificationCount > 0 && (
        <span className="ml-1 px-2 py-0.5 bg-red-500 text-white text-xs rounded-full">
          {notificationCount}
        </span>
      )}
      {isBackgroundMode && (
        <span className="ml-1 text-blue-400" title="Background Mode">
          🌙
        </span>
      )}
    </div>
  );
};

export const DesktopNotification: React.FC<{
  title: string;
  body: string;
  onDismiss: () => void;
  type?: 'info' | 'success' | 'warning' | 'error';
}> = ({ title, body, onDismiss, type = 'info' }) => {
  const typeColors = {
    info: 'bg-blue-600',
    success: 'bg-green-600',
    warning: 'bg-yellow-600',
    error: 'bg-red-600',
  };

  const typeIcons = {
    info: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    success: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    warning: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
    ),
    error: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  };

  return (
    <div className="fixed top-4 right-4 bg-gray-800 border border-gray-700 rounded-lg p-4 shadow-lg max-w-sm animate-slide-in-right">
      <div className="flex items-start gap-3">
        <div className={`flex-shrink-0 ${typeColors[type]} text-white p-2 rounded-lg`}>
          {typeIcons[type]}
        </div>
        <div className="flex-1">
          <h3 className="text-white font-medium">{title}</h3>
          <p className="text-gray-400 text-sm mt-1">{body}</p>
        </div>
        <button
          onClick={onDismiss}
          className="flex-shrink-0 text-gray-400 hover:text-white transition-colors"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  );
};

export const NotificationManager: React.FC = () => {
  const [notifications, setNotifications] = useState<Array<{
    id: number;
    title: string;
    body: string;
    type: 'info' | 'success' | 'warning' | 'error';
  }>>([]);

  useEffect(() => {
    const unsubNotificationSent = TauriAPI.onNotificationSent((data) => {
      const newNotification = {
        id: Date.now(),
        title: data.title,
        body: data.body,
        type: 'info' as const,
      };

      setNotifications(prev => [...prev, newNotification]);

      setTimeout(() => {
        setNotifications(prev => prev.filter(n => n.id !== newNotification.id));
      }, 5000);
    });

    return () => {
      unsubNotificationSent();
    };
  }, []);

  const dismissNotification = (id: number) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2">
      {notifications.map(notification => (
        <DesktopNotification
          key={notification.id}
          title={notification.title}
          body={notification.body}
          type={notification.type}
          onDismiss={() => dismissNotification(notification.id)}
        />
      ))}
    </div>
  );
};

export const UpdateNotification: React.FC = () => {
  const [updateAvailable, setUpdateAvailable] = useState<string | null>(null);
  const [downloading, setDownloading] = useState(false);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const unsubAvailable = TauriAPI.onUpdateAvailable((version) => {
      setUpdateAvailable(version);
    });

    const unsubProgress = TauriAPI.onUpdateProgress((p) => {
      setProgress(p);
    });

    const unsubDownloaded = TauriAPI.onUpdateDownloaded(() => {
      setDownloading(false);
    });

    return () => {
      unsubAvailable();
      unsubProgress();
      unsubDownloaded();
    };
  }, []);

  if (!updateAvailable) return null;

  return (
    <div className="fixed bottom-4 right-4 bg-gray-800 border border-gray-700 rounded-lg p-4 shadow-lg max-w-sm">
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0">
          <svg className="w-6 h-6 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
        </div>
        <div className="flex-1">
          <h3 className="text-white font-medium">Update Available</h3>
          <p className="text-gray-400 text-sm mt-1">
            Version {updateAvailable} is ready to install.
          </p>
          
          {downloading && (
            <div className="mt-2">
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div
                  className="bg-blue-500 h-2 rounded-full transition-all"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <p className="text-gray-500 text-xs mt-1">{progress}% downloaded</p>
            </div>
          )}
          
          <div className="mt-3 flex gap-2">
            <button
              onClick={() => setDownloading(true)}
              className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded transition-colors"
            >
              {downloading ? 'Downloading...' : 'Install Now'}
            </button>
            <button
              onClick={() => setUpdateAvailable(null)}
              className="px-3 py-1 bg-gray-700 hover:bg-gray-600 text-gray-300 text-sm rounded transition-colors"
            >
              Later
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export const QuickActionsMenu: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);

  const handleQuickAction = async (action: string) => {
    await TauriAPI.showWindow();
    await TauriAPI.sendNotification('Quick Action', `Navigating to ${action}`);
    setIsOpen(false);
  };

  return (
    <div className="fixed bottom-4 left-4 z-40">
      <div className="relative">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="w-12 h-12 bg-blue-600 hover:bg-blue-700 text-white rounded-full shadow-lg flex items-center justify-center transition-colors"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </button>

        {isOpen && (
          <div className="absolute bottom-14 left-0 bg-gray-800 border border-gray-700 rounded-lg shadow-xl p-2 min-w-[200px]">
            <button
              onClick={() => handleQuickAction('Dashboard')}
              className="w-full text-left px-3 py-2 text-gray-300 hover:bg-gray-700 rounded transition-colors flex items-center gap-2"
            >
              <span>📊</span>
              <span>Dashboard</span>
            </button>
            <button
              onClick={() => handleQuickAction('Chat')}
              className="w-full text-left px-3 py-2 text-gray-300 hover:bg-gray-700 rounded transition-colors flex items-center gap-2"
            >
              <span>💬</span>
              <span>Chat</span>
            </button>
            <button
              onClick={() => handleQuickAction('Tasks')}
              className="w-full text-left px-3 py-2 text-gray-300 hover:bg-gray-700 rounded transition-colors flex items-center gap-2"
            >
              <span>✅</span>
              <span>Tasks</span>
            </button>
            <button
              onClick={() => handleQuickAction('Analytics')}
              className="w-full text-left px-3 py-2 text-gray-300 hover:bg-gray-700 rounded transition-colors flex items-center gap-2"
            >
              <span>📈</span>
              <span>Analytics</span>
            </button>
            <hr className="my-2 border-gray-700" />
            <button
              onClick={() => handleQuickAction('Settings')}
              className="w-full text-left px-3 py-2 text-gray-300 hover:bg-gray-700 rounded transition-colors flex items-center gap-2"
            >
              <span>⚙️</span>
              <span>Settings</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export const DesktopApp: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isDesktop, setIsDesktop] = useState(false);
  const [currentPage, setCurrentPage] = useState<'chat' | 'settings' | 'default'>('default');

  useEffect(() => {
    setIsDesktop(TauriAPI.isTauri());
  }, []);

  useEffect(() => {
    const unsubNavigate = TauriAPI.onNavigate((path) => {
      if (path === '/chat') {
        setCurrentPage('chat');
      } else if (path === '/settings') {
        setCurrentPage('settings');
      } else if (path === '/') {
        setCurrentPage('default');
      }
    });

    return () => {
      unsubNavigate();
    };
  }, []);

  return (
    <div className="h-screen flex flex-col bg-gray-900">
      {isDesktop && <TitleBar />}
      <div className="flex-1 overflow-hidden">
        {currentPage === 'chat' ? (
          <ChatPage />
        ) : currentPage === 'settings' ? (
          <SettingsPage />
        ) : (
          children
        )}
      </div>
      {isDesktop && <SystemTrayIndicator />}
      {isDesktop && <UpdateNotification />}
      {isDesktop && <NotificationManager />}
      {isDesktop && <QuickActionsMenu />}
    </div>
  );
};

export default DesktopApp;
