"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";

interface ProfileSnapshot {
  display_name: string;
  professional_title: string;
  skills: string[];
  min_salary: number | null;
  work_model: string;
}

const REQUIRED_SKILLS_COUNT = 3;

export function isProfileComplete(p: ProfileSnapshot): boolean {
  return (
    !!p.display_name.trim() &&
    !!p.professional_title.trim() &&
    p.skills.length >= REQUIRED_SKILLS_COUNT &&
    p.min_salary !== null &&
    p.min_salary > 0 &&
    !!p.work_model.trim()
  );
}

export function getMissingFields(p: ProfileSnapshot): string[] {
  const missing: string[] = [];
  if (!p.display_name.trim()) missing.push("Name");
  if (!p.professional_title.trim()) missing.push("Professional Title");
  if (p.skills.length < REQUIRED_SKILLS_COUNT)
    missing.push(`At least ${REQUIRED_SKILLS_COUNT} Skills`);
  if (p.min_salary === null || p.min_salary <= 0) missing.push("Minimum Salary");
  if (!p.work_model.trim()) missing.push("Work Model");
  return missing;
}

/**
 * Hook that checks if the current user's profile is complete enough
 * to allow creating new offers. Returns loading state, completeness,
 * and a tooltip message listing missing fields.
 */
export function useProfileGate() {
  const [profileComplete, setProfileComplete] = useState(false);
  const [missingFields, setMissingFields] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function check() {
      try {
        const p = await apiGet<ProfileSnapshot>("/profile/me");
        const complete = isProfileComplete(p);
        setProfileComplete(complete);
        setMissingFields(complete ? [] : getMissingFields(p));
      } catch {
        // If profile fetch fails (e.g. no profile yet), treat as incomplete
        setProfileComplete(false);
        setMissingFields(["Name", "Professional Title", `At least ${REQUIRED_SKILLS_COUNT} Skills`, "Minimum Salary", "Work Model"]);
      } finally {
        setLoading(false);
      }
    }
    check();
  }, []);

  const tooltipMessage = missingFields.length > 0
    ? `Complete your profile first: ${missingFields.join(", ")}`
    : "";

  return { profileComplete, missingFields, tooltipMessage, loading };
}
