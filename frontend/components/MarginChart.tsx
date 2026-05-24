"use client"

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer
} from "recharts"

const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#a855f7"]

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-zinc-800 border border-zinc-600 rounded-xl px-4 py-3 text-sm shadow-lg">
        <p className="text-zinc-400 mb-2">{label}</p>
        {payload.map((p: any, i: number) => (
          <p key={i} style={{ color: p.color }} className="font-semibold">
            {p.name}: {p.value}%
          </p>
        ))}
      </div>
    )
  }
  return null
}

export default function MarginChart({ data }: any) {
  const companies = [...new Set(data.map((d: any) => d.company))] as string[]

  const quarters = [...new Set(data.map((d: any) => d.quarter))] as string[]

  const pivoted = quarters.map((q) => {
    const row: any = { quarter: q }
    companies.forEach((c) => {
      const match = data.find((d: any) => d.quarter === q && d.company === c)
      row[c] = match ? match.operating_margin : null
    })
    return row
  })

  return (
    <div className="bg-zinc-900 p-6 rounded-3xl">
      <h2 className="text-2xl font-bold mb-6">Operating Margin Trend</h2>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={pivoted}>
          <XAxis dataKey="quarter" stroke="#71717a" tick={{ fill: "#a1a1aa" }} />
          <YAxis stroke="#71717a" tick={{ fill: "#a1a1aa" }} />
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          {companies.map((company, i) => (
            <Line
              key={company}
              type="monotone"
              dataKey={company}
              stroke={COLORS[i % COLORS.length]}
              strokeWidth={2}
              dot={{ r: 5, fill: COLORS[i % COLORS.length], strokeWidth: 0 }}
              activeDot={{ r: 7, strokeWidth: 0 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}