import { LitElement, css, html, nothing, type TemplateResult } from "lit";
import type {
  FlyNowConditionSet,
  FlyNowConditionValue,
  FlyNowSiteData,
  FlyNowSiteSummary,
  FlyNowStatusAttributes,
  HomeAssistantLike,
  WindowKey,
} from "./types";

const SITE_ORDER = ["lzmada", "katarinka", "nitra-luka"] as const;

export class FlyNowCard extends LitElement {
  static properties = {
    hass: { attribute: false },
  };

  private _hass?: HomeAssistantLike;
  private lastKnownAttributes?: FlyNowStatusAttributes;
  private usingStaleCache = false;
  private selectedDetailSiteId?: string;

  set hass(value: HomeAssistantLike | undefined) {
    const oldValue = this._hass;
    this._hass = value;
    this.requestUpdate("hass", oldValue);
  }

  get hass(): HomeAssistantLike | undefined {
    return this._hass;
  }

  static styles = css`
    :host {
      display: block;
    }
    .card-content {
      padding: 16px;
      display: grid;
      gap: 16px;
    }
    .sites-summary {
      display: grid;
      gap: 12px;
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }
    .site-tile {
      border: 1px solid var(--divider-color);
      border-radius: 12px;
      padding: 12px;
      background: var(--card-background-color);
      text-align: left;
      cursor: pointer;
    }
    .site-name {
      margin: 0;
      font-size: 12px;
      font-weight: 600;
      text-transform: uppercase;
    }
    .site-tile.selected {
      border-color: var(--primary-color);
      box-shadow: 0 0 0 1px var(--primary-color);
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
    .selected-site-details {
      display: grid;
      gap: 10px;
      border-top: 1px solid var(--divider-color);
      padding-top: 8px;
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
        <div class="sites-summary">
          ${SITE_ORDER.map((siteId) => this.renderSiteTile(siteId, attrs))}
        </div>
        <div class="selected-site-details">
          ${this.renderConditionSection(attrs)}
          ${this.renderLaunchWindow(attrs)}
        </div>
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

  private renderSiteTile(siteId: string, attrs: FlyNowStatusAttributes): TemplateResult {
    const summary: FlyNowSiteSummary = attrs.sites_summary?.[siteId] ?? {};
    const go = Boolean(summary.go);
    const selected = this.getSelectedSiteId(attrs) === siteId;
    return html`<button
      type="button"
      class="site-tile ${selected ? "selected" : ""}"
      @click=${() => this.selectSite(siteId)}
    >
      <p class="site-name">${this.getSiteLabel(siteId)}</p>
      <span class="status-chip ${go ? "go" : "no-go"}">${go ? "GO" : "NO-GO"}</span>
      <div class="launch-window">
        ${summary.launch_start ?? "n/a"} to ${summary.launch_end ?? "n/a"}
      </div>
    </button>`;
  }

  private renderConditionSection(attrs: FlyNowStatusAttributes): TemplateResult {
    const siteData = this.getSelectedSiteData(attrs);
    const active = (siteData?.active_window?.type as WindowKey) ?? this.getLegacyActiveWindow(attrs);
    const selectedConditions =
      (active && siteData?.windows?.[active]?.conditions) || attrs[`${active}_conditions`] || {};
    const conditions = selectedConditions as FlyNowConditionSet;
    const surfaceWind = conditions.surface_wind ?? conditions.surface_wind_ms;
    const altitudeWind = conditions.altitude_wind ?? conditions.altitude_wind_ms;
    const ceiling = conditions.ceiling ?? conditions.ceiling_m;
    const precipitation =
      conditions.precipitation_probability ?? conditions.precip_prob;
    const visibility = conditions.visibility ?? conditions.visibility_km;
    return html`<section>
      <h3 class="section-title">Condition thresholds</h3>
      ${this.renderConditionRow("Surface wind", surfaceWind)}
      ${this.renderConditionRow("Altitude wind", altitudeWind)}
      ${this.renderConditionRow("Ceiling", ceiling)}
      ${this.renderConditionRow("Precipitation probability", precipitation)}
      ${this.renderConditionRow("Visibility", visibility)}
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
    const siteData = this.getSelectedSiteData(attrs);
    const start = siteData?.active_window?.launch_start ?? attrs.launch_start ?? "n/a";
    const end = siteData?.active_window?.launch_end ?? attrs.launch_end ?? "n/a";
    return html`<div class="launch-window">Launch by ${start} to ${end}</div>`;
  }

  private getLegacyActiveWindow(attrs: FlyNowStatusAttributes): WindowKey {
    return attrs.active_window === "tomorrow_morning" ? "tomorrow_morning" : "today_evening";
  }

  private getSelectedSiteId(attrs: FlyNowStatusAttributes): string {
    if (
      this.selectedDetailSiteId &&
      SITE_ORDER.includes(this.selectedDetailSiteId as (typeof SITE_ORDER)[number])
    ) {
      return this.selectedDetailSiteId;
    }
    const preferred = attrs.selected_site_id ?? "lzmada";
    if (SITE_ORDER.includes(preferred as (typeof SITE_ORDER)[number])) {
      this.selectedDetailSiteId = preferred;
      return preferred;
    }
    this.selectedDetailSiteId = "lzmada";
    return "lzmada";
  }

  private getSelectedSiteData(attrs: FlyNowStatusAttributes): FlyNowSiteData | undefined {
    const siteId = this.getSelectedSiteId(attrs);
    return attrs.sites?.[siteId];
  }

  private selectSite(siteId: string): void {
    this.selectedDetailSiteId = siteId;
    this.requestUpdate();
  }

  private getSiteLabel(siteId: string): string {
    if (siteId === "lzmada") return "LZMADA — Malý Madaras";
    if (siteId === "katarinka") return "Lúka pri Katarínke";
    if (siteId === "nitra-luka") return "Lúka pri Nitre";
    return siteId;
  }

  private formatNumber(value: number | null | undefined): string {
    if (value === null || value === undefined || Number.isNaN(value)) {
      return "n/a";
    }
    return `${value}`;
  }
}
