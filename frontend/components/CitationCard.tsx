import { Source } from "@/types/chat";

interface Props {
  source: Source;
}

export default function CitationCard({
  source,
}: Props) {
  return (
    <div className="w-full max-w-[80%] border rounded-xl p-3 mb-2 bg-white shadow-sm">

      <div className="flex justify-between">

        <p className="text-sm font-semibold">
          Source Chunk {source.chunk}
        </p>

        <p className="text-xs text-gray-500">
          Page {source.page}
        </p>

      </div>

      <p className="text-sm text-gray-700 mt-2">
        {source.text}
      </p>

    </div>
  );
}