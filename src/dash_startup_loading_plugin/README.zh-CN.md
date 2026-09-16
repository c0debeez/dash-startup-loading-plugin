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

默认背景颜色同时适用于原生 Dash、Dash Ant Design 和 Dash Mantine Components。

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

### 主题行为

默认的 `theme_mode="auto"` 会按顺序读取应用显式提供的主题：HTML 根节点
（包括 Mantine 的 `data-mantine-color-scheme`、Tailwind 的 `dark`/`light` 类及常见主题 data 属性）、Mantine 保存的配色、Dash 组件的
持久化主题值，以及 local storage 中的常见主题键。如果应用没有声明主题
偏好，loading 遮罩会使用亮色主题，不会根据操作系统配色自动推断。

当应用没有暴露主题偏好，或 loading 页面需要固定主题时，可手动配置：

```python
setup(theme_mode="light")  # 或 "dark"
```

如果应用主题偏好明确设置为 `"system"` 或 `"auto"`，插件仍会读取
`prefers-color-scheme`。

## Dash Mantine Components

Dash Mantine Components 是可选组件库，插件无需额外配置。检测到 DMC 资源后，
遮罩会读取 Mantine 的 HTML 配色属性和已保存的 `mantine-color-scheme-value`，
亮暗背景均使用 Mantine 的 `--mantine-color-body`（默认分别为 `#fff` 和
`#242424`）；静态 Dash 布局中的
`MantineProvider(forceColorScheme="light" | "dark")` 会在首屏绘制前读取，
遮罩显示期间也会跟随 HTML 配色属性变化。

```python
from dash import Dash
import dash_mantine_components as dmc

app = Dash(__name__)
app.layout = dmc.MantineProvider(
    dmc.Text("Ready"),
    forceColorScheme="dark",
)
```

如果 `app.layout` 是动态决定配色的函数，插件生成首页时不会执行该函数。
此时可用 `dmc.pre_render_color_scheme()` 恢复已保存或系统偏好，固定暗色首屏则用
`setup(theme_mode="dark")`。

## Dash Ant Design

Dash Ant Design 是可选组件库。原生 Dash 和 Dash Ant Design 应用均使用
`setup()` 配置。检测到其组件资源且没有显式配置 loader 时，插件自动使用
`antd` loader 和 Ant Design 蓝色。若应用自定义了主题，可显式设置 loader 颜色：

```bash
pip install dash-ant-design
```

```python
from dash_startup_loading_plugin import setup

setup(background="#f5f5f5", dark_background="#202020", loader="antd")
```

## 关闭时机

插件观察 Dash 标准的 `#react-entry-point`，其中的 `._dash-loading`
消失后立即关闭遮罩。Dash 会在初始化期间维护该节点，并在 hydration 完成时
用应用布局替换它。如果 Dash 一直处于 loading 状态，配置的 loader 也会一直
显示；插件不再设置超时、最短显示时间或淡出时长。

## 配置项

`setup(**changes)` 会更新进程级、不可变的 `StartupLoadingConfig`。

| 参数 | 默认值 | 说明 |
|---|---:|---|
| `enabled` | `True` | 是否启用 index 注入。 |
| `aria_label` | `"Loading"` | 无障碍状态标签。 |
| `z_index` | `9999` | 遮罩层级。 |
| `background` | `"#ffffff"` | 亮色背景。 |
| `dark_background` | `"#121212"` | 暗色背景。 |
| `loader_color` | `None` | 亮色模式下的 loader 颜色；未设置时使用所选 loader 的默认颜色。 |
| `loader_dark_color` | `None` | 暗色模式下的 loader 颜色；未设置时使用所选 loader 的默认颜色。 |
| `theme_mode` | `"auto"` | `"auto"` 自动检测应用主题，未检测到时使用亮色；`"light"` 和 `"dark"` 用于强制指定主题。 |
| `loader` | `"default"` | 1.0.4 版本的单边框圆环；检测到 Dash Ant Design 时自动改用 `"antd"`，显式设置后不再自动切换。 |
| `loader_text` | `"Loading"` | `text-*` Loading UI loader 显示的文字。 |
| `loader_size` | `12` | loader 的目标宽高。默认 loader 和内联 SVG ring 渲染为 12px；Ant Design 在内部固定应用 20/12 的缩放比例，因此新的 12px 基准与原来 20px 的视觉大小一致，其他显式尺寸也按该基准同比缩放。Loading UI 从官方 20px 基准等比缩放，传入 `None` 使用该基准。 |
| `loader_stroke_width` | `2` | 默认圆环、内联 ring 以及适用的 Loading UI loader 的边框和 SVG 描边宽度。 |
| `custom_loader_html` | `None` | 替换默认 spinner 的可信 HTML。 |

`custom_loader_html` 会原样插入页面，禁止传入任何不可信的用户输入。

默认 loader 沿用 1.0.4 版本的单边框圆环动画，内容区域为 12×12px，边框为 2px，旋转周期为 0.8 秒。原生 Dash 和 Loading UI loader 默认在亮色模式使用黑色、暗色模式使用白色；Dash Ant Design 应用在没有显式配置时自动使用四圆点 loader 和蓝色（`#1677ff`、`#4096ff`）：

```python
setup(loader="antd")
```

可用 `loader_size`、`loader_color` 和 `loader_dark_color` 调整尺寸及配色，以匹配应用自定义的 Spin 主题。可用 `loader_text` 替换 `text-*` loader 的默认文字：

```python
setup(loader="text-shimmer", loader_text="正在准备仪表盘")
```

内置的 [Loading UI](https://loading-ui.com/) 集合支持当前上游目录中的全部 47 个 loader 名称：

```text
accordion-loader, analyzing-image, arc, bars, bobbing-dots, bouncing-dots, classic, clock-ring, comet-spinner, concentric-ring, conveyor-loop, dash-ring, diamond, dots, dots-ring, dual-arc, fade-arc, infinity, infinity-square-snake, infinity-track, morphing-infinity, orbit-ring, pulsating-dots, pulse, pulse-dot, quarter-ring, ring, ripple, satellite-ring, skeleton, spiral, spokes, square-accordion, square-grid, square-snake, swirling, symmetric-wave, terminal, text-blink, text-dots, text-shimmer, text-shimmer-wave, triple-dot-spinner, twin-orbit, typing, wandering-eyes, wave
```

例如：

```python
setup(loader="spiral", loader_color="#e91e63", loader_dark_color="#ff80ab")
```

`ring` 使用内联 SVG；其他 Loading UI loader 使用在 Dash 启动前加载、隔离渲染的内置资源。渲染开始前不会显示其他指示器。Loading UI loader 位于居中的 4:3 区域：640px 以下占全宽，640px 起占半宽，768px 起占三分之一，1024px 起占四分之一。每个 loader 均保留官方示例的尺寸规则：正方形图标使用文档中的 `size-*`，矩形 loader 保留官方宽高比，字符网格 loader 根据默认 props 计算固有的 `ch`/`em` 尺寸；文字类 loader 根据文字调整宽度。上游组件采用 MIT 许可；参见[打包的许可文件](src/dash_startup_loading_plugin/resources/LOADING-UI-LICENSE.md)。

## Python API

```python
from dash_startup_loading_plugin import (
    StartupLoadingConfig,
    setup,
    get_config,
    reset_config,
)
```

## 注意事项

- Dash hooks 和插件配置是进程级的，同一进程应共用一套配置。
- 资源以内联方式注入；严格 CSP 部署需要允许相应的 style 和 script。
- 本插件只处理应用初始启动。后续 callback loading 请使用 `dcc.Loading`
  或其他针对 callback 的方案。

## License

MIT
