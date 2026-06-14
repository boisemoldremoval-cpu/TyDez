import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";
import { initSettings } from "./store/settingsStore";

// Ensure settings (theme, font, etc) are initialized immediately
initSettings();

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
