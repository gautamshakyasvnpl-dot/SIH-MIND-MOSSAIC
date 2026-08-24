import { Component, type ErrorInfo, type ReactNode } from "react";
import { Link } from "react-router-dom";

type Props = { children: ReactNode; resetKey?: string };
type State = { error: Error | null };

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("NEUROLEARN render error:", error, info.componentStack);
  }

  componentDidUpdate(prevProps: Props) {
    if (
      this.state.error &&
      prevProps.resetKey !== undefined &&
      prevProps.resetKey !== this.props.resetKey
    ) {
      this.setState({ error: null });
    }
  }

  reset = () => this.setState({ error: null });

  render() {
    const { error } = this.state;
    if (!error) return this.props.children;
    return (
      <main id="main" tabIndex={-1}>
        <section className="card" role="alert">
          <h1 className="page-title" tabIndex={-1}>
            Something went wrong while loading this page.
          </h1>
          <p>
            The rest of NEUROLEARN still works. Nothing you saved was lost —
            your documents and settings are safe.
          </p>
          <p>
            <button type="button" onClick={this.reset}>
              Try again
            </button>{" "}
            <Link to="/dashboard">Go to your dashboard</Link>
          </p>
        </section>
      </main>
    );
  }
}
