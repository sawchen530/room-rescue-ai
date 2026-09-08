const fs = require("fs");
const path = require("path");

const app = JSON.parse(fs.readFileSync(path.join(__dirname, "app.json"), "utf8"));

const productionUrl = app.productionUrl;
const serverUrl = (process.env.CAPACITOR_SERVER_URL || productionUrl).replace(/\/$/, "");

function hostnameOf(url) {
  try {
    return new URL(url).hostname;
  } catch {
    return null;
  }
}

const allowNavigation = new Set(["room-rescue-ai-production.up.railway.app"]);
const serverHost = hostnameOf(serverUrl);
if (serverHost) {
  allowNavigation.add(serverHost);
}

/**
 * Room Rescue native shell.
 *
 * The product is FastAPI + static files. Photo analysis needs the live
 * backend and OpenAI, so the WebView loads the production site (or a
 * local uvicorn URL via CAPACITOR_SERVER_URL). Bundling static/ alone
 * would still require that API. See ../STORE.md.
 *
 * @type {import('@capacitor/cli').CapacitorConfig}
 */
const config = {
  appId: app.appId,
  appName: app.appName,
  webDir: "www",
  server: {
    url: serverUrl,
    cleartext: serverUrl.startsWith("http://"),
    allowNavigation: [...allowNavigation],
  },
  ios: {
    contentInset: "automatic",
    preferredContentMode: "mobile",
    scheme: "RoomRescue",
  },
  android: {
    allowMixedContent: false,
  },
};

module.exports = config;
