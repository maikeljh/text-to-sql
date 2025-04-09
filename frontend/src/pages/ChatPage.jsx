import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

function ChatPage() {
  const [query, setQuery] = useState("");
  const [history, setHistory] = useState([]);

  const navigate = useNavigate();
  const userId = localStorage.getItem("user_id");

  useEffect(() => {
    if (!userId) {
      navigate("/");
    }
  }, [userId, navigate]);

  const handleSend = async () => {
    if (!query.trim()) return;
    const res = await fetch("http://localhost:8000/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: Number(userId), query }),
    });

    const data = await res.json();
    if (res.ok) {
      setHistory(data.history);
      setQuery("");
    }
  };

  return (
    <div
      className="h-screen flex bg-cover bg-no-repeat bg-center text-white"
      style={{ backgroundImage: "url('/chat.png')" }}
    >
      {/* Sidebar */}
      <aside className="w-72 bg-white/5 backdrop-blur-md border-r border-white/10 p-4 hidden md:flex flex-col">
        <button className="w-full bg-white/10 hover:bg-white/20 text-white font-semibold py-2 px-4 rounded-lg mb-6 flex items-center justify-center gap-2 cursor-pointer">
          + New Chat
        </button>

        <div className="overflow-y-auto text-sm text-white/80 space-y-2">
          {history.length > 0 ? (
            history.map((h, idx) => (
              <div
                key={idx}
                className="hover:bg-white/10 px-2 py-1 rounded cursor-pointer truncate"
              >
                {h.user}
              </div>
            ))
          ) : (
            <p className="text-white/40">No chat history yet.</p>
          )}
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 flex flex-col justify-between items-center py-10 px-4 md:px-12">
        {/* Header */}
        <div className="w-full max-w-4xl flex justify-between items-center mb-6">
          <div className="text-xl font-semibold">Chatbot</div>
          <button className="cursor-pointer border border-white/20 p-2 rounded-full hover:bg-white/10">
            Profile
          </button>
        </div>

        {/* Chat history */}
        <div className="w-full max-w-4xl flex-1 overflow-y-auto mb-8 space-y-6">
          {history.map((h, i) => (
            <div key={i} className="bg-white/5 p-4 rounded-xl space-y-2 shadow">
              <p>
                <strong className="text-green-400">You:</strong> {h.user}
              </p>
              <p>
                <strong className="text-blue-300">Bot:</strong> {h.agent}
              </p>
            </div>
          ))}
        </div>

        {/* Input bar */}
        <div className="w-full max-w-4xl">
          <div className="flex items-center bg-white/10 backdrop-blur-md rounded-lg p-3 gap-3">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Type here..."
              className="flex-1 bg-transparent text-white placeholder-white/50 outline-none"
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
            />
            <button
              onClick={handleSend}
              className="cursor-pointer bg-gray-700 hover:bg-gray-500 text-white px-4 py-2 rounded-lg"
            >
              Send
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}

export default ChatPage;
