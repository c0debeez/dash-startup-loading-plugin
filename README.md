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
pip install "dash-startup-loading-plugin>=1.1.0"
```

Dash discovers the plugin through its `dash_hooks` entry point. Installing the
package enables the default loading overlay without an explicit import.

The default background colors work with native Dash, Dash Ant Design, and Dash Mantine Components.

## Quick start

The default configuration requires no plugin-specific code:

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

By default, the overlay only replaces Dash's built-in `._dash-loading`
animation and closes once Dash has rendered the initial application layout.
It does not wait for lazy or asynchronous children that render later.

Call `setup()` before creating `Dash` when custom behavior is needed:

```python
from dash import Dash, html
from dash_startup_loading_plugin import setup

setup(
    loader="wave",
    loader_color="#7950f2",
    loader_dark_color="#b197fc",
    timeout_ms=6000,
    minimum_display_ms=250,
    fade_duration_ms=180,
)

app = Dash(__name__)
app.layout = html.Main(
    [
        html.Header("Header"),
        html.Nav("Sidebar"),
    ]
)
```

### Theme behavior

With the default `theme_mode="auto"`, the startup overlay follows an explicit
application theme from, in order, the root HTML element (including Mantine's
`data-mantine-color-scheme`, Tailwind's `dark`/`light` classes, and common theme
data attributes), Mantine's stored color scheme, a persisted Dash theme
component, or conventional theme keys in local storage. If the
application has not declared a theme preference, the overlay uses the light
theme; it does not infer a preference from the operating system.

Set the mode explicitly when the application does not expose its preference,
or when the loading screen should always use one theme:

```python
setup(theme_mode="light")  # or "dark"
```

An application preference explicitly set to `"system"` or `"auto"` still
uses `prefers-color-scheme`.

## Dash Mantine Components

Dash Mantine Components is optional and needs no plugin configuration. When its
bundle is present, the overlay reads Mantine's HTML color scheme and saved
`mantine-color-scheme-value`, then uses Mantine's `--mantine-color-body` for
both light and dark backgrounds (`#fff` and `#242424` by default). It
also reads `MantineProvider(forceColorScheme="light" | "dark")` from a static
Dash layout before the first paint and follows a color-scheme attribute set
while the overlay is visible.

```python
from dash import Dash
import dash_mantine_components as dmc

app = Dash(__name__)
app.layout = dmc.MantineProvider(
    dmc.Text("Ready"),
    forceColorScheme="dark",
)
```

When `app.layout` is a function that chooses the scheme dynamically, its result
is not evaluated while the index is generated. Use `dmc.pre_render_color_scheme()`
for a saved/system preference, or `setup(theme_mode="dark")` for a fixed dark
first paint in that case.

## Dash Ant Design

Dash Ant Design is optional. The same `setup()` function configures native Dash
and Dash Ant Design applications. When its component bundle is detected and no
loader was explicitly configured, the plugin automatically uses the `antd`
loader with Ant Design blue. To match a customized theme, set the loader colors
explicitly:

```bash
pip install dash-ant-design
```

```python
from dash_startup_loading_plugin import setup

setup(background="#f5f5f5", dark_background="#202020", loader="antd")
```

## Dismissal behavior

The plugin observes Dash's standard `#react-entry-point`. The overlay closes
after that root no longer contains `._dash-loading`, contains rendered
content, and remains ready for two animation frames. These selectors are
implementation details rather than configuration options because the plugin
only replaces Dash's startup loader. It does not track application-specific
lazy or asynchronous components.

`timeout_ms` is a forced-dismiss fallback. `minimum_display_ms` applies to
ready and manual dismissal, but does not delay a timeout.

## Configuration

`setup(**changes)` updates the process-wide immutable
`StartupLoadingConfig`.

| Option | Default | Description |
|---|---:|---|
| `enabled` | `True` | Enable index injection. |
| `overlay_id` | `"dash-loading"` | Injected overlay ID. |
| `aria_label` | `"Loading"` | Accessible status label. |
| `timeout_ms` | `6000` | Forced-dismiss timeout; use `None` to disable. |
| `minimum_display_ms` | `0` | Minimum display time. |
| `fade_duration_ms` | `160` | Fade-out duration. |
| `z_index` | `9999` | Overlay stacking order. |
| `background` | `"#ffffff"` | Light background. |
| `dark_background` | `"#121212"` | Dark background. |
| `loader_color` | `None` | Optional loader color in light mode; uses the selected loader's default when unset. |
| `loader_dark_color` | `None` | Optional loader color in dark mode; uses the selected loader's default when unset. |
| `theme_mode` | `"auto"` | `"auto"` detects application theme signals and otherwise uses light; `"light"` and `"dark"` force a mode. |
| `loader` | `"default"` | The 1.0.4 single-border ring; automatically becomes `"antd"` when Dash Ant Design is detected unless explicitly set. |
| `loader_text` | `"Loading"` | Text rendered by `text-*` Loading UI loaders. |
| `spinner_size_px` | `12` | Target loader width and height: the default value `12` renders at 12px. It directly sizes the default, Ant Design, and inline SVG ring loaders, while Loading UI scales proportionally from its official 20px baseline. Only explicitly passing `None` uses the 20px baseline size. |
| `spinner_stroke_px` | `2` | Border and SVG stroke width for the default, inline ring, and applicable Loading UI loaders. |
| `custom_loader_html` | `None` | Trusted HTML replacing the default spinner. |

`custom_loader_html` is inserted verbatim and must never contain untrusted
user input.

The default loader uses version 1.0.4's single-border ring animation in a 12×12px content area, with a 2px border and 0.8-second rotation. Native Dash and Loading UI loaders default to black in light mode and white in dark mode. Dash Ant Design applications automatically use its four-dot loader and blue colors (`#1677ff` and `#4096ff`) unless the loader or colors were explicitly configured:

```python
setup(loader="antd")
```

Use `spinner_size_px`, `loader_color`, and `loader_dark_color` to match customized Spin theme tokens. Use `loader_text` to replace the default text in `text-*` loaders:

```python
setup(loader="text-shimmer", loader_text="Preparing dashboard")
```

The bundled [Loading UI](https://loading-ui.com/) collection supports all 47 loader names in the current upstream catalog:

```text
accordion-loader, analyzing-image, arc, bars, bobbing-dots, bouncing-dots, classic, clock-ring, comet-spinner, concentric-ring, conveyor-loop, dash-ring, diamond, dots, dots-ring, dual-arc, fade-arc, infinity, infinity-square-snake, infinity-track, morphing-infinity, orbit-ring, pulsating-dots, pulse, pulse-dot, quarter-ring, ring, ripple, satellite-ring, skeleton, spiral, spokes, square-accordion, square-grid, square-snake, swirling, symmetric-wave, terminal, text-blink, text-dots, text-shimmer, text-shimmer-wave, triple-dot-spinner, twin-orbit, typing, wandering-eyes, wave
```

For example:

```python
setup(loader="spiral", loader_color="#e91e63", loader_dark_color="#ff80ab")
```

`ring` uses an inline SVG; other Loading UI loaders use a bundled, isolated renderer loaded before Dash starts. No other indicator is shown while that renderer starts. Loading UI loaders sit in a centered 4:3 region that uses full width below 640px, half width from 640px, one-third from 768px, and one-quarter from 1024px. Each loader keeps the geometry from its official demo: square icons use their documented `size-*`, rectangular loaders keep their documented aspect ratio, and character-grid loaders derive intrinsic `ch`/`em` dimensions from their default props. Text loaders fit their text. The upstream components are MIT licensed; see [the bundled license](src/dash_startup_loading_plugin/resources/LOADING-UI-LICENSE.md).

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
- Resources are inlined, so strict Content Security Policy deployments must
  allow the injected style and script.
- The overlay is only for initial application startup. Use `dcc.Loading` or
  another callback-specific pattern for later callback execution.

## License

MIT
