export type WindowKey = "today_evening" | "tomorrow_morning";

export interface FlyNowConditionValue {
  value: number | null;
  threshold: number | null;
  pass: boolean;
}

export interface FlyNowConditionSet {
  surface_wind?: FlyNowConditionValue;
  altitude_wind?: FlyNowConditionValue;
  ceiling?: FlyNowConditionValue;
  precipitation_probability?: FlyNowConditionValue;
  visibility?: FlyNowConditionValue;
}

export interface FlyNowStatusAttributes {
  active_window: string;
  launch_start: string | null;
  launch_end: string | null;
  data_last_updated_utc: string | null;
  notification_result?: Record<string, unknown>;
  today_evening_go?: boolean;
  today_evening_launch_start?: string | null;
  today_evening_launch_end?: string | null;
  today_evening_conditions?: FlyNowConditionSet;
  tomorrow_morning_go?: boolean;
  tomorrow_morning_launch_start?: string | null;
  tomorrow_morning_launch_end?: string | null;
  tomorrow_morning_conditions?: FlyNowConditionSet;
}

export interface HassEntityState {
  state: string;
  attributes: FlyNowStatusAttributes;
}

export interface HomeAssistantLike {
  states: Record<string, HassEntityState | undefined>;
}
