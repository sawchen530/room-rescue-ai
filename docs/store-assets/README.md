# Store listing assets

Screenshots and Play Console graphics for a **future** App Store / Play listing. **Nothing has been submitted.**

Listing copy lives in [../store-listing.md](../store-listing.md). Submission steps: [../app-store-checklist.md](../app-store-checklist.md).

## What is in this folder

| File | Size | Source |
| --- | --- | --- |
| `iphone-6.7-01-home.png` | 1290×2796 | Live site, iPhone 14/15 Pro Max viewport, device frame |
| `iphone-6.7-02-checklist.png` | 1290×2796 | Sample-room checklist on the live site |
| `iphone-6.7-03-progress.png` | 1290×2796 | After-photo / “Check the work” step (empty dropzone) |
| `iphone-6.7-04-privacy.png` | 1290×2796 | `/privacy` |
| `iphone-6.5-0N-*.png` | 1284×2778 | Scaled from the 6.7" frames (not a separate device capture) |
| `iphone-6.9-0N-*.png` | 1320×2868 | Scaled from the 6.7" frames (not a separate device capture) |
| `play-phone-0N-*.png` | 1080×1920 | Same scenes, 9:16 Play phone canvas |
| `ipad-13-01-home.png` | 2048×2732 | Live site at iPad viewport, tablet frame |
| `ipad-13-02-checklist.png` | 2048×2732 | Sample checklist, if the live analyze call succeeded |
| `ipad-13-04-privacy.png` | 2048×2732 | `/privacy` |
| `play-icon-512.png` | 512×512 | Generated house mark (same as `native/assets/icon.png`) |
| `play-feature-1024x500.png` | 1024×500 | Forest/gold banner + honest tagline |

6.5" and 6.9" iPhone files exist so Jeff can drop *something* into every current iPhone slot. They are **scaled web frames**, not unique photography. Recapture on the matching simulator or device before review.

## Capture plan (for Jeff on a Mac)

App Store Connect and Play want shots from **real devices or simulators**, not a desktop browser chrome. Use the live site or the Capacitor shell pointed at production.

Minimum story (same four scenes as the files above):

1. **Home** — “Start with a photo”, sample-room control visible, no overclaiming headline.
2. **Checklist** — tap **Use a sample room**, wait for the living-room list. Do not crop out the sample banner; it keeps the listing honest.
3. **Progress** — the “Check the work” after-photo step. A real before/after compare is better if you photograph the same corner twice; this repo’s captures use the empty dropzone because a same-photo compare would look like a 0% score.
4. **Privacy** — `/privacy` (“How we handle your photos”). Optional extra: `/terms`.

Do not add XP, streaks, badges, or mock “professional inspection” text on top of screenshots. Dark olive + cream + gold is already the brand; skip extra marketing slogans.

### Apple sizes to recapture

Apple changes the required slot list. As of this pass, plan on:

| Slot | Portrait px | In this folder | Still needs Jeff |
| --- | --- | --- | --- |
| iPhone 6.9" | 1320×2868 | Scaled from 6.7" web frames | **Yes — native capture** (iPhone 16 Pro Max or equivalent simulator) |
| iPhone 6.7" | 1290×2796 | Web + device frame | **Yes — native capture** to replace the web frame |
| iPhone 6.5" | 1284×2778 | Scaled from 6.7" | **Yes — native capture** if Connect still requires 6.5" |
| iPad 13" | 2064×2752 or 2048×2732 | 2048×2732 web + tablet frame | **Yes** if the iOS target includes iPad (`TARGETED_DEVICE_FAMILY` is 1,2) |

Take 3–10 shots per required slot. Portrait only is enough for this utility.

### Play sizes still missing

| Asset | Typical requirement | In this folder | Still needs Jeff |
| --- | --- | --- | --- |
| Phone screenshots | ≥2, 16:9 or 9:16, max 2:1 | Four 1080×1920 frames | Recapture on a phone if Play rejects framed web shots |
| 7" tablet | optional | **Missing** | Only if you claim 7" tablet support |
| 10" tablet | optional | iPad-ish 2048×2732 can be resized; **not a 10" Play capture** | Only if you claim 10" tablet support |
| High-res icon | 512×512 32-bit PNG | `play-icon-512.png` | Replace if you commission a final mark |
| Feature graphic | 1024×500 | `play-feature-1024x500.png` | Replace if you want photography instead of the house mark |

Play rejects iPhone 6.7" pixel sizes (1290×2796 is taller than 2:1). Use the `play-phone-*` files, not the iPhone ones, on Play.

## Regenerating the web frames

From the repo root (needs Pillow + Playwright; not a production dependency):

```bash
python3 -m pip install pillow playwright
python3 -m playwright install chromium
python3 docs/store-assets/capture.py
```

Point at a local server instead of production:

```bash
python3 docs/store-assets/capture.py --url http://127.0.0.1:8000
```

House-mark icon / splash / Play feature graphic:

```bash
python3 native/scripts/generate_placeholders.py
cd native && npm install && npm run assets
```

## Honesty notes for the shots that exist

- Captured from [the live Railway site](https://room-rescue-ai-production.up.railway.app), not from a signed iOS/Android binary.
- Device frames are drawn (forest bezel, gold edge), not Apple’s official product renders.
- The checklist is the **sample living room**, which the UI already labels.
- Compare/progress is the after-photo step, not a completed before/after report.
