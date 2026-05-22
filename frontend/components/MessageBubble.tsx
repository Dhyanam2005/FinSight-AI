import { Message } from "@/types/chat";
import CitationCard from "./CitationCard";

interface Props {
  message: Message;
}

export default function MessageBubble({
  message,
}: Props) {

  const isUser = message.role === "user";

  return (
    <div
      className={`flex flex-col mb-4 ${
        isUser
          ? "items-end"
          : "items-start"
      }`}
    >

      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 ${
          isUser
            ? "bg-black text-white"
            : "bg-gray-200 text-black"
        }`}
      >
        {message.content}
      </div>

      {!isUser &&
        message.sources?.map((source, idx) => (
          <CitationCard
            key={idx}
            source={source}
          />
        ))}

    </div>
  );
}