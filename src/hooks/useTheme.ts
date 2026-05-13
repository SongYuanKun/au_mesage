import { useEffect } from 'react';
import useThemeStore from '@/stores/themeStore';

export function useTheme() {
  const { theme, isDark, toggleTheme } = useThemeStore();

  // Sync DOM class on mount (handles SSR hydration)
  useEffect(() => {
    document.documentElement.classList.remove('light', 'dark');
    document.documentElement.classList.add(theme);
  }, [theme]);

  return {
    theme,
    toggleTheme,
    isDark,
  };
}
