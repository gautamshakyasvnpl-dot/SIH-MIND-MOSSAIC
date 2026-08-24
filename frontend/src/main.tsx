import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import { SensorySettingsProvider } from "./context/SensorySettings";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <SensorySettingsProvider>
      <App />
    </SensorySettingsProvider>
  </React.StrictMode>
);
