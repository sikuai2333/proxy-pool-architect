import { useState, type FormEvent } from "react";

import { ErrorState } from "../components/common/ErrorState";
import { useI18n } from "../i18n";
import { dashboardApi } from "../lib/api-client";

interface LoginPageProps {
  onLoggedIn: () => Promise<void> | void;
}

export function LoginPage({ onLoggedIn }: LoginPageProps) {
  const { t } = useI18n();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError(null);

    try {
      await dashboardApi.login(username.trim(), password);
      await onLoggedIn();
    } catch (err) {
      setError(err instanceof Error ? err.message : t("auth.loginError"));
    } finally {
      setPending(false);
    }
  }

  return (
    <main className="auth-screen">
      <section className="panel auth-card" aria-label={t("auth.title")}>
        <div className="panel-header">
          <div>
            <h1>{t("auth.title")}</h1>
            <p>{t("auth.description")}</p>
          </div>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label className="field">
            <span>{t("auth.username")}</span>
            <input
              autoComplete="username"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              placeholder={t("auth.usernamePlaceholder")}
              required
            />
          </label>

          <label className="field">
            <span>{t("auth.password")}</span>
            <input
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder={t("auth.passwordPlaceholder")}
              required
            />
          </label>

          {error ? <ErrorState title={t("auth.loginFailed")} message={error} /> : null}

          <div className="auth-actions">
            <button className="button button-primary" type="submit" disabled={pending}>
              {pending ? t("auth.loggingIn") : t("auth.login")}
            </button>
          </div>
        </form>
      </section>
    </main>
  );
}
