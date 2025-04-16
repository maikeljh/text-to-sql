import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { FiUser } from "react-icons/fi";
import { BiSearch, BiPlus } from "react-icons/bi";
import { BsSoundwave } from "react-icons/bs";
import toast from "react-hot-toast";

const dummyHistory = [
  {
    id: 1,
    title: "What is React?",
    messages: [
      { sender: "user", message: "What is React?" },
      {
        sender: "bot",
        message: "React is a JavaScript library for building UI.",
      },
    ],
    timestamp: new Date(),
  },
  {
    id: 2,
    title: "Explain Docker",
    messages: [
      { sender: "user", message: "What is Docker?" },
      {
        sender: "bot",
        message: "Docker is a tool to containerize applications.",
      },
    ],
    timestamp: new Date(new Date().setDate(new Date().getDate() - 1)),
  },
];

function ChatPage() {
  const [query, setQuery] = useState("");
  const [historyList, setHistoryList] = useState(dummyHistory);
  const [selectedChat, setSelectedChat] = useState(null);
  const [showDropdown, setShowDropdown] = useState(false);
  const navigate = useNavigate();
  const userId = localStorage.getItem("user_id");

  useEffect(() => {
    if (!userId) {
      navigate("/");
    }
  }, [userId, navigate]);

  const handleSend = () => {
    if (!query.trim()) return;

    const newMessage = { sender: "user", message: query };
    const botReply = {
      sender: "bot",
      message: "This is a dummy reply to: " + query,
    };

    if (selectedChat) {
      const updated = {
        ...selectedChat,
        messages: [...selectedChat.messages, newMessage, botReply],
      };
      setSelectedChat(updated);

      setHistoryList((prev) =>
        prev.map((chat) => (chat.id === selectedChat.id ? updated : chat))
      );
    } else {
      const newChat = {
        id: historyList.length + 1,
        title: query,
        messages: [newMessage, botReply],
        timestamp: new Date(),
      };
      setHistoryList([newChat, ...historyList]);
      setSelectedChat(newChat);
    }

    setQuery("");
  };

  const handleSelectHistory = (chatId) => {
    const found = historyList.find((c) => c.id === chatId);
    setSelectedChat(found);
  };

  const groupByDate = (history) => {
    const today = new Date();
    const yesterday = new Date();
    yesterday.setDate(today.getDate() - 1);

    return {
      Today: history.filter(
        (c) => c.timestamp?.toDateString() === today.toDateString()
      ),
      Yesterday: history.filter(
        (c) => c.timestamp?.toDateString() === yesterday.toDateString()
      ),
      "Previous 7 Days": history.filter(
        (c) =>
          c.timestamp &&
          c.timestamp.toDateString() !== today.toDateString() &&
          c.timestamp.toDateString() !== yesterday.toDateString()
      ),
    };
  };

  const handleLogout = () => {
    localStorage.removeItem("user_id");
    localStorage.removeItem("token");
    toast.success("Logged out successfully", {
      style: {
        background: "#000",
        color: "#fff",
      },
    });
    navigate("/");
  };

  const groupedHistory = groupByDate(historyList);

  return (
    <div
      className="flex h-screen bg-[#0F1422] text-white p-6"
      style={{ backgroundImage: `url('/login.png')`, backgroundSize: "cover" }}
    >
      {/* Sidebar */}
      <aside className="w-[280px] bg-[#1B2332]/60 border border-white/20 rounded-2xl flex flex-col p-4">
        <button
          className="flex items-center gap-2 bg-white text-black px-4 py-2 rounded-lg shadow mb-6 cursor-pointer"
          onClick={() => setSelectedChat(null)}
        >
          <BiPlus size={18} />
          New Chat
        </button>

        <div className="flex items-center bg-white/10 rounded px-2 py-1 mb-6">
          <BiSearch size={18} className="text-white/70" />
          <input
            type="text"
            placeholder="Search"
            className="bg-transparent ml-2 outline-none w-full text-sm text-white"
          />
        </div>

        <div className="overflow-y-auto text-sm space-y-6">
          {Object.entries(groupedHistory).map(([group, chats]) => (
            <div key={group}>
              <p className="text-xs text-white/60 mb-2">{group}</p>
              {chats.map((chat) => (
                <p
                  key={chat.id}
                  onClick={() => handleSelectHistory(chat.id)}
                  className={`mb-1 px-2 py-1 rounded-lg cursor-pointer ${
                    selectedChat?.id === chat.id
                      ? "bg-white/20 text-white"
                      : "hover:bg-white/10 text-white/80"
                  }`}
                >
                  {chat.title}
                </p>
              ))}
            </div>
          ))}
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col ml-4 overflow-hidden">
        {/* Header */}
        <header className="flex items-center justify-between px-6 py-4 border border-white/20 bg-[#1B2332]/60 rounded-2xl">
          <h1 className="text-lg font-semibold flex items-center gap-2">
            <span className="rounded-full bg-white/10 p-1">🤖</span>
            Chatbot
          </h1>
          <div className="relative">
            <div
              className="bg-white/10 rounded-full p-2 cursor-pointer"
              onClick={() => setShowDropdown((prev) => !prev)}
            >
              <FiUser size={20} />
            </div>

            {showDropdown && (
              <div className="absolute right-0 mt-2 w-32 bg-black text-white rounded shadow-lg z-50 cursor-pointer">
                <button
                  onClick={handleLogout}
                  className="w-full text-left px-4 py-2 hover:bg-gray-800 cursor-pointer"
                >
                  Logout
                </button>
              </div>
            )}
          </div>
        </header>

        {/* Chat Area */}
        <div className="flex-1 flex flex-col items-center justify-center text-center px-6 py-4">
          {!selectedChat && (
            <div className="text-center w-1/2">
              <h2 className="text-3xl font-semibold text-white mb-6">
                What can I help with?
              </h2>
              <div className="bg-[#1B2332]/80 rounded-2xl p-4 max-w-2xl w-full ml-6">
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Type here"
                    className="flex-1 bg-transparent outline-none text-white placeholder:text-white/50 px-3 py-3 text-base"
                  />
                  <button
                    onClick={handleSend}
                    className="text-white bg-cyan-600 p-2 rounded-full cursor-pointer"
                  >
                    <BsSoundwave size={20} />
                  </button>
                </div>
              </div>
            </div>
          )}

          {selectedChat && (
            <div className="flex-1 flex flex-col justify-between w-full">
              <div className="flex-1 overflow-y-auto space-y-4 pr-2">
                {selectedChat.messages.map((msg, i) => (
                  <div
                    key={i}
                    className={`flex ${
                      msg.sender === "user" ? "justify-end" : "justify-start"
                    }`}
                  >
                    <div
                      className={`px-4 py-3 rounded-2xl max-w-[75%] text-sm whitespace-pre-line ${
                        msg.sender === "user" ? "bg-cyan-600" : "bg-gray-700"
                      }`}
                    >
                      {msg.message}
                    </div>
                  </div>
                ))}
              </div>

              {/* Input Area */}
              <div className="bg-[#1B2332]/80 rounded-2xl p-4 mt-4">
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Type here"
                    className="flex-1 bg-transparent outline-none text-white placeholder:text-white/50 px-3 py-3 text-base"
                  />
                  <button
                    onClick={handleSend}
                    className="text-white bg-cyan-600 p-2 rounded-full cursor-pointer"
                  >
                    <BsSoundwave size={20} />
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default ChatPage;
