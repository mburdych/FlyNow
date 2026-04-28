export type WindowKey = "today_evening" | "tomorrow_morning";
export type LanguageCode = "sk" | "en";

export type TranslationKey =
  | "unavailable"
  | "staleData"
  | "settings"
  | "showSettings"
  | "hideSettings"
  | "language"
  | "switchLanguage"
  | "go"
  | "noGo"
  | "na"
  | "to"
  | "section"
  | "surfaceWind"
  | "altitudeWind"
  | "precipitation"
  | "visibility"
  | "threshold"
  | "pass"
  | "fail"
  | "info"
  | "risk"
  | "ok"
  | "fogRisk"
  | "launchBy"
  | "easaDayWindow"
  | "civilTwilight"
  | "sunrise"
  | "sunset"
  | "flightLog"
  | "date"
  | "balloon"
  | "launchTime"
  | "durationMin"
  | "site"
  | "outcome"
  | "notesOptional"
  | "saving"
  | "logFlight"
  | "flightLoggedSuccessfully"
  | "flightLogFailed"
  | "previousFlights"
  | "historyLimitText"
  | "loadingFlightHistory"
  | "noFlightsLogged"
  | "outcomeFlown"
  | "outcomeCancelledWeather"
  | "outcomeCancelledOther"
  | "siteLzmada"
  | "siteKatarinka"
  | "siteNitraLuka";

export interface FlyNowConditionValue {
  value: number | string | null;
  threshold: number | string | null;
  pass: boolean;
  ok?: boolean;
  blocking?: boolean;
  reason?: string;
  trend?: string;
  min_visibility_km?: number | null;
  max_relative_humidity_pct?: number | null;
  min_temp_dew_spread_c?: number | null;
}

export interface FlyNowConditionSet {
  surface_wind?: FlyNowConditionValue;
  surface_wind_ms?: FlyNowConditionValue;
  altitude_wind?: FlyNowConditionValue;
  altitude_wind_ms?: FlyNowConditionValue;
  precipitation_probability?: FlyNowConditionValue;
  precip_prob?: FlyNowConditionValue;
  visibility?: FlyNowConditionValue;
  visibility_km?: FlyNowConditionValue;
  fog_risk?: FlyNowConditionValue;
}

export interface FlyNowStatusAttributes {
  active_window: string;
  launch_start: string | null;
  launch_end: string | null;
  data_last_updated_utc: string | null;
  notification_result?: Record<string, unknown>;
  selected_site_id?: string;
  sites_summary?: Record<string, FlyNowSiteSummary>;
  sites?: Record<string, FlyNowSiteData>;
  today_evening_go?: boolean;
  today_evening_launch_start?: string | null;
  today_evening_launch_end?: string | null;
  today_evening_conditions?: FlyNowConditionSet;
  tomorrow_morning_go?: boolean;
  tomorrow_morning_launch_start?: string | null;
  tomorrow_morning_launch_end?: string | null;
  tomorrow_morning_conditions?: FlyNowConditionSet;
  correlation_summary?: FlyNowCorrelationSummary;
  decision_snapshot?: FlyNowWeatherSnapshot;
  weather_snapshot?: FlyNowWeatherSnapshot;
  track_summary?: FlyNowTrackSummary;
  import_warnings?: FlyNowImportWarning[];
}

export interface FlyNowSiteSummary {
  site_name?: string;
  go?: boolean;
  launch_start?: string | null;
  launch_end?: string | null;
  active_window?: string;
  data_last_updated_utc?: string | null;
}

export interface FlyNowSiteData {
  site_id?: string;
  site_name?: string;
  windows?: Record<string, FlyNowWindowData>;
  active_window?: FlyNowWindowData;
}

export interface FlyNowWindowData {
  key?: string;
  type?: string;
  go?: boolean;
  day_start?: string | null;
  day_end?: string | null;
  sunrise?: string | null;
  sunset?: string | null;
  launch_start?: string | null;
  launch_end?: string | null;
  conditions?: FlyNowConditionSet;
}

export interface FlyNowImportWarning {
  code: string;
  row?: number;
  message?: string;
  source?: string;
}

export interface FlyNowTrackPoint {
  latitude: number;
  longitude: number;
  altitude_m?: number | null;
  timestamp_utc?: string | null;
}

export interface FlyNowTrackSummary {
  flight_id?: string;
  point_count?: number;
  start_coordinate?: { latitude: number; longitude: number } | null;
  end_coordinate?: { latitude: number; longitude: number } | null;
  points_preview?: FlyNowTrackPoint[];
}

export interface FlyNowWeatherSnapshotCorrection {
  source: "metar" | "archive" | "manual" | string;
  reason: string;
  timestamp_utc: string;
}

export interface FlyNowWeatherSnapshot {
  observed_source?: "metar" | "archive" | "manual" | null;
  weather_missing?: boolean;
  weather_missing_reason?: string | null;
  corrections?: FlyNowWeatherSnapshotCorrection[];
}

export interface FlyNowCorrelationSummary {
  observed_source?: "metar" | "archive" | "manual" | null;
  weather_missing?: boolean;
  weather_missing_reason?: string | null;
  correction_count?: number;
}

export interface HassEntityState {
  state: string;
  attributes: FlyNowStatusAttributes;
}

export interface HomeAssistantLike {
  states: Record<string, HassEntityState | undefined>;
  language?: string;
  callService<T = unknown>(
    domain: string,
    service: string,
    serviceData?: Record<string, unknown>,
    target?: Record<string, unknown>,
    notifyOnError?: boolean,
    returnResponse?: boolean
  ): Promise<{ context: { id: string }; response?: T }>;
}
