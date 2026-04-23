# FlyNow Lovelace Card

Custom Lovelace card for `binary_sensor.flynow_status`.

## Build

```bash
npm install
npm run build
```

## Home Assistant resource setup

1. Copy `dist/flynow-card.js` into your Home Assistant `/config/www/flynow/` folder.
2. Add a Lovelace resource pointing to `/local/flynow/flynow-card.js`.
3. Add a manual card with `type: custom:flynow-card`.
