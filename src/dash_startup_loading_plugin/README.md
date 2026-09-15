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

The default background colors work with native Dash and Dash Ant Design.

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
animation and closes once Dash has rendered the application layout. Waiting
for lazy or asynchronous component placeholders is opt-in.

Call `setup()` before creating `Dash` when custom behavior is needed:

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

### Theme behavior

With the default `theme_mode="auto"`, the startup overlay follows an explicit
application theme from, in order, the root HTML element (including Tailwind's
`dark`/`light` classes and common theme data attributes), a persisted Dash
theme component, or conventional theme keys in local storage. If the
application has not declared a theme preference, the overlay uses the light
theme; it does not infer a preference from the operating system.

Set the mode explicitly when the application does not expose its preference,
or when the loading screen should always use one theme:

```python
setup(theme_mode="light")  # or "dark"
```

An application preference explicitly set to `"system"` or `"auto"` still
uses `prefers-color-scheme`. Use `dash_theme_component_id` to prefer one Dash
component when multiple persisted theme values exist:

```python
setup(theme_mode="auto", dash_theme_component_id="theme-provider")
```

## Dash Ant Design

Dash Ant Design is optional. The same `setup()` function configures native Dash
and Dash Ant Design applications. To match a customized Ant Design theme, set
the overlay colors explicitly:

```bash
pip install dash-ant-design
```

```python
from dash_startup_loading_plugin import setup

setup(background="#f5f5f5", dark_background="#202020", loader="antd")
```

## Installed examples

The package includes two runnable examples:

```bash
# Dash
dash-startup-loading-plugin examples.dash

# Dash Ant Design
dash-startup-loading-plugin examples.dash-ant-design

```

Install the selected example's component library separately. If it cannot be
imported, the command reports the failed module and the corresponding
installation command.

Server options are available on every example:

```bash
dash-startup-loading-plugin examples.dash \
    --host 127.0.0.1 --port 8050 --debug
```

## Readiness behavior

The overlay closes when:

1. `root_selector` exists and no longer contains `._dash-loading`.
2. The root contains rendered content.
3. Every `required_selectors` entry exists.
4. If `pending_selector` is configured, no matching node remains under the root.
5. The conditions remain true for two animation frames.

`timeout_ms` is a forced-dismiss fallback. `minimum_display_ms` applies to
ready and manual dismissal, but does not delay a timeout.

`pending_selector` optionally delays dismissal while any matching element
remains inside `root_selector`. It is useful for lazy or asynchronous
placeholders that are mounted before the real content. The check is disabled
by default; opt in with an application-specific CSS selector:

```python
setup(pending_selector="[data-async-placeholder]")
setup(pending_selector=None)
```

## Configuration

`setup(**changes)` updates the process-wide immutable
`StartupLoadingConfig`.

| Option | Default | Description |
|---|---:|---|
| `enabled` | `True` | Enable index injection. |
| `overlay_id` | `"dash-loading"` | Injected overlay ID. |
| `aria_label` | `"Loading"` | Accessible status label. |
| `root_selector` | `"#react-entry-point"` | Root observed for rendered content. |
| `required_selectors` | `("#react-entry-point",)` | Selectors that must exist before dismissal. |
| `pending_selector` | `None` | Optional selector checked under `root_selector`; when configured, dismissal waits until all matches disappear. |
| `timeout_ms` | `6000` | Forced-dismiss timeout; use `None` to disable. |
| `minimum_display_ms` | `0` | Minimum display time. |
| `fade_duration_ms` | `160` | Fade-out duration. |
| `z_index` | `9999` | Overlay stacking order. |
| `background` | `"#ffffff"` | Light background. |
| `dark_background` | `"#121212"` | Dark background. |
| `color` | `None` | Optional light loader color; uses the selected loader's default when unset. |
| `dark_color` | `None` | Optional dark loader color; uses the selected loader's default when unset. |
| `loader_color` | `None` | Optional loader color in light mode; falls back to `color`. |
| `loader_dark_color` | `None` | Optional loader color in dark mode; falls back to `dark_color`. |
| `theme_mode` | `"auto"` | `"auto"` detects application theme signals and otherwise uses light; `"light"` and `"dark"` force a mode. |
| `dash_theme_component_id` | `None` | Preferred persisted Dash theme component. |
| `loader` | `"antd"` | Ant Design four-dot indicator, or any Loading UI loader name. |
| `spinner_size_px` | `28` | Loader width and height in pixels, matching version 1.0.4. Passing `None` also uses 28px. |
| `spinner_stroke_px` | `2` | SVG ring stroke width. |
| `hide_default_loading` | `True` | Hide the visual `._dash-loading` indicator while the overlay exists. |
| `custom_loader_html` | `None` | Trusted HTML replacing the default spinner. |

`custom_loader_html` is inserted verbatim and must never contain untrusted
user input.

The default `antd` loader uses Ant Design Spin's four-dot animation and its default blue colors (`#1677ff` in light mode, `#4096ff` in dark mode). To select it explicitly:

```python
setup(loader="antd")
```

Use `spinner_size_px`, `loader_color`, and `loader_dark_color` to match customized Spin theme tokens. Loading UI loaders use the same default blue colors as `antd` in both modes.

The bundled [Loading UI](https://loading-ui.com/) collection supports all 47 loader names in the current upstream catalog:

```text
accordion-loader, analyzing-image, arc, bars, bobbing-dots, bouncing-dots, classic, clock-ring, comet-spinner, concentric-ring, conveyor-loop, dash-ring, diamond, dots, dots-ring, dual-arc, fade-arc, infinity, infinity-square-snake, infinity-track, morphing-infinity, orbit-ring, pulsating-dots, pulse, pulse-dot, quarter-ring, ring, ripple, satellite-ring, skeleton, spiral, spokes, square-accordion, square-grid, square-snake, swirling, symmetric-wave, terminal, text-blink, text-dots, text-shimmer, text-shimmer-wave, triple-dot-spinner, twin-orbit, typing, wandering-eyes, wave
```

For example:

```python
setup(loader="spiral", loader_color="#e91e63", loader_dark_color="#ff80ab")
```

`ring` uses an inline SVG; other Loading UI loaders use a bundled, isolated renderer loaded before Dash starts. No other indicator is shown while that renderer starts. Loading UI loaders sit in a centered 4:3 region that uses full width below 640px, half width from 640px, one-third from 768px, and one-quarter from 1024px. Icon loaders stay 28px by default within that region; text loaders fit their text. The upstream components are MIT licensed; see [the bundled license](src/dash_startup_loading_plugin/resources/LOADING-UI-LICENSE.md).

## Python API

```python
from dash_startup_loading_plugin import (
    StartupLoadingConfig,
    setup,
    get_config,
    reset_config,
)
```

## Browser API

```javascript
// Recheck readiness.
window.dashLoading.check();

// Dismiss the default or a custom overlay.
window.dashLoading.finish();
window.dashLoading.finish("my-loading-overlay");
```

Before fading out, the overlay emits a bubbling `dash-loading:ready` event.
`event.detail.reason` is `"ready"`, `"timeout"`, or `"manual"`.

```javascript
document.addEventListener("dash-loading:ready", function (event) {
    console.log(event.detail.reason);
});
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
