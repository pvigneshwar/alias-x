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
