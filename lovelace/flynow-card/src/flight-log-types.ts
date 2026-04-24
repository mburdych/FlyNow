export type FlightOutcome = "flown" | "cancelled-weather" | "cancelled-other";

export type BalloonId = "OM-0007" | "OM-0008";

export interface LogFlightPayload {
  date: string;
  balloon: BalloonId;
  launch_time: string;
  duration_min: number;
  site: string;
  outcome: FlightOutcome;
  notes?: string;
}

export interface LoggedFlight extends Required<LogFlightPayload> {
  id: string;
  created_at: string;
  schema_version: number;
}

export interface LogFlightResponse {
  entry: LoggedFlight;
}

export interface ListFlightsResponse {
  flights: LoggedFlight[];
}
