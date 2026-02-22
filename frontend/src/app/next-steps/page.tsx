"use client";

import Navbar from "@/components/ui/Navbar";

export default function NextStepsPage() {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />

      <main className="max-w-7xl mx-auto px-4 py-20">
        <div className="flex flex-col items-center justify-center text-center">
          {/* Icon */}
          <div className="w-16 h-16 rounded-2xl bg-chart-5/10 border border-chart-5/20 flex items-center justify-center mb-6">
            <svg className="w-8 h-8 text-chart-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>

          <h1 className="text-2xl font-bold text-foreground mb-2">Next Steps</h1>
          <p className="text-muted-foreground max-w-md leading-relaxed">
            Personalized action items, follow-up reminders, and ghosting alerts to keep your opportunities moving forward.
          </p>

          {/* Mock action items */}
          <div className="mt-10 max-w-sm w-full space-y-2">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="flex items-center gap-3 bg-muted/50 border border-border rounded-lg p-3"
              >
                <div className="w-5 h-5 rounded-full border-2 border-border shrink-0" />
                <div className="flex-1 space-y-1">
                  <div className={`h-3 bg-muted rounded animate-pulse`} style={{ width: `${70 - i * 10}%` }} />
                  <div className="h-2 w-20 bg-muted/60 rounded animate-pulse" />
                </div>
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
