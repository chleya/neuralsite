/**
 * Application constants
 */

// API Configuration
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";
export const API_TIMEOUT = 30000; // 30 seconds

// Pagination
export const DEFAULT_PAGE_SIZE = 20;
export const PAGE_SIZE_OPTIONS = [10, 20, 50, 100];

// Date formats
export const DATE_FORMAT = "YYYY-MM-DD";
export const DATETIME_FORMAT = "YYYY-MM-DD HH:mm:ss";
export const TIME_FORMAT = "HH:mm:ss";

// Storage keys
export const STORAGE_KEYS = {
  TOKEN: "auth_token",
  USER: "user_info",
  THEME: "theme",
  LANGUAGE: "language",
  SETTINGS: "app_settings",
} as const;

// HTTP Status codes
export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  NO_CONTENT: 204,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  INTERNAL_SERVER_ERROR: 500,
} as const;

// Error messages
export const ERROR_MESSAGES = {
  NETWORK_ERROR: "网络连接失败，请检查网络设置",
  SERVER_ERROR: "服务器错误，请稍后重试",
  UNAUTHORIZED: "登录已过期，请重新登录",
  FORBIDDEN: "没有权限执行此操作",
  NOT_FOUND: "请求的资源不存在",
  VALIDATION_ERROR: "数据验证失败",
  UNKNOWN_ERROR: "发生未知错误",
} as const;

// Success messages
export const SUCCESS_MESSAGES = {
  SAVE_SUCCESS: "保存成功",
  DELETE_SUCCESS: "删除成功",
  UPDATE_SUCCESS: "更新成功",
  CREATE_SUCCESS: "创建成功",
} as const;

// App info
export const APP_NAME = "NeuralSite Studio";
export const APP_VERSION = "3.0.0";

// Feature flags
export const FEATURES = {
  ENABLE_ANALYTICS: true,
  ENABLE_DEBUG: import.meta.env.DEV,
  ENABLE_EXPERIMENTAL: false,
} as const;

// Animation durations
export const ANIMATION = {
  FAST: 150,
  NORMAL: 300,
  SLOW: 500,
} as const;

// Z-index layers
export const Z_INDEX = {
  DROPDOWN: 1000,
  STICKY: 1020,
  MODAL_BACKDROP: 1040,
  MODAL: 1050,
  POPOVER: 1060,
  TOAST: 1070,
  TOOLTIP: 1080,
} as const;

// Color palette (Tailwind CSS custom colors)
export const COLORS = {
  PRIMARY: {
    50: "#f0f9ff",
    100: "#e0f2fe",
    200: "#bae6fd",
    300: "#7dd3fc",
    400: "#38bdf8",
    500: "#0ea5e9",
    600: "#0284c7",
    700: "#0369a1",
    800: "#075985",
    900: "#0c4a6e",
  },
  SUCCESS: {
    50: "#f0fdf4",
    100: "#dcfce7",
    200: "#bbf7d0",
    300: "#86efac",
    400: "#4ade80",
    500: "#22c55e",
    600: "#16a34a",
    700: "#15803d",
    800: "#166534",
    900: "#14532d",
  },
  WARNING: {
    50: "#fffbeb",
    100: "#fef3c7",
    200: "#fde68a",
    300: "#fcd34d",
    400: "#fbbf24",
    500: "#f59e0b",
    600: "#d97706",
    700: "#b45309",
    800: "#92400e",
    900: "#78350f",
  },
  DESTRUCTIVE: {
    50: "#fef2f2",
    100: "#fee2e2",
    200: "#fecaca",
    300: "#fca5a5",
    400: "#f87171",
    500: "#ef4444",
    600: "#dc2626",
    700: "#b91c1c",
    800: "#991b1b",
    900: "#7f1d1d",
  },
} as const;
