import UploadBox from "@/components/UploadBox";
import ChatBox from "@/components/ChatBox";

export default function Home() {
  return (
    <main className="min-h-screen bg-[#212121] flex flex-col">
      
      {/* Header */}
      <div className="border-b border-zinc-700 px-6 py-4 flex items-center justify-between">
        <h1 className="text-xl font-semibold text-white">FinSight AI</h1>
        <a 
          href="/dashboard"
          className="text-sm text-zinc-400 hover:text-white transition"
        >
          Dashboard →
        </a>
      </div>

      {/* Main Content */}
      <div className="flex-1 max-w-3xl w-full mx-auto px-4 py-6 space-y-4">
        <UploadBox />
        <ChatBox />
      </div>

    </main>
  );
}