/**
 * au_message — Umami 访客识别与 Session Data
 */
(function () {
  "use strict";

  var VISITOR_KEY = "umami.visitor-id";
  var SINCE_KEY = "umami.visitor-since";

  function detectPageTag() {
    var p = location.pathname;
    if (p.indexOf("/history") === 0) return "history";
    if (p.indexOf("/analysis") === 0) return "analysis";
    return "index";
  }

  function getActiveUnit() {
    var btn = document.querySelector("[data-au-unit].active");
    return btn ? btn.getAttribute("data-au-unit") || "" : "";
  }

  function getOrCreateVisitorId() {
    var isNew = false;
    var id = null;
    try {
      id = localStorage.getItem(VISITOR_KEY);
      isNew = !id;
      if (!id) {
        id =
          typeof crypto !== "undefined" && crypto.randomUUID
            ? crypto.randomUUID()
            : "v-" + Date.now() + "-" + Math.random().toString(36).slice(2, 10);
        localStorage.setItem(VISITOR_KEY, id);
        localStorage.setItem(SINCE_KEY, new Date().toISOString().slice(0, 10));
      }
    } catch (_) {
      return null;
    }
    return { id: id, isNew: isNew };
  }

  function buildSessionData(isNew, since) {
    var theme = "dark";
    try {
      theme =
        document.documentElement.getAttribute("data-theme") ||
        localStorage.getItem("au-theme") ||
        "dark";
    } catch (_) {}
    return {
      主题: theme,
      区域: detectPageTag(),
      单位: getActiveUnit(),
      回访: isNew ? "否" : "是",
      首访: since || "",
    };
  }

  function syncSession() {
    if (!window.umami || typeof window.umami.identify !== "function") return;
    var visitor = getOrCreateVisitorId();
    if (!visitor) return;
    var since = "";
    try {
      since = localStorage.getItem(SINCE_KEY) || "";
    } catch (_) {}
    window.umami.identify(visitor.id, buildSessionData(visitor.isNew, since));
  }

  function init() {
    syncSession();
  }

  if (document.readyState === "complete") {
    init();
  } else {
    document.addEventListener("readystatechange", function () {
      if (document.readyState === "complete") init();
    });
  }

  window.auUmamiSyncSession = syncSession;
})();
