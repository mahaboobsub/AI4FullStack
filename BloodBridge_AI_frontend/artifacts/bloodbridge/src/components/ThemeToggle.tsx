import { Moon, Sun } from "lucide-react";
import { useTheme } from "@/lib/theme";
import { motion } from "framer-motion";

export function ThemeToggle() {
  const { isDark, toggleDark } = useTheme();

  return (
    <button 
      onClick={toggleDark} 
      className="p-2.5 rounded-full bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 transition-colors relative outline-none focus:ring-2 focus:ring-teal-500 shadow-sm"
      aria-label="Toggle theme"
    >
      <motion.div animate={{ rotate: isDark ? 180 : 0 }} transition={{ duration: 0.3 }}>
        {isDark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
      </motion.div>
    </button>
  );
}
