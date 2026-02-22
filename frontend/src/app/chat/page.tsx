"use client";

import Navbar from "@/components/ui/Navbar";

export default function ChatPage() {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />

      <main className="max-w-7xl mx-auto px-4 py-20">
        <div className="flex flex-col items-center justify-center text-center">
          {/* Icon */}
          <div className="w-16 h-16 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center mb-6">
            <svg className="w-8 h-8 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" />
            </svg>
          </div>

          <h1 className="text-2xl font-bold text-foreground mb-2">AI Chat Assistant</h1>
          <p className="text-muted-foreground max-w-md leading-relaxed">
            Have a conversation with your AI assistant about opportunities, negotiate strategies, and get personalized career advice.
          </p>

          {/* Mock chat bubbles */}
          <div className="mt-10 max-w-sm w-full space-y-3">
            <div className="flex justify-start">
              <div className="bg-muted/50 border border-border rounded-2xl rounded-bl-md px-4 py-2.5 max-w-[80%]">
                <div className="h-3 w-36 bg-muted rounded animate-pulse" />
              </div>
            </div>
            <div className="flex justify-end">
              <div className="bg-primary/15 border border-primary/20 rounded-2xl rounded-br-md px-4 py-2.5 max-w-[80%]">
                <div className="h-3 w-28 bg-primary/20 rounded animate-pulse" />
              </div>
            </div>
            <div className="flex justify-start">
              <div className="bg-muted/50 border border-border rounded-2xl rounded-bl-md px-4 py-2.5 max-w-[80%]">
                <div className="space-y-1.5">
                  <div className="h-3 w-44 bg-muted rounded animate-pulse" />
                  <div className="h-3 w-32 bg-muted rounded animate-pulse" />
                </div>
              </div>
            </div>
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
