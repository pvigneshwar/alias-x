# ALIAS_X · DEPLOYMENT & PACKAGING PROTOCOLS

## Windows .EXE + Android .APK — Web Wrapper Strategy

---

## PART 1 — STREAMLIT CLOUD DEPLOYMENT (prerequisite)

Before packaging, deploy your app to get a public URL.

```bash
# 1. Push your Alias_X/ folder to GitHub
git init && git add . && git commit -m "ALIAS_X initial"
git remote add origin https://github.com/YOUR_USERNAME/alias-x.git
git push -u origin main

# 2. Go to https://share.streamlit.io → "New app"
#    Repository: YOUR_USERNAME/alias-x
#    Main file:  app.py
#    Add secrets from .env in "Advanced settings → Secrets" "yblf bcwq haks iron"
```

Your live URL will be: `https://alias-x-uplink.streamlit.app`

### Required: streamlit config (`.streamlit/config.toml`)

```toml
[server]
headless = true
enableCORS = false      # Must be false for WebView wrappers
enableXsrfProtection = false  # Required for iframe/WebView embedding

[browser]
gatherUsageStats = false

[theme]
base = "dark"
backgroundColor = "#000000"
secondaryBackgroundColor = "#0a0a0f"
textColor = "#e8e8f0"
primaryColor = "#ff003c"
```

---

## PART 2 — WINDOWS .EXE PROTOCOL (Electron/Nativefier)

### Prerequisites

```bash
# Install Node.js (v18+) from https://nodejs.org
node --version   # verify: v18.x.x or higher
npm --version    # verify: 9.x.x or higher
```

### Option A: Nativefier (Simplest — one command)

```bash
# Install Nativefier globally
npm install -g nativefier

# Generate .exe with your ALIAS_X icon
# Place your icon as alias_x_icon.ico in the current directory (256x256)
nativefier \
  --name "ALIAS_X" \
  --platform windows \
  --arch x64 \
  --icon ./alias_x_icon.ico \
  --background-color "#000000" \
  --title-bar-style "hidden" \
  --disable-dev-tools \
  --single-instance \
  "https://alias-x-uplink.streamlit.app"

# Output folder: ALIAS_X-win32-x64/
# Distribute: zip ALIAS_X-win32-x64/ and share → users run ALIAS_X.exe
```

### Option B: Electron (Full control + auto-updater)

```bash
mkdir alias-x-electron && cd alias-x-electron
npm init -y
npm install --save-dev electron electron-builder
```

**Create `main.js`:**

```javascript
const { app, BrowserWindow, Menu } = require("electron");
const path = require("path");

const APP_URL = "https://alias-x-uplink.streamlit.app";

function createWindow() {
  const win = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 900,
    minHeight: 600,
    backgroundColor: "#000000",
    icon: path.join(__dirname, "assets/alias_x_icon.ico"),
    title: "ALIAS_X — Autonomous Verification Protocol",
    titleBarStyle: "default",
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      webSecurity: true,
    },
  });

  // Remove default menu bar
  Menu.setApplicationMenu(null);

  // Load the Streamlit app
  win.loadURL(APP_URL);

  // Show loading state
  win.webContents.on("did-start-loading", () => {
    win.setTitle("ALIAS_X — Connecting...");
  });

  win.webContents.on("did-finish-load", () => {
    win.setTitle("ALIAS_X — Autonomous Verification Protocol");
  });
}

app.whenReady().then(createWindow);
app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});
app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});
```

**Update `package.json`:**

```json
{
  "name": "alias-x",
  "version": "2.4.1",
  "description": "ALIAS_X Autonomous Verification Protocol",
  "main": "main.js",
  "scripts": {
    "start": "electron .",
    "build-win": "electron-builder --win --x64"
  },
  "build": {
    "appId": "com.aliasx.verification",
    "productName": "ALIAS_X",
    "directories": { "output": "dist" },
    "win": {
      "target": [{ "target": "nsis", "arch": ["x64"] }],
      "icon": "assets/alias_x_icon.ico"
    },
    "nsis": {
      "oneClick": false,
      "allowToChangeInstallationDirectory": true,
      "installerIcon": "assets/alias_x_icon.ico",
      "installerHeader": "assets/alias_x_icon.ico"
    }
  }
}
```

```bash
# Create assets folder and add your 256x256 .ico icon
mkdir assets
# Copy alias_x_icon.ico to assets/

# Test locally
npm start

# Build installer .exe
npm run build-win
# Output: dist/ALIAS_X Setup 2.4.1.exe
```

### Icon Conversion (PNG → ICO)

```bash
# Using ImageMagick
magick convert alias_x_icon.png \
  -define icon:auto-resize="256,128,64,48,32,16" \
  alias_x_icon.ico
```

---

## PART 3 — ANDROID .APK PROTOCOL

### Option A: Android Studio WebView (Full control)

**Step 1: Create new Android project**

- Android Studio → New Project → Empty Views Activity
- Name: `ALIAS_X` | Package: `com.aliasx.verification`
- Min SDK: API 24 (Android 7.0)
- Language: Kotlin

**Step 2: Replace `AndroidManifest.xml`**

```xml
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.aliasx.verification">

    <!-- REQUIRED PERMISSIONS -->
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />

    <!-- File uploader: camera + storage -->
    <uses-permission android:name="android.permission.CAMERA" />
    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE"
        android:maxSdkVersion="32" />
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE"
        android:maxSdkVersion="29" />
    <!-- Android 13+ scoped media permissions -->
    <uses-permission android:name="android.permission.READ_MEDIA_IMAGES" />
    <uses-permission android:name="android.permission.READ_MEDIA_VIDEO" />
    <uses-permission android:name="android.permission.READ_MEDIA_AUDIO" />

    <!-- Allow mixed HTTP/HTTPS (Streamlit local dev only — remove for production) -->
    <!-- <uses-permission android:name="android.permission.CHANGE_NETWORK_STATE" /> -->

    <application
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:label="ALIAS_X"
        android:roundIcon="@mipmap/ic_launcher_round"
        android:supportsRtl="true"
        android:theme="@style/Theme.AppCompat.NoActionBar"
        android:hardwareAccelerated="true"
        android:usesCleartextTraffic="false">

        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:screenOrientation="portrait"
            android:configChanges="orientation|screenSize|keyboardHidden">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>

        <!-- Required for camera/file picker via WebView -->
        <provider
            android:name="androidx.core.content.FileProvider"
            android:authorities="${applicationId}.fileprovider"
            android:exported="false"
            android:grantUriPermissions="true">
            <meta-data
                android:name="android.support.FILE_PROVIDER_PATHS"
                android:resource="@xml/file_paths" />
        </provider>

    </application>
</manifest>
```

**Step 3: `res/xml/file_paths.xml`** (create this file)

```xml
<?xml version="1.0" encoding="utf-8"?>
<paths xmlns:android="http://schemas.android.com/apk/res/android">
    <external-path name="external_files" path="." />
    <cache-path name="cache_files" path="." />
</paths>
```

**Step 4: `MainActivity.kt`**

```kotlin
package com.aliasx.verification

import android.Manifest
import android.annotation.SuppressLint
import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.webkit.*
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat

class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView
    private val APP_URL = "https://alias-x-uplink.streamlit.app"

    // File chooser callback for Streamlit file uploader
    private var filePathCallback: ValueCallback<Array<Uri>>? = null

    private val filePickerLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode == Activity.RESULT_OK) {
            val data = result.data
            val results: Array<Uri>? = if (data?.data != null) {
                arrayOf(data.data!!)
            } else null
            filePathCallback?.onReceiveValue(results)
        } else {
            filePathCallback?.onReceiveValue(null)
        }
        filePathCallback = null
    }

    private val permissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { /* handle if needed */ }

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Request permissions on launch
        requestAppPermissions()

        webView = WebView(this).apply {
            settings.apply {
                javaScriptEnabled        = true
                domStorageEnabled        = true
                allowFileAccess          = true
                allowContentAccess       = true
                loadWithOverviewMode     = true
                useWideViewPort          = true
                setSupportZoom(false)
                builtInZoomControls      = false
                displayZoomControls      = false
                mediaPlaybackRequiresUserGesture = false
                mixedContentMode         = WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
                cacheMode                = WebSettings.LOAD_DEFAULT
                userAgentString          = userAgentString + " ALIAS_X-Android/2.4.1"
            }

            // Handle file uploads (Streamlit file uploader)
            webChromeClient = object : WebChromeClient() {
                override fun onShowFileChooser(
                    wv: WebView?,
                    callback: ValueCallback<Array<Uri>>?,
                    params: FileChooserParams?
                ): Boolean {
                    filePathCallback?.onReceiveValue(null) // cancel previous
                    filePathCallback = callback
                    val intent = params?.createIntent() ?: Intent(Intent.ACTION_GET_CONTENT).apply {
                        addCategory(Intent.CATEGORY_OPENABLE)
                        type = "image/*"
                    }
                    try {
                        filePickerLauncher.launch(intent)
                    } catch (e: Exception) {
                        filePathCallback = null
                        Toast.makeText(this@MainActivity, "Cannot open file picker", Toast.LENGTH_SHORT).show()
                        return false
                    }
                    return true
                }

                // Allow geolocation if needed
                override fun onGeolocationPermissionsShowPrompt(
                    origin: String?, callback: GeolocationPermissions.Callback?
                ) { callback?.invoke(origin, true, false) }
            }

            webViewClient = object : WebViewClient() {
                override fun onReceivedError(
                    view: WebView?, req: WebResourceRequest?, err: WebResourceError?
                ) {
                    // Show a friendly error page on network failure
                    val errorHtml = """
                        <html><body style="background:#000;color:#ff003c;
                        font-family:monospace;text-align:center;padding-top:30%;">
                        <h1>▲ CONNECTION ERROR</h1>
                        <p>Check network and retry.</p>
                        <button onclick="window.location.reload()"
                        style="background:transparent;color:#00ffaa;border:1px solid #00ffaa;
                        padding:10px 20px;font-family:monospace;cursor:pointer;">
                        ⟳ RETRY</button></body></html>
                    """.trimIndent()
                    view?.loadData(errorHtml, "text/html", "UTF-8")
                }
            }

            loadUrl(APP_URL)
        }

        setContentView(webView)
    }

    private fun requestAppPermissions() {
        val perms = mutableListOf(Manifest.permission.CAMERA)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            perms.add(Manifest.permission.READ_MEDIA_IMAGES)
        } else {
            perms.add(Manifest.permission.READ_EXTERNAL_STORAGE)
        }
        val toRequest = perms.filter {
            ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED
        }.toTypedArray()
        if (toRequest.isNotEmpty()) permissionLauncher.launch(toRequest)
    }

    override fun onBackPressed() {
        if (webView.canGoBack()) webView.goBack() else super.onBackPressed()
    }
}
```

**Step 5: Build APK**

```
Android Studio → Build → Build Bundle(s)/APK(s) → Build APK(s)
Output: app/build/outputs/apk/debug/app-debug.apk

For signed release APK:
Build → Generate Signed Bundle/APK → APK → create keystore → release
```

---

### Option B: Bubblewrap / PWA (No Android Studio needed)

**Prerequisites:**

1. Your Streamlit app must serve a `manifest.json` and a service worker (add via a custom HTML component or host separately)
2. Install Bubblewrap:

```bash
# Prerequisites: Java JDK 8+, Android SDK
npm install -g @bubblewrap/cli

# Initialize (run in empty folder)
bubblewrap init --manifest https://alias-x-uplink.streamlit.app/manifest.json

# Build APK
bubblewrap build

# Output: app-release-signed.apk
```

**Note:** Bubblewrap generates a Trusted Web Activity (TWA) which is the cleanest wrapper
and gets accepted by Google Play Store. However, Streamlit doesn't natively output a
`manifest.json` — you'd need to serve a static one alongside or use Option A instead.

---

## PART 4 — QUICK REFERENCE CHECKLIST

```
ALIAS_X Packaging Checklist
────────────────────────────────────────────────────────────────
☐ .streamlit/config.toml → enableCORS=false, enableXsrfProtection=false
☐ App deployed to Streamlit Cloud with secrets configured
☐ HTTPS URL confirmed working in browser

Windows EXE:
☐ Node.js v18+ installed
☐ alias_x_icon.ico (256x256) created
☐ Nativefier command run OR Electron project built
☐ .exe tested on clean Windows machine

Android APK:
☐ Android Studio installed (Electric Eel or newer)
☐ Min SDK set to API 24
☐ Internet + Camera + Storage permissions in Manifest
☐ FileProvider configured for file upload support
☐ APK signed for distribution (release build)
☐ Tested on Android 7+ physical device or emulator
────────────────────────────────────────────────────────────────
```
