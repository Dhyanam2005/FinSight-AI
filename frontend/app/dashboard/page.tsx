"use client";

import { useEffect, useMemo, useState } from "react";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

interface FinancialData {

  company: string;

  quarter: string;

  section: string;

  revenue: string;

  revenue_growth_yoy: string;

  gross_margin: string;

  operating_margin: string;

  net_income: string;

  eps: string;

  ebitda: string;

  guidance: string;

  key_risks: string[];

  key_opportunities: string[];

  strategic_highlights: string[];
}

interface CompanyScore {

  company: string;

  growth_score: number;

  risk_score: number;

  innovation_score: number;

  overall_score: number;
}

interface TrendPoint {

  quarter: string;

  revenue_growth: string;

  operating_margin: string;
}

export default function DashboardPage() {

  const [companies, setCompanies] =
    useState<string[]>([]);

  const [financialData, setFinancialData] =
    useState<FinancialData[]>([]);

  const [analystInsights, setAnalystInsights] =
    useState("");

  const [scores, setScores] =
    useState<CompanyScore[]>([]);

  const [trendData, setTrendData] =
    useState<Record<string, TrendPoint[]>>({});

  const [loading, setLoading] =
    useState(true);

  useEffect(() => {

    fetchDashboard();

  }, []);

  async function fetchDashboard() {

    try {

      const response = await fetch(
        "http://127.0.0.1:8000/dashboard"
      );

      const data = await response.json();

      setCompanies(
        data.companies || []
      );

      setFinancialData(
        data.financial_data || []
      );

      setAnalystInsights(
        data.analyst_insights || ""
      );

      setScores(
        data.scores || []
      );

      setTrendData(
        data.trend_data || {}
      );

    } catch (error) {

      console.error(error);

    } finally {

      setLoading(false);
    }
  }

  const revenueChartData = useMemo(() => {

    return financialData.map((item) => ({

      label: `${item.company} ${item.quarter}`,

      growth: parseFloat(

        item.revenue_growth_yoy
          .replace("%", "") || "0"
      ),
    }));

  }, [financialData]);

  const marginChartData = useMemo(() => {

    return financialData.map((item) => ({

      label: `${item.company} ${item.quarter}`,

      margin: parseFloat(

        item.operating_margin
          .replace("%", "") || "0"
      ),
    }));

  }, [financialData]);

  if (loading) {

    return (

      <div className="p-10 text-xl text-white bg-black min-h-screen">

        Loading dashboard...

      </div>
    );
  }

  return (

    <div className="min-h-screen bg-black text-white p-8 pt-10">

      <h1 className="text-5xl font-bold mb-10">

        FinSight AI Dashboard

      </h1>

      <div className="mb-12">

        <h2 className="text-2xl font-semibold mb-4">

          Uploaded Companies

        </h2>

        <div className="flex gap-4 flex-wrap">

          {companies.map((company, idx) => (

            <div
              key={idx}
              className="bg-zinc-900 px-5 py-3 rounded-xl border border-zinc-700"
            >
              {company}
            </div>
          ))}
        </div>
      </div>

      <div className="mb-14 overflow-x-auto">

        <h2 className="text-2xl font-semibold mb-4">

          Company Comparison

        </h2>

        <table className="w-full border border-zinc-700 rounded-xl overflow-hidden">

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
                Top Risks
              </th>

            </tr>

          </thead>

          <tbody>

            {financialData.map((item, idx) => (

              <tr
                key={idx}
                className="border-t border-zinc-700"
              >

                <td className="p-4">
                  {item.company}
                </td>

                <td className="p-4">
                  {item.quarter}
                </td>

                <td className="p-4">
                  {item.revenue_growth_yoy || "N/A"}
                </td>

                <td className="p-4">
                  {item.operating_margin || "N/A"}
                </td>

                <td className="p-4">
                  {item.key_risks.join(", ") || "N/A"}
                </td>

              </tr>
            ))}

          </tbody>
        </table>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-10 mb-16">

        <div className="bg-zinc-900 rounded-2xl p-6 border border-zinc-700">

          <h2 className="text-2xl font-semibold mb-6">

            Revenue Growth Comparison

          </h2>

          <div className="h-80">

            <ResponsiveContainer width="100%" height="100%">

              <BarChart data={revenueChartData}>

                <CartesianGrid strokeDasharray="3 3" />

                <XAxis
                  dataKey="label"
                  interval={0}
                  angle={-15}
                  textAnchor="end"
                  height={80}
                />

                <YAxis />

                <Tooltip />

                <Bar dataKey="growth" />

              </BarChart>

            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-zinc-900 rounded-2xl p-6 border border-zinc-700">

          <h2 className="text-2xl font-semibold mb-6">

            Operating Margin Comparison

          </h2>

          <div className="h-80">

            <ResponsiveContainer width="100%" height="100%">

              <BarChart data={marginChartData}>

                <CartesianGrid strokeDasharray="3 3" />

                <XAxis
                  dataKey="label"
                  interval={0}
                  angle={-15}
                  textAnchor="end"
                  height={80}
                />

                <YAxis />

                <Tooltip />

                <Bar dataKey="margin" />

              </BarChart>

            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-16">

        {financialData.map((item, idx) => (

          <div
            key={idx}
            className="bg-zinc-900 rounded-2xl p-6 border border-zinc-700"
          >

            <h2 className="text-3xl font-bold mb-2">

              {item.company}

            </h2>

            <p className="text-zinc-400 mb-5">

              {item.quarter}

            </p>

            <div className="space-y-3">

              <p>

                <span className="font-semibold">

                  Revenue Growth:

                </span>{" "}

                {item.revenue_growth_yoy || "N/A"}

              </p>

              <p>

                <span className="font-semibold">

                  Operating Margin:

                </span>{" "}

                {item.operating_margin || "N/A"}

              </p>
            </div>

            <div className="mt-6">

              <h3 className="text-red-400 font-semibold mb-3">

                Key Risks

              </h3>

              <ul className="list-disc ml-5 space-y-2">

                {item.key_risks.map((risk, i) => (

                  <li key={i}>{risk}</li>
                ))}
              </ul>
            </div>

            <div className="mt-6">

              <h3 className="text-green-400 font-semibold mb-3">

                Opportunities

              </h3>

              <ul className="list-disc ml-5 space-y-2">

                {item.key_opportunities.map((opp, i) => (

                  <li key={i}>{opp}</li>
                ))}
              </ul>
            </div>

            <div className="mt-6">

              <h3 className="text-blue-400 font-semibold mb-3">

                Strategic Highlights

              </h3>

              <ul className="list-disc ml-5 space-y-2">

                {item.strategic_highlights.map(

                  (highlight, i) => (

                    <li key={i}>
                      {highlight}
                    </li>
                  )
                )}
              </ul>
            </div>
          </div>
        ))}
      </div>

      <div className="bg-zinc-900 border border-zinc-700 rounded-2xl p-8 mb-16">

        <h2 className="text-3xl font-bold mb-5">

          Analyst Insights

        </h2>

        <div className="text-zinc-300 leading-8 whitespace-pre-wrap">

          {analystInsights || "No insights available."}

        </div>
      </div>

      <div className="mb-16">

        <h2 className="text-4xl font-bold mb-8">

          Financial Trends

        </h2>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">

          {Object.entries(trendData).map(

            ([company, trends], idx) => {

              const revenueTrendData =
                trends.map((trend) => ({

                  quarter: trend.quarter,

                  growth: parseFloat(

                    trend.revenue_growth.replace(
                      "%",
                      ""
                    ) || "0"
                  ),
                }));

              return (

                <div
                  key={idx}
                  className="bg-zinc-900 border border-zinc-700 rounded-2xl p-6"
                >

                  <h3 className="text-2xl font-bold mb-6">

                    {company} Revenue Trend

                  </h3>

                  <div className="h-80">

                    <ResponsiveContainer
                      width="100%"
                      height="100%"
                    >

                      <BarChart data={revenueTrendData}>

                        <CartesianGrid
                          strokeDasharray="3 3"
                        />

                        <XAxis dataKey="quarter" />

                        <YAxis />

                        <Tooltip />

                        <Bar dataKey="growth" />

                      </BarChart>

                    </ResponsiveContainer>
                  </div>
                </div>
              );
            }
          )}
        </div>
      </div>

      <div className="mt-16">

        <h2 className="text-4xl font-bold mb-8">

          Investment Rankings

        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">

          {scores
            .sort(
              (a, b) =>
                b.overall_score - a.overall_score
            )
            .map((score, idx) => (

              <div
                key={idx}
                className="bg-zinc-900 border border-zinc-700 rounded-2xl p-6"
              >

                <div className="flex items-center justify-between mb-4">

                  <div>

                    <h3 className="text-2xl font-bold">

                      {score.company}

                    </h3>

                    <div className="text-sm text-zinc-400 mt-1">

                      Average Across All Quarters

                    </div>
                  </div>

                  <span className="text-3xl">

                    {idx === 0 && "🥇"}

                    {idx === 1 && "🥈"}

                    {idx === 2 && "🥉"}

                  </span>
                </div>

                <div className="space-y-3 text-sm">

                  <p>

                    <span className="font-semibold">

                      Growth Score:

                    </span>{" "}

                    {score.growth_score}

                  </p>

                  <p>

                    <span className="font-semibold">

                      Risk Score:

                    </span>{" "}

                    {score.risk_score}

                  </p>

                  <p>

                    <span className="font-semibold">

                      Innovation Score:

                    </span>{" "}

                    {score.innovation_score}

                  </p>

                  <p className="text-xl font-bold pt-4">

                    Overall Score:{" "}

                    {score.overall_score}

                  </p>
                </div>
              </div>
            ))}
        </div>
      </div>
    </div>
  );
}