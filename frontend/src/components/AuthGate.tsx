"use client";

import { FormEvent, useEffect, useState } from "react";
import { KanbanBoard } from "@/components/KanbanBoard";

type AuthStatus = "authenticated" | "unauthenticated";

const getErrorMessage = async (response: Response) => {
  try {
    const body = await response.json();
    if (typeof body?.detail === "string") {
      return body.detail;
    }
  } catch {
    return "Login failed. Please try again.";
  }
  return "Login failed. Please try again.";
};

export const AuthGate = () => {
  const [authStatus, setAuthStatus] = useState<AuthStatus>("unauthenticated");
  const [username, setUsername] = useState("user");
  const [password, setPassword] = useState("password");
  const [errorMessage, setErrorMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    const loadSession = async () => {
      try {
        const response = await fetch("/api/auth/session", {
          credentials: "include",
        });
        if (!response.ok) {
          setAuthStatus("unauthenticated");
          return;
        }
        const payload = await response.json();
        setAuthStatus(payload.authenticated ? "authenticated" : "unauthenticated");
      } catch {
        setAuthStatus("unauthenticated");
      }
    };

    loadSession();
  }, []);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setErrorMessage("");
    setIsSubmitting(true);

    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) {
        setErrorMessage(await getErrorMessage(response));
        return;
      }

      setAuthStatus("authenticated");
    } catch {
      setErrorMessage("Login failed. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleLogout = async () => {
    await fetch("/api/auth/logout", {
      method: "POST",
      credentials: "include",
    });
    setAuthStatus("unauthenticated");
  };

  if (authStatus === "unauthenticated") {
    return (
      <main className="grid min-h-screen place-items-center px-6 py-8">
        <section className="w-full max-w-md rounded-3xl border border-[var(--stroke)] bg-white p-8 shadow-[var(--shadow)]">
          <p className="text-xs font-semibold uppercase tracking-[0.25em] text-[var(--gray-text)]">
            Sign In
          </p>
          <h1 className="mt-3 font-display text-3xl text-[var(--navy-dark)]">
            Kanban Studio
          </h1>
          <p className="mt-3 text-sm text-[var(--gray-text)]">
            Use the MVP credentials to continue.
          </p>
          <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
            <label className="block text-sm font-medium text-[var(--navy-dark)]">
              Username
              <input
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                className="mt-2 w-full rounded-xl border border-[var(--stroke)] px-3 py-2 text-sm outline-none focus:border-[var(--primary-blue)]"
                autoComplete="username"
                required
              />
            </label>
            <label className="block text-sm font-medium text-[var(--navy-dark)]">
              Password
              <input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="mt-2 w-full rounded-xl border border-[var(--stroke)] px-3 py-2 text-sm outline-none focus:border-[var(--primary-blue)]"
                autoComplete="current-password"
                required
              />
            </label>
            {errorMessage ? (
              <p className="text-sm text-[var(--secondary-purple)]" role="alert">
                {errorMessage}
              </p>
            ) : null}
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full rounded-full bg-[var(--secondary-purple)] px-4 py-2 text-sm font-semibold text-white transition hover:opacity-95 disabled:cursor-not-allowed disabled:opacity-65"
            >
              {isSubmitting ? "Signing in..." : "Sign in"}
            </button>
          </form>
        </section>
      </main>
    );
  }

  return (
    <>
      <div className="fixed right-6 top-6 z-50">
        <button
          type="button"
          onClick={handleLogout}
          className="rounded-full border border-[var(--stroke)] bg-white px-4 py-2 text-xs font-semibold uppercase tracking-[0.12em] text-[var(--navy-dark)] shadow-[var(--shadow)] transition hover:border-[var(--primary-blue)]"
        >
          Log out
        </button>
      </div>
      <KanbanBoard />
    </>
  );
};
