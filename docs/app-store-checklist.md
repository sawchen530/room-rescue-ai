# App Store / Play Store checklist

**Status: listing package in-repo; not submitted.** Room Rescue is not in review and not on either store. Do not click Submit. Use this list when Jeff has accounts and a Mac.

Canonical packaging notes: [STORE.md](../STORE.md). Live web: [https://room-rescue-ai-production.up.railway.app](https://room-rescue-ai-production.up.railway.app)

Privacy policy URL (already live): `https://room-rescue-ai-production.up.railway.app/privacy`  
Terms URL (already live): `https://room-rescue-ai-production.up.railway.app/terms`

Paste-ready listing copy: [store-listing.md](store-listing.md)  
Framed live-site screenshots + capture plan: [store-assets/README.md](store-assets/README.md)

---

## Done vs still Jeff

| Item | Status |
| --- | --- |
| Capacitor iOS/Android shell, bundle ID `com.roomrescue.app`, version `1.0.0` | **Done** in `native/` |
| Listing copy (subtitle, promo, keywords, long descriptions, What’s New 1.0.0, support + marketing URLs) | **Done** in [store-listing.md](store-listing.md) |
| Screenshot capture plan | **Done** in [store-assets/README.md](store-assets/README.md) |
| Live-site screenshots in device frames (home, sample checklist, after-photo step, privacy) | **Done** as web frames in `docs/store-assets/` — **not** real-device captures |
| Play 512 icon + 1024×500 feature graphic | **Done** (generated house mark) |
| Native icon/splash (forest/gold house) | **Improved** in `native/assets/`; still generated, not commissioned art. Replace path: drop 1024/2732 PNGs there, then `cd native && npm run assets` |
| Apple Developer Program ($99/year) + App Store Connect app record | **Jeff** |
| Google Play Console ($25) + Play app record | **Jeff** |
| Confirm `com.roomrescue.app` is unused | **Jeff** |
| iOS signing + **Mac archive** / upload | **Jeff** (Linux cannot do this) |
| Android Play App Signing + upload keystore + AAB | **Jeff** |
| Export compliance, age rating, privacy nutrition / Data safety questionnaires | Draft answers below; **Jeff** confirms in the forms |
| Final screenshots on **real devices** (or Xcode/Android simulators at the exact slots) | **Jeff** — replace the web frames before review |
| Click Submit for Review | **Jeff — do not treat this PR as a submission** |

---

## Listing copy

Canonical strings are in [store-listing.md](store-listing.md). Do not claim a professional inspection, a guaranteed list, that photos stay on-device, or any XP/game layer.

**Name:** Room Rescue  
**Support URL:** https://room-rescue-ai-production.up.railway.app  
**Marketing URL:** https://room-rescue-ai-production.up.railway.app  
**Privacy URL:** https://room-rescue-ai-production.up.railway.app/privacy  
**Category:** Lifestyle (or Productivity). Not Kids.

---

## Apple App Store

### Only Jeff can do

1. Enroll in the [Apple Developer Program](https://developer.apple.com/programs/) — **$99 USD/year**.
2. In [App Store Connect](https://appstoreconnect.apple.com/) create the app with bundle ID **`com.roomrescue.app`** (or another ID if this one is taken — then update `native/app.json` and re-sync).
3. Create an iOS Distribution certificate and App Store provisioning profile (Xcode “Automatically manage signing” is fine).
4. On a **Mac**: `cd native && npm install && npx cap sync && npx cap open ios`.
5. In Xcode: pick a Team, bump version if needed (`1.0.0` / build `1` is already set), Product → Archive, Distribute to App Store Connect.
6. Fill the listing from [store-listing.md](store-listing.md), privacy nutrition label, age rating, review notes, and **real-device screenshots**.
7. Submit for Review. **Do not treat this PR as a submission.**

Linux CI cannot produce a signed iOS App Store build. `native/ios/` is checked in so the Mac step is “open and archive,” not “invent a project.”

### iOS technical notes already in the scaffold

- Display name: Room Rescue
- Bundle ID: `com.roomrescue.app`
- Camera and photo-library usage strings (the web UI uses `<input type="file" accept="image/*" capture>` inside the WebView)
- `ITSAppUsesNonExemptEncryption` = false — **Jeff must still confirm** export-compliance (HTTPS to our server / OpenAI only; no custom crypto)
- Launch storyboard / splash from the forest/gold house mark in `native/assets/` (still generated; replace before a designer pass)
- Privacy manifest stub (`PrivacyInfo.xcprivacy`) for common UserDefaults / file-timestamp APIs Capacitor and WKWebView may touch

### Age rating (Apple)

Suggested answers for this product (Jeff confirms in the questionnaire):

| Topic | Suggested |
| --- | --- |
| Kids Category | **No** |
| Cartoon / realistic violence, weapons, drugs, gambling, mature/suggestive, horror | None / none of the above |
| Medical / treatment information | No |
| Unrestricted web access (embedded browser that can leave our site) | **No** — WebView is bound to the Room Rescue host |
| User-generated content that is public | **No** — photos are not a social feed |
| Age gate | Content is ordinary home upkeep |

Likely result: **4+**. The privacy page says the product is for adults and not directed at children under 13; that is COPPA / privacy, not the content rating. Do **not** put the app in Kids Category.

### Privacy nutrition label (Apple)

Apple’s “collect” means data that **leaves the device**, even if we do not keep it.

Declare at least:

| Data type | Linked to identity? | Used for tracking? | Purpose |
| --- | --- | --- | --- |
| **Photos or Videos** | No (no accounts) | No | App Functionality — analyze a room and compare before/after |
| **User Content** (the photo + optional room hint / time budget) | No | No | App Functionality |
| **Product Interaction** / **Other Diagnostic Data** (optional) | No | No | Analytics or App Functionality — only if you keep server error logs that are not photos. The public privacy page says a broken request may log an error message, not the image. |

Do **not** claim “Data Not Collected.” Photos go to our server and then to **OpenAI**.

Third parties / privacy policy text: OpenAI processes images under their API terms. We do not sell data. We do not use the photos for advertising. No tracking SDKs are in this scaffold.

### App Review notes (draft)

> Room Rescue is a Capacitor wrapper around our production web app (https://room-rescue-ai-production.up.railway.app). There is no login. Reviewers can tap “Use a sample room” to get a checklist without a camera, or photograph any ordinary room. Photos are sent to our API and OpenAI vision; they are not stored as a product feature. The checklist is a DIY helper and can be wrong — see in-app Terms.

Mention the sample-room path so a reviewer is not blocked without a house photo.

### Required Apple screenshots

**In-repo:** live-site captures with a drawn iPhone/iPad frame are in `docs/store-assets/` (`iphone-6.7-01-home.png`, checklist, progress, privacy; 6.5" and 6.9" are scaled from 6.7"). See [store-assets/README.md](store-assets/README.md).

**Still Jeff:** recapture on a **real device or Xcode simulator** at the sizes App Store Connect currently requires. Apple changes the exact pixel list. Typical 2026 set:

| Device class | Common size (portrait) | How many | This PR |
| --- | --- | --- | --- |
| iPhone 6.9" / 6.7" (required) | 1320×2868 or 1290×2796 | 3–10 | Web frames + scaled 6.9" — replace on device |
| iPhone 6.5" (often still required) | 1284×2778 | 3–10 | Scaled from 6.7" — replace if Connect still asks |
| iPad 13" / 12.9" if you offer iPad | 2064×2752 or 2048×2732 | 3–10 | Web tablet frames at 2048×2732 |

Minimum useful shots (same story as the web frames):

1. Home — “Start with a photo” + sample-room control
2. A generated checklist (sample room is fine; keep the sample banner)
3. After-photo / progress comparison, or the empty after-photo step
4. Privacy or Terms (optional; honesty helps review)

Do not use marketing mockups that imply a different product. Dark olive + cream UI is already the brand. No XP/game overlays.

---

## Google Play

### Only Jeff can do

1. Pay the Play Console registration fee (**$25 USD**, one-time) and verify identity.
2. Create the app **Room Rescue**, package name **`com.roomrescue.app`**.
3. Complete the store listing, content rating (IARC), Target audience, Data safety, and News / COVID / Financial declarations as applicable (this app is none of those).
4. Create a Play App Signing key (Google can generate and hold it) and an upload keystore that **never** goes in git.
5. Build an **AAB** (`cd native && npx cap sync` then Android Studio → Generate App Bundle, or `./gradlew bundleRelease` after a release keystore is configured).
6. Upload to an internal testing track first, then production. **This PR does not upload anything.**

An Android bundle can be produced on Linux; Play still needs Jeff’s account and signing.

### Android technical notes already in the scaffold

- `applicationId` / namespace: `com.roomrescue.app`
- `versionName` `1.0.0`, `versionCode` `1`
- `INTERNET`, camera, and photo-read permissions (WebView file picker)
- `CAMERA` is not required-hardware (`android:required="false"`)
- Cleartext is off for production HTTPS; it turns on only when `CAPACITOR_SERVER_URL` is `http://…`

### Content rating / age (Play)

IARC questionnaire for a utility that shows AI text about home tasks and user-taken photos:

- No user-to-user chat or public UGC feed
- No violence, gambling, or objectionable content in the app itself
- Users may photograph their own rooms (private)

Likely result: **Everyone** (or equivalent). Target audience: **18+** is consistent with “meant for adults” on `/privacy`, even if the content rating is Everyone. Do not enroll in Designed for Families / Kids.

### Data safety (Play)

Match Apple:

- **Photos and videos:** collected, **not** shared for advertising, **shared with OpenAI** as a service provider for app functionality, ephemeral on our servers, not required to be linked to a user account.
- **App activity / crash logs:** only if you actually retain them.
- **Data is encrypted in transit** (HTTPS).
- Users cannot request deletion of photos from our servers because we do not keep them; on-device checkmarks are cleared by clearing app data.
- **Not sold.** **Not used for ads.**

Privacy policy URL is required on Play: use the live `/privacy` page.

### Required Play screenshots / assets

| Asset | Typical requirement | This PR |
| --- | --- | --- |
| High-res icon | 512×512 PNG | `docs/store-assets/play-icon-512.png` (generated house mark) |
| Feature graphic | 1024×500 | `docs/store-assets/play-feature-1024x500.png` |
| Phone screenshots | at least 2, up to 8; 16:9 or 9:16 (max 2:1) | `play-phone-01` … `04` at 1080×1920. Do **not** upload iPhone 6.7" files (taller than 2:1). |
| 7" / 10" tablet | optional unless you claim tablet support | **Missing** — skip unless you claim tablets |
| Short / full description | [store-listing.md](store-listing.md) | Ready to paste |

Same four storyboards as iOS are enough. Recapture on a real phone before production listing if Play rejects framed web shots.

---

## Shared store risks (read before submitting)

1. **Website wrapper (Apple 4.2 / Play “minimum functionality”).** This app loads the production URL. Reviewers may ask what is native. Be honest in review notes. A later PR can add a Capacitor Camera plugin or offline fallback if review bounces; this scaffold does not pretend that work is done.
2. **Photos + AI.** State clearly that images go to OpenAI. Hide-the-ball privacy answers get rejected.
3. **Professional-advice claims.** Listing, screenshots, and review notes must match `/terms`.
4. **Icons / splash** in `native/assets/` are a generated house mark (improved, still not commissioned art). Replace with final art if you want, then `cd native && npm run assets`. See `native/assets/README.md`.
5. **Signing secrets** never belong in this repo.

---

## Version bump (after 1.0.0)

1. Edit `native/app.json` (`version` and increment `versionCode`).
2. `cd native && npm run version:sync`
3. Commit the changed iOS/Android files.
4. Archive / bundle again.

Web Railway deploys do not need a native version bump. Native users pick up web UI changes from the live URL the next time they open the app, without an App Store update — unless you change the Capacitor config, permissions, or icons.
