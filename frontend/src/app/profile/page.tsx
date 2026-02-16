"use client";

import { useCallback, useEffect, useState } from "react";
import { apiGet, apiPut, apiUpload, ApiError } from "@/lib/api";
import Navbar from "@/components/ui/Navbar";
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
  const [toast, setToast] = useState<{ message: string; type: "success" | "error" } | null>(null);

  function showToast(message: string, type: "success" | "error") {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  }

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
      if (err instanceof Error) {
        showToast(err.message, "error");
      }
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
      if (err instanceof Error) {
        showToast(err.message, "error");
      }
      throw err;
    } finally {
      setUploading(false);
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="flex items-center justify-center py-20">
          <p className="text-gray-500">Loading profile...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <main className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Toast notification */}
        {toast && (
          <div
            className={`px-4 py-3 rounded text-sm ${
              toast.type === "success"
                ? "bg-green-50 border border-green-200 text-green-700"
                : "bg-red-50 border border-red-200 text-red-700"
            }`}
          >
            {toast.message}
          </div>
        )}

        {/* Profile form */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">
            {profile ? "Edit Profile" : "Create Profile"}
          </h2>
          <ProfileForm initial={profile} onSave={handleSave} loading={saving} />
        </div>

        {/* CV upload — only show after profile exists */}
        {profile && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">CV / Resume</h2>
            <CVUpload
              currentFilename={profile.cv_filename}
              onUpload={handleUpload}
              loading={uploading}
            />
          </div>
        )}
      </main>
    </div>
  );
}
