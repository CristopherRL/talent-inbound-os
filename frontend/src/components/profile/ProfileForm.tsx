"use client";

import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import SkillChips from "@/components/profile/SkillChips";

interface ProfileData {
  display_name: string;
  professional_title: string;
  skills: string[];
  min_salary: number | null;
  preferred_currency: string;
  work_model: string;
  preferred_locations: string[];
  industries: string[];
  follow_up_days: number;
  ghosting_days: number;
}

interface ProfileFormProps {
  initial: ProfileData | null;
  onSave: (data: ProfileData) => Promise<void>;
  loading: boolean;
}

const WORK_MODELS = ["REMOTE", "HYBRID", "ONSITE"];
const MIN_SKILLS = 3;

function RequiredMark() {
  return <span className="text-destructive ml-0.5">*</span>;
}

function FieldLabel({ htmlFor, children }: { htmlFor?: string; children: React.ReactNode }) {
  return (
    <label htmlFor={htmlFor} className="block text-sm font-medium text-foreground mb-1.5">
      {children}
    </label>
  );
}

function FieldHint({ children }: { children: React.ReactNode }) {
  return <p className="mt-1 text-xs text-destructive">{children}</p>;
}

function parseList(value: string): string[] {
  return value.split(",").map((s) => s.trim()).filter(Boolean);
}

export default function ProfileForm({ initial, onSave, loading }: ProfileFormProps) {
  const [displayName, setDisplayName] = useState(initial?.display_name ?? "");
  const [professionalTitle, setProfessionalTitle] = useState(initial?.professional_title ?? "");
  const [skills, setSkills] = useState<string[]>(initial?.skills ?? []);

  // Sync skills when parent updates them externally (e.g., CV skill extraction)
  const prevSkillsRef = useRef(initial?.skills);
  useEffect(() => {
    const prev = prevSkillsRef.current;
    const next = initial?.skills;
    if (next && prev !== next && JSON.stringify(prev) !== JSON.stringify(next)) {
      setSkills(next);
      prevSkillsRef.current = next;
    }
  }, [initial?.skills]);
  const [minSalary, setMinSalary] = useState(initial?.min_salary?.toString() ?? "");
  const [currency, setCurrency] = useState(initial?.preferred_currency ?? "EUR");
  const [workModel, setWorkModel] = useState(initial?.work_model ?? "");
  const [locations, setLocations] = useState(initial?.preferred_locations?.join(", ") ?? "");
  const [industries, setIndustries] = useState(initial?.industries?.join(", ") ?? "");
  const [followUpDays, setFollowUpDays] = useState(initial?.follow_up_days?.toString() ?? "7");
  const [ghostingDays, setGhostingDays] = useState(initial?.ghosting_days?.toString() ?? "14");

  const salaryNum = minSalary ? parseInt(minSalary) : null;

  const isComplete =
    displayName.trim().length > 0 &&
    professionalTitle.trim().length > 0 &&
    skills.length >= MIN_SKILLS &&
    salaryNum !== null &&
    salaryNum > 0 &&
    workModel.trim().length > 0;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    await onSave({
      display_name: displayName,
      professional_title: professionalTitle,
      skills,
      min_salary: salaryNum,
      preferred_currency: currency || "EUR",
      work_model: workModel,
      preferred_locations: parseList(locations),
      industries: parseList(industries),
      follow_up_days: parseInt(followUpDays) || 7,
      ghosting_days: parseInt(ghostingDays) || 14,
    });
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <p className="text-xs text-muted-foreground">
        Fields marked with <span className="text-destructive">*</span> are required to submit offers.
      </p>

      <div>
        <FieldLabel htmlFor="displayName">Name <RequiredMark /></FieldLabel>
        <Input
          id="displayName"
          type="text"
          value={displayName}
          onChange={(e) => setDisplayName(e.target.value)}
          placeholder="Your name"
        />
        {!displayName.trim() && <FieldHint>Required to submit offers</FieldHint>}
      </div>

      <div>
        <FieldLabel htmlFor="professionalTitle">Professional Title <RequiredMark /></FieldLabel>
        <Input
          id="professionalTitle"
          type="text"
          value={professionalTitle}
          onChange={(e) => setProfessionalTitle(e.target.value)}
          placeholder="e.g., Senior Backend Engineer"
        />
        {!professionalTitle.trim() && <FieldHint>Required to submit offers</FieldHint>}
      </div>

      <div>
        <FieldLabel>Skills <RequiredMark /></FieldLabel>
        <SkillChips skills={skills} onChange={setSkills} />
        {skills.length < MIN_SKILLS && (
          <FieldHint>
            {skills.length === 0
              ? `Add at least ${MIN_SKILLS} skills`
              : `${skills.length}/${MIN_SKILLS} skills — add ${MIN_SKILLS - skills.length} more`}
          </FieldHint>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <FieldLabel htmlFor="minSalary">Minimum Salary <RequiredMark /></FieldLabel>
          <Input
            id="minSalary"
            type="number"
            value={minSalary}
            onChange={(e) => setMinSalary(e.target.value)}
            placeholder="80000"
          />
          {(salaryNum === null || salaryNum <= 0) && (
            <FieldHint>Required to submit offers</FieldHint>
          )}
        </div>
        <div>
          <FieldLabel htmlFor="currency">Currency</FieldLabel>
          <Input
            id="currency"
            type="text"
            maxLength={3}
            value={currency}
            onChange={(e) => setCurrency(e.target.value.toUpperCase())}
            placeholder="EUR"
          />
        </div>
      </div>

      <div>
        <FieldLabel htmlFor="workModel">Work Model <RequiredMark /></FieldLabel>
        <Select value={workModel} onValueChange={setWorkModel}>
          <SelectTrigger id="workModel">
            <SelectValue placeholder="— Select —" />
          </SelectTrigger>
          <SelectContent>
            {WORK_MODELS.map((m) => (
              <SelectItem key={m} value={m}>
                {m}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {!workModel.trim() && <FieldHint>Required to submit offers</FieldHint>}
      </div>

      <div>
        <FieldLabel htmlFor="locations">Preferred Locations (comma-separated)</FieldLabel>
        <Input
          id="locations"
          type="text"
          value={locations}
          onChange={(e) => setLocations(e.target.value)}
          placeholder="Spain, EU Remote"
        />
      </div>

      <div>
        <FieldLabel htmlFor="industries">Industries (comma-separated)</FieldLabel>
        <Input
          id="industries"
          type="text"
          value={industries}
          onChange={(e) => setIndustries(e.target.value)}
          placeholder="FinTech, HealthTech"
        />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <FieldLabel htmlFor="followUpDays">Follow-up alert (days)</FieldLabel>
          <Input
            id="followUpDays"
            type="number"
            min={1}
            max={90}
            value={followUpDays}
            onChange={(e) => setFollowUpDays(e.target.value)}
          />
        </div>
        <div>
          <FieldLabel htmlFor="ghostingDays">Ghosting threshold (days)</FieldLabel>
          <Input
            id="ghostingDays"
            type="number"
            min={1}
            max={180}
            value={ghostingDays}
            onChange={(e) => setGhostingDays(e.target.value)}
          />
        </div>
      </div>

      <Button
        type="submit"
        disabled={loading || !isComplete}
        className="w-full"
      >
        {loading ? "Saving..." : "Save Profile"}
      </Button>

      {!isComplete && (
        <p className="text-center text-xs text-muted-foreground">
          Fill all required fields to enable saving
        </p>
      )}
    </form>
  );
}
