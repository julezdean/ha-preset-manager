import { readFileSync } from "node:fs";

import resolve from "@rollup/plugin-node-resolve";
import terser from "@rollup/plugin-terser";
import typescript from "@rollup/plugin-typescript";

// The card says which build it is in the browser console, and the number it
// says is the integration's - they ship together and there is no second one to
// keep in step.
const version = JSON.parse(
  readFileSync("../custom_components/preset_manager/manifest.json", "utf8"),
).version;

const stampVersion = {
  name: "stamp-version",
  transform(code, id) {
    if (!id.endsWith("const.ts")) return null;
    return { code: code.replace("__CARD_VERSION__", version), map: null };
  },
};

// One self-contained file, committed to the integration. Home Assistant serves
// it as a plain resource, so nothing may be left for a bundler on the other
// side - lit included.
export default {
  input: "src/index.ts",
  output: {
    file: "../custom_components/preset_manager/www/preset-manager-card.js",
    format: "es",
    sourcemap: false,
    generatedCode: "es2015",
  },
  plugins: [
    stampVersion,
    resolve(),
    typescript({
      tsconfig: "./tsconfig.json",
      noEmitOnError: true,
      include: ["src/**/*.ts"],
    }),
    terser({ format: { comments: false } }),
  ],
};
