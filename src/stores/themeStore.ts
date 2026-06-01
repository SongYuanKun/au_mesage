import { create } from "zustand";

type Theme = "light" | "dark";

const STORAGE_KEY = "au-theme";

interface ThemeState {
  theme: Theme;
  isDark: boolean;
  toggleTheme: () => void;
  setTheme: (theme: Theme) => void;
}

function getInitialTheme(): Theme {
  if (typeof window === "undefined") return "dark";
  try {
    const saved =
      (localStorage.getItem(STORAGE_KEY) as Theme | null) ||
      (localStorage.getItem("theme") as Theme | null);
    if (saved === "light" || saved === "dark") return saved;
  } catch {
    /* ignore */
  }
  return "dark";
}

function syncThemeDom(theme: Theme) {
  document.documentElement.setAttribute("data-theme", theme);
  document.documentElement.classList.remove("light", "dark");
  document.documentElement.classList.add(theme);
  document.body.classList.add("redesign-v2");
  try {
    localStorage.setItem(STORAGE_KEY, theme);
    localStorage.setItem("theme", theme);
  } catch {
    /* ignore */
  }
}

const initial = getInitialTheme();
if (typeof document !== "undefined") {
  syncThemeDom(initial);
}

const useThemeStore = create<ThemeState>((set) => ({
  theme: initial,
  isDark: initial === "dark",
  toggleTheme: () =>
    set((state) => {
      const newTheme: Theme = state.theme === "light" ? "dark" : "light";
      syncThemeDom(newTheme);
      return { theme: newTheme, isDark: newTheme === "dark" };
    }),
  setTheme: (theme: Theme) =>
    set(() => {
      syncThemeDom(theme);
      return { theme, isDark: theme === "dark" };
    }),
}));

export default useThemeStore;
