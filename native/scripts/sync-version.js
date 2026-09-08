#!/usr/bin/env node
/**
 * Copy native/app.json version + versionCode into the generated iOS/Android projects.
 * Run after bumping app.json, then commit the native file changes.
 */

const fs = require("fs");
const path = require("path");

const root = path.join(__dirname, "..");
const app = JSON.parse(fs.readFileSync(path.join(root, "app.json"), "utf8"));
const { version, versionCode, appId, appName } = app;

function replaceOnce(file, pattern, replacement, label) {
  if (!fs.existsSync(file)) {
    console.warn(`skip missing ${label}: ${path.relative(root, file)}`);
    return;
  }
  const before = fs.readFileSync(file, "utf8");
  const after = before.replace(pattern, replacement);
  if (before === after) {
    console.warn(`no change for ${label}: ${path.relative(root, file)}`);
    return;
  }
  fs.writeFileSync(file, after);
  console.log(`updated ${label}: ${path.relative(root, file)}`);
}

const gradle = path.join(root, "android/app/build.gradle");
replaceOnce(gradle, /versionCode\s+\d+/, `versionCode ${versionCode}`, "android versionCode");
replaceOnce(gradle, /versionName\s+"[^"]+"/, `versionName "${version}"`, "android versionName");
replaceOnce(
  gradle,
  /applicationId\s+"[^"]+"/,
  `applicationId "${appId}"`,
  "android applicationId",
);
replaceOnce(
  gradle,
  /namespace\s+"[^"]+"/,
  `namespace "${appId}"`,
  "android namespace",
);

const pbx = path.join(root, "ios/App/App.xcodeproj/project.pbxproj");
replaceOnce(pbx, /MARKETING_VERSION = [^;]+;/g, `MARKETING_VERSION = ${version};`, "ios MARKETING_VERSION");
replaceOnce(
  pbx,
  /CURRENT_PROJECT_VERSION = [^;]+;/g,
  `CURRENT_PROJECT_VERSION = ${versionCode};`,
  "ios CURRENT_PROJECT_VERSION",
);
replaceOnce(
  pbx,
  /PRODUCT_BUNDLE_IDENTIFIER = [^;]+;/g,
  `PRODUCT_BUNDLE_IDENTIFIER = ${appId};`,
  "ios bundle id",
);

const plist = path.join(root, "ios/App/App/Info.plist");
replaceOnce(
  plist,
  /<key>CFBundleDisplayName<\/key>\s*<string>[^<]*<\/string>/,
  `<key>CFBundleDisplayName</key>\n\t<string>${appName}</string>`,
  "ios display name",
);

const pkg = path.join(root, "package.json");
replaceOnce(pkg, /"version":\s*"[^"]+"/, `"version": "${version}"`, "package.json version");

console.log(`Room Rescue native version ${version} (${versionCode}) — ${appId}`);
