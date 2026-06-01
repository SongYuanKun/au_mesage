import { NavLink } from "react-router-dom";
import { Settings } from "lucide-react";
import { useTheme } from "@/hooks/useTheme";
import { useAuth } from "@/auth/AuthContext";
import { isAuthRequired } from "@/auth/tokenStorage";

const NAV = [
  { to: "/", label: "实时价格", end: true },
  { to: "/history", label: "趋势图表" },
  { to: "/analysis", label: "行情分析" },
  { to: "/alerts", label: "价格提醒" },
];

export default function SiteNavbar() {
  const { theme, toggleTheme } = useTheme();
  const { role, logout } = useAuth();
  const showAdmin = !isAuthRequired() || role === "admin" || role === "ops";

  return (
    <header>
      <nav className="koen-navbar" aria-label="主导航">
        <div className="koen-navbar-inner">
          <NavLink to="/" className="koen-logo">
            <img src="/assets/logo.svg" alt="" width={30} height={30} />
            <span>Koen</span>
            <span className="text-sm font-semibold text-[var(--v2-text-muted)] hidden sm:inline">
              · 金价监控
            </span>
          </NavLink>

          <div className="koen-nav-links">
            {NAV.map(({ to, label, end }) => (
              <NavLink
                key={to}
                to={to}
                end={end}
                className={({ isActive }) =>
                  `koen-nav-link${isActive ? " active" : ""}`
                }
              >
                {label}
              </NavLink>
            ))}
            {showAdmin && (
              <NavLink
                to="/admin/sources"
                className={({ isActive }) =>
                  `koen-nav-link${isActive ? " active" : ""}`
                }
              >
                <Settings className="inline w-4 h-4 mr-1 -mt-0.5" aria-hidden />
                管理
              </NavLink>
            )}
            <a
              href="https://tools.songyuankun.top"
              className="koen-nav-link"
              target="_blank"
              rel="noopener noreferrer"
            >
              工具箱
            </a>
            {isAuthRequired() && role && (
              <button
                type="button"
                onClick={() => void logout()}
                className="koen-nav-link border-0 bg-transparent cursor-pointer"
              >
                退出
              </button>
            )}
            <button
              type="button"
              className="koen-theme-toggle"
              onClick={toggleTheme}
              aria-label="切换主题"
            >
              {theme === "dark" ? "亮色" : "暗色"}
            </button>
          </div>
        </div>
      </nav>
    </header>
  );
}
