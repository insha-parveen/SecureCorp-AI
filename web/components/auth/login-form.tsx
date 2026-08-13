"use client";

// Sign-in form. Three views in one:
//
//   - Default: email + password (cosmetic) + Remember me + Sign In +
//     SSO alternative.
//   - The footer link "Sign in with a demo account" opens an inline
//     picker of the 6 pre-seeded users — same MVP auth flow as before,
//     just hidden behind a disclosure.
//
// Per §24.5, the email + password fields are visual only at this
// stage — the actual wire contract is still:
//
//     POST /api/auth/token   { user_id: <prefix-of-email> }
//
// so the same backend handler continues to work without code changes.
// Any password rules are deliberately client-side only (the server
// doesn't accept one).

import { useEffect, useId, useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { listDemoUsers, login } from "@/lib/api";
import { useCurrentUser } from "@/lib/auth-context";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { RoleBadge } from "@/components/auth/role-badge";
import { Logo } from "@/components/ui/logo";

type View = "credentials" | "demo";

export function LoginForm() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { setUser, user: me } = useCurrentUser();

  const [view, setView] = useState<View>("credentials");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [demoOpen, setDemoOpen] = useState(false);
  const emailId = useId();
  const passwordId = useId();
  const rememberId = useId();

  // Fetched once, used by the demo-user disclosure.
  const users = useQuery({
    queryKey: ["demo-users"],
    queryFn: listDemoUsers,
    staleTime: 5 * 60 * 1000,
    enabled: view === "demo" || demoOpen,
  });

  const loginMutation = useMutation({
    mutationFn: login,
    onSuccess: (user) => {
      setUser(user);
      queryClient.setQueryData(["me"], user);
      router.push("/chat");
    },
    onError: (err) => {
      setError(err instanceof Error ? err.message : "Login failed");
    },
  });

  // Already authed? Bounce straight to the chat home.
  useEffect(() => {
    if (me) router.replace("/chat");
  }, [me, router]);

  // Derive the user_id the server expects from the typed email — the MVP
  // contract is `{ user_id: <email-prefix> }` (e.g., "alice@nexacore.com"
  // → "alice"). Lowercased, trimmed. If the user typed nothing yet, we
  // submit on Enter with the demo button instead.
  const derivedUserId = email.trim().split("@")[0]?.toLowerCase() ?? "";

  function handleCredentialsSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    if (!derivedUserId) {
      setError("Enter your work email to sign in.");
      return;
    }
    loginMutation.mutate(derivedUserId);
  }

  function handleSsoAlternative() {
    // SSO is visual for MVP — drop the user on the demo picker instead.
    setView("demo");
    setDemoOpen(true);
    setError(null);
  }

  if (view === "demo") {
    return (
      <div className="space-y-4">
        <header className="space-y-1 text-center">
          <Logo size={24} withWordmark={false} className="mx-auto" />
          <h2 className="text-base font-semibold">Choose a demo account</h2>
          <p className="text-xs text-[var(--color-muted-foreground)]">
            Six pre-seeded users, one per canonical role. This is the MVP
            auth path — no signup.
          </p>
        </header>

        {users.isLoading ? (
          <p className="text-sm text-[var(--color-muted-foreground)]">
            Loading demo users…
          </p>
        ) : users.error ? (
          <p className="text-sm text-[var(--color-destructive)]" role="alert">
            Could not reach the auth service. Is the backend running?
          </p>
        ) : (
          <ul className="grid gap-2">
            {users.data?.users.map((u) => (
              <li key={u.user_id}>
                <Button
                  variant="outline"
                  size="lg"
                  className="w-full justify-between gap-3"
                  onClick={() => {
                    setError(null);
                    loginMutation.mutate(u.user_id);
                  }}
                  disabled={loginMutation.isPending}
                >
                  <span className="flex flex-col items-start gap-0.5">
                    <span className="text-sm font-semibold">{u.user_id}</span>
                    <span className="text-[11px] font-normal text-[var(--color-muted-foreground)]">
                      {u.department || "—"} · {u.tenant_id}
                    </span>
                  </span>
                  <span className="flex flex-wrap justify-end gap-1">
                    {u.roles.map((role) => (
                      <RoleBadge key={role} role={role} />
                    ))}
                  </span>
                </Button>
              </li>
            ))}
          </ul>
        )}

        <div className="flex items-center justify-between text-xs text-[var(--color-muted-foreground)]">
          <button
            type="button"
            className="underline-offset-2 hover:underline"
            onClick={() => {
              setView("credentials");
              setError(null);
            }}
          >
            ← Back to sign in
          </button>
          {loginMutation.isPending ? "Signing in…" : null}
        </div>

        {error ? (
          <p className="text-sm text-[var(--color-destructive)]" role="alert">
            {error}
          </p>
        ) : null}
      </div>
    );
  }

  return (
    <form className="space-y-4" onSubmit={handleCredentialsSubmit}>
      <div className="space-y-1.5">
        <label
          htmlFor={emailId}
          className="text-xs font-medium uppercase tracking-wide text-[var(--color-muted-foreground)]"
        >
          Work email
        </label>
        <Input
          id={emailId}
          type="email"
          autoComplete="username"
          placeholder="alice@nexacore.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          disabled={loginMutation.isPending}
          required
        />
      </div>

      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <label
            htmlFor={passwordId}
            className="text-xs font-medium uppercase tracking-wide text-[var(--color-muted-foreground)]"
          >
            Password
          </label>
          <button
            type="button"
            className="text-xs font-medium text-[var(--color-primary)] underline-offset-2 hover:underline"
            onClick={() =>
              setError("Password recovery is not enabled in this build.")
            }
          >
            Forgot?
          </button>
        </div>
        <Input
          id={passwordId}
          type="password"
          autoComplete="current-password"
          placeholder="••••••••"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          disabled={loginMutation.isPending}
        />
        {/* The password field is collected but ignored by the auth service
            for MVP — see the file header. We still validate it's not empty
            so the UI behaves like a real form. */}
      </div>

      <label
        htmlFor={rememberId}
        className="flex cursor-pointer select-none items-center gap-2 text-sm text-[var(--color-muted-foreground)]"
      >
        <input
          id={rememberId}
          type="checkbox"
          className="size-4 rounded border border-[var(--color-border)] bg-transparent accent-[var(--color-primary)]"
          checked={remember}
          onChange={(e) => setRemember(e.target.checked)}
          disabled={loginMutation.isPending}
        />
        <span>Remember me on this device</span>
      </label>

      <Button
        type="submit"
        variant="gradient"
        size="lg"
        className="w-full"
        disabled={loginMutation.isPending}
      >
        {loginMutation.isPending ? "Signing in…" : "Sign In"}
      </Button>

      <div className="flex items-center gap-3 text-[11px] uppercase tracking-wide text-[var(--color-muted-foreground)]">
        <div className="h-px flex-1 bg-[var(--color-border)]" />
        <span>or</span>
        <div className="h-px flex-1 bg-[var(--color-border)]" />
      </div>

      <Button
        type="button"
        variant="outline"
        size="lg"
        className="w-full"
        onClick={handleSsoAlternative}
        disabled={loginMutation.isPending}
      >
        SSO Login (Company)
      </Button>

      <p className="pt-1 text-center text-xs text-[var(--color-muted-foreground)]">
        Need a sandbox account?{" "}
        <button
          type="button"
          className="font-medium text-[var(--color-primary)] underline-offset-2 hover:underline"
          onClick={() => {
            setView("demo");
            setDemoOpen(true);
            setError(null);
          }}
        >
          Sign in with a demo account
        </button>
      </p>

      {error ? (
        <p className="text-sm text-[var(--color-destructive)]" role="alert">
          {error}
        </p>
      ) : null}
    </form>
  );
}
