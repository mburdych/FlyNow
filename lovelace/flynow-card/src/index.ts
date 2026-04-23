import { FlyNowCard } from "./flynow-card";

declare global {
  interface Window {
    customCards?: Array<Record<string, unknown>>;
  }
}

if (!customElements.get("flynow-card")) {
  customElements.define("flynow-card", FlyNowCard);
}

window.customCards = window.customCards || [];
window.customCards.push({
  type: "flynow-card",
  name: "FlyNow Card",
  description: "Displays go/no-go windows and conditions for balloon operations.",
});
