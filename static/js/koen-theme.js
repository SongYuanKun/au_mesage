/**
 * 主题切换（与 Koen 工具箱一致：默认暗色，localStorage 持久化）
 */
(function (global) {
  var STORAGE_KEY = "au-theme";

  function applyThemeToBtn(btn, theme) {
    if (!btn) return;
    var isDark = theme === "dark";
    var label = isDark ? "切换到亮色主题" : "切换到暗色主题";
    btn.setAttribute("aria-label", label);
    btn.setAttribute("title", label);
    if (!btn.querySelector(".koen-icon")) {
      btn.textContent = isDark ? "亮色" : "暗色";
    }
  }

  function applyTheme(theme) {
    var next = theme === "light" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    document.documentElement.classList.remove("light", "dark");
    document.documentElement.classList.add(next);
    try {
      localStorage.setItem(STORAGE_KEY, next);
      localStorage.setItem("theme", next);
    } catch (e) {
      /* ignore */
    }
    applyThemeToBtn(document.getElementById("themeToggle"), next);
  }

  function initTheme() {
    var saved = "dark";
    try {
      saved =
        localStorage.getItem(STORAGE_KEY) ||
        localStorage.getItem("au-koen-theme") ||
        localStorage.getItem("theme") ||
        "dark";
    } catch (e) {
      /* ignore */
    }
    applyTheme(saved);
    var btn = document.getElementById("themeToggle");
    if (btn && !btn.getAttribute("data-bound")) {
      btn.setAttribute("data-bound", "1");
      btn.addEventListener("click", function () {
        var current = document.documentElement.getAttribute("data-theme") || "dark";
        applyTheme(current === "dark" ? "light" : "dark");
      });
    }
  }

  global.KoenTheme = { applyTheme: applyTheme, initTheme: initTheme };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initTheme);
  } else {
    initTheme();
  }
})(typeof window !== "undefined" ? window : this);
