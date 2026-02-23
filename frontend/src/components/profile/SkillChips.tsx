"use client";

import { useState, useRef } from "react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";

interface SkillChipsProps {
  skills: string[];
  onChange: (skills: string[]) => void;
  disabled?: boolean;
  placeholder?: string;
}

export default function SkillChips({
  skills,
  onChange,
  disabled = false,
  placeholder = "Add skill...",
}: SkillChipsProps) {
  const [inputVisible, setInputVisible] = useState(false);
  const [inputValue, setInputValue] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  function removeSkill(index: number) {
    if (disabled) return;
    onChange(skills.filter((_, i) => i !== index));
  }

  function showInput() {
    setInputVisible(true);
    setTimeout(() => inputRef.current?.focus(), 0);
  }

  function addSkill() {
    const trimmed = inputValue.trim();
    if (trimmed && !skills.includes(trimmed)) {
      onChange([...skills, trimmed]);
    }
    setInputValue("");
    setInputVisible(false);
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") {
      e.preventDefault();
      addSkill();
    }
    if (e.key === "Escape") {
      setInputValue("");
      setInputVisible(false);
    }
  }

  return (
    <div className="flex flex-wrap gap-1.5 min-h-[2.5rem] p-2 border border-input rounded-md bg-background">
      {skills.map((skill, idx) => (
        <Badge
          key={skill}
          variant="secondary"
          className={cn(
            "flex items-center gap-1 pr-1 text-sm",
            disabled && "opacity-70"
          )}
        >
          {skill}
          {!disabled && (
            <button
              type="button"
              onClick={() => removeSkill(idx)}
              aria-label={`Remove ${skill}`}
              className="ml-0.5 rounded-full hover:bg-muted-foreground/20 p-0.5 leading-none"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-3 w-3"
                viewBox="0 0 20 20"
                fill="currentColor"
                aria-hidden="true"
              >
                <path
                  fillRule="evenodd"
                  d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                  clipRule="evenodd"
                />
              </svg>
            </button>
          )}
        </Badge>
      ))}

      {!disabled && (
        inputVisible ? (
          <input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            onBlur={addSkill}
            placeholder={placeholder}
            className="text-sm border-none outline-none bg-transparent min-w-[8rem] flex-1"
          />
        ) : (
          <button
            type="button"
            onClick={showInput}
            aria-label="Add skill"
            className="flex items-center gap-0.5 text-sm text-muted-foreground hover:text-foreground transition-colors px-1"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-3.5 w-3.5"
              viewBox="0 0 20 20"
              fill="currentColor"
              aria-hidden="true"
            >
              <path
                fillRule="evenodd"
                d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z"
                clipRule="evenodd"
              />
            </svg>
            Add
          </button>
        )
      )}
    </div>
  );
}
