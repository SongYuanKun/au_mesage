/**
 * au_message — Umami 自定义事件埋点
 * 零依赖，事件委托模式，不侵入业务代码
 */
(function () {
  'use strict';

  function track(name, props) {
    try {
      if (typeof umami !== 'undefined' && typeof umami.track === 'function') {
        umami.track(name, props);
      }
    } catch (e) {}
  }

  function attr(el, name) {
    if (!el) return '';
    return el.getAttribute(name) || '';
  }

  // 导航点击
  document.addEventListener('click', function (e) {
    var link = e.target.closest('a[data-page]');
    if (link) {
      track('nav_click', {
        page: attr(link, 'data-page'),
        label: link.textContent.trim().slice(0, 50)
      });
    }
  });

  // 单位切换
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('[data-au-unit]');
    if (btn) {
      var active = document.querySelector('[data-au-unit].active');
      var from = active ? attr(active, 'data-au-unit') : '';
      var to = attr(btn, 'data-au-unit');
      if (from && to && from !== to) {
        track('unit_switch', { from: from, to: to });
      }
    }
  });

  // 计算器使用
  document.addEventListener('click', function (e) {
    var modeBtn = e.target.closest('[data-calc-mode]');
    if (modeBtn) {
      var metalTab = document.querySelector('.calc-mode-panel .type-tab.active');
      track('calc_use', {
        tool: attr(modeBtn, 'data-calc-mode'),
        metal: metalTab ? metalTab.textContent.trim().replace(/\s+/g, '') : ''
      });
    }
    if (e.target.closest('#btnDcaCalc')) {
      var metalTab2 = document.querySelector('.calc-mode-panel .type-tab.active');
      track('calc_use', {
        tool: 'dca_calculate',
        metal: metalTab2 ? metalTab2.textContent.trim().replace(/\s+/g, '') : ''
      });
    }
  });

  // 价格提醒
  document.addEventListener('click', function (e) {
    var action = null;
    if (e.target.closest('#btnSubscribe')) action = 'subscribe';
    if (e.target.closest('#btnUnsubscribe')) action = 'unsubscribe';
    if (action) {
      var metalTab = document.querySelector('[data-alert-type].active');
      track('alert_action', {
        action: action,
        metal: metalTab ? metalTab.textContent.trim().replace(/\s+/g, '') : ''
      });
    }
  });

  // 图表交互
  document.addEventListener('click', function (e) {
    var rangeTab = e.target.closest('.range-tab');
    if (rangeTab) {
      track('chart_interact', {
        metal: (document.querySelector('[data-metal].active') || {}).textContent || '',
        type: 'range',
        value: rangeTab.textContent.trim()
      });
    }
    var indBtn = e.target.closest('[data-ind]');
    if (indBtn) {
      track('chart_interact', {
        metal: (document.querySelector('[data-metal].active') || {}).textContent || '',
        type: 'indicator',
        value: attr(indBtn, 'data-ind')
      });
    }
  });

  // 主题切换
  document.addEventListener('click', function (e) {
    if (e.target.closest('#themeToggle')) {
      var current = document.documentElement.getAttribute('data-theme') || 'dark';
      var next = current === 'dark' ? 'light' : 'dark';
      track('theme_toggle', { from: current, to: next });
    }
  });
})();
