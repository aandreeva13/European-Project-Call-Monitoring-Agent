import React, { useEffect, useState } from 'react';
import { FundingCard } from '../types';

interface SharedProjectViewProps {
    projectId: string;
}

const HISTORY_SESSIONS_KEY = 'eurofundfinder:sessions:v1';
const LIKED_PROJECTS_KEY = 'eurofundfinder:liked:v1';

const SharedProjectView: React.FC<SharedProjectViewProps> = ({ projectId }) => {
    const [project, setProject] = useState<FundingCard | null>(null);

    useEffect(() => {
        let foundCard: FundingCard | null = null;
        try {
            // Check liked projects first
            const likedRaw = localStorage.getItem(LIKED_PROJECTS_KEY);
            if (likedRaw) {
                const parsed = JSON.parse(likedRaw);
                if (Array.isArray(parsed)) {
                    foundCard = parsed.find(p => p && p.id === projectId) || null;
                }
            }

            // Check sessions if not found
            if (!foundCard) {
                const sessionsRaw = localStorage.getItem(HISTORY_SESSIONS_KEY);
                if (sessionsRaw) {
                    const parsed = JSON.parse(sessionsRaw);
                    if (Array.isArray(parsed)) {
                        for (const entry of parsed) {
                            const cards = entry?.result?.funding_cards;
                            if (Array.isArray(cards)) {
                                const found = cards.find(c => c && c.id === projectId);
                                if (found) {
                                    foundCard = found;
                                    break;
                                }
                            }
                        }
                    }
                }
            }
        } catch {
            // ignore parsing errors
        }

        setProject(foundCard);
    }, [projectId]);

    const handleReturnHome = () => {
        window.location.hash = '';
    };

    if (!project) {
        return (
            <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-4">
                <div className="bg-white p-8 rounded-xl shadow-lg border border-slate-200 text-center max-w-md w-full">
                    <div className="w-16 h-16 bg-red-100 text-red-500 rounded-full flex items-center justify-center mx-auto mb-4">
                        <span className="material-icons text-3xl">error_outline</span>
                    </div>
                    <h2 className="text-xl font-bold text-slate-900 mb-2">Project Not Found</h2>
                    <p className="text-slate-600 mb-6">
                        The shared project could not be found. It may have been from a session that is no longer available on this device.
                    </p>
                    <button
                        onClick={handleReturnHome}
                        className="w-full py-2.5 bg-primary text-white rounded-lg font-medium hover:bg-primary/90 transition-colors"
                    >
                        Return to App
                    </button>
                </div>
            </div>
        );
    }

    // Format budget safely
    const formatBudget = (budget: string) => {
        if (!budget || budget === 'N/A') return 'Budget N/A';
        const normalized = String(budget).replace(/\s+/g, ' ').trim();
        const matches = normalized.match(/\d[\d\s,.]*/g) || [];
        const parsed = matches
            .map(m => {
                const digits = m.replace(/[^\d]/g, '');
                if (!digits) return null;
                const n = Number(digits);
                return Number.isFinite(n) ? n : null;
            })
            .filter((n): n is number => n !== null);

        const candidates = parsed.filter(n => n >= 10000);

        if (candidates.length > 0) {
            const max = Math.max(...candidates);
            if (max >= 1_000_000_000) return `€${(max / 1_000_000_000).toFixed(1)}B`;
            if (max >= 1_000_000) return `€${(max / 1_000_000).toFixed(1)}M`;
            if (max >= 1_000) return `€${(max / 1_000).toFixed(0)}K`;
            return `€${max}`;
        }
        if (normalized.includes('€') || normalized.toLowerCase().includes('eur')) return normalized;
        return `€${normalized}`;
    };

    return (
        <div className="min-h-screen bg-slate-50 py-8 px-4">
            <div className="max-w-4xl mx-auto space-y-6">

                {/* Header navigation */}
                <div className="flex items-center justify-between bg-white px-6 py-4 rounded-xl shadow-sm border border-slate-200">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center text-primary">
                            <span className="material-icons">folder_shared</span>
                        </div>
                        <div>
                            <h1 className="font-bold text-slate-900 leading-none">Shared Project View</h1>
                            <span className="text-xs text-slate-500">EU Funding Matcher</span>
                        </div>
                    </div>
                    <button
                        onClick={handleReturnHome}
                        className="flex items-center gap-2 px-4 py-2 bg-slate-100 text-slate-600 rounded-lg font-medium hover:bg-slate-200 transition-colors"
                    >
                        <span className="material-icons text-sm">home</span>
                        Back to App
                    </button>
                </div>

                {/* Project Content */}
                <div className="bg-white rounded-xl shadow-lg border border-slate-200 overflow-hidden">
                    <div className="p-8">
                        {/* Header info */}
                        <div className="flex items-start justify-between gap-4 mb-6">
                            <div>
                                {project.eligibility_passed && (
                                    <span className="inline-block px-3 py-1 bg-green-100 text-green-700 text-xs font-bold rounded-full mb-3">
                                        Eligible call
                                    </span>
                                )}
                                <h2 className="text-2xl font-bold text-slate-900 mb-2">{project.title}</h2>
                                {project.programme && (
                                    <p className="text-primary font-medium">{project.programme}</p>
                                )}
                            </div>
                        </div>

                        {/* Quick Stats */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                            <div className="bg-slate-50 rounded-lg p-4 border border-slate-100">
                                <span className="block text-slate-500 text-xs font-semibold uppercase tracking-wider mb-1">Total Budget</span>
                                <span className="font-bold text-slate-900">{formatBudget(project.budget)}</span>
                            </div>
                            <div className="bg-slate-50 rounded-lg p-4 border border-slate-100">
                                <span className="block text-slate-500 text-xs font-semibold uppercase tracking-wider mb-1">EU Contribution</span>
                                <span className="font-bold text-slate-900">{project.contribution && project.contribution !== 'N/A' ? formatBudget(project.contribution) : 'Varies'}</span>
                            </div>
                            <div className="bg-slate-50 rounded-lg p-4 border border-slate-100">
                                <span className="block text-slate-500 text-xs font-semibold uppercase tracking-wider mb-1">Deadline</span>
                                <span className="font-bold text-slate-900">{project.deadline}</span>
                            </div>
                            <div className="bg-slate-50 rounded-lg p-4 border border-slate-100">
                                <span className="block text-slate-500 text-xs font-semibold uppercase tracking-wider mb-1">Status</span>
                                <span className="font-bold text-slate-900 capitalize text-green-600">{project.status}</span>
                            </div>
                        </div>

                        {/* Main Content Area */}
                        <div className="space-y-8">

                            {/* Description */}
                            <div className="bg-slate-50 p-6 rounded-xl border border-slate-100">
                                <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2 mb-3">
                                    <span className="material-icons text-primary">description</span>
                                    Project Overview
                                </h3>
                                <div className="prose prose-slate max-w-none text-slate-700 leading-relaxed text-[15px]">
                                    {(project.project_summary?.overview || project.description || 'No description available.').split('\n').map((paragraph, i) => (
                                        <p key={i} className="mb-2">{paragraph}</p>
                                    ))}
                                </div>
                            </div>

                            {/* Company Fit */}
                            {project.project_summary?.company_fit_assessment && (
                                <div className="bg-purple-50 p-6 rounded-xl border border-purple-100">
                                    <h3 className="text-lg font-bold text-purple-900 flex items-center gap-2 mb-3">
                                        <span className="material-icons text-purple-600">psychology</span>
                                        Strategic Fit Assessment
                                    </h3>
                                    <div className="prose prose-slate max-w-none text-slate-700 leading-relaxed text-[15px]">
                                        {project.project_summary.company_fit_assessment.split('\n').map((paragraph, i) => (
                                            <p key={i} className="mb-2">{paragraph}</p>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Key Alignments & Benefits */}
                            {((project.project_summary?.key_alignment_points && project.project_summary.key_alignment_points.length > 0) || (project.key_benefits && project.key_benefits.length > 0)) && (
                                <div className="bg-green-50 rounded-xl p-6 border border-green-100">
                                    <h3 className="text-lg font-bold text-green-800 flex items-center gap-2 mb-4">
                                        <span className="material-icons">check_circle</span>
                                        Key Strengths & Benefits
                                    </h3>
                                    <ul className="space-y-3">
                                        {(project.project_summary?.key_alignment_points || project.key_benefits || []).map((item, i) => (
                                            <li key={i} className="flex items-start gap-3">
                                                <span className="material-icons text-green-600 text-sm mt-1">done</span>
                                                <span className="text-slate-700">{item}</span>
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}

                            {/* Potential Challenges */}
                            {project.project_summary?.potential_challenges && project.project_summary.potential_challenges.length > 0 && (
                                <div className="bg-orange-50 rounded-xl p-6 border border-orange-100">
                                    <h3 className="text-lg font-bold text-orange-800 flex items-center gap-2 mb-4">
                                        <span className="material-icons text-orange-600">warning</span>
                                        Potential Challenges & Risks
                                    </h3>
                                    <ul className="space-y-3">
                                        {project.project_summary.potential_challenges.map((item, i) => (
                                            <li key={i} className="flex items-start gap-3">
                                                <span className="material-icons text-orange-500 text-sm mt-1">chevron_right</span>
                                                <span className="text-slate-700">{item}</span>
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}

                            {/* Action Items */}
                            {project.action_items && project.action_items.length > 0 && (
                                <div className="bg-eu-blue/5 rounded-xl p-6 border border-eu-blue/10">
                                    <h3 className="text-lg font-bold text-eu-blue flex items-center gap-2 mb-4">
                                        <span className="material-icons">fact_check</span>
                                        Recommended Actions
                                    </h3>
                                    <ul className="space-y-3">
                                        {project.action_items.map((item, i) => (
                                            <li key={i} className="flex items-start gap-3">
                                                <span className="material-icons text-eu-blue text-sm mt-1">arrow_right</span>
                                                <span className="text-slate-700">{item}</span>
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}

                            {/* Tags/Keywords */}
                            {project.tags && project.tags.length > 0 && (
                                <div>
                                    <h3 className="text-sm font-bold text-slate-900 mb-3 uppercase tracking-wider flex items-center gap-2">
                                        <span className="material-icons text-primary text-sm">local_offer</span>
                                        Keywords
                                    </h3>
                                    <div className="flex flex-wrap gap-2">
                                        {project.tags.map((tag, i) => (
                                            <span key={i} className="px-3 py-1.5 bg-slate-100 text-slate-600 rounded-full text-sm font-medium border border-slate-200">
                                                {tag}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Call to Action */}
                            <div className="pt-6 border-t border-slate-200 flex justify-end">
                                <a
                                    href={project.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="flex items-center gap-2 px-6 py-3 bg-eu-blue text-white rounded-lg font-bold hover:bg-eu-blue/90 transition-colors shadow-md"
                                >
                                    View Official Call Page
                                    <span className="material-icons text-sm">open_in_new</span>
                                </a>
                            </div>

                        </div>
                    </div>
                </div>

            </div>
        </div>
    );
};

export default SharedProjectView;
