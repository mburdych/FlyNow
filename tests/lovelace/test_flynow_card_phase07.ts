import { test } from "node:test";
import assert from "node:assert/strict";

import { buildPolylineCoordinates } from "../../lovelace/flynow-card/src/map-renderer";

test("buildPolylineCoordinates returns empty for missing track", () => {
  const coords = buildPolylineCoordinates(undefined);
  assert.equal(coords.length, 0);
});

test("buildPolylineCoordinates filters invalid coordinates", () => {
  const coords = buildPolylineCoordinates({
    points_preview: [
      { latitude: 48.1, longitude: 17.3 },
      { latitude: Number.NaN, longitude: 17.4 },
      { latitude: 48.2, longitude: 17.5 },
    ],
  });
  assert.deepEqual(coords, [
    [48.1, 17.3],
    [48.2, 17.5],
  ]);
});
