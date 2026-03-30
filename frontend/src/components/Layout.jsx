import { useState } from "react";
import { Outlet, NavLink, useLocation } from "react-router-dom";
import { 
  LayoutDashboard, 
  MessageSquare, 
  Shield, 
  History, 
  Settings, 
  FileText,
  Flame,
  Menu,
  X,
  Folder,
  ChevronRight,
  Radio
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";

const navItems = [
  { path: "/", icon: LayoutDashboard, label: "Dashboard" },
  { path: "/sessions", icon: Folder, label: "Sessions" },
  { path: "/chat", icon: MessageSquare, label: "AI Chat" },
  { path: "/interceptor", icon: Radio, label: "Interceptor" },
  { path: "/findings", icon: Shield, label: "Findings" },
  { path: "/proxy-history", icon: History, label: "Proxy History" },
  { path: "/reports", icon: FileText, label: "Reports" },
  { path: "/settings", icon: Settings, label: "Settings" },
];

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const location = useLocation();

  return (
    <div className="flex h-screen bg-[#09090b]">
      {/* Sidebar */}
      <aside 
        className={`sidebar flex flex-col transition-all duration-300 ${
          sidebarOpen ? "w-64" : "w-16"
        }`}
      >
        {/* Logo */}
        <div className="p-4 border-b border-zinc-800">
          <div className="flex items-center gap-3">
            <div className="relative w-10 h-10 flex items-center justify-center bg-emerald-500/10 border border-emerald-500/30">
              <Flame className="w-6 h-6 text-emerald-500" />
            </div>
            {sidebarOpen && (
              <div className="fade-in">
                <h1 className="font-mono text-sm font-semibold text-zinc-100 tracking-tight">
                  MCP'Arsonist
                </h1>
                <p className="font-mono text-[10px] text-emerald-500 uppercase tracking-widest">
                  AI Security
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Navigation */}
        <ScrollArea className="flex-1 py-4">
          <nav className="space-y-1 px-2">
            {navItems.map((item) => {
              const isActive = location.pathname === item.path || 
                (item.path !== "/" && location.pathname.startsWith(item.path));
              
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  data-testid={`nav-${item.label.toLowerCase().replace(/\s/g, '-')}`}
                  className={`sidebar-item ${isActive ? "active" : ""}`}
                >
                  <item.icon className="w-5 h-5 flex-shrink-0" />
                  {sidebarOpen && (
                    <span className="font-mono text-sm truncate">{item.label}</span>
                  )}
                  {sidebarOpen && isActive && (
                    <ChevronRight className="w-4 h-4 ml-auto text-emerald-500" />
                  )}
                </NavLink>
              );
            })}
          </nav>
        </ScrollArea>

        {/* Sidebar Toggle */}
        <div className="p-4 border-t border-zinc-800">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="w-full justify-center text-zinc-500 hover:text-zinc-100 hover:bg-zinc-800"
            data-testid="toggle-sidebar"
          >
            {sidebarOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
          </Button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="app-header px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className="status-indicator status-online" />
              <span className="font-mono text-xs text-zinc-500 uppercase tracking-wider">
                System Online
              </span>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="font-mono text-xs text-zinc-500">
              {new Date().toLocaleString('en-US', { 
                hour12: false, 
                hour: '2-digit', 
                minute: '2-digit',
                second: '2-digit'
              })}
            </div>
          </div>
        </header>

        {/* Page Content */}
        <div className="flex-1 overflow-auto p-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
