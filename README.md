# dash-startup-loading-plugin

[English](https://github.com/C0deBeez/dash-startup-loading-plugin/blob/master/README.md) |
[简体中文](https://github.com/C0deBeez/dash-startup-loading-plugin/blob/master/README.zh-CN.md)

An installable [Dash Hooks plugin](https://dash.plotly.com/dash-plugins-using-hooks)
that replaces Dash's initial loading presentation with a configurable
full-screen overlay.

The plugin injects its CSS and JavaScript into Dash's normal index document
before React mounts. Applications do not need to copy assets or replace
`index_string`, and Dash's built-in `<div class="_dash-loading">` remains in the
document.

## Requirements

- Python 3.9 or later
- Dash 3.0.3 or later

## Installation

```bash
pip install "dash-startup-loading-plugin>=2.0.0"
```

Dash discovers the plugin through its `dash_hooks` entry point. Installing the
package enables the default loading overlay without an explicit import.

The default background colors work with native Dash and Dash Ant Design.

## Quick start

The plugin is discovered automatically, so a native Dash app needs no
plugin-specific code:

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

The example above uses Dash's native components from `dash.html`. You can also
use the plugin with `dash-antd-components`:

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
    dac.Title("My Dash Ant Design app", level=2),
    dac.Button("Continue", type="primary"),
    dac.Input(placeholder="Search"),
  ],
  orientation="vertical",
  size="middle",
)

if __name__ == "__main__":
  app.run(debug=True)
```

When the `dash-antd-components` bundle is present, the plugin automatically
uses Ant Design's four-dot loader unless `loader` is explicitly configured.
Native Dash apps use the Loading UI `ring` loader by default.

### Theme behavior

Theme initialization belongs to the application. Set `dark`/`light` on the
root HTML element before Dash mounts, for example in `index_string`; the
plugin's CSS follows `html.dark`. This avoids a theme flash without making the
plugin own application preferences or asynchronous theme callbacks.
Use `prefers-color-scheme` in that head script when the application follows the
operating system preference.

## Dash Ant Design

Dash Ant Design is optional. The same `setup()` function configures native Dash
and Dash Ant Design applications. When its component bundle is present and
`loader` was not explicitly configured, the plugin uses Ant Design's four-dot
loader and `colorPrimary` defaults. Other component libraries use Loading UI's
`ring` loader by default. Explicit loader and color options always take
precedence:

```bash
pip install dash-ant-design
```

```bash
uv add dash-ant-design
```

```python
from dash_startup_loading_plugin import setup

setup(loader="antd")
```

## Dismissal behavior

By default, the plugin preserves its original behavior: it observes Dash's
standard `#react-entry-point` and closes the overlay after Dash's
`._dash-loading` element disappears. Theme initialization and application
specific callback/layout settling belong in the application's `index_string`
and callbacks.

## Configuration

`setup(**changes)` updates the process-wide immutable
`StartupLoadingConfig`.

| Option | Default | Description |
| --- | ---: | --- |
| `enabled` | `True` | Enable index injection. |
| `aria_label` | `"Loading"` | Accessible status label. |
| `z_index` | `9999` | Overlay stacking order. |
| `loader_color` | `#1677ff` | Loader color in light mode. |
| `loader_dark_color` | `#1668dc` | Loader color in dark mode. |
| `loader_text_color` | `rgba(0,0,0,0.88)` | Text color for `text-*` Loading UI loaders in light mode. |
| `loader_dark_text_color` | `rgba(255,255,255,0.85)` | Text color for `text-*` Loading UI loaders in dark mode. |
| `loader` | `"default"` | Loading UI's `ring` animation. |
| `loader_text` | `"Loading"` | Text rendered by `text-*` Loading UI loaders. |
| `loader_size` | `64` | Target loader width and height. Loading UI uses its `ring` default of 4rem (64px); the `antd` loader uses Ant Design Spin's medium visual size of 20px. Other Loading UI loaders scale proportionally from their bundled default geometry. `None` uses the 64px baseline. |
| `loader_stroke_width` | `2` | Loading UI border and SVG stroke width, generated from its 2px default at the 64px ring baseline. |
| `custom_loader_html` | `None` | Trusted HTML replacing the default spinner. |

`custom_loader_html` is inserted verbatim and must never contain untrusted
user input.

The default loader uses Loading UI's `ring` animation. To use Ant Design's
four-dot loader, configure it explicitly:

```python
setup(loader="antd")
```

The overlay background follows the application's `html.dark` class and `--layout-bg` CSS variable, with `#f5f5f5` and `#111825` fallbacks. The plugin does not inspect ConfigProvider tokens. Explicit color options always take precedence. Use `loader_size`, `loader_color`, `loader_dark_color`, `loader_text_color`, and `loader_dark_text_color` to match a customized theme. Use `loader_text` to replace the default text in `text-*` loaders:

```python
setup(loader="text-shimmer", loader_text="Preparing dashboard")
```

## Loader gallery

The effective default depends on the component bundle:

| Application | Default loader | Notes |
| --- | --- | --- |
| Native Dash components | `ring` | Loading UI renderer. |
| `dash-antd-components` | `antd` | Ant Design's four-dot spinner. |
| Any app with an explicit `setup(loader=...)` | The selected loader | Explicit configuration always wins. |

All Loading UI loaders are bundled separately and loaded only when selected.
The preview images below link to the official interactive demos. Open a preview
to see its live animation and source details. The `text-*` loaders accept
custom text through `loader_text`; `loader_color`, `loader_dark_color`,
`loader_size`, and `loader_stroke_width` apply where supported.

| Preview | Preview | Preview |
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
| [![wandering-eyes](https://loading-ui.com/api/og/components/wandering-eyes/image.png)](https://loading-ui.com/docs/components/wandering-eyes)<br>`wandering-eyes` | [![wave](https://loading-ui.com/api/og/components/wave/image.png)](https://loading-ui.com/docs/components/wave)<br>`wave` | [Default: ring](https://loading-ui.com/docs/components/ring)<br>`default` |
| [Ant Design Spin](https://ant.design/components/spin)<br>`antd` |  |  |

The bundled [Loading UI](https://loading-ui.com/) collection supports all 47 loader names in the current upstream catalog:

```text
accordion-loader, analyzing-image, arc, bars, bobbing-dots, bouncing-dots, classic, clock-ring, comet-spinner, concentric-ring, conveyor-loop, dash-ring, diamond, dots, dots-ring, dual-arc, fade-arc, infinity, infinity-square-snake, infinity-track, morphing-infinity, orbit-ring, pulsating-dots, pulse, pulse-dot, quarter-ring, ring, ripple, satellite-ring, skeleton, spiral, spokes, square-accordion, square-grid, square-snake, swirling, symmetric-wave, terminal, text-blink, text-dots, text-shimmer, text-shimmer-wave, triple-dot-spinner, twin-orbit, typing, wandering-eyes, wave
```

For example:

```python
setup(loader="spiral", loader_color="#e91e63", loader_dark_color="#ff80ab")
```

The default loader, `ring`, and other Loading UI loaders use a bundled, isolated renderer loaded before Dash starts. Each loader ships as its own bundle, and the index only references the selected one at `<requests_pathname_prefix>_dash-startup-loading/<loader>.js`. That keeps the HTML document small and lets the browser cache the renderer, so the choice of loader does not grow the first-screen payload. No other indicator is shown while that renderer starts. Loading UI loaders sit in a centered 4:3 region that uses full width below 640px, half width from 640px, one-third from 768px, and one-quarter from 1024px. Each loader keeps the geometry from its official demo: square icons use their documented `size-*`, rectangular loaders keep their documented aspect ratio, and character-grid loaders derive intrinsic `ch`/`em` dimensions from their default props. Text loaders fit their text.

## Python API

```python
from dash_startup_loading_plugin import (
    StartupLoadingConfig,
    setup,
    get_config,
    reset_config,
)
```

## Notes

- Dash's hook and plugin configuration is process-wide. Use one configuration
  per process.
- Readiness gates apply only to startup. Later callbacks do not recreate the overlay.
- The overlay markup and its small startup runtime are inlined, so strict Content
  Security Policy deployments must allow the injected style and script. The
  Loading UI renderer is served from a plugin route instead of being inlined.
- The overlay is only for initial application startup. Use `dcc.Loading` or
  another callback-specific pattern for later callback execution.

## License

This project is distributed under the MIT License.

MIT
