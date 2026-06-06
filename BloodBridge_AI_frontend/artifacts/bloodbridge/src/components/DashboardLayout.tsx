import React from "react";
import { Link, useLocation } from "wouter";
import { useTheme } from "@/lib/theme";
import { Droplet, Siren, Network, Map as MapIcon, Users, Settings, Moon, Sun, Bell, LogOut } from "lucide-react";
import { motion } from "framer-motion";
import { ThemeToggle } from "@/components/ThemeToggle";

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { isDark, toggleDark } = useTheme();
  const [location, setLocation] = useLocation();

  const navItems = [
    { icon: Siren, label: "Emergency OC", path: "/dashboard/emergency" },
    { icon: Network, label: "Graph View", path: "/dashboard/graph" },
    { icon: MapIcon, label: "Blood Map", path: "/dashboard/map" },
    { icon: Users, label: "Donor Engagement", path: "/dashboard/donors" },
    { icon: Settings, label: "Admin", path: "/dashboard/admin" },
  ];

  const getPageName = () => {
    const item = navItems.find(n => n.path === location);
    return item ? item.label : "Dashboard";
  };

  return (
    <div className="flex h-screen w-full overflow-hidden bg-background text-foreground">
      {/* Sidebar */}
      <div className="w-56 fixed inset-y-0 left-0 bg-sidebar text-sidebar-foreground flex flex-col border-r border-sidebar-border z-20">
        <div className="p-4 flex items-center gap-3 border-b border-sidebar-border h-[52px]">
          <div className="w-6 h-6 rounded-full bg-teal-600 flex items-center justify-center rounded-br-none rotate-45 flex-shrink-0">
            <div className="w-1.5 h-1.5 bg-white rounded-full -rotate-45" />
          </div>
          <div className="font-bold text-sm tracking-wide flex gap-1">
            <span className="text-white">inquilab</span>
            <span className="text-teal-400">AI</span>
          </div>
        </div>
        
        <div className="flex-1 py-4 flex flex-col gap-1 px-2">
          {navItems.map((item) => (
            <Link key={item.path} href={item.path} className={`flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-lg transition-colors ${location === item.path ? "bg-teal-600 text-white" : "text-slate-400 hover:bg-slate-800 hover:text-white"}`}>
              <item.icon className="w-4 h-4" />
              {item.label}
            </Link>
          ))}
        </div>
        
        <div className="p-4 border-t border-sidebar-border">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-xs text-slate-400">All systems online</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center text-xs font-bold text-white">DP</div>
            <div className="flex flex-col">
              <span className="text-xs font-semibold text-white">Dr. Priya</span>
              <span className="text-[10px] text-slate-400">KIMS</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col ml-56 min-h-0 bg-background transition-colors duration-200">
        {/* Topbar */}
        <div className="h-[52px] bg-card border-b border-border flex items-center justify-between px-6 flex-shrink-0 z-10 transition-colors duration-200">
          <div className="text-sm font-medium text-muted-foreground flex gap-2">
            <span>Dashboard</span>
            <span>/</span>
            <span className="text-foreground">{getPageName()}</span>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-xs font-medium text-emerald-600 dark:text-emerald-400 px-3 py-1 rounded-full bg-emerald-50 dark:bg-emerald-500/10 border border-emerald-100 dark:border-emerald-500/20">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              System Online
            </div>
            
            <ThemeToggle />
            
            <button className="p-2 rounded-full hover:bg-secondary text-muted-foreground transition-colors relative outline-none focus:ring-2 ring-primary">
              <Bell className="w-4 h-4" />
              <div className="absolute top-1.5 right-2 w-1.5 h-1.5 bg-red-500 rounded-full border-[1px] border-card" />
            </button>
            
            <div className="flex items-center gap-2 border-l border-border pl-4 ml-2">
              <div className="w-7 h-7 rounded-full bg-primary flex items-center justify-center text-xs font-bold text-primary-foreground">DP</div>
              <button 
                onClick={() => {
                  setLocation("/login");
                }}
                className="p-2 rounded-full hover:bg-secondary text-muted-foreground transition-colors relative outline-none focus:ring-2 ring-primary"
                title="Log out"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
        
        {/* Page Content */}
        <main className="flex-1 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
