import { LitElement, css, html, nothing, type TemplateResult } from "lit";
import type {
  FlyNowConditionSet,
  FlyNowConditionValue,
  FlyNowStatusAttributes,
  HomeAssistantLike,
  WindowKey,
} from "./types";

export class FlyNowCard extends LitElement {
  static properties = {
    hass: { attribute: false },
  };

  declare hass?: HomeAssistantLike;
  private lastKnownAttributes?: FlyNowStatusAttributes;
  private usingStaleCache = false;

  static styles = css`
    :host {
      display: block;
    }
    .card-content {
      padding: 16px;
      display: grid;
      gap: 16px;
    }
    .window-summary {
      display: grid;
      gap: 12px;
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .window-tile {
      border: 1px solid var(--divider-color);
      border-radius: 12px;
      padding: 12px;
      background: var(--card-background-color);
    }
    .window-name {
      margin: 0;
      font-size: 12px;
      font-weight: 600;
      text-transform: uppercase;
    }
    .status-chip {
      display: inline-block;
      margin-top: 8px;
      padding: 2px 8px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 600;
    }
    .status-chip.go {
      color: var(--primary-text-color);
      background: var(--state-icon-active-color);
    }
    .status-chip.no-go {
      color: var(--primary-text-color);
      background: var(--error-color);
    }
    .section-title {
      margin: 0;
      font-size: 14px;
      font-weight: 600;
    }
    .condition-row {
      display: grid;
      grid-template-columns: 1fr auto auto;
      gap: 8px;
      align-items: center;
      margin: 6px 0;
      font-size: 13px;
    }
    .result-pass {
      color: var(--success-color, var(--state-icon-active-color));
      font-weight: 600;
    }
    .result-fail {
      color: var(--error-color);
      font-weight: 600;
    }
    .launch-window {
      font-size: 13px;
    }
    .stale-badge {
      padding: 6px 10px;
      border-radius: 8px;
      background: var(--warning-color, #8a6d3b);
      color: #fff;
      font-size: 12px;
      font-weight: 600;
    }
  `;

  protected render(): TemplateResult {
    const stateObj = this.hass?.states["binary_sensor.flynow_status"];
    const attrs = this.resolveAttributes(stateObj?.state, stateObj?.attributes);

    if (!attrs) {
      return html`<ha-card>
        <div class="card-content">FlyNow card unavailable.</div>
      </ha-card>`;
    }

    return html`<ha-card>
      <div class="card-content">
        ${this.usingStaleCache
          ? html`<div class="stale-badge">
              Data temporarily unavailable - showing last known values
            </div>`
          : nothing}
        <div class="window-summary">
          ${this.renderWindowTile("today_evening", "Today's Evening", attrs)}
          ${this.renderWindowTile("tomorrow_morning", "Tomorrow Morning", attrs)}
        </div>
        ${this.renderConditionSection(attrs)}
        ${this.renderLaunchWindow(attrs)}
      </div>
    </ha-card>`;
  }

  private resolveAttributes(
    entityState: string | undefined,
    attributes: FlyNowStatusAttributes | undefined
  ): FlyNowStatusAttributes | undefined {
    if (
      attributes &&
      entityState !== "unavailable" &&
      entityState !== "unknown"
    ) {
      this.lastKnownAttributes = attributes;
      this.usingStaleCache = false;
      return attributes;
    }

    if (this.lastKnownAttributes) {
      this.usingStaleCache = true;
      return this.lastKnownAttributes;
    }

    this.usingStaleCache = false;
    return undefined;
  }

  private renderWindowTile(
    key: WindowKey,
    label: string,
    attrs: FlyNowStatusAttributes
  ): TemplateResult {
    const go = Boolean(attrs[`${key}_go`]);
    return html`<section class="window-tile">
      <p class="window-name">${label}</p>
      <span class="status-chip ${go ? "go" : "no-go"}">${go ? "GO" : "NO-GO"}</span>
    </section>`;
  }

  private renderConditionSection(attrs: FlyNowStatusAttributes): TemplateResult {
    const active: WindowKey =
      attrs.active_window === "tomorrow_morning" ? "tomorrow_morning" : "today_evening";
    const conditions = attrs[`${active}_conditions`] ?? {};
    return html`<section>
      <h3 class="section-title">Condition thresholds</h3>
      ${this.renderConditionRow("Surface wind", conditions.surface_wind)}
      ${this.renderConditionRow("Altitude wind", conditions.altitude_wind)}
      ${this.renderConditionRow("Ceiling", conditions.ceiling)}
      ${this.renderConditionRow(
        "Precipitation probability",
        conditions.precipitation_probability
      )}
      ${this.renderConditionRow("Visibility", conditions.visibility)}
    </section>`;
  }

  private renderConditionRow(
    label: string,
    item: FlyNowConditionValue | undefined
  ): TemplateResult {
    const value = this.formatNumber(item?.value);
    const threshold = this.formatNumber(item?.threshold);
    const pass = item?.pass ?? false;
    return html`<div class="condition-row">
      <span>${label}</span>
      <span>${value} / ${threshold} threshold</span>
      <span class="${pass ? "result-pass" : "result-fail"}">${pass ? "PASS" : "FAIL"}</span>
    </div>`;
  }

  private renderLaunchWindow(attrs: FlyNowStatusAttributes): TemplateResult {
    const start = attrs.launch_start ?? "n/a";
    const end = attrs.launch_end ?? "n/a";
    return html`<div class="launch-window">Launch by ${start} to ${end}</div>`;
  }

  private formatNumber(value: number | null | undefined): string {
    if (value === null || value === undefined || Number.isNaN(value)) {
      return "n/a";
    }
    return `${value}`;
  }
}
