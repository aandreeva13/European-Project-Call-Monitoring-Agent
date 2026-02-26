import React, { useEffect, useMemo, useState } from "react";
import type { FundingCard } from "../types";

const HISTORY_SESSIONS_KEY = "eurofundfinder:sessions:v1";
const LIKED_PROJECTS_KEY = "eurofundfinder:liked:v1";

type SessionEntry = {
  id: string;
  createdAt: number;
  company?: any;
  result?: any;
};

type LikedProject = FundingCard & {
  searchContext?: {
    companyName: string;
    sessionId?: string;
    searchedAt?: number;
  };
};

type Props = {
  projectId: string;
};

function safeParseJson<T>(raw: string | null): T | null {
  if (!raw) return null;
  try {
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

function findProjectInSessions(projectId: string): FundingCard | null {
  const sessions = safeParseJson<SessionEntry[]>(localStorage.getItem(HISTORY_SESSIONS_KEY));
  if (!Array.isArray(sessions)) return null;

  for (const entry of sessions) {
    const cards = entry?.result?.funding_cards;
    if (Array.isArray(cards)) {
      const found = cards.find((c: any) => c?.id === projectId);
      if (found) return found as FundingCard;
    }
  }

  return null;
}

function findProjectInLiked(projectId: string): FundingCard | null {
  const liked = safeParseJson<LikedProject[]>(localStorage.getItem(LIKED_PROJECTS_KEY));
  if (!Array.isArray(liked)) return null;
  const found = liked.find((c) => c?.id === projectId);
  return (found as FundingCard) || null;
}

const formatBudget = (budget: string) => {
  if (!budget || budget === "N/A") return "Budget N/A";

  const normalized = String(budget).replace(/\s+/g, " ").trim();

  const matches = normalized.match(/\d[\d\s,.]*/g) || [];
  const parsed = matches
    .map((m) => {
      const digits = m.replace(/[^\d]/g, "");
      if (!digits) return null;
      const n = Number(digits);
      return Number.isFinite(n) ? n : null;
    })
    .filter((n): n is number => n !== null);

  const candidates = parsed.filter((n) => n >= 10000);

  if (candidates.length > 0) {
    const max = Math.max(...candidates);
    if (max >= 1_000_000_000) return `€${(max / 1_000_000_000).toFixed(1)}B`;
    if (max >= 1_000_000) return `€${(max / 1_000_000).toFixed(1)}M`;
    if (max >= 1_000) return `€${(max / 1_000).toFixed(0)}K`;
    return `€${max}`;
  }

  if (normalized.includes("€") || normalized.toLowerCase().includes("eur")) return normalized;
  return `€${normalized}`;
};

function SectionCard({ title, icon, children }: { title: string; icon: string; children: React.ReactNode }) {
  return (
    <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-lg border border-slate-200 dark:border-slate-800 p-6">
      <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
        <span className="material-icons text-primary">{icon}</span>
        {title}
      </h3>
      {children}
    </div>
  );
}

export default function SharedProjectView({ projectId }: Props): React.ReactElement {
  const [project, setProject] = useState<FundingCard | null>(null);

  useEffect(() => {
    // This view is opened in a new tab via `#shared/<id>`.
    // We can only render data available locally (localStorage).
    const fromSessions = findProjectInSessions(projectId);
    const fromLiked = findProjectInLiked(projectId);
    setProject(fromSessions || fromLiked);
  }, [projectId]);

  const shareUrl = useMemo(() => {
    try {
      return `${window.location.origin}${window.location.pathname}#shared/${encodeURIComponent(projectId)}`;
    } catch {
      return `#shared/${encodeURIComponent(projectId)}`;
    }
  }, [projectId]);

  if (!project) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="text-center py-20">
          <div className="inline-flex items-center justify-center p-3 mb-6 bg-blue-500/10 rounded-full">
            <span className="material-icons text-blue-600 text-4xl">link</span>
          </div>
          <h2 className="text-2xl font-extrabold text-slate-900 dark:text-white">Shared project</h2>
          <p className="mt-3 text-slate-600 dark:text-slate-400 max-w-xl mx-auto">
            This project is not available in this browser yet.
          </p>

          <div className="mt-6 p-4 bg-slate-50 dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 text-left">
            <div className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
              Share URL
            </div>
            <div className="font-mono text-xs text-slate-700 dark:text-slate-200 break-all">{shareUrl}</div>
          </div>

          <p className="mt-6 text-sm text-slate-500 dark:text-slate-400 max-w-xl mx-auto">
            This view loads the project from your local browser cache (stored results / liked projects).
            Run a search in this browser first (or like the project), then open the share link again.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-200 dark:border-blue-800 text-blue-800 dark:text-blue-200 text-xs font-semibold">
              <span className="material-icons text-sm">link</span>
              Shared project view
            </div>
            <h1 className="mt-3 text-3xl font-extrabold text-slate-900 dark:text-white leading-tight">
              {project.title || "Shared project"}
            </h1>
            <div className="mt-2 text-sm text-slate-500 dark:text-slate-400">
              <span className="font-mono">id: {project.id}</span>
            </div>
          </div>

          {project.url && (
            <a
              href={project.url}
              target="_blank"
              rel="noopener noreferrer"
              className="shrink-0 px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors font-semibold flex items-center gap-2"
            >
              <span>Open official call</span>
              <span className="material-icons text-[18px]">open_in_new</span>
            </a>
          )}
        </div>

        {/* Meta badges */}
        <div className="mt-5 flex flex-wrap gap-3">
          <span
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 text-sm font-semibold"
            title="Profile match based on your inputs and the call text. Not a funding success prediction."
          >
            <span className="material-icons text-[18px] text-primary">verified</span>
            {project.match_percentage}% Profile match
          </span>

          {project.eligibility_passed && (
            <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-900 text-green-700 dark:text-green-300 text-sm font-semibold">
              <span className="material-icons text-[18px]">check_circle</span>
              Eligible
            </span>
          )}

          {project.success_probability && (
            <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-900 text-blue-700 dark:text-blue-300 text-sm font-semibold">
              <span className="material-icons text-[18px]">insights</span>
              {project.success_probability} success
            </span>
          )}

          {project.programme && (
            <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-900 text-purple-700 dark:text-purple-300 text-sm font-semibold">
              <span className="material-icons text-[18px]">hub</span>
              {project.programme}
            </span>
          )}

          {project.budget && project.budget !== "N/A" && (
            <span
              className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 text-sm font-semibold"
              title="Total indicative topic budget (may be split across multiple grants)"
            >
              <span className="material-icons text-[18px]">account_balance</span>
              {formatBudget(project.budget)}
            </span>
          )}

          {project.deadline && (
            <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-900 text-red-700 dark:text-red-300 text-sm font-semibold">
              <span className="material-icons text-[18px]">event</span>
              {project.deadline}
            </span>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="grid grid-cols-1 gap-6">
        <SectionCard title="Summary" icon="description">
          <p className="text-slate-700 dark:text-slate-300 leading-relaxed whitespace-pre-wrap">
            {project.short_summary || project.description || ""}
          </p>
        </SectionCard>

        {project.project_summary?.overview && (
          <SectionCard title="Project overview" icon="description">
            <p className="text-slate-700 dark:text-slate-300 leading-relaxed whitespace-pre-wrap">
              {project.project_summary.overview}
            </p>
          </SectionCard>
        )}

        {project.why_recommended && (
          <SectionCard title="Why recommended" icon="person_check">
            <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-5 border-l-4 border-green-500">
              <p className="text-slate-700 dark:text-slate-300 leading-relaxed whitespace-pre-wrap">
                {project.why_recommended}
              </p>
            </div>
          </SectionCard>
        )}

        {(project.key_benefits?.length ?? 0) > 0 && (
          <SectionCard title="Key benefits" icon="stars">
            <ul className="space-y-3">
              {project.key_benefits.map((benefit, i) => (
                <li key={i} className="flex items-start gap-3 bg-slate-50 dark:bg-slate-800 rounded-lg p-3">
                  <span className="material-icons text-green-500 text-lg">check_circle</span>
                  <span className="text-slate-700 dark:text-slate-300">{benefit}</span>
                </li>
              ))}
            </ul>
          </SectionCard>
        )}

        {(project.action_items?.length ?? 0) > 0 && (
          <SectionCard title="Recommended actions" icon="task_alt">
            <div className="space-y-3">
              {project.action_items.map((action, i) => (
                <div key={i} className="flex items-start gap-3 bg-amber-50 dark:bg-amber-900/20 rounded-lg p-4 border-l-4 border-amber-500">
                  <span className="material-icons text-amber-600 text-lg">arrow_forward</span>
                  <span className="text-slate-700 dark:text-slate-300 font-medium">{action}</span>
                </div>
              ))}
            </div>
          </SectionCard>
        )}

        {(project.suggested_partners?.length ?? 0) > 0 && (
          <SectionCard title="Suggested partners" icon="groups">
            <ul className="space-y-3">
              {project.suggested_partners.map((partner, i) => (
                <li key={i} className="flex items-start gap-3 rounded-lg p-3">
                  <span className="material-icons text-slate-400 text-lg mt-0.5">business</span>
                  <span className="text-slate-700 dark:text-slate-300">{partner}</span>
                </li>
              ))}
            </ul>
          </SectionCard>
        )}

        {(project.tags?.length ?? 0) > 0 && (
          <SectionCard title="Tags" icon="label">
            <div className="flex flex-wrap gap-2">
              {project.tags.map((tag, i) => (
                <span
                  key={i}
                  className="px-3 py-1.5 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-sm rounded-lg font-medium"
                >
                  #{tag}
                </span>
              ))}
            </div>
          </SectionCard>
        )}

        {/* Footer */}
        <div className="p-5 bg-slate-50 dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700">
          <div className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
            Share URL
          </div>
          <div className="font-mono text-xs text-slate-700 dark:text-slate-200 break-all">{shareUrl}</div>
        </div>
      </div>
    </div>
  );
}
