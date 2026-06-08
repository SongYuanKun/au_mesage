# Umami 接入说明 — au_message

> 域名：`au.songyuankun.top`  
> Website ID：`0a0f5b9f-b2ca-41a5-a1d0-4ef7a6bbaad3`  
> 采集服务：`https://umami.songyuankun.top`

## 文件结构

| 文件 | 作用 |
|------|------|
| `static/js/umami-core.js` | 核心 tracker：PV/UV、identify、Performance |
| `static/js/umami-labels.js` | 事件中文 `描述` |
| `static/js/umami-helper.js` | 业务事件委托 |
| `templates/_nav.html` | 全站加载 `umami-core.js` |

## 平台能力

- **访客识别**：`umami.visitor-id` + `identify()`
- **Session Data**：`主题 / 区域 / 单位 / 回访 / 首访`
- **Tag**：`index / history / analysis`
- **Performance**：Core Web Vitals
- **滚动深度 / 页面停留 / JS 错误**

## 自定义事件

| 事件名 | 场景 |
|--------|------|
| `nav_click` | 导航、页脚链接 |
| `unit_switch` | USD/盎司 ↔ 人民币/克 |
| `calc_use` | 计算器模式 / 定投试算 |
| `alert_action` | 订阅 / 取消价格提醒 |
| `chart_interact` | 图表时间范围 / 指标 |
| `theme_toggle` | 主题切换 |
| `scroll_depth` | 滚动 25/50/75/100% |
| `page_exit` | 离开页面 |
| `js_error` | JS / Promise 错误 |

## 调试

```js
localStorage.setItem('umami.disabled', '1')
```
