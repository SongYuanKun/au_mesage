/** @type {import('tailwindcss').Config} */

export default {
  darkMode: ["class", '[data-theme="dark"]'],
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    container: {
      center: true,
    },
    extend: {
      colors: {
        koen: {
          accent: "var(--v2-accent)",
          "accent-hover": "var(--v2-accent-hover)",
          surface: "var(--v2-surface-solid)",
          muted: "var(--v2-text-muted)",
          border: "var(--v2-border)",
        },
      },
      fontFamily: {
        koen: ["var(--v2-font)"],
      },
      borderRadius: {
        koen: "var(--v2-radius)",
      },
      boxShadow: {
        koen: "var(--v2-shadow)",
      },
    },
  },
  plugins: [],
};
