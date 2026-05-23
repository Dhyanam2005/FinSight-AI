type Props = {
  sentiment: string
  score: number
  tone: string
}

export default function SentimentCard({
  sentiment,
  score,
  tone,
}: Props) {
  return (
    <div className="bg-zinc-900 p-6 rounded-2xl border border-zinc-800">
      <h2 className="text-xl font-semibold mb-4">
        Financial Sentiment
      </h2>

      <div className="space-y-3">
        <p>
          <span className="font-semibold">Sentiment:</span>{" "}
          {sentiment}
        </p>

        <p>
          <span className="font-semibold">Confidence:</span>{" "}
          {(score * 100).toFixed(1)}%
        </p>

        <p>
          <span className="font-semibold">Tone:</span>{" "}
          {tone}
        </p>
      </div>
    </div>
  )
}