import { Source } from "@/types/chat";

interface Props {
  source: Source;
}

export default function CitationCard({ source }: Props) {
  return (
    <div className="w-full max-w-[80%] border border-zinc-700 rounded-xl p-3 mb-2 bg-zinc-800">
      <div className="flex justify-between items-center mb-1">
        <p className="text-xs font-semibold text-zinc-300">
          Source {source.chunk}
          {source.document && source.document !== "?" && (
            <span className="text-zinc-500 font-normal ml-1">· {source.document}</span>
          )}
        </p>
        <p className="text-xs text-zinc-500">pg {source.page}</p>
      </div>
      <p className="text-xs text-zinc-400 leading-relaxed">{source.text}</p>
    </div>
  );
}