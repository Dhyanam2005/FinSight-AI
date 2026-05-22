import UploadBox from "@/components/UploadBox";
import ChatBox from "@/components/ChatBox";

export default function Home() {
  return (
    <main className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-4xl mx-auto space-y-6">

        <h1 className="text-4xl font-bold">
          FinSight AI
        </h1>

        <UploadBox />

        <ChatBox />

      </div>
    </main>
  );
}