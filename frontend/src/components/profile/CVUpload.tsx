"use client";

import { useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { apiPost } from "@/lib/api";

interface CVUploadProps {
  currentFilename: string | null;
  onUpload: (file: File) => Promise<void>;
  loading: boolean;
  /** Called after skills are extracted — gives the parent merged or replaced skill list */
  onSkillsExtracted?: (skills: string[], mode: "replace" | "merge") => void;
  /** Existing skills to offer replace/merge dialog */
  existingSkills?: string[];
}

const ACCEPTED_TYPES = ".pdf,.docx,.md";
const MAX_SIZE_MB = 10;

interface ExtractSkillsResponse {
  skills: string[];
}

export default function CVUpload({
  currentFilename,
  onUpload,
  loading,
  onSkillsExtracted,
  existingSkills = [],
}: CVUploadProps) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [error, setError] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [extractedSkills, setExtractedSkills] = useState<string[] | null>(null);
  const [extractDialogOpen, setExtractDialogOpen] = useState(false);
  const [extracting, setExtracting] = useState(false);

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    setError("");
    const file = e.target.files?.[0];
    if (!file) return;

    const ext = file.name.split(".").pop()?.toLowerCase();
    if (!ext || !["pdf", "docx", "md"].includes(ext)) {
      setError("Only PDF, DOCX, and Markdown files are allowed.");
      return;
    }

    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      setError(`File too large. Maximum size is ${MAX_SIZE_MB}MB.`);
      return;
    }

    setSelectedFile(file);
  }

  async function handleUpload() {
    if (!selectedFile) return;
    setError("");
    try {
      await onUpload(selectedFile);
      setSelectedFile(null);
      if (fileRef.current) fileRef.current.value = "";

      // After successful upload, try to extract skills if handler provided
      if (onSkillsExtracted) {
        setExtracting(true);
        try {
          const result = await apiPost<ExtractSkillsResponse>("/profile/me/cv/extract-skills", {});
          if (result.skills.length > 0) {
            setExtractedSkills(result.skills);
            // If user already has skills, show dialog; otherwise apply directly
            if (existingSkills.length > 0) {
              setExtractDialogOpen(true);
            } else {
              onSkillsExtracted(result.skills, "replace");
            }
          }
        } catch {
          // Skill extraction failure is non-fatal — silently ignore
        } finally {
          setExtracting(false);
        }
      }
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Upload failed.");
      }
    }
  }

  function handleReplace() {
    if (extractedSkills && onSkillsExtracted) {
      onSkillsExtracted(extractedSkills, "replace");
    }
    setExtractDialogOpen(false);
    setExtractedSkills(null);
  }

  function handleMerge() {
    if (extractedSkills && onSkillsExtracted) {
      const merged = Array.from(new Set([...existingSkills, ...extractedSkills]));
      onSkillsExtracted(merged, "merge");
    }
    setExtractDialogOpen(false);
    setExtractedSkills(null);
  }

  function handleSkipExtraction() {
    setExtractDialogOpen(false);
    setExtractedSkills(null);
  }

  return (
    <>
      <div className="space-y-3">
        <label className="block text-sm font-medium text-foreground">CV Upload</label>

        {currentFilename && (
          <p className="text-sm text-muted-foreground">
            Current file: <span className="font-medium text-foreground">{currentFilename}</span>
          </p>
        )}

        <div className="flex items-center gap-3">
          <input
            ref={fileRef}
            type="file"
            accept={ACCEPTED_TYPES}
            onChange={handleFileChange}
            className="block w-full text-sm text-foreground file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-primary/10 file:text-primary hover:file:bg-primary/20"
          />
          <Button
            type="button"
            onClick={handleUpload}
            disabled={!selectedFile || loading || extracting}
            variant="default"
            size="sm"
            className="whitespace-nowrap"
          >
            {loading ? "Uploading..." : extracting ? "Extracting..." : "Upload"}
          </Button>
        </div>

        <p className="text-xs text-muted-foreground">Accepted: PDF, DOCX, Markdown. Max 10MB.</p>

        {error && <p className="text-sm text-destructive">{error}</p>}
      </div>

      {/* Replace/Merge dialog */}
      <Dialog open={extractDialogOpen} onOpenChange={setExtractDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Skills extracted from CV</DialogTitle>
          </DialogHeader>
          <p className="text-sm text-muted-foreground">
            Found <strong>{extractedSkills?.length}</strong> skills in your CV. What would you
            like to do with your existing {existingSkills.length} skills?
          </p>
          <div className="flex flex-wrap gap-1 mt-2 max-h-32 overflow-y-auto">
            {extractedSkills?.slice(0, 20).map((s) => (
              <span
                key={s}
                className="inline-flex items-center rounded-full bg-primary/10 px-2 py-0.5 text-xs text-primary"
              >
                {s}
              </span>
            ))}
            {(extractedSkills?.length ?? 0) > 20 && (
              <span className="text-xs text-muted-foreground">
                +{(extractedSkills?.length ?? 0) - 20} more
              </span>
            )}
          </div>
          <DialogFooter className="flex gap-2 mt-4">
            <Button variant="outline" onClick={handleSkipExtraction}>
              Keep existing
            </Button>
            <Button variant="outline" onClick={handleMerge}>
              Merge with existing
            </Button>
            <Button onClick={handleReplace}>
              Replace all
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
