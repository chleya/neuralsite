// NeuralSite App Store
// Zustand store for application-wide state

import { create } from 'zustand';

export interface AppNotification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  duration?: number;
}

interface AppState {
  // UI State
  sidebarOpen: boolean;
  theme: 'light' | 'dark' | 'system';
  isLoading: boolean;

  // Notifications
  notifications: AppNotification[];

  // Project context
  currentProjectId: string | null;
  currentProjectName: string | null;

  // Actions
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
  setLoading: (loading: boolean) => void;
  addNotification: (notification: Omit<AppNotification, 'id'>) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;
  setCurrentProject: (projectId: string | null, projectName?: string | null) => void;
}

export const useAppStore = create<AppState>((set, get) => ({
  // Initial UI state
  sidebarOpen: true,
  theme: 'system',
  isLoading: false,

  // Initial notifications
  notifications: [],

  // Project context
  currentProjectId: null,
  currentProjectName: null,

  // Toggle sidebar
  toggleSidebar: () => {
    set((state) => ({ sidebarOpen: !state.sidebarOpen }));
  },

  // Set sidebar state
  setSidebarOpen: (open: boolean) => {
    set({ sidebarOpen: open });
  },

  // Set theme
  setTheme: (theme: 'light' | 'dark' | 'system') => {
    set({ theme });
    // Apply theme to document
    const root = document.documentElement;
    if (theme === 'system') {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      root.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
    } else {
      root.setAttribute('data-theme', theme);
    }
  },

  // Set loading state
  setLoading: (loading: boolean) => {
    set({ isLoading: loading });
  },

  // Add notification
  addNotification: (notification: Omit<AppNotification, 'id'>) => {
    const id = `notification-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const newNotification: AppNotification = {
      ...notification,
      id,
      duration: notification.duration ?? 5000,
    };

    set((state) => ({
      notifications: [...state.notifications, newNotification],
    }));

    // Auto remove after duration
    if (newNotification.duration && newNotification.duration > 0) {
      setTimeout(() => {
        get().removeNotification(id);
      }, newNotification.duration);
    }
  },

  // Remove notification
  removeNotification: (id: string) => {
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    }));
  },

  // Clear all notifications
  clearNotifications: () => {
    set({ notifications: [] });
  },

  // Set current project
  setCurrentProject: (projectId: string | null, projectName: string | null = null) => {
    set({
      currentProjectId: projectId,
      currentProjectName: projectName,
    });
  },
}));

export default useAppStore;
