import { useEffect } from "react";
import { useLocation } from "react-router-dom";

let lastPath: string | null = null;

export function usePageTitle(title: string): void {
  const { pathname } = useLocation();

  useEffect(() => {
    document.title = `${title} · NEUROLEARN`;
  }, [title]);

  useEffect(() => {
    const navigated = lastPath !== null && lastPath !== pathname;
    lastPath = pathname;
    if (!navigated) return;
    const heading = document.querySelector<HTMLElement>("#main h1");
    if (!heading) return;
    if (!heading.hasAttribute("tabindex")) heading.setAttribute("tabindex", "-1");
    heading.focus({ preventScroll: true });
  }, [pathname]);
}
