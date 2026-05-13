import { create } from "zustand";

type Theme = "light" | "dark";

interface ThemeState {
  theme: Theme;
  isDark: boolean;
  toggleTheme: () => void;
  setTheme: (theme: Theme) => void;
}

function getInitialTheme(): Theme {
  if (typeof window === "undefined") return "light";
  const savedTheme = localStorage.getItem("theme") as Theme;
  if (savedTheme) return savedTheme;
  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

const useThemeStore = create<ThemeState>((set) => ({
  theme: getInitialTheme(),
  isDark: getInitialTheme() === "dark",
  toggleTheme: () =>
    set((state) => {
      const newTheme: Theme = state.theme === "light" ? "dark" : "light";
      document.documentElement.classList.remove("light", "dark");
      document.documentElement.classList.add(newTheme);
      localStorage.setItem("theme", newTheme);
      return { theme: newTheme, isDark: newTheme === "dark" };
    }),
  setTheme: (theme: Theme) =>
    set(() => {
      document.documentElement.classList.remove("light", "dark");
      document.documentElement.classList.add(theme);
      localStorage.setItem("theme", theme);
      return { theme, isDark: theme === "dark" };
    }),
}));

export default useThemeStore;
