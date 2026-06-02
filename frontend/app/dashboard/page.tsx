"use client";

import { useEffect, useState } from "react";
import RevenueChart from "@/components/RevenueChart";
import MarginChart from "@/components/MarginChart";

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

// ── Score bar ──────────────────────────────────────────
function ScoreBar({ label, value, color }: {
  label: string; value: number; color: string;
}) {
  const pct = Math.min(100, (value / 10) * 100);
  return (
    <div className="mb-3">
      <div className="flex justify-between text-sm mb-1">
        <span className="text-zinc-400">{label}</span>
        <span className="font-semibold">{value.toFixed(1)}</span>
      </div>
      <div className="w-full bg-zinc-700 rounded-full h-2">
        <div className={`h-2 rounded-full transition-all duration-500 ${color}`}
          style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

function scoreColor(s: number) {
  return s >= 7 ? "text-green-400" : s >= 4 ? "text-yellow-400" : "text-red-400";
}
function scoreBg(s: number) {
  return s >= 7 ? "border-green-700 bg-green-900/20"
    : s >= 4 ? "border-yellow-700 bg-yellow-900/20"
    : "border-red-700 bg-red-900/20";
}
function scoreLabel(s: number) {
  return s >= 7 ? "Strong" : s >= 4 ? "Moderate" : "Weak";
}
function riskBadge(level: string) {
  if (level === "High")   return "bg-red-900 text-red-300";
  if (level === "Medium") return "bg-yellow-900 text-yellow-300";
  return "bg-green-900 text-green-300";
}

export default function DashboardPage() {
  const [kpis, setKpis]               = useState<KPIData | null>(null);
  const [comparisonData, setComparisonData] = useState<ComparisonRow[]>([]);
  const [trendData, setTrendData]     = useState<Record<string, TrendPoint[]>>({});
  const [sentiments, setSentiments]   = useState<SentimentData[]>([]);
  const [scores, setScores]           = useState<ScoreData[]>([]);
  const [loading, setLoading]         = useState(true);
  const [thesis, setThesis]           = useState<Record<string, string>>({});
  const [thesisLoading, setThesisLoading] = useState<Record<string, boolean>>({});

  useEffect(() => {
    fetchDashboard();
    const interval = setInterval(fetchDashboard, 30000);
    return () => clearInterval(interval);
  }, []);

  async function fetchDashboard() {
    try {
      const res  = await fetch("http://localhost:8000/dashboard");
      if (!res.ok) throw new Error("Failed");
      const data = await res.json();
      setKpis(data.kpis || null);
      setComparisonData(data.comparison_table || []);
      setTrendData(data.trend_data || {});
      setSentiments(data.sentiments || []);
      setScores(data.scores || []);
    } catch (e) {
      console.error("Dashboard fetch failed:", e);
    } finally {
      setLoading(false);
    }
  }

  async function generateThesis(company: string) {
    setThesisLoading((prev) => ({ ...prev, [company]: true }));
    try {
      const res  = await fetch("http://localhost:8000/thesis", {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ company }),
      });
      const data = await res.json();
      setThesis((prev) => ({ ...prev, [company]: data.thesis }));
    } catch (e) {
      console.error("Thesis failed:", e);
    } finally {
      setThesisLoading((prev) => ({ ...prev, [company]: false }));
    }
  }

  // ── Anomalies across all companies ────────────────────
  const anomalies: { company: string; quarter: string; type: string; value: number }[] = [];
  Object.entries(trendData).forEach(([company, trends]) => {
    trends.forEach((t) => {
      if (!t.is_forecast) {
        if (t.rg_anomaly) anomalies.push({ company, quarter: t.quarter, type: "Revenue Growth", value: t.revenue_growth });
        if (t.om_anomaly) anomalies.push({ company, quarter: t.quarter, type: "Operating Margin", value: t.operating_margin });
      }
    });
  });

  if (loading) {
    return <div className="min-h-screen bg-black text-white p-10">Loading dashboard...</div>;
  }

  return (
    <div className="min-h-screen bg-black text-white p-10">

      {/* HEADER */}
      <div className="flex items-center justify-between mb-12">
        <h1 className="text-5xl font-bold">FinSight AI Dashboard</h1>
        <div className="flex gap-3">
          <button onClick={fetchDashboard}
            className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-white rounded-xl text-sm border border-zinc-600 transition">
            🔄 Refresh
          </button>
          <button onClick={() => window.open("http://localhost:8000/export/pdf", "_blank")}
            className="px-4 py-2 bg-white hover:bg-zinc-200 text-black rounded-xl text-sm font-semibold transition">
            📄 Export PDF
          </button>
        </div>
      </div>

      {/* KPI CARDS */}
      {kpis && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
          {[
            { label: "Companies",          value: kpis.total_companies },
            { label: "Reports",            value: kpis.total_reports },
            { label: "Avg Revenue Growth", value: `${kpis.avg_revenue_growth?.toFixed(2)}%` },
            { label: "Avg Operating Margin", value: `${kpis.avg_operating_margin?.toFixed(2)}%` },
          ].map((kpi) => (
            <div key={kpi.label} className="bg-zinc-900 p-6 rounded-2xl border border-zinc-800">
              <h2 className="text-zinc-400 mb-2">{kpi.label}</h2>
              <p className="text-4xl font-bold">{kpi.value}</p>
            </div>
          ))}
        </div>
      )}

      {/* ANOMALY ALERTS */}
      {anomalies.length > 0 && (
        <div className="mb-16">
          <h2 className="text-4xl font-bold mb-6">🚨 Anomaly Detection</h2>
          <div className="space-y-3">
            {anomalies.map((a, idx) => (
              <div key={idx}
                className="bg-red-900/20 border border-red-700 rounded-xl px-5 py-4 flex items-center gap-4">
                <span className="text-red-400 text-xl">⚠️</span>
                <div>
                  <span className="font-bold text-red-300">{a.company}</span>
                  <span className="text-zinc-400 mx-2">•</span>
                  <span className="text-zinc-300">{a.quarter}</span>
                  <span className="text-zinc-400 mx-2">•</span>
                  <span className="text-red-300">
                    {a.type} of <strong>{a.value}%</strong> is statistically anomalous
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* FINANCIAL HEALTH SCORES + EARNINGS PREDICTOR */}
      {scores.length > 0 && (
        <div className="mb-16">
          <h2 className="text-4xl font-bold mb-8">Financial Health Score</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {scores.map((s) => (
              <div key={s.company}
                className={`rounded-2xl border p-6 ${scoreBg(s.overall_score)}`}>
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-2xl font-bold">{s.company}</h3>
                  <div className="text-right">
                    <p className={`text-4xl font-bold ${scoreColor(s.overall_score)}`}>
                      {s.overall_score.toFixed(1)}
                      <span className="text-lg text-zinc-400">/10</span>
                    </p>
                    <p className={`text-sm font-semibold ${scoreColor(s.overall_score)}`}>
                      {scoreLabel(s.overall_score)}
                    </p>
                  </div>
                </div>
                <ScoreBar label="Growth"     value={s.growth_score}     color="bg-blue-500" />
                <ScoreBar label="Risk Safety" value={s.risk_score}      color="bg-green-500" />
                <ScoreBar label="Innovation" value={s.innovation_score} color="bg-purple-500" />

                {/* Earnings Predictor */}
                {(s.predicted_revenue_growth !== null || s.predicted_operating_margin !== null) && (
                  <div className="mt-4 pt-4 border-t border-zinc-700">
                    <p className="text-xs text-zinc-400 uppercase tracking-wide mb-2">
                      🔮 Next Quarter Forecast
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
                    </div>
                    <div className="grid grid-cols-2 gap-2 mt-2">
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
        </div>
      )}

      {/* COMPANY COMPARISON WITH RISK BADGES */}
      <div className="mb-16 overflow-x-auto">
        <h2 className="text-4xl font-bold mb-8">Company Comparison</h2>
        <table className="w-full border border-zinc-800">
          <thead className="bg-zinc-900">
            <tr>
              <th className="p-4 text-left">Company</th>
              <th className="p-4 text-left">Quarter</th>
              <th className="p-4 text-left">Revenue Growth</th>
              <th className="p-4 text-left">Operating Margin</th>
              <th className="p-4 text-left">Net Income Growth</th>
              <th className="p-4 text-left">Risk Level</th>
              <th className="p-4 text-left">Investment Score</th>
            </tr>
          </thead>
          <tbody>
            {(() => {
              // Merge risk from trendData into comparisonData
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
                  <tr key={idx} className="border-t border-zinc-800">
                    <td className="p-4 font-semibold">{row.company}</td>
                    <td className="p-4">{row.quarter}</td>
                    <td className={`p-4 font-semibold ${row.revenue_growth >= 0 ? "text-green-400" : "text-red-400"}`}>
                      {row.revenue_growth}%
                    </td>
                    <td className={`p-4 font-semibold ${row.operating_margin >= 10 ? "text-green-400" : row.operating_margin >= 5 ? "text-yellow-400" : "text-red-400"}`}>
                      {row.operating_margin}%
                    </td>
                    <td className="p-4">{row.net_income_growth}%</td>
                    <td className="p-4">
                      <span className={`px-3 py-1 rounded-xl text-xs font-bold ${riskBadge(riskLevel)}`}>
                        {riskLevel === "High" ? "🔴" : riskLevel === "Medium" ? "🟡" : "🟢"} {riskLevel}
                      </span>
                    </td>
                    <td className="p-4">
                      <span className={`px-3 py-1 rounded-xl font-bold ${row.investment_score >= 40 ? "bg-green-900 text-green-300" : row.investment_score >= 20 ? "bg-yellow-900 text-yellow-300" : "bg-red-900 text-red-300"}`}>
                        {row.investment_score}
                      </span>
                    </td>
                  </tr>
                );
              });
            })()}
          </tbody>
        </table>
      </div>

      {/* FINANCIAL SENTIMENT */}
      <div className="mb-16">
        <h2 className="text-4xl font-bold mb-8">Financial Sentiment Analysis</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {sentiments?.map((item, idx) => (
            <div key={idx} className="bg-zinc-900 border border-zinc-700 rounded-2xl p-6">
              <h3 className="text-2xl font-bold mb-2">{item.company}</h3>
              <p className="text-zinc-400 mb-5">{item.quarter}</p>
              <div className="space-y-4">
                <div>
                  <span className="font-semibold">Sentiment: </span>
                  <span className={item.sentiment === "positive" ? "text-green-400" : item.sentiment === "negative" ? "text-red-400" : "text-yellow-400"}>
                    {item.sentiment}
                  </span>
                </div>
                <div><span className="font-semibold">Confidence: </span>{(item.score * 100).toFixed(1)}%</div>
                <div><span className="font-semibold">Tone: </span>{item.tone}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* CHARTS — actual + forecast */}
      <div className="space-y-10 mb-16">
        <div className="bg-zinc-900 border border-zinc-800 rounded-3xl p-8">
          <h2 className="text-3xl font-bold mb-2">Revenue Growth Trend</h2>
          <p className="text-zinc-400 text-sm mb-6">Solid = actual · Dotted = forecast</p>
          <RevenueChart
            data={Object.entries(trendData || {}).flatMap(([company, trends]) =>
              trends.map((t) => ({ ...t, company }))
            )}
          />
        </div>
        <div className="bg-zinc-900 border border-zinc-800 rounded-3xl p-8">
          <h2 className="text-3xl font-bold mb-2">Operating Margin Trend</h2>
          <p className="text-zinc-400 text-sm mb-6">Solid = actual · Dotted = forecast</p>
          <MarginChart
            data={Object.entries(trendData || {}).flatMap(([company, trends]) =>
              trends.map((t) => ({ ...t, company }))
            )}
          />
        </div>
      </div>

      {/* AI INSIGHTS + RISK */}
      <div className="mb-16">
        <h2 className="text-4xl font-bold mb-8">AI Financial Insights</h2>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {Object.entries(trendData || {}).map(([company, trends]) => {
            const actual  = trends.filter((t) => !t.is_forecast);
            const latest  = actual[actual.length - 1];
            if (!latest) return null;
            return (
              <div key={company} className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-2xl font-bold">{company}</h3>
                  <div className="flex gap-2">
                    {latest.risk && (
                      <span className={`px-3 py-1 rounded-xl text-xs font-bold ${riskBadge(latest.risk.level)}`}>
                        {latest.risk.level === "High" ? "🔴" : latest.risk.level === "Medium" ? "🟡" : "🟢"} {latest.risk.level} Risk
                      </span>
                    )}
                    <div className={`px-4 py-1 rounded-xl text-sm font-bold ${(latest.investment_score || 0) >= 40 ? "bg-green-900 text-green-300" : (latest.investment_score || 0) >= 20 ? "bg-yellow-900 text-yellow-300" : "bg-red-900 text-red-300"}`}>
                      Score: {latest.investment_score}
                    </div>
                  </div>
                </div>
                <p className="text-zinc-400 mb-4">Latest Quarter: {latest.quarter}</p>
                <div className="space-y-2 mb-6">
                  {latest.insights?.map((insight, i) => (
                    <div key={i} className="bg-zinc-800 rounded-xl p-3 text-zinc-200 text-sm">
                      {insight}
                    </div>
                  ))}
                </div>

                {/* Investment Thesis button */}
                <button
                  onClick={() => generateThesis(company)}
                  disabled={thesisLoading[company]}
                  className="w-full py-2 bg-zinc-700 hover:bg-zinc-600 rounded-xl text-sm font-semibold transition disabled:opacity-50"
                >
                  {thesisLoading[company] ? "Generating thesis..." : "🧠 Generate Investment Thesis"}
                </button>

                {/* Thesis output */}
                {thesis[company] && (
                  <div className="mt-4 bg-zinc-800 rounded-xl p-4 text-zinc-200 text-sm whitespace-pre-wrap leading-relaxed">
                    {thesis[company]}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

    </div>
  );
}