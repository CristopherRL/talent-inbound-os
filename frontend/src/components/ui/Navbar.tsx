"use client";

import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import { apiPost } from "@/lib/api";
import { useProfileGate } from "@/hooks/use-profile-gate";

const NAV_LINKS = [
  { href: "/dashboard", label: "Dashboard", requiresProfile: false },
  { href: "/ingest", label: "New Offer", requiresProfile: true },
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
    <header className="bg-white shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
        <div className="flex items-center gap-6">
          <Link href="/dashboard" className="text-xl font-bold text-gray-900 hover:text-gray-700">
            Talent Inbound OS
          </Link>
          <nav className="hidden sm:flex items-center gap-4">
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
                    className="text-sm font-medium px-2 py-1 rounded text-gray-400 cursor-not-allowed"
                  >
                    {link.label}
                  </span>
                );
              }

              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`text-sm font-medium px-2 py-1 rounded transition-colors ${
                    isActive
                      ? "text-blue-700 bg-blue-50"
                      : "text-gray-600 hover:text-gray-900 hover:bg-gray-50"
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
          className="text-sm text-gray-600 hover:text-gray-900 px-3 py-1.5 rounded border border-gray-300 hover:border-gray-400 transition-colors"
        >
          Logout
        </button>
      </div>
    </header>
  );
}
