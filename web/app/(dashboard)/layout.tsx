"use client";

// (dashboard) layout — shared by every authenticated surface inside the route
// group: /chat (home), /knowledge, /analytics, /security, /settings.
//
// Composes:
//   - <Providers> (TanStack Query + AuthContext)
//   - <DashboardGate> — auth check; bounces to /login on 401
//   - <DashboardTopNav> — the single top navigation chrome
//   - The page slot (each page renders its own <PageHeader/> + body)
//
// Per §24.5: do not modify the backend. The auth gate keeps the
// /api/auth/me cookie check (cookie is httpOnly, same as before).

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { me } from "@/lib/api";
import { useCurrentUser } from "@/lib/auth-context";
import { Providers } from "@/components/providers";
import { DashboardTopNav } from "@/components/layout/dashboard-top-nav";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <Providers>
      <DashboardGate>
        <div className="flex min-h-dvh flex-col bg-[var(--color-background)]">
          <DashboardTopNav />
          <main className="min-w-0 flex-1">{children}</main>
        </div>
      </DashboardGate>
    </Providers>
  );
}

// Auth gate — mirror of ChatGate in /chat, kept local so the two
// surfaces can evolve independently. If a user lands here without a
// valid cookie, they bounce to /login.
function DashboardGate({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, setUser } = useCurrentUser();

  const meQuery = useQuery({
    queryKey: ["me"],
    queryFn: me,
    enabled: user === null,
    retry: false,
  });

  useEffect(() => {
    if (user) return;
    if (meQuery.data) {
      setUser(meQuery.data);
      return;
    }
    if (meQuery.isError) {
      router.replace(`/login?next=${encodeURIComponent(pathname ?? "/")}`);
    }
  }, [user, meQuery.data, meQuery.isError, router, setUser, pathname]);

  if (!user && !meQuery.data) {
    return (
      <div className="grid min-h-dvh place-items-center">
        <p className="text-sm text-[var(--color-muted-foreground)]">Loading…</p>
      </div>
    );
  }

  return <>{children}</>;
}
