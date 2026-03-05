import * as React from "react";
import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Camera,
  Map,
  Folder,
  AlertTriangle,
  MessageSquare,
  BookOpen,
  Settings,
  ChevronLeft,
  ChevronRight,
  HardDrive,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

interface NavItem {
  title: string;
  href: string;
  icon: React.ElementType;
  badge?: number;
}

interface SidebarProps {
  /** Whether the sidebar is collapsed */
  collapsed?: boolean;
  /** Callback when collapse state changes */
  onCollapseChange?: (collapsed: boolean) => void;
  /** Additional className */
  className?: string;
  /** Custom navigation items */
  items?: NavItem[];
}

const defaultNavItems: NavItem[] = [
  { title: "仪表盘", href: "/dashboard", icon: LayoutDashboard },
  { title: "任务巡航", href: "/capture", icon: Camera },
  { title: "模型预览", href: "/model", icon: HardDrive },
  { title: "BIM查看器", href: "/bim", icon: Map },
  { title: "照片管理", href: "/photos", icon: Folder, badge: 12 },
  { title: "问题列表", href: "/issues", icon: AlertTriangle, badge: 5 },
  { title: "知识问答", href: "/knowledge", icon: MessageSquare },
  { title: "站点查询", href: "/station", icon: BookOpen },
];

export function Sidebar({
  collapsed = false,
  onCollapseChange,
  className,
  items = defaultNavItems,
}: SidebarProps) {
  const [isCollapsed, setIsCollapsed] = React.useState(collapsed);

  React.useEffect(() => {
    setIsCollapsed(collapsed);
  }, [collapsed]);

  const handleToggle = () => {
    const newState = !isCollapsed;
    setIsCollapsed(newState);
    onCollapseChange?.(newState);
  };

  return (
    <aside
      className={cn(
        "flex flex-col border-r border-[#2a2a44] bg-[#0f0f1a] transition-all duration-300",
        isCollapsed ? "w-16" : "w-64",
        className
      )}
    >
      {/* Logo */}
      <div className="flex h-16 items-center justify-center border-b border-[#2a2a44] px-4">
        {!isCollapsed ? (
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#4f8cff]">
              <span className="text-white font-bold text-sm">NS</span>
            </div>
            <span className="text-base font-semibold text-[#e8e8ed]">
              NeuralSite
            </span>
          </div>
        ) : (
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#4f8cff]">
            <span className="text-white font-bold text-sm">NS</span>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-4">
        <ul className="space-y-1 px-2">
          {items.map((item) => (
            <li key={item.href}>
              <NavLink
                to={item.href}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-[#252542] text-[#4f8cff]"
                      : "text-[#9898a6] hover:bg-[#1a1a2e] hover:text-[#e8e8ed]"
                  )
                }
              >
                <item.icon className="h-5 w-5 shrink-0" />
                {!isCollapsed && (
                  <>
                    <span className="flex-1">{item.title}</span>
                    {item.badge && (
                      <span className="flex h-5 min-w-[20px] items-center justify-center rounded-full bg-[#4f8cff] px-1.5 text-xs text-white">
                        {item.badge}
                      </span>
                    )}
                  </>
                )}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      {/* Footer */}
      <div className="border-t border-[#2a2a44] p-2">
        <NavLink
          to="/settings"
          className={({ isActive }) =>
            cn(
              "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
              isActive
                ? "bg-[#252542] text-[#4f8cff]"
                : "text-[#9898a6] hover:bg-[#1a1a2e] hover:text-[#e8e8ed]"
            )
          }
        >
          <Settings className="h-5 w-5 shrink-0" />
          {!isCollapsed && <span>系统设置</span>}
        </NavLink>

        {/* Collapse Toggle */}
        <Button
          variant="ghost"
          size="sm"
          onClick={handleToggle}
          className={cn(
            "mt-2 w-full justify-center text-[#9898a6] hover:text-[#e8e8ed]",
            isCollapsed ? "px-2" : "px-3"
          )}
        >
          {isCollapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <>
              <ChevronLeft className="h-4 w-4" />
              <span>收起</span>
            </>
          )}
        </Button>
      </div>
    </aside>
  );
}
