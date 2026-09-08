# Native image placeholders

These PNGs are **scaffolding**, generated from the same house + gold-bar mark as the web favicon. They are good enough to open the Xcode / Android Studio projects. They are **not** final store art.

| File | Size | Use |
| --- | --- | --- |
| `icon.png` | 1024×1024 | App icon source (no rounded-rect mask baked in) |
| `icon-foreground.png` | 1024×1024 | Android adaptive foreground |
| `icon-background.png` | 1024×1024 | Android adaptive background |
| `splash.png` | 2732×2732 | Launch screen |
| `splash-dark.png` | 2732×2732 | Dark launch screen (same art for now) |

## Replace before store submission

1. Drop a final 1024×1024 icon (and 2732 splash) here.
2. From `native/`: `npm install` then `npm run assets`.
3. Open the iOS and Android projects and confirm the icon is not blurry and sits inside each platform’s safe zone / mask.

Regenerate these placeholders (needs Pillow, not a production dependency):

```bash
python3 -m pip install pillow
python3 native/scripts/generate_placeholders.py
```
