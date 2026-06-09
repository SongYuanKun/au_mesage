/**
 * au_message — Umami 事件中文描述
 */
(function () {
  "use strict";

  var EVENT_LABELS = {
    nav_click: "导航点击",
    theme_toggle: "主题切换",
    unit_switch: "单位切换",
    calc_use: "计算器使用",
    alert_action: "价格提醒",
    chart_interact: "图表交互",
    scroll_depth: "滚动深度",
    page_exit: "页面离开",
    js_error: "JS 错误"
  };

  var UNIT_LABELS = {
    usd_oz: "美元/盎司",
    cny_g: "人民币/克"
  };

  var CALC_LABELS = {
    diff: "价差计算",
    pnl: "盈亏计算",
    breakeven: "保本计算",
    dca: "定投计算",
    dca_calculate: "定投试算"
  };

  var ALERT_LABELS = {
    subscribe: "订阅提醒",
    unsubscribe: "取消订阅"
  };

  function pick(map, key) {
    return map[key] || key || "";
  }

  function buildDesc(name, data) {
    data = data || {};
    var base = EVENT_LABELS[name] || name;
    var d = data;

    if (name === "nav_click") {
      return base + "：" + (d.label || d.page || "");
    }
    if (name === "theme_toggle") {
      return base + "：" + (d.from || "") + " → " + (d.to || "");
    }
    if (name === "unit_switch") {
      return base + "：" + pick(UNIT_LABELS, d.from) + " → " + pick(UNIT_LABELS, d.to);
    }
    if (name === "calc_use") {
      return base + "：" + pick(CALC_LABELS, d.tool) + (d.metal ? "（" + d.metal + "）" : "");
    }
    if (name === "alert_action") {
      return base + "：" + pick(ALERT_LABELS, d.action) + (d.metal ? "（" + d.metal + "）" : "");
    }
    if (name === "chart_interact") {
      return base + "：" + (d.metal || "") + " " + (d.type || "") + "=" + (d.value || "");
    }
    if (name === "scroll_depth") {
      return base + "：" + (d.depth != null ? d.depth + "%" : "");
    }
    if (name === "page_exit") {
      return base + "：停留 " + (d.duration != null ? Math.round(d.duration / 1000) + "s" : "");
    }
    if (name === "js_error") {
      return base + "：" + (d.message || "");
    }

    return base;
  }

  function enrich(name, data) {
    var props = Object.assign({}, data || {});
    if (!props.描述) {
      props.描述 = buildDesc(name, props);
    }
    return props;
  }

  window.umamiEnrich = enrich;
  window.umamiTrack = function (name, data) {
    try {
      if (typeof umami !== "undefined" && typeof umami.track === "function") {
        umami.track(name, enrich(name, data));
      }
    } catch (_) {}
  };
})();
