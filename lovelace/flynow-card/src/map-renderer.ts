import type { FlyNowTrackPoint, FlyNowTrackSummary } from "./types";

type LatLngExpression = [number, number];

export function buildPolylineCoordinates(track: FlyNowTrackSummary | undefined): LatLngExpression[] {
  const preview = track?.points_preview ?? [];
  return preview
    .filter((point): point is FlyNowTrackPoint => Number.isFinite(point.latitude) && Number.isFinite(point.longitude))
    .map((point) => [point.latitude, point.longitude]);
}

export class FlyNowMapRenderer {
  private map: any | null = null;
  private polyline: any | null = null;

  async init(container: HTMLElement): Promise<void> {
    if (this.map) {
      return;
    }
    const leaflet = await import("leaflet");
    const L = leaflet.default;
    this.map = L.map(container, { zoomControl: true, attributionControl: true });
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "© OpenStreetMap contributors",
    }).addTo(this.map);
  }

  async updateTrack(track: FlyNowTrackSummary | undefined): Promise<void> {
    if (!this.map) {
      return;
    }
    const leaflet = await import("leaflet");
    const L = leaflet.default;
    const coords = buildPolylineCoordinates(track);
    if (!coords.length) {
      if (this.polyline) {
        this.map.removeLayer(this.polyline);
        this.polyline = null;
      }
      return;
    }

    if (this.polyline) {
      this.map.removeLayer(this.polyline);
    }
    this.polyline = L.polyline(coords, { color: "#1e88e5", weight: 3 }).addTo(this.map);
    this.map.fitBounds(this.polyline.getBounds(), { padding: [20, 20] });
  }

  dispose(): void {
    if (this.map) {
      this.map.remove();
    }
    this.map = null;
    this.polyline = null;
  }
}
