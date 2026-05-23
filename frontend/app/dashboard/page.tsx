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

export default function DashboardPage() {
  const [companies, setCompanies] = useState<string[]>([]);

  const [financialData, setFinancialData] =
    useState<FinancialData[]>([]);

  const [analystInsights, setAnalystInsights] =
    useState("");

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboard();
  }, []);

  async function fetchDashboard() {
    try {
      const response = await fetch(
        "http://127.0.0.1:8000/dashboard"
      );

      const data = await response.json();

      setCompanies(data.companies || []);

      setFinancialData(data.financial_data || []);

      setAnalystInsights(
        data.analyst_insights || ""
      );

    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  }

  const revenueChartData = useMemo(() => {
    return financialData.map((item) => ({
      company: item.company,
      growth: parseFloat(
        item.revenue_growth_yoy.replace("%", "") || "0"
      ),
    }));
  }, [financialData]);

  const marginChartData = useMemo(() => {
    return financialData.map((item) => ({
      company: item.company,
      margin: parseFloat(
        item.operating_margin.replace("%", "") || "0"
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

      {/* ================================= */}
      {/* HEADER */}
      {/* ================================= */}

      <h1 className="text-5xl font-bold mb-10">
        FinSight AI Dashboard
      </h1>

      {/* ================================= */}
      {/* COMPANY LIST */}
      {/* ================================= */}

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

      {/* ================================= */}
      {/* COMPARISON TABLE */}
      {/* ================================= */}

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

      {/* ================================= */}
      {/* CHARTS */}
      {/* ================================= */}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-10 mb-16">

        {/* Revenue Growth Chart */}

        <div className="bg-zinc-900 rounded-2xl p-6 border border-zinc-700">

          <h2 className="text-2xl font-semibold mb-6">
            Revenue Growth Comparison
          </h2>

          <div className="h-80">

            <ResponsiveContainer width="100%" height="100%">

              <BarChart data={revenueChartData}>

                <CartesianGrid strokeDasharray="3 3" />

                <XAxis dataKey="company" />

                <YAxis />

                <Tooltip />

                <Bar dataKey="growth" />

              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Operating Margin Chart */}

        <div className="bg-zinc-900 rounded-2xl p-6 border border-zinc-700">

          <h2 className="text-2xl font-semibold mb-6">
            Operating Margin Comparison
          </h2>

          <div className="h-80">

            <ResponsiveContainer width="100%" height="100%">

              <BarChart data={marginChartData}>

                <CartesianGrid strokeDasharray="3 3" />

                <XAxis dataKey="company" />

                <YAxis />

                <Tooltip />

                <Bar dataKey="margin" />

              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* ================================= */}
      {/* KPI CARDS */}
      {/* ================================= */}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-16">

        {financialData.map((item, idx) => (

          <div
            key={idx}
            className="bg-zinc-900 rounded-2xl p-6 border border-zinc-700 shadow-lg"
          >

            <h2 className="text-3xl font-bold mb-5">
              {item.company}
            </h2>

            {/* KPI INFO */}

            <div className="space-y-3 text-sm">

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

              <p>
                <span className="font-semibold">
                  EBITDA:
                </span>{" "}
                {item.ebitda || "N/A"}
              </p>
            </div>

            {/* RISKS */}

            <div className="mt-6">

              <h3 className="font-semibold text-red-400 mb-3 text-lg">
                Key Risks
              </h3>

              <ul className="list-disc ml-5 text-sm space-y-2">

                {item.key_risks.map((risk, i) => (
                  <li key={i}>{risk}</li>
                ))}
              </ul>
            </div>

            {/* OPPORTUNITIES */}

            <div className="mt-6">

              <h3 className="font-semibold text-green-400 mb-3 text-lg">
                Opportunities
              </h3>

              <ul className="list-disc ml-5 text-sm space-y-2">

                {item.key_opportunities.map((opp, i) => (
                  <li key={i}>{opp}</li>
                ))}
              </ul>
            </div>

            {/* STRATEGIC HIGHLIGHTS */}

            <div className="mt-6">

              <h3 className="font-semibold text-blue-400 mb-3 text-lg">
                Strategic Highlights
              </h3>

              <ul className="list-disc ml-5 text-sm space-y-2">

                {item.strategic_highlights.map((highlight, i) => (
                  <li key={i}>{highlight}</li>
                ))}
              </ul>
            </div>
          </div>
        ))}
      </div>

      {/* ================================= */}
      {/* ANALYST INSIGHTS */}
      {/* ================================= */}

      <div className="bg-zinc-900 border border-zinc-700 rounded-2xl p-8">

        <h2 className="text-3xl font-bold mb-5">
          Analyst Insights
        </h2>

        <div className="text-zinc-300 leading-8 whitespace-pre-wrap">

          {analystInsights || "No insights available."}

        </div>
      </div>
    </div>
  );
}