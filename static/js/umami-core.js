/**
 * au_message — Umami 数据采集（identify / performance / tag / PV·UV）
 */
(function () {
  var UMAMI_HOST = "https://umami.songyuankun.top";
  var WEBSITE_ID = "0a0f5b9f-b2ca-41a5-a1d0-4ef7a6bbaad3";
  var VISITOR_KEY = "umami.visitor-id";
  var SINCE_KEY = "umami.visitor-since";
  var NAV_DELAY = 300;
  var MAX_RETRIES = 2;
  var RETRY_DELAY = 1500;

  function dntEnabled() {
    var v = navigator.doNotTrack || window.doNotTrack || navigator.msDoNotTrack;
    return v === "1" || v === "yes";
  }

  try {
    if (localStorage.getItem("umami.disabled") || dntEnabled()) return;
  } catch (_) {
    if (dntEnabled()) return;
  }

  var scr = window.screen || { width: 0, height: 0 };
  var screen = scr.width + "x" + scr.height;
  var language = navigator.language || "";
  var location = window.location;
  var doc = document;

  var cache;
  var distinctId;
  var currentUrl = normalizeUrl(location.pathname + location.search);
  var currentRef = normalizeRef(document.referrer);
  var pageTag = detectPageTag();
  var onPerfPageHide;
  var isNewVisitor = false;

  function detectPageTag() {
    var p = location.pathname;
    if (p.indexOf("/history") === 0) return "history";
    if (p.indexOf("/analysis") === 0) return "analysis";
    return "index";
  }

  function normalizeUrl(url) {
    if (!url) return url;
    try {
      var u = new URL(url, location.origin);
      u.search = "";
      u.hash = "";
      return u.pathname;
    } catch (_) {
      return url.split("?")[0].split("#")[0];
    }
  }

  function normalizeRef(ref) {
    if (!ref) return "";
    try {
      if (new URL(ref).origin === location.origin) return "";
    } catch (_) {}
    return ref;
  }

  function getActiveUnit() {
    var btn = document.querySelector("[data-au-unit].active");
    return btn ? btn.getAttribute("data-au-unit") || "" : "";
  }

  function getOrCreateVisitorId() {
    try {
      var id = localStorage.getItem(VISITOR_KEY);
      isNewVisitor = !id;
      if (!id) {
        id = typeof crypto !== "undefined" && crypto.randomUUID
          ? crypto.randomUUID()
          : "v-" + Date.now() + "-" + Math.random().toString(36).slice(2, 10);
        localStorage.setItem(VISITOR_KEY, id);
        localStorage.setItem(SINCE_KEY, new Date().toISOString().slice(0, 10));
      }
      return id;
    } catch (_) {
      return null;
    }
  }

  function buildSessionData() {
    var theme = "dark";
    var since = "";
    try {
      theme = document.documentElement.getAttribute("data-theme") || localStorage.getItem("au-theme") || "dark";
      since = localStorage.getItem(SINCE_KEY) || "";
    } catch (_) {}
    return {
      主题: theme,
      区域: pageTag,
      单位: getActiveUnit(),
      回访: isNewVisitor ? "否" : "是",
      首访: since
    };
  }

  function basePayload() {
    return {
      website: WEBSITE_ID,
      hostname: location.hostname,
      screen: screen,
      language: language,
      title: doc.title,
      url: currentUrl,
      referrer: currentRef,
      tag: pageTag,
      id: distinctId || undefined
    };
  }

  function beforeSend(type, payload) {
    if (typeof window.umamiBeforeSend !== "function") return payload;
    try {
      var next = window.umamiBeforeSend(type, payload);
      return next || null;
    } catch (_) {
      return payload;
    }
  }

  function send(payload, type, attempt) {
    type = type || "event";
    attempt = attempt || 0;
    payload = beforeSend(type, payload);
    if (!payload) return;

    var headers = { "Content-Type": "application/json" };
    if (cache) headers["x-umami-cache"] = cache;

    fetch(UMAMI_HOST + "/api/send", {
      method: "POST",
      body: JSON.stringify({ type: type, payload: payload }),
      headers: headers,
      keepalive: true,
      credentials: "omit"
    })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (d && d.cache) cache = d.cache;
        if (d && d.disabled) cache = "";
      })
      .catch(function () {
        if (attempt < MAX_RETRIES) {
          setTimeout(function () { send(payload, type, attempt + 1); }, RETRY_DELAY * (attempt + 1));
        }
      });
  }

  function trackPageview() {
    send(basePayload(), "event");
  }

  function sendEvent(name, data) {
    var props = data;
    if (window.umamiEnrich) props = window.umamiEnrich(name, data);
    var payload = basePayload();
    payload.name = name;
    payload.data = props;
    send(payload, "event");
  }

  function identify(idOrData, data) {
    if (typeof idOrData === "string") {
      distinctId = idOrData;
      try { localStorage.setItem(VISITOR_KEY, idOrData); } catch (_) {}
    } else {
      data = idOrData;
    }
    cache = "";
    var payload = basePayload();
    payload.data = data || {};
    send(payload, "identify");
  }

  distinctId = getOrCreateVisitorId();

  var origPush = history.pushState;
  var origReplace = history.replaceState;
  history.pushState = function () { origPush.apply(this, arguments); onNav(); };
  history.replaceState = function () { origReplace.apply(this, arguments); onNav(); };
  window.addEventListener("popstate", onNav);

  function onNav() {
    if (onPerfPageHide) onPerfPageHide();
    var prev = currentUrl;
    currentRef = prev;
    currentUrl = normalizeUrl(location.pathname + location.search);
    pageTag = detectPageTag();
    if (currentUrl !== prev) setTimeout(trackPageview, NAV_DELAY);
  }

  window.umami = {
    _rawTrack: function (name, data) {
      sendEvent(name, data);
    },
    track: function (name, data) {
      if (typeof name === "string") {
        if (typeof window.umamiTrack === "function") {
          window.umamiTrack(name, data);
        } else {
          sendEvent(name, data);
        }
      } else if (typeof name === "function") {
        send(name(basePayload()), "event");
      } else if (name && typeof name === "object") {
        send(Object.assign({}, basePayload(), name), "event");
      } else {
        trackPageview();
      }
    },
    identify: identify,
    getSession: function () {
      return { cache: cache, website: WEBSITE_ID, id: distinctId };
    }
  };

  function startTracking() {
    identify(distinctId, buildSessionData());
    trackPageview();
    initPerformance();
  }

  if (doc.readyState === "complete") {
    startTracking();
  } else {
    doc.addEventListener("readystatechange", function () {
      if (doc.readyState === "complete") startTracking();
    });
  }

  window.addEventListener("error", function (e) {
    sendEvent("js_error", {
      message: e.message,
      source: (e.filename || "").split("/").pop(),
      line: e.lineno
    });
  });
  window.addEventListener("unhandledrejection", function (e) {
    var reason = e.reason;
    sendEvent("js_error", {
      message: reason && reason.message ? reason.message : String(reason),
      source: "promise",
      line: 0
    });
  });

  function initPerformance() {
    if (!window.PerformanceObserver) return;

    var metrics = {};
    var sent = false;
    var timer;
    var activationStart = 0;
    var clsScore = 0;
    var clsEntries = [];
    var pageStart = performance.now();

    function observe(type, onEntry) {
      try {
        new PerformanceObserver(function (list) {
          list.getEntries().forEach(onEntry);
        }).observe({ type: type, buffered: true });
      } catch (_) {}
    }

    observe("navigation", function (e) {
      activationStart = e.activationStart || 0;
      metrics.ttfb = Math.max(e.responseStart - activationStart, 0);
    });
    observe("paint", function (e) {
      if (e.name === "first-contentful-paint") {
        metrics.fcp = Math.max(e.startTime - activationStart, 0);
      }
    });
    observe("largest-contentful-paint", function (e) {
      metrics.lcp = Math.max(e.startTime - activationStart, 0);
    });
    observe("layout-shift", function (e) {
      if (e.hadRecentInput) return;
      var last = clsEntries[clsEntries.length - 1];
      var first = clsEntries[0];
      if (last && e.startTime - last.startTime - last.duration < 1000 && e.startTime - first.startTime < 5000) {
        clsScore += e.value;
        clsEntries.push(e);
      } else {
        clsScore = e.value;
        clsEntries = [e];
      }
      if (clsScore > (metrics.cls || 0)) metrics.cls = clsScore;
    });

    try {
      var interactions = {};
      new PerformanceObserver(function (list) {
        list.getEntries().forEach(function (e) {
          if (!e.interactionId) return;
          var prev = interactions[e.interactionId];
          if (!prev || e.duration > prev) interactions[e.interactionId] = e.duration;
          var sorted = Object.values(interactions).sort(function (a, b) { return b - a; });
          if (sorted.length) {
            var idx = Math.floor(0.02 * Math.max(sorted.length, 10));
            metrics.inp = sorted[Math.min(idx, sorted.length - 1)];
          }
        });
      }).observe({ type: "event", buffered: true, durationThreshold: 40 });
    } catch (_) {}

    function flushPerformance() {
      if (sent) return;
      sent = true;
      if (timer) clearTimeout(timer);
      metrics.duration = Math.round(performance.now() - pageStart);
      var payload = basePayload();
      Object.keys(metrics).forEach(function (k) { payload[k] = metrics[k]; });
      send(payload, "performance");
    }

    function resetPerformance() {
      flushPerformance();
      sent = false;
      metrics = {};
      clsScore = 0;
      clsEntries = [];
      activationStart = 0;
      pageStart = performance.now();
      if (timer) clearTimeout(timer);
      timer = setTimeout(flushPerformance, 10000);
    }

    onPerfPageHide = resetPerformance;
    timer = setTimeout(flushPerformance, 10000);
    doc.addEventListener("visibilitychange", function () {
      if (doc.visibilityState === "hidden") flushPerformance();
    });
    window.addEventListener("pagehide", flushPerformance);
  }

  (function loadHelper() {
    var scripts = document.getElementsByTagName("script");
    var root = "/static/js/";
    for (var i = scripts.length - 1; i >= 0; i--) {
      var src = scripts[i].src || "";
      if (src.indexOf("umami-core.js") !== -1) {
        root = src.replace(/\/umami-core\.js(?:\?.*)?$/, "/");
        break;
      }
    }

    function loadScript(src, cb) {
      var s = document.createElement("script");
      s.defer = true;
      s.src = src;
      s.onload = function () { if (cb) cb(); };
      document.head.appendChild(s);
    }

    loadScript(root + "umami-labels.js", function () {
      loadScript(root + "umami-helper.js");
    });
  })();
})();
