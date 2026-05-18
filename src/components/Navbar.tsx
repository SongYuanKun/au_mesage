import { NavLink } from "react-router-dom";
import { Moon, Sun, Home, TrendingUp, BarChart3, Bell } from "lucide-react";
import { useTheme } from "@/hooks/useTheme";

const NAV_ITEMS = [
  { to: "/", label: "实时", emoji: "🏠", icon: Home },
  { to: "/history", label: "历史", emoji: "📈", icon: TrendingUp },
  { to: "/analysis", label: "分析", emoji: "📊", icon: BarChart3 },
  { to: "/alerts", label: "提醒", emoji: "🔔", icon: Bell },
];

export default function Navbar() {
  const { isDark, toggleTheme } = useTheme();

  return (
    <nav aria-label="主导航" className="sticky top-0 z-50 w-full border-b border-gray-200 dark:border-gray-700 bg-white/80 dark:bg-gray-900/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo + Nav Links */}
          <div className="flex items-center gap-2 sm:gap-6">
            <span className="text-2xl">🪙</span>
            <h1 className="text-xl font-bold text-gray-900 dark:text-white hidden sm:block">
              实时金价监控
            </h1>

            {/* Navigation Links */}
            <div className="flex items-center gap-1 ml-2 sm:ml-4">
              {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
                <NavLink
                  key={to}
                  to={to}
                  end={to === "/"}
                  className={({ isActive }) =>
                    `flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                      isActive
                        ? "bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400"
                        : "text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 hover:text-gray-900 dark:hover:text-white"
                    }`
                  }
                >
                  <Icon className="w-4 h-4" />
                  <span className="hidden sm:inline">{label}</span>
                </NavLink>
              ))}
            </div>
          </div>

          {/* Theme Toggle */}
          <button
            onClick={toggleTheme}
            className="p-2 rounded-lg bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
            aria-label="切换主题"
          >
            {isDark ? (
              <Sun className="w-5 h-5 text-yellow-400" />
            ) : (
              <Moon className="w-5 h-5 text-gray-600" />
            )}
          </button>
        </div>
      </div>
    </nav>
  );
}
