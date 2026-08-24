import { useCallback, useEffect, useState } from "react";
import { Link, Navigate, Outlet } from "react-router-dom";
import {
  SESSION_EXPIRED_EVENT,
  clearToken,
  getMe,
  getToken,
} from "../lib/api";
import { useProfileSync } from "../hooks/useProfileSync";

type AuthStatus = "checking" | "authed" | "anonymous" | "unreachable";

export default function RequireAuth() {
  const [status, setStatus] = useState<AuthStatus>(() =>
    getToken() ? "checking" : "anonymous"
  );
  const syncProfile = useProfileSync();

  useEffect(() => {
    function onSessionExpired() {
      setStatus("anonymous");
    }
    window.addEventListener(SESSION_EXPIRED_EVENT, onSessionExpired);
    return () =>
      window.removeEventListener(SESSION_EXPIRED_EVENT, onSessionExpired);
  }, []);

  const verify = useCallback(() => {
    if (!getToken()) {
      setStatus("anonymous");
      return;
    }
    setStatus("checking");
    getMe()
      .then(() => {
        void syncProfile();
        setStatus("authed");
      })
      .catch((err: unknown) => {
        const http = (err as { status?: number }).status;
        if (http === 401 || http === 403) {
          clearToken();
          setStatus("anonymous");
        } else {
          setStatus("unreachable");
        }
      });
  }, [syncProfile]);

  useEffect(() => {
    verify();
  }, [verify]);

  if (status === "anonymous") return <Navigate to="/login" replace />;

  if (status === "checking") {
    return (
      <p role="status" aria-live="polite" className="prose">
        Checking your sign-in…
      </p>
    );
  }

  if (status === "unreachable") {
    return (
      <main id="main" tabIndex={-1}>
        <section className="card" role="alert">
          <h1 className="page-title" tabIndex={-1}>
            We could not reach the server.
          </h1>
          <p>Your sign-in could not be confirmed just now.</p>
          <p>
            <button type="button" onClick={verify}>
              Try again
            </button>{" "}
            <Link to="/login">Back to sign in</Link>
          </p>
        </section>
      </main>
    );
  }

  return <Outlet />;
}
