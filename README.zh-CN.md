# dash-startup-loading-plugin

[English](https://github.com/C0deBeez/dash-startup-loading-plugin/blob/master/README.md) |
[简体中文](https://github.com/C0deBeez/dash-startup-loading-plugin/blob/master/README.zh-CN.md)

一个基于 [Dash Hooks 插件规范](https://dash.plotly.com/dash-plugins-using-hooks) 的可安装插件，用于替换 Dash 初始 loading 遮罩。

## 环境要求

- Python 3.9 或更高版本
- Dash 3.0.3 或更高版本

## 安装

```bash
pip install "dash-startup-loading-plugin>=2.0.0rc1"
```

Dash 会通过 `dash_hooks` entry point 自动发现插件，安装后默认 loading 遮罩会自动启用。

## 使用示例

### Dash 原生组件

插件会自动发现，无需额外注册：

```python
from dash import Dash, html

app = Dash(__name__)
app.layout = html.Main(
    [
        html.H1("我的 Dash 应用"),
        html.P("页面布局加载完成后，启动遮罩会自动关闭。"),
    ]
)

if __name__ == "__main__":
    app.run(debug=True)
```

### dash-antd-components

安装 PyPI 包 `dash-ant-design` 后，Python 中使用模块名
`dash_antd_components`：

```bash
pip install dash-ant-design
```

```bash
uv add dash-ant-design
```

```python
import dash_antd_components as dac
from dash import Dash

app = Dash(__name__)
app.layout = dac.Space(
    [
        dac.Title("我的 Dash Ant Design 应用", level=2),
        dac.Button("继续", type="primary"),
        dac.Input(placeholder="搜索"),
    ],
    orientation="vertical",
    size="middle",
)

if __name__ == "__main__":
    app.run(debug=True)
```

检测到 `dash-antd-components` bundle 后，如果没有显式设置 `loader`，插件会自动使用
Ant Design 四圆点 loader；Dash 原生组件默认使用 Loading UI 的 `ring` loader。

## 主题初始化

主题由应用负责。请在 `index_string` 中于 Dash 挂载前设置根节点的 `dark`/`light` class，并可使用 `prefers-color-scheme` 读取系统偏好。插件样式会跟随 `html.dark`，避免插件接管应用主题和异步 callback。

## Dash Ant Design

检测到 Dash Ant Design bundle 且没有显式设置 `loader` 时，插件使用 Ant Design 四圆点 loader；其他应用默认使用 Loading UI 的 `ring`。显式 loader 和颜色参数始终优先。

```bash
pip install dash-ant-design
```

```bash
uv add dash-ant-design
```

```python
from dash_startup_loading_plugin import setup

setup(loader="antd", loader_color="#1677ff")
```

也可以仅显式选择 Ant Design loader：

```python
setup(loader="antd")
```

## 配置项

| 参数 | 默认值 | 说明 |
| --- | ---: | --- |
| `enabled` | `True` | 是否注入 startup overlay。 |
| `aria_label` | `"Loading"` | 无障碍状态标签。 |
| `z_index` | `9999` | 遮罩层级。 |
| `loader_color` | `#1677ff` | loader 亮色颜色。 |
| `loader_dark_color` | `#1668dc` | loader 暗色颜色。 |
| `loader_text_color` | `rgba(0,0,0,0.88)` | `text-*` loader 亮色文字颜色。 |
| `loader_dark_text_color` | `rgba(255,255,255,0.85)` | `text-*` loader 暗色文字颜色。 |
| `loader` | `"default"` | 默认使用 Loading UI `ring`；Dash Ant Design 未显式配置时使用 `antd`。 |
| `loader_text` | `"Loading"` | `text-*` loader 的文字。 |
| `loader_size` | `64` | Loading UI 的目标尺寸；AntD loader 使用 Spin medium 的 20px 视觉尺寸。 |
| `loader_stroke_width` | `2` | Loading UI 边框和 SVG 描边宽度。 |
| `custom_loader_html` | `None` | 替换 loader 的可信 HTML。 |

`custom_loader_html` 会原样插入页面，禁止传入不可信用户输入。

遮罩背景跟随应用的 `html.dark` class 和 `--layout-bg` CSS 变量，默认亮色和暗色回退值分别为 `#f5f5f5`、`#111825`。插件不会读取 ConfigProvider token。

## Loading UI

除 `antd` 外的 Loading UI loader 会按需加载隔离 renderer。每个 loader 单独打包，页面只引用当前选中的那个（`<requests_pathname_prefix>_dash-startup-loading/<loader>.js`），因此 HTML 体积不受 loader 选择影响，且 renderer 可被浏览器长期缓存，不拖慢首屏。可用 `loader_text`、颜色参数和尺寸参数自定义 loader：

```python
setup(loader="text-shimmer", loader_text="正在准备仪表盘", loader_color="#1677ff")
```

## Loader 预览

实际默认 loader 取决于应用使用的组件 bundle：

| 应用 | 默认 loader | 说明 |
| --- | --- | --- |
| Dash 原生组件 | `ring` | Loading UI renderer。 |
| `dash-antd-components` | `antd` | Ant Design 四圆点 spinner。 |
| 显式调用 `setup(loader=...)` 的应用 | 选定的 loader | 显式配置始终优先。 |

所有 Loading UI loader 都单独打包，只在被选中时加载。下面的预览图链接到官方
交互式演示页面，点击图片即可查看动态效果和源码。`text-*` loader 支持通过
`loader_text` 自定义文字；`loader_color`、`loader_dark_color`、`loader_size` 和
`loader_stroke_width` 会在对应 loader 支持时生效。

| 预览 | 预览 | 预览 |
| --- | --- | --- |
| [![accordion-loader](https://loading-ui.com/api/og/components/accordion-loader/image.png)](https://loading-ui.com/docs/components/accordion-loader)<br>`accordion-loader` | [![analyzing-image](https://loading-ui.com/api/og/components/analyzing-image/image.png)](https://loading-ui.com/docs/components/analyzing-image)<br>`analyzing-image` | [![arc](https://loading-ui.com/api/og/components/arc/image.png)](https://loading-ui.com/docs/components/arc)<br>`arc` |
| [![bars](https://loading-ui.com/api/og/components/bars/image.png)](https://loading-ui.com/docs/components/bars)<br>`bars` | [![bobbing-dots](https://loading-ui.com/api/og/components/bobbing-dots/image.png)](https://loading-ui.com/docs/components/bobbing-dots)<br>`bobbing-dots` | [![bouncing-dots](https://loading-ui.com/api/og/components/bouncing-dots/image.png)](https://loading-ui.com/docs/components/bouncing-dots)<br>`bouncing-dots` |
| [![classic](https://loading-ui.com/api/og/components/classic/image.png)](https://loading-ui.com/docs/components/classic)<br>`classic` | [![clock-ring](https://loading-ui.com/api/og/components/clock-ring/image.png)](https://loading-ui.com/docs/components/clock-ring)<br>`clock-ring` | [![comet-spinner](https://loading-ui.com/api/og/components/comet-spinner/image.png)](https://loading-ui.com/docs/components/comet-spinner)<br>`comet-spinner` |
| [![concentric-ring](https://loading-ui.com/api/og/components/concentric-ring/image.png)](https://loading-ui.com/docs/components/concentric-ring)<br>`concentric-ring` | [![conveyor-loop](https://loading-ui.com/api/og/components/conveyor-loop/image.png)](https://loading-ui.com/docs/components/conveyor-loop)<br>`conveyor-loop` | [![dash-ring](https://loading-ui.com/api/og/components/dash-ring/image.png)](https://loading-ui.com/docs/components/dash-ring)<br>`dash-ring` |
| [![diamond](https://loading-ui.com/api/og/components/diamond/image.png)](https://loading-ui.com/docs/components/diamond)<br>`diamond` | [![dots](https://loading-ui.com/api/og/components/dots/image.png)](https://loading-ui.com/docs/components/dots)<br>`dots` | [![dots-ring](https://loading-ui.com/api/og/components/dots-ring/image.png)](https://loading-ui.com/docs/components/dots-ring)<br>`dots-ring` |
| [![dual-arc](https://loading-ui.com/api/og/components/dual-arc/image.png)](https://loading-ui.com/docs/components/dual-arc)<br>`dual-arc` | [![fade-arc](https://loading-ui.com/api/og/components/fade-arc/image.png)](https://loading-ui.com/docs/components/fade-arc)<br>`fade-arc` | [![infinity](https://loading-ui.com/api/og/components/infinity/image.png)](https://loading-ui.com/docs/components/infinity)<br>`infinity` |
| [![infinity-square-snake](https://loading-ui.com/api/og/components/infinity-square-snake/image.png)](https://loading-ui.com/docs/components/infinity-square-snake)<br>`infinity-square-snake` | [![infinity-track](https://loading-ui.com/api/og/components/infinity-track/image.png)](https://loading-ui.com/docs/components/infinity-track)<br>`infinity-track` | [![morphing-infinity](https://loading-ui.com/api/og/components/morphing-infinity/image.png)](https://loading-ui.com/docs/components/morphing-infinity)<br>`morphing-infinity` |
| [![orbit-ring](https://loading-ui.com/api/og/components/orbit-ring/image.png)](https://loading-ui.com/docs/components/orbit-ring)<br>`orbit-ring` | [![pulsating-dots](https://loading-ui.com/api/og/components/pulsating-dots/image.png)](https://loading-ui.com/docs/components/pulsating-dots)<br>`pulsating-dots` | [![pulse](https://loading-ui.com/api/og/components/pulse/image.png)](https://loading-ui.com/docs/components/pulse)<br>`pulse` |
| [![pulse-dot](https://loading-ui.com/api/og/components/pulse-dot/image.png)](https://loading-ui.com/docs/components/pulse-dot)<br>`pulse-dot` | [![quarter-ring](https://loading-ui.com/api/og/components/quarter-ring/image.png)](https://loading-ui.com/docs/components/quarter-ring)<br>`quarter-ring` | [![ring](https://loading-ui.com/api/og/components/ring/image.png)](https://loading-ui.com/docs/components/ring)<br>`ring` |
| [![ripple](https://loading-ui.com/api/og/components/ripple/image.png)](https://loading-ui.com/docs/components/ripple)<br>`ripple` | [![satellite-ring](https://loading-ui.com/api/og/components/satellite-ring/image.png)](https://loading-ui.com/docs/components/satellite-ring)<br>`satellite-ring` | [![skeleton](https://loading-ui.com/api/og/components/skeleton/image.png)](https://loading-ui.com/docs/components/skeleton)<br>`skeleton` |
| [![spiral](https://loading-ui.com/api/og/components/spiral/image.png)](https://loading-ui.com/docs/components/spiral)<br>`spiral` | [![spokes](https://loading-ui.com/api/og/components/spokes/image.png)](https://loading-ui.com/docs/components/spokes)<br>`spokes` | [![square-accordion](https://loading-ui.com/api/og/components/square-accordion/image.png)](https://loading-ui.com/docs/components/square-accordion)<br>`square-accordion` |
| [![square-grid](https://loading-ui.com/api/og/components/square-grid/image.png)](https://loading-ui.com/docs/components/square-grid)<br>`square-grid` | [![square-snake](https://loading-ui.com/api/og/components/square-snake/image.png)](https://loading-ui.com/docs/components/square-snake)<br>`square-snake` | [![swirling](https://loading-ui.com/api/og/components/swirling/image.png)](https://loading-ui.com/docs/components/swirling)<br>`swirling` |
| [![symmetric-wave](https://loading-ui.com/api/og/components/symmetric-wave/image.png)](https://loading-ui.com/docs/components/symmetric-wave)<br>`symmetric-wave` | [![terminal](https://loading-ui.com/api/og/components/terminal/image.png)](https://loading-ui.com/docs/components/terminal)<br>`terminal` | [![text-blink](https://loading-ui.com/api/og/components/text-blink/image.png)](https://loading-ui.com/docs/components/text-blink)<br>`text-blink` |
| [![text-dots](https://loading-ui.com/api/og/components/text-dots/image.png)](https://loading-ui.com/docs/components/text-dots)<br>`text-dots` | [![text-shimmer](https://loading-ui.com/api/og/components/text-shimmer/image.png)](https://loading-ui.com/docs/components/text-shimmer)<br>`text-shimmer` | [![text-shimmer-wave](https://loading-ui.com/api/og/components/text-shimmer-wave/image.png)](https://loading-ui.com/docs/components/text-shimmer-wave)<br>`text-shimmer-wave` |
| [![triple-dot-spinner](https://loading-ui.com/api/og/components/triple-dot-spinner/image.png)](https://loading-ui.com/docs/components/triple-dot-spinner)<br>`triple-dot-spinner` | [![twin-orbit](https://loading-ui.com/api/og/components/twin-orbit/image.png)](https://loading-ui.com/docs/components/twin-orbit)<br>`twin-orbit` | [![typing](https://loading-ui.com/api/og/components/typing/image.png)](https://loading-ui.com/docs/components/typing)<br>`typing` |
| [![wandering-eyes](https://loading-ui.com/api/og/components/wandering-eyes/image.png)](https://loading-ui.com/docs/components/wandering-eyes)<br>`wandering-eyes` | [![wave](https://loading-ui.com/api/og/components/wave/image.png)](https://loading-ui.com/docs/components/wave)<br>`wave` | [默认：ring](https://loading-ui.com/docs/components/ring)<br>`default` |
| [Ant Design Spin](https://ant.design/components/spin)<br>`antd` |  |  |

## 关闭时机

插件只观察 Dash 的 `#react-entry-point ._dash-loading` 生命周期：Dash 内置 loading 消失后移除 startup overlay。页面主题和应用特定的异步布局等待由应用自身处理。

## Python API

```python
from dash_startup_loading_plugin import (
    StartupLoadingConfig,
    setup,
    get_config,
    reset_config,
)
```

## License

本项目采用 MIT License。
