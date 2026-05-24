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
}

interface SentimentData {
  company: string;
  quarter: string;
  sentiment: string;
  score: number;
  tone: string;
}

export default function DashboardPage() {

  const [kpis, setKpis] =
    useState<KPIData | null>(null);

  const [comparisonData, setComparisonData] =
    useState<ComparisonRow[]>([]);

  const [trendData, setTrendData] =
    useState<Record<string, TrendPoint[]>>({});

  const [sentiments, setSentiments] =
    useState<SentimentData[]>([]);

  const [loading, setLoading] =
    useState(true);

  useEffect(() => {

    fetchDashboard();

  }, []);

  async function fetchDashboard() {

    try {

      const response = await fetch(
        "http://localhost:8000/dashboard"
      );

      if (!response.ok) {

        throw new Error(
          "Failed to fetch dashboard"
        );
      }

      const data = await response.json();

      console.log(
        "DASHBOARD DATA:",
        data
      );

      setKpis(
        data.kpis || null
      );

      setComparisonData(
        data.comparison_table || []
      );

      setTrendData(
        data.trend_data || {}
      );

      setSentiments(
        data.sentiments || []
      );

    } catch (error) {

      console.error(
        "Dashboard fetch failed:",
        error
      );

    } finally {

      setLoading(false);

    }
  }

  if (loading) {

    return (

      <div className="min-h-screen bg-black text-white p-10">

        Loading dashboard...

      </div>
    );
  }

  return (

    <div className="min-h-screen bg-black text-white p-10">

      <h1 className="text-5xl font-bold mb-12">

        FinSight AI Dashboard

      </h1>

      {/* KPI CARDS */}

      {kpis && (

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-16">

          <div className="bg-zinc-900 p-6 rounded-2xl border border-zinc-800">

            <h2 className="text-zinc-400 mb-2">

              Companies

            </h2>

            <p className="text-4xl font-bold">

              {kpis.total_companies}

            </p>

          </div>

          <div className="bg-zinc-900 p-6 rounded-2xl border border-zinc-800">

            <h2 className="text-zinc-400 mb-2">

              Reports

            </h2>

            <p className="text-4xl font-bold">

              {kpis.total_reports}

            </p>

          </div>

          <div className="bg-zinc-900 p-6 rounded-2xl border border-zinc-800">

            <h2 className="text-zinc-400 mb-2">

              Avg Revenue Growth

            </h2>

            <p className="text-4xl font-bold">

              {kpis.avg_revenue_growth?.toFixed(2)}%

            </p>

          </div>

          <div className="bg-zinc-900 p-6 rounded-2xl border border-zinc-800">

            <h2 className="text-zinc-400 mb-2">

              Avg Operating Margin

            </h2>

            <p className="text-4xl font-bold">

              {kpis.avg_operating_margin?.toFixed(2)}%

            </p>

          </div>

        </div>
      )}

      {/* COMPANY COMPARISON */}

      <div className="mb-16 overflow-x-auto">

        <h2 className="text-4xl font-bold mb-8">

          Company Comparison

        </h2>

        <table className="w-full border border-zinc-800">

          <thead className="bg-zinc-900">

            <tr>

              <th className="p-4 text-left">
                Company
              </th>

              <th className="p-4 text-left">
                Quarter
              </th>

              <th className="p-4 text-left">
                Revenue Growth
              </th>

              <th className="p-4 text-left">
                Operating Margin
              </th>

              <th className="p-4 text-left">
                Net Income Growth
              </th>

              <th className="p-4 text-left">
                Investment Score
              </th>

            </tr>

          </thead>

          <tbody>

            {comparisonData?.map((row, idx) => (

              <tr
                key={idx}
                className="border-t border-zinc-800"
              >

                <td className="p-4">
                  {row.company}
                </td>

                <td className="p-4">
                  {row.quarter}
                </td>

                <td className="p-4">
                  {row.revenue_growth}%
                </td>

                <td className="p-4">
                  {row.operating_margin}%
                </td>

                <td className="p-4">
                  {row.net_income_growth}%
                </td>

                <td className="p-4">

                  <span
                    className={`px-3 py-1 rounded-xl font-bold ${
                      row.investment_score >= 40
                        ? "bg-green-900 text-green-300"
                        : row.investment_score >= 20
                        ? "bg-yellow-900 text-yellow-300"
                        : "bg-red-900 text-red-300"
                    }`}
                  >

                    {row.investment_score}

                  </span>

                </td>

              </tr>
            ))}

          </tbody>

        </table>

      </div>

      {/* FINANCIAL SENTIMENT */}

      <div className="mb-16">

        <h2 className="text-4xl font-bold mb-8">

          Financial Sentiment Analysis

        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">

          {sentiments?.map((item, idx) => (

            <div
              key={idx}
              className="bg-zinc-900 border border-zinc-700 rounded-2xl p-6"
            >

              <h3 className="text-2xl font-bold mb-2">

                {item.company}

              </h3>

              <p className="text-zinc-400 mb-5">

                {item.quarter}

              </p>

              <div className="space-y-4">

                <div>

                  <span className="font-semibold">

                    Sentiment:

                  </span>{" "}

                  <span
                    className={
                      item.sentiment === "positive"
                        ? "text-green-400"
                        : item.sentiment === "negative"
                        ? "text-red-400"
                        : "text-yellow-400"
                    }
                  >

                    {item.sentiment}

                  </span>

                </div>

                <div>

                  <span className="font-semibold">

                    Confidence:

                  </span>{" "}

                  {(item.score * 100).toFixed(1)}%

                </div>

                <div>

                  <span className="font-semibold">

                    Tone:

                  </span>{" "}

                  {item.tone}

                </div>

              </div>

            </div>
          ))}

        </div>

      </div>

      {/* CHARTS */}

      <div className="space-y-10 mb-16">

        {/* REVENUE CHART */}

        <div className="bg-zinc-900 border border-zinc-800 rounded-3xl p-8">

          <h2 className="text-3xl font-bold mb-8">

            Revenue Growth Comparison

          </h2>

          <RevenueChart
            data={
              Object.entries(trendData || {}).flatMap(
                ([company, trends]) =>

                  trends.map((trend) => ({

                    ...trend,

                    company

                  }))
              )
            }
          />

        </div>

        {/* OPERATING MARGIN CHART */}

        <div className="bg-zinc-900 border border-zinc-800 rounded-3xl p-8">

          <h2 className="text-3xl font-bold mb-8">

            Operating Margin Comparison

          </h2>

          <MarginChart
            data={
              Object.entries(trendData || {}).flatMap(
                ([company, trends]) =>

                  trends.map((trend) => ({

                    ...trend,

                    company

                  }))
              )
            }
          />

        </div>

      </div>

      {/* AI INSIGHTS */}

      <div className="mb-16">

        <h2 className="text-4xl font-bold mb-8">

          AI Financial Insights

        </h2>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

          {Object.entries(trendData || {}).map(
            ([company, trends]) => {

              const latestTrend =
                trends[trends.length - 1];

              return (

                <div
                  key={company}
                  className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6"
                >

                  <div className="flex items-center justify-between mb-4">

                    <h3 className="text-2xl font-bold">

                      {company}

                    </h3>

                    <div
                      className={`px-4 py-2 rounded-xl text-sm font-bold ${
                        (latestTrend.investment_score || 0) >= 40
                          ? "bg-green-900 text-green-300"
                          : (latestTrend.investment_score || 0) >= 20
                          ? "bg-yellow-900 text-yellow-300"
                          : "bg-red-900 text-red-300"
                      }`}
                    >

                      Score:
                      {" "}
                      {latestTrend.investment_score}

                    </div>

                  </div>

                  <p className="text-zinc-400 mb-6">

                    Latest Quarter:
                    {" "}
                    {latestTrend.quarter}

                  </p>

                  <div className="space-y-3">

                    {latestTrend.insights?.map(
                      (insight, idx) => (

                        <div
                          key={idx}
                          className="bg-zinc-800 rounded-xl p-4 text-zinc-200"
                        >

                          • {insight}

                        </div>
                    ))}

                  </div>

                </div>
              );
          })}

        </div>

      </div>

    </div>
  );
}