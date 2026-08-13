// `/` — the landing page. Previously a bare redirect (authed → /dashboard,
// else /login); per CLAUDE.md §25 (user-confirmed) it is now a real
// long-scroll destination for everyone. Signed-in users see it too; the CTAs
// simply point at /dashboard instead of /login (resolved inside LandingShell).
//
// This file stays a thin server component that exports metadata and wraps the
// client shell in <Providers>, matching the /login route's structure.

import { Providers } from "@/components/providers";
import { LandingShell } from "@/components/landing/landing-shell";

export const metadata = {
  title: "SecureCorp AI — secure enterprise HybridRAG",
  description:
    "Authorization before retrieval. Hybrid search, cross-encoder reranking, and server-validated citations over synthetic enterprise data.",
};

export default function RootPage() {
  return (
    <Providers>
      <LandingShell />
    </Providers>
  );
}
