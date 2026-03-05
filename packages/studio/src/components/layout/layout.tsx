import * as React from "react";
import { Outlet } from "react-router-dom";
import { Header } from "./header";
import { Sidebar } from "./sidebar";
import { cn } from "@/lib/utils";

interface LayoutProps {
  /** Show hamburger menu in header */
  showMenu?: boolean;
  /** Callback when menu button is clicked */
  onMenuClick?: () => void;
  /** Page title to show in header */
  title?: string;
  /** Additional className for main content */
  className?: string;
  /** Custom actions to render in header */
  headerActions?: React.ReactNode;
}

export function Layout({
  showMenu = false,
  onMenuClick,
  title,
  className,
  headerActions,
}: LayoutProps) {
  const [sidebarCollapsed, setSidebarCollapsed] = React.useState(false);

  return (
    <div className="flex h-screen bg-[#0f0f1a]">
      {/* Sidebar */}
      <Sidebar
        collapsed={sidebarCollapsed}
        onCollapseChange={setSidebarCollapsed}
        className="hidden lg:flex"
      />

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Header */}
        <Header
          showMenu={showMenu}
          onMenuClick={onMenuClick}
          title={title}
          actions={headerActions}
        />

        {/* Page Content */}
        <main
          className={cn(
            "flex-1 overflow-auto p-4 md:p-6",
            className
          )}
        >
          <Outlet />
        </main>
      </div>
    </div>
  );
}
