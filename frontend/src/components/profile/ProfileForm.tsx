"use client";

import { useState } from "react";

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

const WORK_MODELS = ["", "REMOTE", "HYBRID", "ONSITE"];
const MIN_SKILLS = 3;

function RequiredMark() {
  return <span className="text-red-500 ml-0.5">*</span>;
}

export default function ProfileForm({ initial, onSave, loading }: ProfileFormProps) {
  const [displayName, setDisplayName] = useState(initial?.display_name ?? "");
  const [professionalTitle, setProfessionalTitle] = useState(initial?.professional_title ?? "");
  const [skills, setSkills] = useState(initial?.skills?.join(", ") ?? "");
  const [minSalary, setMinSalary] = useState(initial?.min_salary?.toString() ?? "");
  const [currency, setCurrency] = useState(initial?.preferred_currency ?? "EUR");
  const [workModel, setWorkModel] = useState(initial?.work_model ?? "");
  const [locations, setLocations] = useState(initial?.preferred_locations?.join(", ") ?? "");
  const [industries, setIndustries] = useState(initial?.industries?.join(", ") ?? "");
  const [followUpDays, setFollowUpDays] = useState(initial?.follow_up_days?.toString() ?? "7");
  const [ghostingDays, setGhostingDays] = useState(initial?.ghosting_days?.toString() ?? "14");

  function parseList(value: string): string[] {
    return value
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
  }

  const parsedSkills = parseList(skills);
  const salaryNum = minSalary ? parseInt(minSalary) : null;

  const isComplete =
    displayName.trim().length > 0 &&
    professionalTitle.trim().length > 0 &&
    parsedSkills.length >= MIN_SKILLS &&
    salaryNum !== null &&
    salaryNum > 0 &&
    workModel.trim().length > 0;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    await onSave({
      display_name: displayName,
      professional_title: professionalTitle,
      skills: parsedSkills,
      min_salary: salaryNum,
      preferred_currency: currency || "EUR",
      work_model: workModel,
      preferred_locations: parseList(locations),
      industries: parseList(industries),
      follow_up_days: parseInt(followUpDays) || 7,
      ghosting_days: parseInt(ghostingDays) || 14,
    });
  }

  const inputClass =
    "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 text-sm text-gray-900 placeholder:text-gray-400";
  const labelClass = "block text-sm font-medium text-gray-700";
  const hintClass = "mt-1 text-xs text-red-500";

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <p className="text-xs text-gray-500">
        Fields marked with <span className="text-red-500">*</span> are required to submit offers.
      </p>

      <div>
        <label htmlFor="displayName" className={labelClass}>Name <RequiredMark /></label>
        <input
          id="displayName"
          type="text"
          value={displayName}
          onChange={(e) => setDisplayName(e.target.value)}
          className={inputClass}
          placeholder="Your name"
        />
        {!displayName.trim() && (
          <p className={hintClass}>Required to submit offers</p>
        )}
      </div>

      <div>
        <label htmlFor="professionalTitle" className={labelClass}>Professional Title <RequiredMark /></label>
        <input
          id="professionalTitle"
          type="text"
          value={professionalTitle}
          onChange={(e) => setProfessionalTitle(e.target.value)}
          className={inputClass}
          placeholder="e.g., Senior Backend Engineer"
        />
        {!professionalTitle.trim() && (
          <p className={hintClass}>Required to submit offers</p>
        )}
      </div>

      <div>
        <label htmlFor="skills" className={labelClass}>
          Skills (comma-separated) <RequiredMark />
        </label>
        <input
          id="skills"
          type="text"
          value={skills}
          onChange={(e) => setSkills(e.target.value)}
          className={inputClass}
          placeholder="Python, FastAPI, PostgreSQL"
        />
        {parsedSkills.length < MIN_SKILLS && (
          <p className={hintClass}>
            {parsedSkills.length === 0
              ? `Add at least ${MIN_SKILLS} skills`
              : `${parsedSkills.length}/${MIN_SKILLS} skills — add ${MIN_SKILLS - parsedSkills.length} more`}
          </p>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="minSalary" className={labelClass}>Minimum Salary <RequiredMark /></label>
          <input
            id="minSalary"
            type="number"
            value={minSalary}
            onChange={(e) => setMinSalary(e.target.value)}
            className={inputClass}
            placeholder="80000"
          />
          {(salaryNum === null || salaryNum <= 0) && (
            <p className={hintClass}>Required to submit offers</p>
          )}
        </div>
        <div>
          <label htmlFor="currency" className={labelClass}>Currency</label>
          <input
            id="currency"
            type="text"
            maxLength={3}
            value={currency}
            onChange={(e) => setCurrency(e.target.value.toUpperCase())}
            className={inputClass}
            placeholder="EUR"
          />
        </div>
      </div>

      <div>
        <label htmlFor="workModel" className={labelClass}>Work Model <RequiredMark /></label>
        <select
          id="workModel"
          value={workModel}
          onChange={(e) => setWorkModel(e.target.value)}
          className={inputClass}
        >
          {WORK_MODELS.map((m) => (
            <option key={m} value={m}>
              {m || "— Select —"}
            </option>
          ))}
        </select>
        {!workModel.trim() && (
          <p className={hintClass}>Required to submit offers</p>
        )}
      </div>

      <div>
        <label htmlFor="locations" className={labelClass}>Preferred Locations (comma-separated)</label>
        <input
          id="locations"
          type="text"
          value={locations}
          onChange={(e) => setLocations(e.target.value)}
          className={inputClass}
          placeholder="Spain, EU Remote"
        />
      </div>

      <div>
        <label htmlFor="industries" className={labelClass}>Industries (comma-separated)</label>
        <input
          id="industries"
          type="text"
          value={industries}
          onChange={(e) => setIndustries(e.target.value)}
          className={inputClass}
          placeholder="FinTech, HealthTech"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="followUpDays" className={labelClass}>Follow-up alert (days)</label>
          <input
            id="followUpDays"
            type="number"
            min={1}
            max={90}
            value={followUpDays}
            onChange={(e) => setFollowUpDays(e.target.value)}
            className={inputClass}
          />
        </div>
        <div>
          <label htmlFor="ghostingDays" className={labelClass}>Ghosting threshold (days)</label>
          <input
            id="ghostingDays"
            type="number"
            min={1}
            max={180}
            value={ghostingDays}
            onChange={(e) => setGhostingDays(e.target.value)}
            className={inputClass}
          />
        </div>
      </div>

      <button
        type="submit"
        disabled={loading || !isComplete}
        className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading ? "Saving..." : "Save Profile"}
      </button>
      {!isComplete && (
        <p className="text-center text-xs text-gray-400">
          Fill all required fields to enable saving
        </p>
      )}
    </form>
  );
}
