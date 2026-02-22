"use client";

import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";

export type ToastVariant = "success" | "error";

export interface ToastMessage {
  id: string;
  message: string;
  variant: ToastVariant;
}

interface ToastProps {
  toast: ToastMessage | null;
}

export function Toast({ toast }: ToastProps) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (toast) {
      setVisible(true);
    } else {
      setVisible(false);
    }
  }, [toast]);

  if (!toast || !visible) return null;

  return (
    <div
      role="alert"
      aria-live="assertive"
      aria-atomic="true"
      className={cn(
        "fixed top-4 left-1/2 -translate-x-1/2 z-50",
        "flex items-center gap-2 px-4 py-3 rounded-lg shadow-lg",
        "text-sm font-medium text-white",
        "animate-in fade-in slide-in-from-top-2 duration-300",
        toast.variant === "success" ? "bg-green-600" : "bg-red-600"
      )}
    >
      {toast.variant === "success" ? (
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-4 w-4 shrink-0"
          viewBox="0 0 20 20"
          fill="currentColor"
          aria-hidden="true"
        >
          <path
            fillRule="evenodd"
            d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
            clipRule="evenodd"
          />
        </svg>
      ) : (
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-4 w-4 shrink-0"
          viewBox="0 0 20 20"
          fill="currentColor"
          aria-hidden="true"
        >
          <path
            fillRule="evenodd"
            d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
            clipRule="evenodd"
          />
        </svg>
      )}
      <span>{toast.message}</span>
    </div>
  );
}

/**
 * Hook for managing toast notifications.
 * Usage:
 *   const { toast, showToast } = useToast();
 *   // In JSX: <Toast toast={toast} />
 *   // To trigger: showToast("Saved!", "success");
 */
export function useToast(durationMs = 3000) {
  const [toast, setToast] = useState<ToastMessage | null>(null);

  function showToast(message: string, variant: ToastVariant) {
    const id = Date.now().toString();
    setToast({ id, message, variant });
    setTimeout(() => setToast(null), durationMs);
  }

  return { toast, showToast };
}
