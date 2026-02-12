"use client";

import { useRouter } from "next/navigation";
import { apiPost } from "@/lib/api";

export default function DashboardPage() {
  const router = useRouter();

  async function handleLogout() {
    try {
      await apiPost("/auth/logout");
    } catch {
      // Even if the API call fails, clear local state
    }
    router.push("/login");
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <h1 className="text-xl font-bold text-gray-900">
            Talent Inbound OS
          </h1>
          <div className="flex items-center gap-4">
            <a href="/profile" className="text-sm text-blue-600 hover:text-blue-500">
              Profile
            </a>
            <button
              onClick={handleLogout}
              className="text-sm text-gray-600 hover:text-gray-900 px-3 py-1 rounded border border-gray-300 hover:border-gray-400"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow p-6 text-center">
          <h2 className="text-lg font-medium text-gray-900">
            Welcome to your Dashboard
          </h2>
          <p className="mt-2 text-gray-600">
            Your opportunities will appear here once you start ingesting recruiter messages.
          </p>
          <p className="mt-4 text-sm text-gray-400">
            This is a placeholder — full dashboard implementation coming in Phase 8 (US6).
          </p>
        </div>
      </main>
    </div>
  );
}
