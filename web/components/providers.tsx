"use client";

// The root provider tree. Mounts:
//   - QueryClientProvider (TanStack Query for non-streaming fetches)
//   - AuthProvider — exposes the current user to any descendant

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";
import { AuthContext } from "@/lib/auth-context";
import type { User } from "@/lib/types";

export function Providers({ children, initialUser = null }: { children: React.ReactNode; initialUser?: User | null }) {
  // Lazy initializer: one QueryClient per browser tab.
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: { staleTime: 30_000, refetchOnWindowFocus: false, retry: 1 },
        },
      }),
  );

  const [user, setUser] = useState<User | null>(initialUser);

  return (
    <QueryClientProvider client={client}>
      <AuthContext.Provider value={{ user, setUser }}>{children}</AuthContext.Provider>
    </QueryClientProvider>
  );
}