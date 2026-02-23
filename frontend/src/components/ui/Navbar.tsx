"use client";

import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import { apiPost } from "@/lib/api";
import { useProfileGate } from "@/hooks/use-profile-gate";

const NAV_LINKS = [
  { href: "/dashboard", label: "Dashboard", requiresProfile: false },
  { href: "/ingest", label: "New Offer", requiresProfile: true },
  { href: "/next-steps", label: "Next Steps", requiresProfile: false },
  { href: "/analytics", label: "Analytics", requiresProfile: false },
  { href: "/chat", label: "Chat", requiresProfile: false },
  { href: "/profile", label: "Profile", requiresProfile: false },
];

export default function Navbar() {
  const router = useRouter();
  const pathname = usePathname();
  const { profileComplete, tooltipMessage, loading } = useProfileGate();

  async function handleLogout() {
    try {
      await apiPost("/auth/logout");
    } catch {
      // Redirect even if call fails
    }
    router.push("/login");
  }

  return (
    <header className="sticky top-0 z-40 backdrop-blur-xl bg-background/80 border-b border-border">
      <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-primary/40 to-transparent" />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex justify-between items-center">
        <div className="flex items-center gap-6">
          <Link
            href="/dashboard"
            className="text-lg font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent hover:from-blue-300 hover:to-cyan-300 transition-all"
          >
            Talent Inbound OS
          </Link>
          <nav className="hidden sm:flex items-center gap-1">
            {NAV_LINKS.map((link) => {
              const isActive =
                pathname === link.href ||
                (link.href !== "/dashboard" && pathname.startsWith(link.href));
              const isDisabled = link.requiresProfile && !loading && !profileComplete;

              if (isDisabled) {
                return (
                  <span
                    key={link.href}
                    title={tooltipMessage}
                    className="text-sm font-medium px-3 py-1.5 rounded-md text-muted-foreground/40 cursor-not-allowed"
                  >
                    {link.label}
                  </span>
                );
              }

              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`text-sm font-medium px-3 py-1.5 rounded-md transition-all ${
                    isActive
                      ? "text-primary bg-primary/10"
                      : "text-muted-foreground hover:text-foreground hover:bg-muted"
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}
          </nav>
        </div>
        <button
          onClick={handleLogout}
          className="text-sm text-muted-foreground hover:text-foreground px-3 py-1.5 rounded-md border border-border hover:border-primary/30 hover:bg-primary/5 transition-all"
        >
          Logout
        </button>
      </div>
    </header>
  );
}
