"use client"

import { Fragment } from "react"
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts"

const COLORS = [
  "#10b981",
  "#3b82f6",
  "#f59e0b",
  "#ef4444",
  "#a855f7",
]

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-zinc-800 border border-zinc-600 rounded-xl px-4 py-3 text-sm shadow-lg">
        <p className="text-zinc-400 mb-2">{label}</p>

        {payload
          .filter(
            (p: any) => p.value !== null && p.value !== undefined
          )
          .map((p: any, i: number) => (
            <p
              key={i}
              style={{ color: p.color }}
              className="font-semibold"
            >
              {p.name.replace("__forecast", " (forecast)")}: {p.value}%
            </p>
          ))}
      </div>
    )
  }

  return null
}

export default function MarginChart({ data }: any) {
  const actualData = data.filter((d: any) => !d.is_forecast)
  const forecastData = data.filter((d: any) => d.is_forecast)

  // FIX #1: include forecast-only companies
  const companies = [
    ...new Set(data.map((d: any) => d.company)),
  ] as string[]

  const actualQuarters = [
    ...new Set(actualData.map((d: any) => d.quarter)),
  ] as string[]

  const forecastQuarters = [
    ...new Set(forecastData.map((d: any) => d.quarter)),
  ] as string[]

  const allQuarters = [
    ...actualQuarters,
    ...forecastQuarters.filter(
      (q) => !actualQuarters.includes(q)
    ),
  ]

  const pivoted = allQuarters.map((q) => {
    const row: any = { quarter: q }

    companies.forEach((company) => {
      const actualMatch = actualData.find(
        (d: any) =>
          d.company === company &&
          d.quarter === q
      )

      const forecastMatch = forecastData.find(
        (d: any) =>
          d.company === company &&
          d.quarter === q
      )

      row[company] = actualMatch
        ? actualMatch.operating_margin
        : null

      // FIX #2: last actual quarter PER COMPANY
      const companyActuals = actualData.filter(
        (d: any) => d.company === company
      )

      const lastActualQuarter =
        companyActuals.length > 0
          ? companyActuals[companyActuals.length - 1].quarter
          : null

      if (forecastMatch) {
        row[`${company}__forecast`] =
          forecastMatch.operating_margin
      } else if (
        actualMatch &&
        q === lastActualQuarter
      ) {
        // bridge actual → forecast
        row[`${company}__forecast`] =
          actualMatch.operating_margin
      } else {
        row[`${company}__forecast`] = null
      }
    })

    return row
  })

  return (
    <ResponsiveContainer width="100%" height={320}>
      <LineChart data={pivoted}>
        <XAxis
          dataKey="quarter"
          stroke="#71717a"
          tick={{
            fill: "#a1a1aa",
            fontSize: 12,
          }}
        />

        <YAxis
          stroke="#71717a"
          tick={{
            fill: "#a1a1aa",
            fontSize: 12,
          }}
        />

        <Tooltip content={<CustomTooltip />} />

        <Legend
          formatter={(value) =>
            value.includes("__forecast")
              ? `${value.replace(
                  "__forecast",
                  ""
                )} (forecast)`
              : value
          }
        />

        {companies.map((company, i) => (
          <Fragment key={company}>
            {/* Actual */}
            <Line
              key={`${company}-actual`}
              type="monotone"
              dataKey={company}
              name={company}
              stroke={COLORS[i % COLORS.length]}
              strokeWidth={2}
              dot={{
                r: 5,
                fill: COLORS[i % COLORS.length],
                strokeWidth: 0,
              }}
              activeDot={{
                r: 7,
                strokeWidth: 0,
              }}
              connectNulls={false}
            />

            {/* Forecast */}
            <Line
              key={`${company}-forecast`}
              type="monotone"
              dataKey={`${company}__forecast`}
              name={`${company}__forecast`}
              stroke={COLORS[i % COLORS.length]}
              strokeWidth={2}
              strokeDasharray="6 4"
              strokeOpacity={0.6}
              connectNulls={true}
              dot={{
                r: 4,
                fill: "transparent",
                stroke:
                  COLORS[i % COLORS.length],
                strokeWidth: 2,
              }}
              activeDot={{
                r: 6,
                strokeWidth: 0,
              }}
              legendType="none"
            />
          </Fragment>
        ))}
      </LineChart>
    </ResponsiveContainer>
  )
}