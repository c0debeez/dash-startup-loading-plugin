# dash-startup-loading-plugin

[English](https://github.com/C0deBeez/dash-startup-loading-plugin/blob/master/README.md) |
[简体中文](https://github.com/C0deBeez/dash-startup-loading-plugin/blob/master/README.zh-CN.md)

一个基于 [Dash Hooks 插件规范](https://dash.plotly.com/dash-plugins-using-hooks)
的可安装插件，用于将 Dash 初始加载提示替换为可配置的全屏 loading 遮罩。

插件会在 React 挂载前，将 CSS 和 JavaScript 注入 Dash 的标准 index
文档。应用无需复制 assets，也无需替换 `index_string`。Dash 自带的
`<div class="_dash-loading">` 节点仍会保留。

## 环境要求

- Python 3.9 或更高版本
- Dash 3.0.3 或更高版本

## 安装

```bash
pip install "dash-startup-loading-plugin>=1.1.0"
```

Dash 会通过 `dash_hooks` entry point 自动发现插件。安装后，默认 loading
效果会自动启用，无需在应用中显式导入。

默认背景颜色同时适用于原生 Dash 和 Dash Ant Design。

## 快速开始

默认配置无需编写插件相关代码：

```python
from dash import Dash, html

app = Dash(__name__)
app.layout = html.Main(
    [
        html.H1("My Dash app"),
        html.P("The overlay closes after this layout is ready."),
    ]
)

if __name__ == "__main__":
    app.run(debug=True)
```

默认情况下，遮罩只替换 Dash 自带的 `._dash-loading` 动画，并在 Dash
渲染出应用布局后关闭。等待懒加载或异步组件的占位节点消失属于可选行为。

如需自定义行为，请在创建 `Dash` 实例前调用 `setup()`：

```python
from dash import Dash, html
from dash_startup_loading_plugin import setup

setup(
    required_selectors=["#header", "#sidebar-menu"],
    pending_selector="[data-async-placeholder]",
    timeout_ms=6000,
    minimum_display_ms=250,
    fade_duration_ms=180,
)

app = Dash(__name__)
app.layout = html.Main(
    [
        html.Header("Header", id="header"),
        html.Nav("Sidebar", id="sidebar-menu"),
    ]
)
```

### 主题行为

默认的 `theme_mode="auto"` 会按顺序读取应用显式提供的主题：HTML 根节点
（包括 Tailwind 的 `dark`/`light` 类及常见主题 data 属性）、Dash 组件的
持久化主题值，以及 local storage 中的常见主题键。如果应用没有声明主题
偏好，loading 遮罩会使用亮色主题，不会根据操作系统配色自动推断。

当应用没有暴露主题偏好，或 loading 页面需要固定主题时，可手动配置：

```python
setup(theme_mode="light")  # 或 "dark"
```

如果应用主题偏好明确设置为 `"system"` 或 `"auto"`，插件仍会读取
`prefers-color-scheme`。当页面中存在多个持久化主题值时，可用
`dash_theme_component_id` 指定优先读取的 Dash 组件：

```python
setup(theme_mode="auto", dash_theme_component_id="theme-provider")
```

## Dash Ant Design

Dash Ant Design 是可选组件库。原生 Dash 和 Dash Ant Design 应用均使用
`setup()` 配置。若应用自定义了 Ant Design 主题，可显式设置遮罩颜色：

```bash
pip install dash-ant-design
```

```python
from dash_startup_loading_plugin import setup

setup(background="#f5f5f5", dark_background="#202020", loader="antd")
```

## 内置示例

安装包中包含两个可直接运行的示例：

```bash
# Dash
dash-startup-loading-plugin examples.dash

# Dash Ant Design
dash-startup-loading-plugin examples.dash-ant-design

```

组件库需要单独安装。如果所选示例无法导入对应组件库，命令会显示导入失败的
模块和安装命令。

所有示例都支持服务器参数：

```bash
dash-startup-loading-plugin examples.dash \
    --host 127.0.0.1 --port 8050 --debug
```

## 就绪判断

满足以下条件后，遮罩会关闭：

1. `root_selector` 已存在，且内部不再包含 `._dash-loading`。
2. 根节点中已有实际渲染内容。
3. `required_selectors` 中的所有选择器都已匹配到节点。
4. 如果配置了 `pending_selector`，根节点中已不存在匹配它的节点。
5. 上述状态连续保持两个动画帧。

`timeout_ms` 是强制关闭的安全兜底。`minimum_display_ms` 适用于正常就绪和
手动关闭，但不会延迟 timeout。

`pending_selector` 可用于在异步或懒加载占位节点仍存在时延迟关闭遮罩。它只会
在 `root_selector` 内查找匹配节点。该检查默认关闭；如需等待异步组件加载完成，
请显式设置为应用自己的 CSS 选择器：

```python
setup(pending_selector="[data-async-placeholder]")
setup(pending_selector=None)
```

## 配置项

`setup(**changes)` 会更新进程级、不可变的 `StartupLoadingConfig`。

| 参数 | 默认值 | 说明 |
|---|---:|---|
| `enabled` | `True` | 是否启用 index 注入。 |
| `overlay_id` | `"dash-loading"` | 注入遮罩的 ID。 |
| `aria_label` | `"Loading"` | 无障碍状态标签。 |
| `root_selector` | `"#react-entry-point"` | 用于观察渲染内容的根节点。 |
| `required_selectors` | `("#react-entry-point",)` | 关闭遮罩前必须存在的节点选择器。 |
| `pending_selector` | `None` | 可选的根节点内选择器；配置后，所有匹配节点消失才允许关闭。 |
| `timeout_ms` | `6000` | 强制关闭超时；设置为 `None` 可禁用。 |
| `minimum_display_ms` | `0` | 最短显示时间。 |
| `fade_duration_ms` | `160` | 淡出时长。 |
| `z_index` | `9999` | 遮罩层级。 |
| `background` | `"#ffffff"` | 亮色背景。 |
| `dark_background` | `"#121212"` | 暗色背景。 |
| `color` | `None` | 可选亮色 loader 颜色；未设置时使用所选 loader 的默认颜色。 |
| `dark_color` | `None` | 可选暗色 loader 颜色；未设置时使用所选 loader 的默认颜色。 |
| `loader_color` | `None` | 亮色模式下的 loader 颜色；未指定时使用 `color`。 |
| `loader_dark_color` | `None` | 暗色模式下的 loader 颜色；未指定时使用 `dark_color`。 |
| `theme_mode` | `"auto"` | `"auto"` 自动检测应用主题，未检测到时使用亮色；`"light"` 和 `"dark"` 用于强制指定主题。 |
| `dash_theme_component_id` | `None` | 优先读取主题状态的 Dash 持久化组件 ID。 |
| `loader` | `"antd"` | Ant Design 四圆点指示器，或 Loading UI 的任一 loader 名称。 |
| `spinner_size_px` | `28` | loader 的宽高，默认 28px，与 1.0.4 版本一致；传入 `None` 也使用 28px。 |
| `spinner_stroke_px` | `2` | SVG ring 的描边宽度。 |
| `hide_default_loading` | `True` | 遮罩存在时隐藏 `._dash-loading` 的视觉效果。 |
| `custom_loader_html` | `None` | 替换默认 spinner 的可信 HTML。 |

`custom_loader_html` 会原样插入页面，禁止传入任何不可信的用户输入。

默认的 `antd` loader 使用 Ant Design Spin 的四圆点动画和默认蓝色（亮色 `#1677ff`、暗色 `#4096ff`）。如需显式指定：

```python
setup(loader="antd")
```

可用 `spinner_size_px`、`loader_color` 和 `loader_dark_color` 调整尺寸及配色，以匹配应用自定义的 Spin 主题。Loading UI loader 在亮暗模式下使用与 `antd` 相同的默认蓝色。

内置的 [Loading UI](https://loading-ui.com/) 集合支持当前上游目录中的全部 47 个 loader 名称：

```text
accordion-loader, analyzing-image, arc, bars, bobbing-dots, bouncing-dots, classic, clock-ring, comet-spinner, concentric-ring, conveyor-loop, dash-ring, diamond, dots, dots-ring, dual-arc, fade-arc, infinity, infinity-square-snake, infinity-track, morphing-infinity, orbit-ring, pulsating-dots, pulse, pulse-dot, quarter-ring, ring, ripple, satellite-ring, skeleton, spiral, spokes, square-accordion, square-grid, square-snake, swirling, symmetric-wave, terminal, text-blink, text-dots, text-shimmer, text-shimmer-wave, triple-dot-spinner, twin-orbit, typing, wandering-eyes, wave
```

例如：

```python
setup(loader="spiral", loader_color="#e91e63", loader_dark_color="#ff80ab")
```

`ring` 使用内联 SVG；其他 Loading UI loader 使用在 Dash 启动前加载、隔离渲染的内置资源。渲染开始前不会显示其他指示器。 Loading UI loader 位于居中的 4:3 区域：640px 以下占全宽，640px 起占半宽，768px 起占三分之一，1024px 起占四分之一。图标类 loader 在区域内默认保持 28px；文字类 loader 根据文字调整宽度。上游组件采用 MIT 许可；参见[打包的许可文件](src/dash_startup_loading_plugin/resources/LOADING-UI-LICENSE.md)。

## Python API

```python
from dash_startup_loading_plugin import (
    StartupLoadingConfig,
    setup,
    get_config,
    reset_config,
)
```

## 浏览器 API

```javascript
// 重新检查就绪条件。
window.dashLoading.check();

// 关闭默认或指定遮罩。
window.dashLoading.finish();
window.dashLoading.finish("my-loading-overlay");
```

淡出前，遮罩会触发可冒泡的 `dash-loading:ready` 事件。
`event.detail.reason` 为 `"ready"`、`"timeout"` 或 `"manual"`。

```javascript
document.addEventListener("dash-loading:ready", function (event) {
    console.log(event.detail.reason);
});
```

## 注意事项

- Dash hooks 和插件配置是进程级的，同一进程应共用一套配置。
- 资源以内联方式注入；严格 CSP 部署需要允许相应的 style 和 script。
- 本插件只处理应用初始启动。后续 callback loading 请使用 `dcc.Loading`
  或其他针对 callback 的方案。

## License

MIT
