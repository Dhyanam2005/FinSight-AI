"use client";

import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import RevenueChart from "@/components/RevenueChart";
import MarginChart from "@/components/MarginChart";

// ── Inline SVG icons (no extra dependencies) ─────────────────────────────────
const RefreshIcon = () => (
  <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8" />
    <path d="M21 3v5h-5" />
    <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16" />
    <path d="M8 16H3v5" />
  </svg>
);
const ExportIcon = () => (
  <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline points="14 2 14 8 20 8" />
    <line x1="12" y1="18" x2="12" y2="12" />
    <polyline points="9 15 12 18 15 15" />
  </svg>
);
const FileIcon = () => (
  <svg className="w-5 h-5 text-zinc-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline points="14 2 14 8 20 8" />
    <line x1="16" y1="13" x2="8" y2="13" />
    <line x1="16" y1="17" x2="8" y2="17" />
    <polyline points="10 9 9 9 8 9" />
  </svg>
);
const CheckCircleIcon = () => (
  <svg className="w-4 h-4 text-green-400 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
    <polyline points="22 4 12 14.01 9 11.01" />
  </svg>
);
const WarningIcon = ({ className = "w-4 h-4" }: { className?: string }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
    <line x1="12" y1="9" x2="12" y2="13" />
    <line x1="12" y1="17" x2="12.01" y2="17" />
  </svg>
);
const AlertIcon = () => (
  <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10" />
    <line x1="12" y1="8" x2="12" y2="12" />
    <line x1="12" y1="16" x2="12.01" y2="16" />
  </svg>
);
const ChartIcon = () => (
  <svg className="w-10 h-10 text-zinc-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <line x1="18" y1="20" x2="18" y2="10" />
    <line x1="12" y1="20" x2="12" y2="4" />
    <line x1="6" y1="20" x2="6" y2="14" />
    <line x1="2" y1="20" x2="22" y2="20" />
  </svg>
);
const ForecastIcon = () => (
  <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="22 7 13.5 15.5 8.5 10.5 2 17" />
    <polyline points="16 7 22 7 22 13" />
  </svg>
);
const ThesisIcon = () => (
  <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10" />
    <path d="M12 8v4l3 3" />
    <path d="M9.5 9.5a5 5 0 0 1 7.43 6.43" />
  </svg>
);
const ChevronUpIcon = () => (
  <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="18 15 12 9 6 15" />
  </svg>
);
const ChevronDownIcon = () => (
  <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="6 9 12 15 18 9" />
  </svg>
);
const RiskDot = ({ level }: { level: string }) => (
  <span className={`w-2 h-2 rounded-full inline-block mr-1.5 ${
    level === "High" ? "bg-red-400" : level === "Medium" ? "bg-yellow-400" : "bg-green-400"
  }`} />
);

interface KPIData {
  total_companies: number;
  total_reports: number;
  avg_revenue_growth: number;
  avg_operating_margin: number;
}

interface ComparisonRow {
  company: string;
  quarter: string;
  revenue_growth: number;
  operating_margin: number;
  net_income_growth: number;
  investment_score: number;
}

interface TrendPoint {
  company?: string;
  quarter: string;
  revenue_growth: number;
  operating_margin: number;
  investment_score?: number;
  insights?: string[];
  is_forecast?: boolean;
  rg_anomaly?: boolean;
  om_anomaly?: boolean;
  risk?: { level: string; color: string };
}

interface SentimentData {
  company: string;
  quarter: string;
  sentiment: string;
  score: number;
  tone: string;
}

interface ScoreData {
  company: string;
  growth_score: number;
  risk_score: number;
  innovation_score: number;
  overall_score: number;
  predicted_revenue_growth: number | null;
  predicted_operating_margin: number | null;
  revenue_volatility: number;
  margin_volatility: number;
}

interface UploadedFile {
  filename: string;
  company: string;
  quarters: number;
  pages: number;
}

interface ComparisonPair {
  company1: string;
  company2: string;
  comparison: string;
}

function ScoreBar({ label, value, color }: {
  label: string; value: number; color: string;
}) {
  const pct = Math.min(100, (value / 10) * 100);
  return (
    <div className="mb-3">
      <div className="flex justify-between text-sm mb-1">
        <span className="text-zinc-400 text-xs">{label}</span>
        <span className="font-semibold text-xs text-white">{value.toFixed(1)}</span>
      </div>
      <div className="w-full bg-zinc-700 rounded-full h-1.5">
        <div className={`h-1.5 rounded-full transition-all duration-500 ${color}`}
          style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

function scoreColor(s: number) {
  return s >= 7 ? "text-green-400" : s >= 4 ? "text-yellow-400" : "text-red-400";
}
function scoreBg(s: number) {
  return s >= 7 ? "border-green-800" : s >= 4 ? "border-yellow-800" : "border-red-800";
}
function scoreLabel(s: number) {
  return s >= 7 ? "Strong" : s >= 4 ? "Moderate" : "Weak";
}
function riskBadge(level: string) {
  if (level === "High") return "bg-red-900/50 text-red-300 border border-red-800";
  if (level === "Medium") return "bg-yellow-900/50 text-yellow-300 border border-yellow-800";
  return "bg-green-900/50 text-green-300 border border-green-800";
}

// ── Skeleton loader ──
function SkeletonCard() {
  return (
    <div className="bg-[#2f2f2f] border border-zinc-800 rounded-xl p-4 animate-pulse">
      <div className="h-3 bg-zinc-700 rounded w-1/2 mb-3" />
      <div className="h-7 bg-zinc-700 rounded w-1/3" />
    </div>
  );
}

function SkeletonSection() {
  return (
    <section>
      <div className="h-3 bg-zinc-800 rounded w-32 mb-3 animate-pulse" />
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {[...Array(4)].map((_, i) => <SkeletonCard key={i} />)}
      </div>
    </section>
  );
}

export default function DashboardPage() {
  const [kpis, setKpis] = useState<KPIData | null>(null);
  const [comparisonData, setComparisonData] = useState<ComparisonRow[]>([]);
  const [comparisons, setComparisons] = useState<ComparisonPair[]>([]);
  const [expandedPair, setExpandedPair] = useState<string | null>(null);
  const [trendData, setTrendData] = useState<Record<string, TrendPoint[]>>({});
  const [sentiments, setSentiments] = useState<SentimentData[]>([]);
  const [scores, setScores] = useState<ScoreData[]>([]);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [thesis, setThesis] = useState<Record<string, string>>({});
  const [thesisLoading, setThesisLoading] = useState<Record<string, boolean>>({});

  useEffect(() => {
    fetchDashboard();
    const interval = setInterval(fetchDashboard, 30000);
    window.addEventListener("session-reset", fetchDashboard);
    window.addEventListener("pdf-uploaded", fetchDashboard);
    return () => {
      clearInterval(interval);
      window.removeEventListener("session-reset", fetchDashboard);
      window.removeEventListener("pdf-uploaded", fetchDashboard);
    };
  }, []);

  async function fetchDashboard() {
    try {
      setError(null);
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/dashboard`);
      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      const data = await res.json();
      setKpis(data.kpis || null);
      setComparisonData(data.comparison_table || []);
      setComparisons(data.comparisons || []);
      setTrendData(data.trend_data || {});
      setSentiments(data.sentiments || []);
      setScores(data.scores || []);
      setUploadedFiles(data.uploaded_files || []);
    } catch (e) {
      console.error("Dashboard fetch failed:", e);
      setError("Failed to load dashboard. Is the backend running?");
    } finally {
      setLoading(false);
    }
  }

  async function generateThesis(company: string) {
    setThesisLoading((prev) => ({ ...prev, [company]: true }));
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/thesis`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ company }),
      });
      const data = await res.json();
      setThesis((prev) => ({ ...prev, [company]: data.thesis }));
    } catch (e) {
      console.error("Thesis failed:", e);
    } finally {
      setThesisLoading((prev) => ({ ...prev, [company]: false }));
    }
  }

  const anomalies: {
    company: string; quarter: string; type: string; value: number;
  }[] = [];
  Object.entries(trendData).forEach(([company, trends]) => {
    trends.forEach((t) => {
      if (!t.is_forecast) {
        if (t.rg_anomaly) anomalies.push({ company, quarter: t.quarter, type: "Revenue Growth", value: t.revenue_growth });
        if (t.om_anomaly) anomalies.push({ company, quarter: t.quarter, type: "Operating Margin", value: t.operating_margin });
      }
    });
  });

  // ── Loading skeleton ──
  if (loading) {
    return (
      <div className="min-h-screen bg-[#212121] text-white">
        <div className="border-b border-zinc-700 px-6 py-4 flex items-center justify-between">
          <h1 className="text-xl font-semibold text-white">FinSight AI Dashboard</h1>
          <div className="h-4 w-32 bg-zinc-800 rounded animate-pulse" />
        </div>
        <div className="max-w-6xl mx-auto px-6 py-8 space-y-10">
          <SkeletonSection />
          <SkeletonSection />
        </div>
      </div>
    );
  }

  // ── Error state ──
  if (error) {
    return (
      <div className="min-h-screen bg-[#212121] text-white flex flex-col items-center justify-center gap-4">
        <WarningIcon className="w-10 h-10 text-yellow-500" />
        <p className="text-zinc-300 font-semibold">{error}</p>
        <button
          onClick={fetchDashboard}
          className="text-sm bg-white text-black px-4 py-2 rounded-lg hover:bg-zinc-200 transition"
        >
          Try Again
        </button>
        <a href="/" className="text-zinc-500 text-sm hover:text-white transition">
          ← Back to Chat
        </a>
      </div>
    );
  }

  // ── Empty state ──
  if (uploadedFiles.length === 0) {
    return (
      <div className="min-h-screen bg-[#212121] text-white">
        <div className="border-b border-zinc-700 px-6 py-4 flex items-center justify-between sticky top-0 bg-[#212121] z-10">
          <h1 className="text-xl font-semibold text-white">FinSight AI Dashboard</h1>
          <a href="/" className="text-sm text-zinc-400 hover:text-white transition px-3 py-1">
            ← Chat
          </a>
        </div>
        <div className="flex flex-col items-center justify-center h-[80vh] gap-4">
          <ChartIcon />
          <p className="text-zinc-300 font-semibold">No documents uploaded yet</p>
          <p className="text-zinc-500 text-sm">Upload a financial PDF in the chat to see analysis here.</p>
          <a href="/"
            className="text-sm bg-white text-black px-4 py-2 rounded-lg hover:bg-zinc-200 transition">
            ← Upload a PDF
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#212121] text-white">

      {/* HEADER */}
      <div className="border-b border-zinc-700 px-6 py-4 flex items-center justify-between sticky top-0 bg-[#212121] z-10">
        <h1 className="text-xl font-semibold text-white">FinSight AI Dashboard</h1>
        <div className="flex gap-2">
          <a href="/" className="text-sm text-zinc-400 hover:text-white transition px-3 py-1">
            ← Chat
          </a>
          <button onClick={fetchDashboard}
            className="flex items-center gap-1.5 text-sm text-zinc-400 hover:text-white border border-zinc-700 px-3 py-1.5 rounded-lg transition">
            <RefreshIcon /> Refresh
          </button>
          <button onClick={() => window.open(`${process.env.NEXT_PUBLIC_API_URL}/export/pdf`, "_blank")}
            className="flex items-center gap-1.5 text-sm bg-white text-black px-3 py-1.5 rounded-lg font-semibold hover:bg-zinc-200 transition">
            <ExportIcon /> Export PDF
          </button>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-6 py-8 space-y-10">

        {/* UPLOADED DOCUMENTS */}
        <section>
          <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-3">
            Loaded Documents ({uploadedFiles.length})
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {uploadedFiles.map((file, idx) => (
              <div key={idx}
                className="bg-[#2f2f2f] border border-zinc-700 rounded-xl px-4 py-3 flex items-center gap-3">
                <FileIcon />
                <div className="min-w-0 flex-1">
                  <p className="font-medium text-sm truncate text-white">{file.filename}</p>
                  <p className="text-zinc-400 text-xs">{file.company}</p>
                  <p className="text-zinc-500 text-xs">{file.quarters} quarters · {file.pages} pages</p>
                </div>
                <CheckCircleIcon />
              </div>
            ))}
          </div>
        </section>

        {/* KPI CARDS */}
        {kpis && (
          <section>
            <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-3">
              Portfolio Overview
            </h2>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
              {[
                { label: "Companies", value: kpis.total_companies },
                { label: "Reports", value: kpis.total_reports },
                { label: "Avg Revenue Growth", value: `${kpis.avg_revenue_growth?.toFixed(2)}%` },
                { label: "Avg Operating Margin", value: `${kpis.avg_operating_margin?.toFixed(2)}%` },
              ].map((kpi) => (
                <div key={kpi.label} className="bg-[#2f2f2f] border border-zinc-700 rounded-xl p-4">
                  <p className="text-zinc-400 text-xs mb-1">{kpi.label}</p>
                  <p className="text-2xl font-bold text-white">{kpi.value}</p>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* ANOMALY ALERTS */}
        {anomalies.length > 0 && (
          <section>
            <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-3">
                <span className="flex items-center gap-1.5"><AlertIcon /> Anomaly Detection</span>
            </h2>
            <div className="space-y-2">
              {anomalies.map((a, idx) => (
                <div key={idx}
                  className="bg-red-900/20 border border-red-800 rounded-xl px-4 py-3 flex items-center gap-3 text-sm">
                  <WarningIcon className="w-4 h-4 text-red-400 shrink-0" />
                  <span className="font-semibold text-red-300">{a.company}</span>
                  <span className="text-zinc-500">·</span>
                  <span className="text-zinc-300">{a.quarter}</span>
                  <span className="text-zinc-500">·</span>
                  <span className="text-red-300">
                    {a.type} of <strong>{a.value}%</strong> is anomalous
                  </span>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* FINANCIAL HEALTH SCORES */}
        {scores.length > 0 && (
          <section>
            <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-3">
              Financial Health Scores
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {scores.map((s) => (
                <div key={s.company}
                  className={`bg-[#2f2f2f] border rounded-xl p-5 ${scoreBg(s.overall_score)}`}>
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-semibold text-white">{s.company}</h3>
                    <div className="text-right">
                      <p className={`text-2xl font-bold ${scoreColor(s.overall_score)}`}>
                        {s.overall_score.toFixed(1)}
                        <span className="text-sm text-zinc-500">/10</span>
                      </p>
                      <p className={`text-xs font-semibold ${scoreColor(s.overall_score)}`}>
                        {scoreLabel(s.overall_score)}
                      </p>
                    </div>
                  </div>
                  <ScoreBar label="Growth" value={s.growth_score} color="bg-blue-500" />
                  <ScoreBar label="Risk Safety" value={s.risk_score} color="bg-green-500" />
                  <ScoreBar label="Innovation" value={s.innovation_score} color="bg-purple-500" />

                  {(s.predicted_revenue_growth !== null || s.predicted_operating_margin !== null) && (
                    <div className="mt-4 pt-3 border-t border-zinc-700">
                      <p className="text-xs text-zinc-500 uppercase tracking-wide mb-2 flex items-center gap-1">
                        <ForecastIcon /> Next Quarter Forecast
                      </p>
                      <div className="grid grid-cols-2 gap-2">
                        {s.predicted_revenue_growth !== null && (
                          <div className="bg-zinc-800 rounded-lg p-2 text-center">
                            <p className="text-xs text-zinc-400">Rev Growth</p>
                            <p className={`font-bold text-sm ${s.predicted_revenue_growth >= 0 ? "text-green-400" : "text-red-400"}`}>
                              {s.predicted_revenue_growth}%
                            </p>
                          </div>
                        )}
                        {s.predicted_operating_margin !== null && (
                          <div className="bg-zinc-800 rounded-lg p-2 text-center">
                            <p className="text-xs text-zinc-400">Op Margin</p>
                            <p className={`font-bold text-sm ${s.predicted_operating_margin >= 5 ? "text-green-400" : "text-red-400"}`}>
                              {s.predicted_operating_margin}%
                            </p>
                          </div>
                        )}
                        <div className="bg-zinc-800 rounded-lg p-2 text-center">
                          <p className="text-xs text-zinc-400">Rev Volatility</p>
                          <p className="font-bold text-sm text-yellow-400">{s.revenue_volatility}%</p>
                        </div>
                        <div className="bg-zinc-800 rounded-lg p-2 text-center">
                          <p className="text-xs text-zinc-400">Margin Volatility</p>
                          <p className="font-bold text-sm text-yellow-400">{s.margin_volatility}%</p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </section>
        )}

        {/* COMPANY COMPARISON TABLE */}
        <section>
          <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-3">
            Company Comparison
          </h2>
          <div className="bg-[#2f2f2f] border border-zinc-700 rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-zinc-700">
                  <th className="text-left px-4 py-3 text-zinc-400 font-medium">Company</th>
                  <th className="text-left px-4 py-3 text-zinc-400 font-medium">Quarter</th>
                  <th className="text-left px-4 py-3 text-zinc-400 font-medium">Rev Growth</th>
                  <th className="text-left px-4 py-3 text-zinc-400 font-medium">Op Margin</th>
                  <th className="text-left px-4 py-3 text-zinc-400 font-medium">Net Inc Growth</th>
                  <th className="text-left px-4 py-3 text-zinc-400 font-medium">Risk</th>
                </tr>
              </thead>
              <tbody>
                {(() => {
                  const riskMap: Record<string, string> = {};
                  Object.values(trendData).forEach((trends) => {
                    trends.forEach((t) => {
                      if (!t.is_forecast && t.risk) {
                        riskMap[`${t.company}-${t.quarter}`] = t.risk.level;
                      }
                    });
                  });
                  return comparisonData?.map((row, idx) => {
                    const riskLevel = riskMap[`${row.company}-${row.quarter}`] || "Low";
                    return (
                      <tr key={idx} className="border-t border-zinc-800 hover:bg-zinc-800/50 transition">
                        <td className="px-4 py-3 font-medium text-white">{row.company}</td>
                        <td className="px-4 py-3 text-zinc-300">{row.quarter}</td>
                        <td className={`px-4 py-3 font-semibold ${row.revenue_growth >= 0 ? "text-green-400" : "text-red-400"}`}>
                          {row.revenue_growth}%
                        </td>
                        <td className={`px-4 py-3 font-semibold ${row.operating_margin >= 10 ? "text-green-400" : row.operating_margin >= 5 ? "text-yellow-400" : "text-red-400"}`}>
                          {row.operating_margin}%
                        </td>
                        <td className="px-4 py-3 text-zinc-300">{row.net_income_growth}%</td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-0.5 rounded-lg text-xs font-semibold ${riskBadge(riskLevel)}`}>
                            <RiskDot level={riskLevel} />{riskLevel}
                          </span>
                        </td>
                      </tr>
                    );
                  });
                })()}
              </tbody>
            </table>
          </div>
        </section>

        {/* ANALYST COMPARISONS */}
        {comparisons.length > 0 && (
          <section>
            <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-3">
              AI Analyst Comparisons ({comparisons.length} pair{comparisons.length > 1 ? "s" : ""})
            </h2>
            <div className="space-y-3">
              {comparisons.map((pair, idx) => {
                const key = `${pair.company1}-${pair.company2}`;
                const isOpen = expandedPair === key;
                return (
                  <div key={idx} className="bg-[#2f2f2f] border border-zinc-700 rounded-xl overflow-hidden">
                    <button
                      onClick={() => setExpandedPair(isOpen ? null : key)}
                      className="w-full flex items-center justify-between px-5 py-4 hover:bg-zinc-800/50 transition text-left"
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-white font-semibold">{pair.company1}</span>
                        <span className="text-zinc-500 text-sm">vs</span>
                        <span className="text-white font-semibold">{pair.company2}</span>
                      </div>
                      <span className="text-zinc-500 flex items-center gap-1 text-xs">
                        {isOpen ? <><ChevronUpIcon /> Collapse</> : <><ChevronDownIcon /> Expand</>}
                      </span>
                    </button>
                    {isOpen && (
                      <div className="px-5 pb-5 border-t border-zinc-700 pt-4 text-sm text-zinc-300 leading-relaxed prose prose-invert prose-sm max-w-none">
                        <ReactMarkdown
                          components={{
                            h1: ({ children }) => <h1 className="text-lg font-bold text-white mb-2">{children}</h1>,
                            h2: ({ children }) => <h2 className="text-base font-bold text-white mb-2 mt-4">{children}</h2>,
                            strong: ({ children }) => <strong className="text-white font-semibold">{children}</strong>,
                            p: ({ children }) => <p className="mb-3 text-zinc-300">{children}</p>,
                            ul: ({ children }) => <ul className="list-disc list-inside mb-3 space-y-1">{children}</ul>,
                            li: ({ children }) => <li className="text-zinc-300">{children}</li>,
                            hr: () => <hr className="border-zinc-700 my-4" />,
                          }}
                        >
                          {pair.comparison}
                        </ReactMarkdown>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </section>
        )}

        {/* SENTIMENT */}
        {sentiments.length > 0 && (
          <section>
            <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-3">
              Financial Sentiment
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {sentiments.map((item, idx) => (
                <div key={idx} className="bg-[#2f2f2f] border border-zinc-700 rounded-xl p-4">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="font-semibold text-white">{item.company}</h3>
                    <span className={`text-xs font-semibold px-2 py-0.5 rounded-lg ${
                      item.sentiment === "positive"
                        ? "bg-green-900/50 text-green-400 border border-green-800"
                        : item.sentiment === "negative"
                        ? "bg-red-900/50 text-red-400 border border-red-800"
                        : "bg-yellow-900/50 text-yellow-400 border border-yellow-800"
                    }`}>
                      {item.sentiment}
                    </span>
                  </div>
                  <p className="text-zinc-500 text-xs mb-3">{item.quarter}</p>
                  <div className="space-y-1 text-sm">
                    <div className="flex justify-between">
                      <span className="text-zinc-400">Confidence</span>
                      <span className="text-white font-medium">{(item.score * 100).toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-zinc-400">Tone</span>
                      <span className="text-white font-medium">{item.tone}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* CHARTS */}
        <section>
          <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-3">
            Revenue Growth Trend
          </h2>
          <div className="bg-[#2f2f2f] border border-zinc-700 rounded-xl p-5">
            <p className="text-zinc-500 text-xs mb-4">Solid = actual · Dotted = forecast</p>
            <RevenueChart
              data={Object.entries(trendData || {}).flatMap(([company, trends]) =>
                trends.map((t) => ({ ...t, company }))
              )}
            />
          </div>
        </section>

        <section>
          <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-3">
            Operating Margin Trend
          </h2>
          <div className="bg-[#2f2f2f] border border-zinc-700 rounded-xl p-5">
            <p className="text-zinc-500 text-xs mb-4">Solid = actual · Dotted = forecast</p>
            <MarginChart
              data={Object.entries(trendData || {}).flatMap(([company, trends]) =>
                trends.map((t) => ({ ...t, company }))
              )}
            />
          </div>
        </section>

        {/* AI INSIGHTS */}
        <section>
          <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-3">
            AI Financial Insights
          </h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {Object.entries(trendData || {}).map(([company, trends]) => {
              const actual = trends.filter((t) => !t.is_forecast);
              const latest = actual[actual.length - 1];
              if (!latest) return null;
              return (
                <div key={company} className="bg-[#2f2f2f] border border-zinc-700 rounded-xl p-5">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="font-semibold text-white">{company}</h3>
                    <div className="flex gap-2">
                      {latest.risk && (
                        <span className={`px-2 py-0.5 rounded-lg text-xs font-semibold ${riskBadge(latest.risk.level)}`}>
                          <RiskDot level={latest.risk.level} />{latest.risk.level}
                        </span>
                      )}
                    </div>
                  </div>
                  <p className="text-zinc-500 text-xs mb-3">Latest: {latest.quarter}</p>
                  <div className="space-y-2 mb-4">
                    {latest.insights?.map((insight, i) => (
                      <div key={i} className="bg-zinc-800 rounded-lg p-3 text-zinc-200 text-sm">
                        {insight}
                      </div>
                    ))}
                  </div>
                  <button
                    onClick={() => generateThesis(company)}
                    disabled={thesisLoading[company]}
                    className="w-full py-2 bg-zinc-700 hover:bg-zinc-600 rounded-lg text-sm font-medium transition disabled:opacity-50 text-white"
                  >
                    {thesisLoading[company] ? (
                      <span className="flex items-center justify-center gap-2">
                        <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10" strokeOpacity="0.25"/><path d="M12 2a10 10 0 0 1 10 10" strokeLinecap="round"/></svg>
                        Generating...
                      </span>
                    ) : (
                      <span className="flex items-center justify-center gap-2"><ThesisIcon /> Generate Investment Thesis</span>
                    )}
                  </button>
                  {thesis[company] && (
                    <div className="mt-3 bg-zinc-800 rounded-lg p-4 text-sm prose prose-invert prose-sm max-w-none">
                      <ReactMarkdown
                        components={{
                          h1: ({ children }) => <h1 className="text-base font-bold text-white mb-2">{children}</h1>,
                          h2: ({ children }) => <h2 className="text-sm font-bold text-white mb-1 mt-3">{children}</h2>,
                          strong: ({ children }) => <strong className="text-white font-semibold">{children}</strong>,
                          p: ({ children }) => <p className="mb-2 text-zinc-300 leading-relaxed">{children}</p>,
                          ul: ({ children }) => <ul className="list-disc list-inside mb-2 space-y-0.5">{children}</ul>,
                          li: ({ children }) => <li className="text-zinc-300">{children}</li>,
                          hr: () => <hr className="border-zinc-700 my-3" />,
                        }}
                      >
                        {thesis[company]}
                      </ReactMarkdown>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </section>

      </div>
    </div>
  );
}