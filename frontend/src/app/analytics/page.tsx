"use client";

import Navbar from "@/components/ui/Navbar";

export default function AnalyticsPage() {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />

      <main className="max-w-7xl mx-auto px-4 py-20">
        <div className="flex flex-col items-center justify-center text-center">
          {/* Icon */}
          <div className="w-16 h-16 rounded-2xl bg-chart-2/10 border border-chart-2/20 flex items-center justify-center mb-6">
            <svg className="w-8 h-8 text-chart-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
            </svg>
          </div>

          <h1 className="text-2xl font-bold text-foreground mb-2">Analytics Dashboard</h1>
          <p className="text-muted-foreground max-w-md leading-relaxed">
            Track your opportunity pipeline, match score trends, response rates, and recruiter source breakdown.
          </p>

          <div className="mt-10 grid grid-cols-3 gap-4 max-w-lg w-full">
            {[
              { label: "Pipeline Funnel", h: "h-24" },
              { label: "Score Distribution", h: "h-20" },
              { label: "Source Breakdown", h: "h-16" },
            ].map((item) => (
              <div key={item.label} className="flex flex-col items-center gap-2">
                <div className={`w-full ${item.h} rounded-lg bg-muted/50 border border-border animate-pulse`} />
                <span className="text-xs text-muted-foreground">{item.label}</span>
              </div>
            ))}
          </div>

          <div className="mt-8 flex items-center gap-2 text-sm text-muted-foreground">
            <div className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
            Under construction
          </div>
        </div>
      </main>
    </div>
  );
}
