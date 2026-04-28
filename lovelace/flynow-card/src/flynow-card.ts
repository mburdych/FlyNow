import { LitElement, css, html, nothing, type TemplateResult } from "lit";
import type {
  BalloonId,
  FlightOutcome,
  ListFlightsResponse,
  LogFlightPayload,
  LogFlightResponse,
  LoggedFlight,
} from "./flight-log-types";
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
const BALLOON_IDS: readonly BalloonId[] = ["OM-0007", "OM-0008"] as const;
const OUTCOME_OPTIONS: ReadonlyArray<{ value: FlightOutcome; label: string }> = [
  { value: "flown", label: "Flown" },
  { value: "cancelled-weather", label: "Cancelled - weather" },
  { value: "cancelled-other", label: "Cancelled - other" },
];
const LAST_BALLOON_KEY = "flynow.last_balloon";
const HISTORY_LIMIT_TEXT = "Showing newest 200 entries";

export class FlyNowCard extends LitElement {
  static properties = {
    hass: { attribute: false },
  };

  private _config?: Record<string, unknown>;
  private _hass?: HomeAssistantLike;
  private lastKnownAttributes?: FlyNowStatusAttributes;
  private usingStaleCache = false;
  private selectedDetailSiteId?: string;
  private flightHistory: LoggedFlight[] = [];
  private historyLoading = false;
  private flightSubmitState: "idle" | "saving" | "success" | "error" = "idle";
  private submitMessage = "";
  private logForm: LogFlightPayload = this.createDefaultLogForm();
  private siteLockedToSelection = true;

  set hass(value: HomeAssistantLike | undefined) {
    const oldValue = this._hass;
    this._hass = value;
    if (!oldValue && value) {
      void this.refreshFlightHistory();
    }
    this.requestUpdate("hass", oldValue);
  }

  get hass(): HomeAssistantLike | undefined {
    return this._hass;
  }

  public setConfig(config: Record<string, unknown>): void {
    if (!config || typeof config !== "object") {
      throw new Error("Invalid configuration");
    }
    this._config = config;
  }

  public getCardSize(): number {
    return 6;
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
    .result-warn {
      color: var(--warning-color, #e6a700);
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
    .flight-log-section {
      border-top: 1px solid var(--divider-color);
      padding-top: 10px;
      display: grid;
      gap: 10px;
    }
    .flight-log-form {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px 12px;
    }
    .flight-log-form label {
      display: grid;
      gap: 4px;
      font-size: 12px;
      font-weight: 600;
    }
    .flight-log-form label.notes {
      grid-column: 1 / -1;
    }
    .flight-log-form input,
    .flight-log-form select,
    .flight-log-form textarea {
      width: 100%;
      box-sizing: border-box;
      border: 1px solid var(--divider-color);
      border-radius: 8px;
      padding: 8px;
      font: inherit;
      color: var(--primary-text-color);
      background: var(--card-background-color);
    }
    .flight-log-form button {
      grid-column: 1 / -1;
      justify-self: start;
      border: 1px solid var(--primary-color);
      border-radius: 8px;
      background: var(--primary-color);
      color: var(--text-primary-color, #fff);
      padding: 8px 12px;
      font-weight: 600;
      cursor: pointer;
    }
    .flight-log-form button[disabled] {
      opacity: 0.6;
      cursor: not-allowed;
    }
    .submit-status {
      font-size: 12px;
      font-weight: 600;
    }
    .submit-status.success {
      color: var(--success-color, var(--state-icon-active-color));
    }
    .submit-status.error {
      color: var(--error-color);
    }
    .history-meta {
      display: flex;
      justify-content: space-between;
      gap: 8px;
      font-size: 12px;
      color: var(--secondary-text-color);
    }
    .flight-history-list {
      list-style: none;
      padding: 0;
      margin: 0;
      display: grid;
      gap: 8px;
    }
    .flight-history-item {
      border: 1px solid var(--divider-color);
      border-radius: 8px;
      padding: 8px;
      font-size: 12px;
      display: grid;
      gap: 2px;
    }
  `;

  connectedCallback(): void {
    super.connectedCallback();
    void this.refreshFlightHistory();
  }

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
        ${this.renderFlightLogSection(attrs)}
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
    const active =
      (siteData?.active_window?.key as WindowKey | undefined) ?? this.getLegacyActiveWindow(attrs);
    const selectedConditions =
      (active && siteData?.windows?.[active]?.conditions) || attrs[`${active}_conditions`] || {};
    const conditions = selectedConditions as FlyNowConditionSet;
    const surfaceWind = conditions.surface_wind ?? conditions.surface_wind_ms;
    const altitudeWind = conditions.altitude_wind ?? conditions.altitude_wind_ms;
    const cloudBase = conditions.cloud_base_min_m ?? conditions.ceiling ?? conditions.ceiling_m;
    const precipitation =
      conditions.precipitation_probability ?? conditions.precip_prob;
    const visibility = conditions.visibility ?? conditions.visibility_km;
    const fogRisk = conditions.fog_risk;
    const labels = this.labels;
    return html`<section>
      <h3 class="section-title">${labels.section}</h3>
      ${this.renderConditionRow(labels.surfaceWind, surfaceWind)}
      ${this.renderConditionRow(labels.altitudeWind, altitudeWind)}
      ${this.renderConditionRow(labels.cloudBase, cloudBase)}
      ${this.renderConditionRow(labels.precipitation, precipitation)}
      ${this.renderConditionRow(labels.visibility, visibility)}
      ${this.renderFogRiskRow(fogRisk)}
    </section>`;
  }

  private renderConditionRow(
    label: string,
    item: FlyNowConditionValue | undefined
  ): TemplateResult {
    const value = this.formatValue(item?.value);
    const threshold = this.formatValue(item?.threshold);
    const pass = item?.pass ?? item?.ok ?? false;
    const thresholdText =
      item?.threshold === null || item?.threshold === undefined
        ? value
        : `${value} / ${threshold} threshold`;
    return html`<div class="condition-row">
      <span>${label}</span>
      <span>${thresholdText}</span>
      <span class="${pass ? "result-pass" : "result-fail"}">${pass ? this.labels.pass : this.labels.fail}</span>
    </div>`;
  }

  private renderFogRiskRow(item: FlyNowConditionValue | undefined): TemplateResult {
    if (!item) {
      return html``;
    }
    const risk = this.formatValue(item.value).toUpperCase();
    const trend = item.trend ? ` (${item.trend})` : "";
    const riskClass = this.fogRiskClass(item.value);
    const badge = this.fogRiskBadge(item.value);
    return html`<div class="condition-row">
      <span>${this.labels.fogRisk}</span>
      <span>${risk}${trend}</span>
      <span class="${riskClass}">${badge}</span>
    </div>`;
  }

  private fogRiskClass(value: number | string | null | undefined): string {
    switch (value) {
      case "high":
        return "result-fail";
      case "medium":
      case "low-medium":
        return "result-warn";
      default:
        return "result-pass";
    }
  }

  private fogRiskBadge(value: number | string | null | undefined): string {
    if (value === "high") {
      return this.labels.risk;
    }
    if (value === "low") {
      return this.labels.ok;
    }
    return this.labels.info;
  }

  private renderLaunchWindow(attrs: FlyNowStatusAttributes): TemplateResult {
    const siteData = this.getSelectedSiteData(attrs);
    const active = siteData?.active_window;
    const activeKey =
      (active?.key as string | undefined) ??
      ((active?.type as string | undefined) === "morning"
        ? "tomorrow_morning"
        : "tomorrow_evening");
    const windowData = siteData?.windows?.[activeKey] ?? active;
    const start = windowData?.launch_start ?? active?.launch_start ?? attrs.launch_start ?? "n/a";
    const end = windowData?.launch_end ?? active?.launch_end ?? attrs.launch_end ?? "n/a";
    const dayStart = windowData?.day_start ?? active?.day_start ?? "n/a";
    const dayEnd = windowData?.day_end ?? active?.day_end ?? "n/a";
    const sunrise = windowData?.sunrise ?? active?.sunrise ?? "n/a";
    const sunset = windowData?.sunset ?? active?.sunset ?? "n/a";
    return html`
      <div class="launch-window">Launch by ${start} to ${end}</div>
      <div class="launch-window">EASA day window ${dayStart} to ${dayEnd} (civil twilight)</div>
      <div class="launch-window">Sunrise ${sunrise} · Sunset ${sunset}</div>
    `;
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
    if (this.siteLockedToSelection) {
      this.logForm = { ...this.logForm, site: siteId };
    }
    this.requestUpdate();
  }

  private renderFlightLogSection(attrs: FlyNowStatusAttributes): TemplateResult {
    const selectedSiteId = this.getSelectedSiteId(attrs);
    if (this.siteLockedToSelection && this.logForm.site !== selectedSiteId) {
      this.logForm = { ...this.logForm, site: selectedSiteId };
    }
    return html`<section class="flight-log-section">
      <h3 class="section-title">Flight log</h3>
      <form class="flight-log-form" @submit=${this.handleFlightSubmit}>
        <label>
          Date
          <input
            name="date"
            type="date"
            required
            .value=${this.logForm.date}
            @input=${this.handleInput}
          />
        </label>
        <label>
          Balloon
          <select
            name="balloon"
            required
            .value=${this.logForm.balloon}
            @change=${this.handleInput}
          >
            ${BALLOON_IDS.map(
              (balloon) => html`<option value=${balloon}>${balloon}</option>`
            )}
          </select>
        </label>
        <label>
          Launch time
          <input
            name="launch_time"
            type="time"
            required
            .value=${this.logForm.launch_time}
            @input=${this.handleInput}
          />
        </label>
        <label>
          Duration (min)
          <input
            name="duration_min"
            type="number"
            min="15"
            max="300"
            required
            .value=${String(this.logForm.duration_min)}
            @input=${this.handleInput}
          />
        </label>
        <label>
          Site
          <select
            name="site"
            required
            .value=${this.logForm.site}
            @change=${this.handleInput}
          >
            ${SITE_ORDER.map((siteId) => html`<option value=${siteId}>${this.getSiteLabel(siteId)}</option>`)}
          </select>
        </label>
        <label>
          Outcome
          <select
            name="outcome"
            required
            .value=${this.logForm.outcome}
            @change=${this.handleInput}
          >
            ${OUTCOME_OPTIONS.map(
              (option) => html`<option value=${option.value}>${option.label}</option>`
            )}
          </select>
        </label>
        <label class="notes">
          Notes (optional)
          <textarea
            name="notes"
            rows="3"
            .value=${this.logForm.notes ?? ""}
            @input=${this.handleInput}
          ></textarea>
        </label>
        <button type="submit" ?disabled=${this.flightSubmitState === "saving"}>
          ${this.flightSubmitState === "saving" ? "Saving..." : "Log flight"}
        </button>
      </form>
      ${this.submitMessage
        ? html`<div
            class="submit-status ${this.flightSubmitState === "error" ? "error" : "success"}"
          >
            ${this.submitMessage}
          </div>`
        : nothing}
      <div class="history-meta">
        <span>Previous flights</span>
        <span>${HISTORY_LIMIT_TEXT}</span>
      </div>
      ${this.historyLoading
        ? html`<div>Loading flight history...</div>`
        : this.renderFlightHistoryList()}
    </section>`;
  }

  private renderFlightHistoryList(): TemplateResult {
    if (!this.flightHistory.length) {
      return html`<div>No flights logged yet.</div>`;
    }
    return html`<ul class="flight-history-list">
      ${this.flightHistory.map(
        (entry) => html`<li class="flight-history-item">
          <div>${entry.date} ${entry.launch_time} - ${this.getSiteLabel(entry.site)}</div>
          <div>${entry.balloon} - ${entry.outcome} - ${entry.duration_min} min</div>
          ${entry.notes ? html`<div>${entry.notes}</div>` : nothing}
        </li>`
      )}
    </ul>`;
  }

  private handleInput = (event: Event): void => {
    const target = event.target as HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement;
    const name = target.name as keyof LogFlightPayload;
    if (name === "duration_min") {
      this.logForm = { ...this.logForm, duration_min: Number(target.value) || 90 };
      return;
    }
    if (name === "balloon") {
      window.localStorage?.setItem(LAST_BALLOON_KEY, target.value);
    }
    if (name === "site") {
      this.siteLockedToSelection = false;
    }
    this.logForm = { ...this.logForm, [name]: target.value };
  };

  private handleFlightSubmit = async (event: Event): Promise<void> => {
    event.preventDefault();
    if (!this.hass) {
      return;
    }
    this.flightSubmitState = "saving";
    this.submitMessage = "";
    try {
      const response = await this.hass.callService<LogFlightResponse>(
        "flynow",
        "log_flight",
        { ...this.logForm },
        undefined,
        false,
        true
      );
      const created = response.response?.entry;
      if (!created) {
        throw new Error("missing response");
      }
      this.flightSubmitState = "success";
      this.submitMessage = "Flight logged successfully.";
      this.logForm = {
        ...this.logForm,
        launch_time: "",
        notes: "",
      };
      await this.refreshFlightHistory();
    } catch (_error) {
      this.flightSubmitState = "error";
      this.submitMessage = "Flight log failed. Try again.";
    }
  };

  private async refreshFlightHistory(): Promise<void> {
    if (!this.hass) {
      return;
    }
    this.historyLoading = true;
    try {
      const response = await this.hass.callService<ListFlightsResponse>(
        "flynow",
        "list_flights",
        {},
        undefined,
        false,
        true
      );
      this.flightHistory = response.response?.flights ?? [];
    } catch (_error) {
      this.flightHistory = [];
    } finally {
      this.historyLoading = false;
    }
  }

  private createDefaultLogForm(): LogFlightPayload {
    const now = new Date();
    const date = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(
      now.getDate()
    ).padStart(2, "0")}`;
    const lastBalloon = (window.localStorage?.getItem(LAST_BALLOON_KEY) as BalloonId | null) ?? "OM-0007";
    return {
      date,
      balloon: BALLOON_IDS.includes(lastBalloon) ? lastBalloon : "OM-0007",
      launch_time: "",
      duration_min: 90,
      site: "lzmada",
      outcome: "flown",
      notes: "",
    };
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

  private formatValue(value: number | string | null | undefined): string {
    if (typeof value === "number") {
      return this.formatNumber(value);
    }
    if (value === null || value === undefined || value === "") {
      return "n/a";
    }
    return `${value}`;
  }

  private get labels(): Record<string, string> {
    const isSk = (this.hass?.language ?? "en").toLowerCase().startsWith("sk");
    if (isSk) {
      return {
        cloudBase: "Spodná hranica oblačnosti (m AGL)",
        fogRisk: "Riziko hmly",
        section: "Podmienky",
        surfaceWind: "Vietor pri zemi",
        altitudeWind: "Vietor vo výške",
        precipitation: "Pravdepodobnosť zrážok",
        visibility: "Dohľadnosť",
        pass: "OK",
        fail: "ZLE",
        info: "INFO",
        risk: "RIZIKO",
        ok: "OK",
      };
    }
    return {
      cloudBase: "Cloud base (m AGL)",
      fogRisk: "Fog risk",
      section: "Condition thresholds",
      surfaceWind: "Surface wind",
      altitudeWind: "Altitude wind",
      precipitation: "Precipitation probability",
      visibility: "Visibility",
      pass: "PASS",
      fail: "FAIL",
      info: "INFO",
      risk: "RISK",
      ok: "OK",
    };
  }
}
