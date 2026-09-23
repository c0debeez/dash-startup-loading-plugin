// Shared entry-point runtime for every generated per-loader bundle.
import React from "react";
import { createRoot } from "react-dom/client";

const SHADOW_RESET =
  ":host{display:inline-block;width:100%;height:100%;color:inherit}" +
  "*,*::before,*::after{box-sizing:border-box;border-width:var(--dash-loading-ui-stroke,2px)!important}" +
  "svg,svg *{stroke-width:var(--dash-loading-ui-stroke,2px)!important}" +
  ".sr-only{position:absolute!important;width:1px!important;height:1px!important;padding:0!important;" +
  "margin:-1px!important;overflow:hidden!important;clip:rect(0,0,0,0)!important;" +
  "white-space:nowrap!important;border:0!important}";

export interface LoaderBundle {
  component: React.ComponentType<any>;
  css: string;
  /** Geometry from the loader's official demo; empty when it is intrinsically sized. */
  geometry: React.CSSProperties;
  /** ``text-*`` loaders render the configured loading text as children. */
  usesText: boolean;
  /** Loaders that size themselves through ``style`` rather than a utility class. */
  forwardsStyle: boolean;
}

export function mount({ component, css, geometry, usesText, forwardsStyle }: LoaderBundle): void {
  const host = document.querySelector("[data-dash-loading-ui]") as HTMLElement | null;
  if (!host) return;

  const shadow = host.attachShadow({ mode: "open" });
  const style = document.createElement("style");
  style.textContent = SHADOW_RESET + css;
  shadow.appendChild(style);

  const target = document.createElement("span");
  target.style.cssText = "display:inline-flex;width:auto;height:auto";
  Object.assign(target.style, geometry);
  shadow.appendChild(target);

  const fillsTarget = Boolean(geometry.width || geometry.height);
  const children = usesText ? host.dataset.dashLoadingText || "Loading" : undefined;
  const props =
    forwardsStyle && fillsTarget
      ? { style: { width: "100%", height: "100%" }, children }
      : { className: fillsTarget ? "size-full" : undefined, children };
  createRoot(target).render(React.createElement(component, props));
}
