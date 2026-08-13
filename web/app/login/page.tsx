import { Providers } from "@/components/providers";
import { LoginBackdrop } from "@/components/auth/login-backdrop";
import { LoginCard } from "@/components/auth/login-card";

export const metadata = {
  title: "Sign in — SecureCorp AI",
};

export default function LoginPage() {
  return (
    <Providers>
      {/* Backdrop is fixed full-bleed behind everything. The card sits in
          a centered column on top. */}
      <main className="relative isolate flex min-h-dvh items-center justify-center px-4 py-12">
        <LoginBackdrop />
        <LoginCard />
      </main>
    </Providers>
  );
}
