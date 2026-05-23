# FreightDesk Pro — Android Build Guide

Produces a Play Store `.aab` (Android App Bundle) or a debug `.apk` using
**Capacitor 6** + **Android Studio**.

---

## Prerequisites

| Tool | Version | Download |
|------|---------|----------|
| Node.js | 18+ | nodejs.org |
| Android Studio | Hedgehog or newer | developer.android.com/studio |
| Java (JDK) | 17 | bundled with Android Studio |
| Android SDK | API 34 (Target), API 23 (Min) | via SDK Manager in Android Studio |

After installing Android Studio, open **SDK Manager → SDK Platforms** and install **Android 14 (API 34)**.

---

## First-time setup

```bash
cd android-app
npm install
```

That's it — the `android/` directory is already generated and committed.

---

## Open in Android Studio

```bash
npx cap open android
```

Or open Android Studio → **Open** → select the `android-app/android/` folder.

---

## Build a debug APK (for testing)

From Android Studio: **Build → Build APK(s)**

Or from the terminal:

```bash
cd android-app/android
./gradlew assembleDebug
# APK: android/app/build/outputs/apk/debug/app-debug.apk
```

Install directly on a connected device:
```bash
adb install android/app/build/outputs/apk/debug/app-debug.apk
```

---

## Build a release AAB for Play Store

### 1. Create a signing keystore (one-time)

```bash
keytool -genkey -v \
  -keystore freightdesk-release.jks \
  -alias freightdesk \
  -keyalg RSA -keysize 2048 \
  -validity 10000
```

Store the `.jks` file somewhere safe — **never commit it to git**.

### 2. Configure signing in `android/app/build.gradle`

Add a `signingConfigs` block (before `buildTypes`):

```groovy
signingConfigs {
    release {
        storeFile     file(System.getenv("KEYSTORE_PATH") ?: "../../freightdesk-release.jks")
        storePassword System.getenv("KEYSTORE_PASSWORD") ?: "your-store-password"
        keyAlias      System.getenv("KEY_ALIAS")         ?: "freightdesk"
        keyPassword   System.getenv("KEY_PASSWORD")      ?: "your-key-password"
    }
}
```

And reference it in `buildTypes.release`:
```groovy
release {
    signingConfig signingConfigs.release
    minifyEnabled false
    ...
}
```

### 3. Build the bundle

```bash
cd android-app/android
./gradlew bundleRelease
# AAB: android/app/build/outputs/bundle/release/app-release.aab
```

---

## Update web content (after changing HTML/JS)

Whenever you change `www/index.html` or `www/sync.js`, sync the changes into the Android project:

```bash
cd android-app
npx cap sync android
```

Then rebuild in Android Studio.

---

## Play Store submission checklist

- [ ] AAB signed with your release keystore
- [ ] `versionCode` incremented in `android/app/build.gradle` for each upload
- [ ] Play Store icon: `playstore-icon.png` (512×512) — run `node ../scripts/gen-icons.js` to regenerate
- [ ] Short description (80 chars) and full description ready
- [ ] Screenshots for phone and 7-inch tablet
- [ ] Privacy Policy URL (required — even for apps with no server)
- [ ] Content rating questionnaire completed

---

## Connecting to the sync server

In the app: **Settings → ☁ Server Sync** → enter your server URL → Connect → Sign In.

The server runs on any machine with Node.js:
```bash
cd ../server
npm install
PORT=3742 JWT_SECRET=your-secret npm start
```

For Android on a physical device testing against a local server, use your machine's LAN IP (e.g. `http://192.168.1.X:3742`) instead of `localhost`.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `JAVA_HOME` not set | Set it to Android Studio's bundled JDK: `export JAVA_HOME=/Applications/Android\ Studio.app/Contents/jbr/Contents/Home` |
| Gradle download hangs | Check your internet connection; the first build downloads ~200 MB |
| WebView blank screen | Run `adb logcat` and look for JS errors; enable `webContentsDebuggingEnabled: true` in `capacitor.config.json` temporarily |
| localStorage not persisting | Make sure `androidScheme: "https"` is in `capacitor.config.json` (already set) |
