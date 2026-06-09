# Umami 接入说明 — au_message

> 域名：`au.songyuankun.top`  
> Website ID：`0a0f5b9f-b2ca-41a5-a1d0-4ef7a6bbaad3`  
> 采集服务：`https://umami.songyuankun.top`

## 文件结构

| 文件 | 作用 |
|------|------|
| `templates/_umami.html` | 官方 tracker + 业务脚本加载 |
| `static/js/umami-session.js` | 访客 ID、Session Data（主题/区域/单位） |
| `static/js/umami-labels.js` | 事件中文 `描述` |
| `static/js/umami-helper.js` | 业务事件委托 |
| `templates/_v2_head.html` | 全站 include `_umami.html` |

## 平台能力

- **访客识别**：`umami.visitor-id` + `umami.identify()`
- **Session Data**：`主题 / 区域 / 单位 / 回访 / 首访`
- **Performance**：Core Web Vitals（官方 `data-performance="true"`）
- **滚动深度 / 页面停留 / JS 错误**

## 自定义事件

| 事件名 | 场景 | Umami 查看位置 |
|--------|------|----------------|
| `nav_click` | 导航、页脚链接 | Events |
| `unit_switch` | USD/盎司 ↔ 人民币/克 | Events |
| `calc_use` | 计算器模式 / 定投试算 | Events |
| `alert_action` | 订阅 / 取消价格提醒 | Events |
| `chart_interact` | 图表时间范围 / 指标 | Events |
| `theme_toggle` | 主题切换 | Events |
| `scroll_depth` | 滚动 25/50/75/100% | Events |
| `page_exit` | 离开页面 | Events |
| `js_error` | JS / Promise 错误 | Events |

PV/UV 在 **Overview / Realtime**；Session Data 在 **Sessions** 详情。

## PRD 指标映射（§11.1）

| PRD 指标 | Umami 口径 |
|----------|------------|
| `uv_daily` | Overview → Unique visitors（按日） |
| `dau` | 当日有 PV 或任意自定义事件的独立访客 |
| `alert_create_rate` | `alert_action`（action=subscribe）独立访客 ÷ `/` PV 独立访客 |
| `calculator_use_rate` | `calc_use` 独立访客 ÷ `/` PV 独立访客 |
| `export_use_rate` | `export_use` 独立访客 ÷ `/history` PV 独立访客（P1，待导出功能上线） |

在 Umami **Reports → Funnel** 或导出 CSV 后按事件名聚合即可计算比率。

## 调试

```js
// 禁用采集
localStorage.setItem('umami.disabled', '1')

// 恢复
localStorage.removeItem('umami.disabled')

// 手动验证
window.umami.track('nav_click', { page: 'test', label: '调试' })
```

Network 面板应看到 `POST https://umami.songyuankun.top/api/send` 返回 200。

## 部署注意

修改 `_umami.html` 或 `static/js/umami-*.js` 后需重建 Docker 镜像（`docker compose up --build -d`）。
