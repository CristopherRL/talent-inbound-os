"use client";

import { apiGet, apiPost, apiPatch } from "@/lib/api";

export interface OpportunityListItem {
  id: string;
  company_name: string | null;
  role_title: string | null;
  status: string;
  match_score: number | null;
  missing_fields: string[];
  tech_stack: string[];
  work_model: string | null;
  recruiter_name: string | null;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
}

export interface OpportunityDetail {
  id: string;
  company_name: string | null;
  client_name: string | null;
  role_title: string | null;
  salary_range: string | null;
  tech_stack: string[];
  work_model: string | null;
  recruiter_name: string | null;
  recruiter_type: string | null;
  recruiter_company: string | null;
  match_score: number | null;
  match_reasoning: string | null;
  missing_fields: string[];
  status: string;
  is_archived: boolean;
  interactions: {
    id: string;
    interaction_type: string;
    source: string;
    raw_content: string;
    created_at: string;
  }[];
  status_history: {
    id: string;
    from_status: string;
    to_status: string;
    triggered_by: string;
    is_unusual: boolean;
    note: string | null;
    created_at: string;
  }[];
  draft_responses: {
    id: string;
    response_type: string;
    generated_content: string;
    edited_content: string | null;
    is_final: boolean;
    created_at: string;
  }[];
  created_at: string;
  updated_at: string;
  last_interaction_at: string | null;
}

export interface StaleItem {
  id: string;
  company_name: string | null;
  role_title: string | null;
  status: string;
  last_interaction_at: string | null;
  days_since_interaction: number | null;
}

export interface ChangeStatusResult {
  id: string;
  status: string;
  is_unusual: boolean;
  transition: {
    from_status: string;
    to_status: string;
    triggered_by: string;
    is_unusual: boolean;
    note: string | null;
    created_at: string;
  };
}

export async function fetchOpportunities(
  params?: { status?: string; archived?: string },
): Promise<OpportunityListItem[]> {
  const query = new URLSearchParams();
  if (params?.status) query.set("status", params.status);
  if (params?.archived) query.set("archived", params.archived);
  const qs = query.toString();
  return apiGet<OpportunityListItem[]>(`/opportunities${qs ? `?${qs}` : ""}`);
}

export async function fetchOpportunityDetail(
  id: string,
): Promise<OpportunityDetail> {
  return apiGet<OpportunityDetail>(`/opportunities/${id}`);
}

export async function fetchStaleOpportunities(): Promise<StaleItem[]> {
  return apiGet<StaleItem[]>("/opportunities/stale");
}

export async function changeStatus(
  opportunityId: string,
  newStatus: string,
  note?: string,
): Promise<ChangeStatusResult> {
  return apiPatch<ChangeStatusResult>(`/opportunities/${opportunityId}/status`, {
    new_status: newStatus,
    note,
  });
}

export async function archiveOpportunity(
  opportunityId: string,
): Promise<{ id: string; is_archived: boolean; message: string }> {
  return apiPost(`/opportunities/${opportunityId}/archive`);
}

export async function unarchiveOpportunity(
  opportunityId: string,
): Promise<{ id: string; is_archived: boolean; message: string }> {
  return apiPost(`/opportunities/${opportunityId}/unarchive`);
}
