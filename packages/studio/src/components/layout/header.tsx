import * as React from "react";
import { Menu, Bell, Search, Settings, User } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

interface HeaderProps {
  /** Title to display in the header */
  title?: string;
  /** Show hamburger menu button */
  showMenu?: boolean;
  /** Callback when menu button is clicked */
  onMenuClick?: () => void;
  /** Additional className */
  className?: string;
  /** Custom actions to render in header */
  actions?: React.ReactNode;
}

export function Header({
  title,
  showMenu = false,
  onMenuClick,
  className,
  actions,
}: HeaderProps) {
  return (
    <header
      className={cn(
        "sticky top-0 z-40 flex h-16 items-center justify-between border-b border-[#2a2a44] bg-[#0f0f1a]/95 px-4 md:px-6 backdrop-blur",
        className
      )}
    >
      <div className="flex items-center gap-4">
        {showMenu && (
          <Button
            variant="ghost"
            size="icon"
            onClick={onMenuClick}
            className="lg:hidden"
            aria-label="Toggle menu"
          >
            <Menu className="h-5 w-5" />
          </Button>
        )}
        {title && (
          <h1 className="text-lg font-semibold text-[#e8e8ed]">{title}</h1>
        )}
      </div>

      <div className="flex items-center gap-2">
        {actions}
        <Button variant="ghost" size="icon" aria-label="Search">
          <Search className="h-5 w-5 text-[#9898a6]" />
        </Button>
        <Button variant="ghost" size="icon" aria-label="Notifications">
          <Bell className="h-5 w-5 text-[#9898a6]" />
          <span className="absolute top-1 right-1 h-2 w-2 rounded-full bg-[#f87171]" />
        </Button>
        <Button variant="ghost" size="icon" aria-label="Settings">
          <Settings className="h-5 w-5 text-[#9898a6]" />
        </Button>
        <Button variant="ghost" size="icon" aria-label="Profile">
          <User className="h-5 w-5 text-[#9898a6]" />
        </Button>
      </div>
    </header>
  );
}
