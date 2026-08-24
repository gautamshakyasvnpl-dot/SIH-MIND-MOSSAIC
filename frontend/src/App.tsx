import { useEffect, useState, type ReactNode } from "react";
import { BrowserRouter, Navigate, Outlet, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import SiteHeader from "./components/SiteHeader";
import ErrorBoundary from "./components/ErrorBoundary";
import RequireAuth from "./components/RequireAuth";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Onboarding from "./pages/Onboarding";
import Dashboard from "./pages/Dashboard";
import Library from "./pages/Library";
import DocumentView from "./pages/DocumentView";
import SprintBoard from "./pages/SprintBoard";
import VivaStudio from "./pages/VivaStudio";
import Wellbeing from "./pages/Wellbeing";
import Reader from "./pages/Reader";
import FocusMode from "./pages/FocusMode";
import Preferences from "./pages/Preferences";
import Communicate from "./pages/Communicate";
import "./styles/tokens.css";

function RootRedirect() {
  const hasToken = Boolean(localStorage.getItem("sahaik_token"));
  return <Navigate to={hasToken ? "/dashboard" : "/landing"} replace />;
}

const SKIP_STYLE = {
  position: "absolute",
  left: "-9999px",
  top: 0,
  background: "#fffdf7",
  color: "#29241c",
  padding: "10px 18px",
  zIndex: 1000,
  borderRadius: "0 0 12px 0",
} as const;

function SkipLink() {
  return (
    <a href="#main" style={SKIP_STYLE} className="skip-link" onFocus={(e) => {
      const el = e.currentTarget;
      el.onblur = () => (el.style.left = "-9999px");
      el.style.left = "8px";
    }}>
      Skip to main content
    </a>
  );
}

const SHORTCUT_ROUTES: Record<string, string> = {
  Digit1: "/library",
  Digit2: "/tasks",
  Digit3: "/wellbeing",
  Digit4: "/communicate",
  Digit5: "/preferences",
};

function KeyboardShortcuts() {
  const navigate = useNavigate();
  const [announce, setAnnounce] = useState("");

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (!e.altKey) return;
      if (SHORTCUT_ROUTES[e.code]) {
        e.preventDefault();
        navigate(SHORTCUT_ROUTES[e.code]);
        setAnnounce(`Navigated to ${SHORTCUT_ROUTES[e.code]}.`);
        return;
      }
      if (e.code === "KeyM") {
        const players = Array.from(document.querySelectorAll("audio"));
        for (const p of players) p.muted = !p.muted;
        setAnnounce(
          players.length
            ? `Audio ${players[0].muted ? "muted" : "unmuted"}.`
            : "No audio players on this page."
        );
        e.preventDefault();
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [navigate]);

  return (
    <>
      <p role="status" aria-live="polite" style={{ position: "absolute", left: "-9999px" }}>
        {announce}
      </p>
      <p className="shortcut-hint">
        <small>Alt+1 Library · Alt+2 Sprints · Alt+3 Wellbeing · Alt+4 Communicate · Alt+5 Preferences · Alt+M mute audio</small>
      </p>
    </>
  );
}

function PageBoundary({ children }: { children: ReactNode }) {
  const { pathname } = useLocation();
  return <ErrorBoundary resetKey={pathname}>{children}</ErrorBoundary>;
}

function AppLayout() {
  return (
    <>
      <SiteHeader />
      <PageBoundary>
        <Outlet />
      </PageBoundary>
      <KeyboardShortcuts />
    </>
  );
}

export default function App() {
  return (
    <>
      <SkipLink />
      <BrowserRouter>
        <PageBoundary>
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/landing" element={<Landing />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route element={<AppLayout />}>
              <Route element={<RequireAuth />}>
                <Route path="/onboarding" element={<Onboarding />} />
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/library" element={<Library />} />
                <Route path="/tasks" element={<SprintBoard />} />
                <Route path="/wellbeing" element={<Wellbeing />} />
                <Route path="/preferences" element={<Preferences />} />
                <Route path="/communicate" element={<Communicate />} />
                <Route path="/document/:id" element={<DocumentView />} />
                <Route path="/document/:id/reader" element={<Reader />} />
                <Route path="/document/:id/viva" element={<VivaStudio />} />
                <Route path="/focus/:id?" element={<FocusMode />} />
              </Route>
            </Route>
            <Route path="*" element={<RootRedirect />} />
          </Routes>
        </PageBoundary>
      </BrowserRouter>
    </>
  );
}
