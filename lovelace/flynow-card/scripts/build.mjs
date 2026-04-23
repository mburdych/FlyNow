import { build } from "esbuild";

await build({
  entryPoints: ["src/index.ts"],
  bundle: true,
  sourcemap: true,
  format: "esm",
  target: "es2022",
  outfile: "dist/flynow-card.js",
});
