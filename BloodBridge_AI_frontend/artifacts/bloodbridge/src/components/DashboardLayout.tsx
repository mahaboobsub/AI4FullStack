import React, { useEffect, useState } from "react";
import { Link, useLocation } from "wouter";
import { useTheme } from "@/lib/theme";
import { Siren, Network, Map as MapIcon, Users, Settings, Bell, LogOut, ChevronLeft, ChevronDown, User, Building2, Shield } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { ThemeToggle } from "@/components/ThemeToggle";

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  const [location, setLocation] = useLocation();
  const [showProfile, setShowProfile] = useState(false);
  const [staffProfile, setStaffProfile] = useState({
    name: "Dr. Priya",
    hospital: "KIMS Secunderabad",
    role: "Admin",
    initials: "DP",
  });

  useEffect(() => {
    const name = localStorage.getItem("staff_name") || "Dr. Priya";
    const hospital = localStorage.getItem("staff_hospital") || "KIMS Secunderabad";
    const role = localStorage.getItem("staff_role") || "Admin";
    const initials = name.split(" ").map((w: string) => w[0] || "").join("").slice(0, 2).toUpperCase() || "DP";
    setStaffProfile({ name, hospital, role, initials });
  }, []);

  const navItems = [
    { icon: Siren,   label: "Emergency OC",    path: "/dashboard/emergency" },
    { icon: Network, label: "Graph View",       path: "/dashboard/graph" },
    { icon: MapIcon, label: "Blood Map",        path: "/dashboard/map" },
    { icon: Users,   label: "Donor Engagement", path: "/dashboard/donors" },
    { icon: Settings,label: "Admin",            path: "/dashboard/admin" },
  ];

  const getPageName = () => navItems.find(n => n.path === location)?.label ?? "Dashboard";

  return (
    <div className="flex h-screen w-full overflow-hidden bg-background text-foreground">
      {/* ── Sidebar ──────────────────────────────────────────────── */}
      <div className="w-56 fixed inset-y-0 left-0 bg-sidebar text-sidebar-foreground flex flex-col border-r border-sidebar-border z-20">
        {/* Logo */}
        <Link href="/" className="p-4 flex items-center gap-3 border-b border-sidebar-border h-[52px] hover:bg-slate-800/50 transition-colors">
          <div className="w-6 h-6 rounded-full bg-teal-600 flex items-center justify-center rounded-br-none rotate-45 flex-shrink-0">
            <div className="w-1.5 h-1.5 bg-white rounded-full -rotate-45" />
          </div>
          <div className="font-bold text-sm tracking-wide flex gap-1">
            <span className="text-white">inquilab</span>
            <span className="text-teal-400">AI</span>
          </div>
        </Link>

        {/* Nav */}
        <div className="flex-1 py-4 flex flex-col gap-1 px-2 overflow-y-auto">
          {navItems.map((item) => (
            <Link
              key={item.path}
              href={item.path}
              className={`flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                location === item.path
                  ? "bg-teal-600 text-white"
                  : "text-slate-400 hover:bg-slate-800 hover:text-white"
              }`}
            >
              <item.icon className="w-4 h-4 flex-shrink-0" />
              {item.label}
            </Link>
          ))}
        </div>

        {/* ── Admin Profile ──────────────────────────────────────── */}
        <div className="p-3 border-t border-sidebar-border">
          {/* Status dot */}
          <div className="flex items-center gap-2 mb-2 px-1">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-xs text-slate-400">All systems online</span>
          </div>

          {/* Profile toggle button */}
          <button
            onClick={() => setShowProfile(p => !p)}
            className="w-full flex items-center gap-2.5 p-2 rounded-lg hover:bg-slate-800/60 transition-colors"
          >
            <div className="w-8 h-8 rounded-full bg-teal-700 flex items-center justify-center text-xs font-bold text-white flex-shrink-0">
              {staffProfile.initials}
            </div>
            <div className="flex-1 min-w-0 text-left">
              <div className="text-xs font-semibold text-white truncate">{staffProfile.name}</div>
              <div className="text-[10px] text-slate-400 truncate">{staffProfile.hospital}</div>
            </div>
            <ChevronDown className={`w-3 h-3 text-slate-500 flex-shrink-0 transition-transform ${showProfile ? "rotate-180" : ""}`} />
          </button>

          {/* Expanded profile card */}
          <AnimatePresence>
            {showProfile && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.15 }}
                className="overflow-hidden"
              >
                <div className="mt-2 bg-slate-900/80 border border-slate-700 rounded-lg p-3 space-y-2">
                  <div className="flex items-center gap-2 text-xs text-slate-300">
                    <User className="w-3 h-3 text-slate-500 flex-shrink-0" />
                    <span className="truncate">{staffProfile.name}</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-slate-300">
                    <Building2 className="w-3 h-3 text-slate-500 flex-shrink-0" />
                    <span className="truncate">{staffProfile.hospital}</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <Shield className="w-3 h-3 text-slate-500 flex-shrink-0" />
                    <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold uppercase ${
                      staffProfile.role === "Admin"
                        ? "bg-purple-500/20 text-purple-400"
                        : staffProfile.role === "Coordinator"
                        ? "bg-blue-500/20 text-blue-400"
                        : "bg-slate-700 text-slate-300"
                    }`}>
                      {staffProfile.role}
                    </span>
                  </div>
                  {/* Bot link */}
                  <div className="pt-1 border-t border-slate-700/50">
                    <a
                      href="https://t.me/ummedrakho_bot"
                      target="_blank"
                      rel="noopener"
                      className="text-[10px] text-[#229ED9] hover:underline flex items-center gap-1"
                    >
                      <svg className="w-2.5 h-2.5 flex-shrink-0" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/>
                      </svg>
                      @ummedrakho_bot
                    </a>
                  </div>
                  {/* Logout */}
                  <button
                    onClick={() => {
                      localStorage.removeItem("auth_token");
                      localStorage.removeItem("staff_id");
                      setLocation("/login");
                    }}
                    className="w-full text-left text-[10px] text-red-400 hover:text-red-300 flex items-center gap-1 pt-1"
                  >
                    <LogOut className="w-2.5 h-2.5" />
                    Sign out
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* ── Main Content ──────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col ml-56 min-h-0 bg-background transition-colors duration-200">
        {/* Topbar */}
        <div className="h-[52px] bg-card border-b border-border flex items-center justify-between px-6 flex-shrink-0 z-10">
          <div className="flex items-center gap-3 text-sm font-medium text-muted-foreground">
            {/* Back button */}
            <button
              onClick={() => window.history.back()}
              className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors px-2 py-1 rounded-md hover:bg-secondary"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
              Back
            </button>
            <span className="text-muted-foreground/40">|</span>
            <span>Dashboard</span>
            <span>/</span>
            <span className="text-foreground font-semibold">{getPageName()}</span>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-xs font-medium text-emerald-600 dark:text-emerald-400 px-3 py-1 rounded-full bg-emerald-50 dark:bg-emerald-500/10 border border-emerald-100 dark:border-emerald-500/20">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              System Online
            </div>

            <ThemeToggle />

            <button className="p-2 rounded-full hover:bg-secondary text-muted-foreground transition-colors relative">
              <Bell className="w-4 h-4" />
              <div className="absolute top-1.5 right-2 w-1.5 h-1.5 bg-red-500 rounded-full border-[1px] border-card" />
            </button>

            <div className="flex items-center gap-2 border-l border-border pl-4 ml-2">
              <div className="w-7 h-7 rounded-full bg-teal-700 flex items-center justify-center text-xs font-bold text-white">
                {staffProfile.initials}
              </div>
              <button
                onClick={() => {
                  localStorage.removeItem("auth_token");
                  localStorage.removeItem("staff_id");
                  setLocation("/login");
                }}
                className="p-2 rounded-full hover:bg-secondary text-muted-foreground transition-colors"
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
