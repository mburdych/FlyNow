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
  LanguageCode,
  FlyNowSiteData,
  FlyNowSiteSummary,
  FlyNowStatusAttributes,
  HomeAssistantLike,
  TranslationKey,
  WindowKey,
} from "./types";

const SITE_ORDER = ["lzmada", "katarinka", "nitra-luka"] as const;
const BALLOON_IDS: readonly BalloonId[] = ["OM-0007", "OM-0008"] as const;
const LAST_BALLOON_KEY = "flynow.last_balloon";
const LANGUAGE_KEY = "flynow.card.language";
const DEFAULT_LANGUAGE: LanguageCode = "en";

const TRANSLATIONS: Record<LanguageCode, Record<TranslationKey, string>> = {
  en: {
    unavailable: "FlyNow card unavailable.",
    staleData: "Data temporarily unavailable - showing last known values",
    settings: "Settings",
    showSettings: "Show settings",
    hideSettings: "Hide settings",
    language: "Language",
    switchLanguage: "Switch language",
    go: "GO",
    noGo: "NO-GO",
    na: "n/a",
    to: "to",
    section: "Condition thresholds",
    surfaceWind: "Surface wind",
    altitudeWind: "Altitude wind",
    precipitation: "Precipitation probability",
    visibility: "Visibility",
    threshold: "threshold",
    pass: "PASS",
    fail: "FAIL",
    info: "INFO",
    risk: "RISK",
    ok: "OK",
    fogRisk: "Fog risk",
    launchBy: "Launch by",
    easaDayWindow: "EASA day window",
    civilTwilight: "civil twilight",
    sunrise: "Sunrise",
    sunset: "Sunset",
    flightLog: "Flight log",
    date: "Date",
    balloon: "Balloon",
    launchTime: "Launch time",
    durationMin: "Duration (min)",
    site: "Site",
    outcome: "Outcome",
    notesOptional: "Notes (optional)",
    saving: "Saving...",
    logFlight: "Log flight",
    flightLoggedSuccessfully: "Flight logged successfully.",
    flightLogFailed: "Flight log failed. Try again.",
    previousFlights: "Previous flights",
    historyLimitText: "Showing newest 200 entries",
    loadingFlightHistory: "Loading flight history...",
    noFlightsLogged: "No flights logged yet.",
    outcomeFlown: "Flown",
    outcomeCancelledWeather: "Cancelled - weather",
    outcomeCancelledOther: "Cancelled - other",
    siteLzmada: "LZMADA - Maly Madaras",
    siteKatarinka: "Luka pri Katarinke",
    siteNitraLuka: "Luka pri Nitre",
  },
  sk: {
    unavailable: "Karta FlyNow nie je dostupna.",
    staleData: "Data su docasne nedostupne - zobrazujem posledne zname hodnoty",
    settings: "Nastavenia",
    showSettings: "Zobrazit nastavenia",
    hideSettings: "Skryt nastavenia",
    language: "Jazyk",
    switchLanguage: "Prepnut jazyk",
    go: "GO",
    noGo: "NO-GO",
    na: "n/a",
    to: "do",
    section: "Limity podmienok",
    surfaceWind: "Vietor pri zemi",
    altitudeWind: "Vietor vo vyske",
    precipitation: "Pravdepodobnost zrazok",
    visibility: "Dohladnost",
    threshold: "limit",
    pass: "OK",
    fail: "ZLE",
    info: "INFO",
    risk: "RIZIKO",
    ok: "OK",
    fogRisk: "Riziko hmly",
    launchBy: "Start medzi",
    easaDayWindow: "EASA denny interval",
    civilTwilight: "obciansky sumrak",
    sunrise: "Vychod slnka",
    sunset: "Zapad slnka",
    flightLog: "Letovy zaznam",
    date: "Datum",
    balloon: "Balon",
    launchTime: "Cas startu",
    durationMin: "Dlzka (min)",
    site: "Lokalita",
    outcome: "Vysledok",
    notesOptional: "Poznamky (volitelne)",
    saving: "Ukladam...",
    logFlight: "Ulozit let",
    flightLoggedSuccessfully: "Let bol uspesne ulozeny.",
    flightLogFailed: "Ulozenie letu zlyhalo. Skuste to znova.",
    previousFlights: "Predchadzajuce lety",
    historyLimitText: "Zobrazenych najnovsich 200 zaznamov",
    loadingFlightHistory: "Nacitavam historiu letov...",
    noFlightsLogged: "Zatial nie su evidovane ziadne lety.",
    outcomeFlown: "Odletene",
    outcomeCancelledWeather: "Zrusene - pocasie",
    outcomeCancelledOther: "Zrusene - ine",
    siteLzmada: "LZMADA - Maly Madaras",
    siteKatarinka: "Luka pri Katarinke",
    siteNitraLuka: "Luka pri Nitre",
  },
};

export class FlyNowCard extends LitElement {
  static properties = {
    hass: { attribute: false },
    selectedLanguage: { state: true },
    settingsOpen: { state: true },
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
  private selectedLanguage: LanguageCode = DEFAULT_LANGUAGE;
  private settingsOpen = false;

  set hass(value: HomeAssistantLike | undefined) {
    const oldValue = this._hass;
    this._hass = value;
    if (!oldValue && value) {
      this.ensureLanguageInitialized();
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
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 8px;
    }
    .settings-toggle {
      border: 1px solid var(--divider-color);
      border-radius: 8px;
      background: var(--card-background-color);
      padding: 4px 8px;
      font-size: 12px;
      cursor: pointer;
    }
    .settings-panel {
      display: grid;
      gap: 6px;
      border: 1px solid var(--divider-color);
      border-radius: 10px;
      padding: 8px;
      background: var(--secondary-background-color, rgba(127, 127, 127, 0.12));
    }
    .settings-label {
      font-size: 12px;
      font-weight: 600;
    }
    .lang-segments {
      display: inline-flex;
      gap: 4px;
    }
    .lang-segment {
      min-height: 44px;
      min-width: 52px;
      border: 1px solid var(--divider-color);
      border-radius: 8px;
      background: var(--card-background-color);
      cursor: pointer;
      font-weight: 600;
    }
    .lang-segment.active {
      border-color: var(--primary-color);
      background: var(--primary-color);
      color: var(--text-primary-color, #fff);
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
        <div class="card-content">${this.t("unavailable")}</div>
      </ha-card>`;
    }

    return html`<ha-card>
      <div class="card-content">
        <div class="card-header">
          <h3 class="section-title">FlyNow</h3>
          <button
            type="button"
            class="settings-toggle"
            @click=${this.toggleSettingsPanel}
            title=${this.settingsOpen ? this.t("hideSettings") : this.t("showSettings")}
            aria-expanded=${this.settingsOpen ? "true" : "false"}
          >
            ${this.t("settings")} ${this.settingsOpen ? "▾" : "▸"}
          </button>
        </div>
        ${this.settingsOpen
          ? html`<div class="settings-panel">
              <div class="settings-label">${this.t("switchLanguage")}</div>
              <div class="lang-segments" role="group" aria-label=${this.t("language")}>
                ${this.renderLanguageButton("sk", "SK")}
                ${this.renderLanguageButton("en", "EN")}
              </div>
            </div>`
          : nothing}
        ${this.usingStaleCache
          ? html`<div class="stale-badge">
              ${this.t("staleData")}
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
      <span class="status-chip ${go ? "go" : "no-go"}">${go ? this.t("go") : this.t("noGo")}</span>
      <div class="launch-window">
        ${summary.launch_start ?? this.t("na")} ${this.t("to")} ${summary.launch_end ?? this.t("na")}
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
    const precipitation =
      conditions.precipitation_probability ?? conditions.precip_prob;
    const visibility = conditions.visibility ?? conditions.visibility_km;
    const fogRisk = conditions.fog_risk;
    const labels = this.labels;
    return html`<section>
      <h3 class="section-title">${labels.section}</h3>
      ${this.renderConditionRow(labels.surfaceWind, surfaceWind)}
      ${this.renderConditionRow(labels.altitudeWind, altitudeWind)}
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
        : `${value} / ${threshold} ${this.t("threshold")}`;
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
    const start = windowData?.launch_start ?? active?.launch_start ?? attrs.launch_start ?? this.t("na");
    const end = windowData?.launch_end ?? active?.launch_end ?? attrs.launch_end ?? this.t("na");
    const dayStart = windowData?.day_start ?? active?.day_start ?? this.t("na");
    const dayEnd = windowData?.day_end ?? active?.day_end ?? this.t("na");
    const sunrise = windowData?.sunrise ?? active?.sunrise ?? this.t("na");
    const sunset = windowData?.sunset ?? active?.sunset ?? this.t("na");
    return html`
      <div class="launch-window">${this.t("launchBy")} ${start} ${this.t("to")} ${end}</div>
      <div class="launch-window">${this.t("easaDayWindow")} ${dayStart} ${this.t("to")} ${dayEnd} (${this.t("civilTwilight")})</div>
      <div class="launch-window">${this.t("sunrise")} ${sunrise} · ${this.t("sunset")} ${sunset}</div>
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
      <h3 class="section-title">${this.t("flightLog")}</h3>
      <form class="flight-log-form" @submit=${this.handleFlightSubmit}>
        <label>
          ${this.t("date")}
          <input
            name="date"
            type="date"
            required
            .value=${this.logForm.date}
            @input=${this.handleInput}
          />
        </label>
        <label>
          ${this.t("balloon")}
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
          ${this.t("launchTime")}
          <input
            name="launch_time"
            type="time"
            required
            .value=${this.logForm.launch_time}
            @input=${this.handleInput}
          />
        </label>
        <label>
          ${this.t("durationMin")}
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
          ${this.t("site")}
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
          ${this.t("outcome")}
          <select
            name="outcome"
            required
            .value=${this.logForm.outcome}
            @change=${this.handleInput}
          >
            ${this.getOutcomeOptions().map(
              (option) => html`<option value=${option.value}>${option.label}</option>`
            )}
          </select>
        </label>
        <label class="notes">
          ${this.t("notesOptional")}
          <textarea
            name="notes"
            rows="3"
            .value=${this.logForm.notes ?? ""}
            @input=${this.handleInput}
          ></textarea>
        </label>
        <button type="submit" ?disabled=${this.flightSubmitState === "saving"}>
          ${this.flightSubmitState === "saving" ? this.t("saving") : this.t("logFlight")}
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
        <span>${this.t("previousFlights")}</span>
        <span>${this.t("historyLimitText")}</span>
      </div>
      ${this.historyLoading
        ? html`<div>${this.t("loadingFlightHistory")}</div>`
        : this.renderFlightHistoryList()}
    </section>`;
  }

  private renderFlightHistoryList(): TemplateResult {
    if (!this.flightHistory.length) {
      return html`<div>${this.t("noFlightsLogged")}</div>`;
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
      this.submitMessage = this.t("flightLoggedSuccessfully");
      this.logForm = {
        ...this.logForm,
        launch_time: "",
        notes: "",
      };
      await this.refreshFlightHistory();
    } catch (_error) {
      this.flightSubmitState = "error";
      this.submitMessage = this.t("flightLogFailed");
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
    if (siteId === "lzmada") return this.t("siteLzmada");
    if (siteId === "katarinka") return this.t("siteKatarinka");
    if (siteId === "nitra-luka") return this.t("siteNitraLuka");
    return siteId;
  }

  private formatNumber(value: number | null | undefined): string {
    if (value === null || value === undefined || Number.isNaN(value)) {
      return this.t("na");
    }
    return `${value}`;
  }

  private formatValue(value: number | string | null | undefined): string {
    if (typeof value === "number") {
      return this.formatNumber(value);
    }
    if (value === null || value === undefined || value === "") {
      return this.t("na");
    }
    return `${value}`;
  }

  private get labels(): Record<string, string> {
    return {
      fogRisk: this.t("fogRisk"),
      section: this.t("section"),
      surfaceWind: this.t("surfaceWind"),
      altitudeWind: this.t("altitudeWind"),
      precipitation: this.t("precipitation"),
      visibility: this.t("visibility"),
      pass: this.t("pass"),
      fail: this.t("fail"),
      info: this.t("info"),
      risk: this.t("risk"),
      ok: this.t("ok"),
    };
  }

  private getOutcomeOptions(): ReadonlyArray<{ value: FlightOutcome; label: string }> {
    return [
      { value: "flown", label: this.t("outcomeFlown") },
      { value: "cancelled-weather", label: this.t("outcomeCancelledWeather") },
      { value: "cancelled-other", label: this.t("outcomeCancelledOther") },
    ];
  }

  private toggleSettingsPanel = (): void => {
    this.settingsOpen = !this.settingsOpen;
  };

  private renderLanguageButton(language: LanguageCode, label: string): TemplateResult {
    const active = this.selectedLanguage === language;
    return html`<button
      type="button"
      class="lang-segment ${active ? "active" : ""}"
      @click=${() => this.setLanguage(language)}
      @keydown=${(event: KeyboardEvent) => this.handleLanguageButtonKeydown(event, language)}
      aria-pressed=${active ? "true" : "false"}
    >
      ${label}
    </button>`;
  }

  private handleLanguageButtonKeydown(event: KeyboardEvent, language: LanguageCode): void {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      this.setLanguage(language);
    }
  }

  private setLanguage(language: LanguageCode): void {
    if (this.selectedLanguage === language) {
      return;
    }
    this.selectedLanguage = language;
    this.persistLanguage(language);
  }

  private ensureLanguageInitialized(): void {
    const stored = this.readStoredLanguage();
    if (stored) {
      this.selectedLanguage = stored;
      return;
    }
    const inferred = this.inferLanguageFromHass();
    this.selectedLanguage = inferred;
    this.persistLanguage(inferred);
  }

  private readStoredLanguage(): LanguageCode | undefined {
    const raw = window.localStorage?.getItem(LANGUAGE_KEY);
    if (!raw) {
      return undefined;
    }
    if (raw === "sk" || raw === "en") {
      return raw;
    }
    const inferred = this.inferLanguageFromHass();
    this.persistLanguage(inferred);
    return inferred;
  }

  private inferLanguageFromHass(): LanguageCode {
    const candidate = (this.hass?.language ?? DEFAULT_LANGUAGE).toLowerCase();
    return candidate.startsWith("sk") ? "sk" : "en";
  }

  private persistLanguage(language: LanguageCode): void {
    window.localStorage?.setItem(LANGUAGE_KEY, language);
  }

  private t(key: TranslationKey): string {
    return TRANSLATIONS[this.selectedLanguage]?.[key] ?? TRANSLATIONS.en[key];
  }
}
