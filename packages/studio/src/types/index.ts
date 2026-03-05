/**
 * Common type definitions
 */

// API Response types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  success: boolean;
}

export interface ApiListResponse<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, string>;
}

// Pagination
export interface PaginationParams {
  page: number;
  pageSize: number;
  sortBy?: string;
  sortOrder?: "asc" | "desc";
}

export interface PaginatedResult<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
}

// User types
export interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  role: "admin" | "user" | "guest";
  createdAt: string;
  updatedAt: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

// Form types
export interface FormFieldError {
  field: string;
  message: string;
}

// Modal/Dialog types
export interface ModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

// Table types
export interface TableColumn<T> {
  key: keyof T | string;
  title: string;
  render?: (value: unknown, item: T) => React.ReactNode;
  sortable?: boolean;
  width?: number | string;
}

export interface TableSort {
  key: string;
  order: "asc" | "desc";
}

// Filter types
export interface FilterOption {
  label: string;
  value: string;
}

export interface FilterParams {
  search?: string;
  filters?: Record<string, string | string[]>;
}

// Notification types
export interface Notification {
  id: string;
  type: "info" | "success" | "warning" | "error";
  title: string;
  message: string;
  timestamp: number;
  read?: boolean;
}

// Common utility types
export type Omit<T, K extends keyof T> = Pick<T, Exclude<keyof T, K>>;
export type PartialBy<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;
export type RequiredBy<T, K extends keyof T> = T & Required<Pick<T, K>>;

// Re-export React types
import type React from "react";

// Re-export collision types
export * from './collision';
