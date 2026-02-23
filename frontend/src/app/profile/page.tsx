"use client";

import { useCallback, useEffect, useState } from "react";
import { apiGet, apiPut, apiUpload, ApiError } from "@/lib/api";
import Navbar from "@/components/ui/Navbar";
import { Toast, useToast } from "@/components/ui/Toast";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import ProfileForm from "@/components/profile/ProfileForm";
import CVUpload from "@/components/profile/CVUpload";

interface ProfileData {
  display_name: string;
  professional_title: string;
  skills: string[];
  min_salary: number | null;
  preferred_currency: string;
  work_model: string;
  preferred_locations: string[];
  industries: string[];
  cv_filename: string | null;
  follow_up_days: number;
  ghosting_days: number;
  updated_at: string;
}

export default function ProfilePage() {
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const { toast, showToast } = useToast();

  const fetchProfile = useCallback(async () => {
    try {
      const data = await apiGet<ProfileData>("/profile/me");
      setProfile(data);
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) {
        setProfile(null);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProfile();
  }, [fetchProfile]);

  async function handleSave(data: Omit<ProfileData, "cv_filename" | "updated_at">) {
    setSaving(true);
    try {
      const saved = await apiPut<ProfileData>("/profile/me", data);
      setProfile(saved);
      showToast("Profile saved successfully!", "success");
    } catch (err: unknown) {
      if (err instanceof Error) showToast(err.message, "error");
    } finally {
      setSaving(false);
    }
  }

  async function handleUpload(file: File) {
    setUploading(true);
    try {
      await apiUpload("/profile/me/cv", file);
      await fetchProfile();
      showToast("CV uploaded successfully!", "success");
    } catch (err: unknown) {
      if (err instanceof Error) showToast(err.message, "error");
      throw err;
    } finally {
      setUploading(false);
    }
  }

  async function handleSkillsExtracted(skills: string[]) {
    if (!profile) return;
    const previousProfile = profile;
    // Update local state immediately so SkillChips shows the new skills
    const updatedProfile = { ...profile, skills };
    setProfile(updatedProfile);

    // Auto-save the profile with the new skills to the backend
    try {
      const saved = await apiPut<ProfileData>("/profile/me", {
        display_name: updatedProfile.display_name,
        professional_title: updatedProfile.professional_title,
        skills: updatedProfile.skills,
        min_salary: updatedProfile.min_salary,
        preferred_currency: updatedProfile.preferred_currency,
        work_model: updatedProfile.work_model,
        preferred_locations: updatedProfile.preferred_locations,
        industries: updatedProfile.industries,
        follow_up_days: updatedProfile.follow_up_days,
        ghosting_days: updatedProfile.ghosting_days,
      });
      setProfile(saved);
      showToast(`Skills updated (${skills.length} skills)`, "success");
    } catch (err: unknown) {
      setProfile(previousProfile);
      if (err instanceof Error) showToast(err.message, "error");
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar />
        <div className="flex items-center justify-center py-20">
          <p className="text-muted-foreground">Loading profile...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-muted/40">
      <Navbar />
      <Toast toast={toast} />

      <main className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>{profile ? "Edit Profile" : "Create Profile"}</CardTitle>
          </CardHeader>
          <CardContent>
            <ProfileForm initial={profile} onSave={handleSave} loading={saving} />
          </CardContent>
        </Card>

        {profile && (
          <Card>
            <CardHeader>
              <CardTitle>CV / Resume</CardTitle>
            </CardHeader>
            <CardContent>
              <CVUpload
                currentFilename={profile.cv_filename}
                onUpload={handleUpload}
                loading={uploading}
                existingSkills={profile.skills}
                onSkillsExtracted={handleSkillsExtracted}
              />
            </CardContent>
          </Card>
        )}
      </main>
    </div>
  );
}
