# Room Rescue native shell

Capacitor 8 project that wraps the live FastAPI web app.

Full instructions: [../README.md](../README.md) (web vs native) and [../STORE.md](../STORE.md).

```bash
npm install
npx cap sync
npx cap open ios       # Mac + Xcode
npx cap open android   # Android Studio
```

Point at local uvicorn:

```bash
CAPACITOR_SERVER_URL=http://192.168.1.20:8000 npx cap sync
```

Identity lives in `app.json` (`com.roomrescue.app`, version `1.0.0`). After a version bump, run `npm run version:sync`.
