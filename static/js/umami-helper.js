/**
 * au_message — Umami 自定义事件埋点
 */
(function () {
  "use strict";

  function track(name, props) {
    try {
      if (typeof window.umamiTrack === "function") {
        window.umamiTrack(name, props);
      } else if (typeof umami !== "undefined" && typeof umami.track === "function") {
        umami.track(name, props);
      }
    } catch (_) {}
  }

  var EVENT_ATTR = /^data-umami-event-([\w-_]+)/;

  function attr(el, name) {
    if (!el) return "";
    return el.getAttribute(name) || "";
  }

  function trackDeclarative(el) {
    var name = attr(el, "data-umami-event");
    if (!name) return;
    var props = {};
    el.getAttributeNames().forEach(function (key) {
      var m = key.match(EVENT_ATTR);
      if (m) props[m[1]] = el.getAttribute(key);
    });
    track(name, props);
  }

  function syncUnitSession() {
    if (window.umami && typeof window.umami.identify === "function") {
      var btn = document.querySelector("[data-au-unit].active");
      window.umami.identify({ 单位: btn ? attr(btn, "data-au-unit") : "" });
    }
  }

  document.addEventListener("click", function (e) {
    var declarative = e.target.closest("[data-umami-event]");
    if (declarative) {
      trackDeclarative(declarative);
      return;
    }

    var link = e.target.closest("a[data-page], .footer-links a");
    if (link) {
      track("nav_click", {
        page: attr(link, "data-page") || link.getAttribute("href") || "",
        label: (link.textContent || "").trim().slice(0, 50)
      });
      return;
    }

    var unitBtn = e.target.closest("[data-au-unit]");
    if (unitBtn) {
      var active = document.querySelector("[data-au-unit].active");
      var from = active ? attr(active, "data-au-unit") : "";
      var to = attr(unitBtn, "data-au-unit");
      if (from && to && from !== to) {
        track("unit_switch", { from: from, to: to });
        syncUnitSession();
      }
      return;
    }

    var modeBtn = e.target.closest("[data-calc-mode]");
    if (modeBtn) {
      var metalTab = document.querySelector(".calc-mode-panel .type-tab.active");
      track("calc_use", {
        tool: attr(modeBtn, "data-calc-mode"),
        metal: metalTab ? metalTab.textContent.trim().replace(/\s+/g, "") : ""
      });
      return;
    }
    if (e.target.closest("#btnDcaCalc")) {
      var metalTab2 = document.querySelector(".calc-mode-panel .type-tab.active");
      track("calc_use", {
        tool: "dca_calculate",
        metal: metalTab2 ? metalTab2.textContent.trim().replace(/\s+/g, "") : ""
      });
      return;
    }

    var action = null;
    if (e.target.closest("#btnSubscribe")) action = "subscribe";
    if (e.target.closest("#btnUnsubscribe")) action = "unsubscribe";
    if (action) {
      var alertTab = document.querySelector("[data-alert-type].active");
      track("alert_action", {
        action: action,
        metal: alertTab ? alertTab.textContent.trim().replace(/\s+/g, "") : ""
      });
      return;
    }

    var rangeTab = e.target.closest(".range-tab");
    if (rangeTab) {
      track("chart_interact", {
        metal: (document.querySelector("[data-metal].active") || {}).textContent || "",
        type: "range",
        value: rangeTab.textContent.trim()
      });
      return;
    }
    var indBtn = e.target.closest("[data-ind]");
    if (indBtn) {
      track("chart_interact", {
        metal: (document.querySelector("[data-metal].active") || {}).textContent || "",
        type: "indicator",
        value: attr(indBtn, "data-ind")
      });
      return;
    }

    if (e.target.closest("#themeToggle")) {
      var current = document.documentElement.getAttribute("data-theme") || "dark";
      var next = current === "dark" ? "light" : "dark";
      track("theme_toggle", { from: current, to: next });
    }
  });

  var scrollMarks = [25, 50, 75, 100];
  var scrollFired = {};
  var pageStart = Date.now();

  window.addEventListener("scroll", function () {
    var root = document.documentElement;
    var max = Math.max(root.scrollHeight - window.innerHeight, 1);
    var pct = Math.round((window.scrollY / max) * 100);
    scrollMarks.forEach(function (mark) {
      if (!scrollFired[mark] && pct >= mark) {
        scrollFired[mark] = true;
        track("scroll_depth", { depth: mark });
      }
    });
  }, { passive: true });

  window.addEventListener("pagehide", function () {
    track("page_exit", { duration: Date.now() - pageStart });
  });
})();
