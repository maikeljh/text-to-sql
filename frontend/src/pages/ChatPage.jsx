import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { FiUser } from "react-icons/fi";
import { BiSearch, BiPlus } from "react-icons/bi";
import { BsSoundwave } from "react-icons/bs";
import toast from "react-hot-toast";

function ChatPage() {
  const [query, setQuery] = useState("");
  const [historyList, setHistoryList] = useState([]);
  const [selectedChat, setSelectedChat] = useState(null);
  const [showDropdown, setShowDropdown] = useState(false);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [targetChatId, setTargetChatId] = useState(null);
  const navigate = useNavigate();
  const userId = localStorage.getItem("user_id");
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (!userId) {
      navigate("/");
    }
  }, [userId, navigate]);

  useEffect(() => {
    const fetchHistories = async () => {
      try {
        const res = await fetch(
          `${import.meta.env.VITE_API_BASE_URL}/chat/histories`,
          {
            headers: {
              Authorization: `Bearer ${localStorage.getItem("token")}`,
            },
          }
        );
        const data = await res.json();
        setHistoryList(data);
      } catch {
        toast.error("Failed to fetch histories", {
          style: { background: "#000", color: "#fff" },
        });
      }
    };

    if (userId) fetchHistories();
  }, [userId]);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [selectedChat?.messages]);

  const handleSend = async () => {
    if (!query.trim()) return;

    const userMessage = { sender: "user", message: query };
    const loadingMessage = { sender: "bot", message: "Thinking...", data: [] };

    setQuery("");
    setLoading(true);

    // Append only if chat is selected
    if (selectedChat) {
      setSelectedChat((prev) => ({
        ...prev,
        messages: [...prev.messages, userMessage, loadingMessage],
      }));
    }

    try {
      const res = await fetch(
        `${import.meta.env.VITE_API_BASE_URL}/chat/query`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
          body: JSON.stringify({
            query,
            chat_id: selectedChat?.id || null,
          }),
        }
      );

      const data = await res.json();
      if (res.ok) {
        const newChatId = data.chat_id;

        // Always update history list
        const refresh = await fetch(
          `${import.meta.env.VITE_API_BASE_URL}/chat/histories`,
          {
            headers: {
              Authorization: `Bearer ${localStorage.getItem("token")}`,
            },
          }
        );
        const updatedList = await refresh.json();
        setHistoryList(updatedList);

        // If new chat just created, this will select it
        await handleSelectHistory(newChatId);
      } else {
        toast.error("Failed to send message");
      }
    } catch {
      toast.error("Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  const handleSelectHistory = async (chatId) => {
    try {
      const res = await fetch(
        `${import.meta.env.VITE_API_BASE_URL}/chat/history/${chatId}`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        }
      );
      const data = await res.json();

      const transformedMessages = data.messages.flatMap((msg) => [
        { sender: "user", message: msg.user },
        {
          sender: "bot",
          message: msg.agent.response,
          data: msg.agent.data.result || [],
          id: msg.id,
          feedback: msg.feedback || null,
        },
      ]);


      setSelectedChat({
        id: data.chat_id,
        title: data.chat_title,
        messages: transformedMessages,
        timestamp: new Date(data.messages[0]?.timestamp || Date.now()),
      });
    } catch {
      toast.error("Failed to load chat", {
        style: { background: "#000", color: "#fff" },
      });
    }
  };

  const openDeleteModal = (chatId) => {
    setTargetChatId(chatId);
    setShowDeleteModal(true);
  };

  const confirmDelete = async () => {
    try {
      const res = await fetch(
        `${import.meta.env.VITE_API_BASE_URL}/chat/history/${targetChatId}`,
        {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        }
      );

      if (res.ok) {
        toast.success("Chat deleted", {
          style: { background: "#000", color: "#fff" },
        });
        setHistoryList((prev) => prev.filter((c) => c.id !== targetChatId));
        if (selectedChat?.id === targetChatId) setSelectedChat(null);
      } else {
        toast.error("Failed to delete chat");
      }
    } catch {
      toast.error("Something went wrong");
    } finally {
      setShowDeleteModal(false);
      setTargetChatId(null);
    }
  };

  const sendFeedback = async (messageId, feedback) => {
    try {
      await fetch(`${import.meta.env.VITE_API_BASE_URL}/chat/feedback`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({ message_id: messageId, feedback }),
      });
      toast.success("Feedback sent!", {
        style: { background: "#000", color: "#fff" },
      });
      setSelectedChat((prev) => ({
        ...prev,
        messages: prev.messages.map((m) =>
          m.id === messageId ? { ...m, feedback } : m
        ),
      }));
    } catch {
      toast.error("Failed to send feedback");
    }
  };

  const groupByDate = (history) => {
    const today = new Date().toDateString();
    const yesterday = new Date(
      new Date().setDate(new Date().getDate() - 1)
    ).toDateString();

    return {
      Today: history.filter(
        (c) => new Date(c.created_at).toDateString() === today
      ),
      Yesterday: history.filter(
        (c) => new Date(c.created_at).toDateString() === yesterday
      ),
      "Previous 7 Days": history.filter((c) => {
        const d = new Date(c.created_at).toDateString();
        return d !== today && d !== yesterday;
      }),
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

  const filteredHistories = historyList.filter((chat) =>
    chat.title.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const groupedHistory = groupByDate(filteredHistories);

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
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search"
            className="bg-transparent ml-2 outline-none w-full text-sm text-white"
          />
        </div>

        <div className="overflow-y-auto text-sm space-y-6">
          {Object.entries(groupedHistory).map(([group, chats]) => (
            <div key={group}>
              <p className="text-xs text-white/60 mb-2">{group}</p>
              {chats.map((chat) => (
                <div
                  key={chat.id}
                  className="flex items-center justify-between group"
                >
                  <p
                    onClick={() => handleSelectHistory(chat.id)}
                    className={`flex-1 px-2 py-1 rounded-lg cursor-pointer truncate ${
                      selectedChat?.id === chat.id
                        ? "bg-white/20 text-white"
                        : "hover:bg-white/10 text-white/80"
                    }`}
                  >
                    {chat.title}
                  </p>
                  <button
                    onClick={() => openDeleteModal(chat.id)}
                    className="text-white/50 hover:text-red-400 text-sm ml-2 opacity-0 group-hover:opacity-100 transition cursor-pointer"
                    title="Delete"
                  >
                    ✕
                  </button>
                </div>
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

              {loading && (
                <div className="flex flex-col items-center justify-center text-white/70 mt-4">
                  <div className="flex items-center space-x-1 text-sm font-light tracking-wider">
                    <span>Thinking</span>
                    <span className="animate-bounce [animation-delay:0ms]">
                      .
                    </span>
                    <span className="animate-bounce [animation-delay:150ms]">
                      .
                    </span>
                    <span className="animate-bounce [animation-delay:300ms]">
                      .
                    </span>
                  </div>
                </div>
              )}

              <div className="bg-[#1B2332]/80 rounded-2xl p-4 max-w-2xl w-full ml-10">
                <div className="flex items-center gap-2">
                  <textarea
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        handleSend();
                      }
                    }}
                    placeholder="Type here"
                    className="flex-1 bg-transparent outline-none text-white placeholder:text-white/50 px-3 py-3 text-base resize-none"
                    rows={1}
                  />
                  <button
                    onClick={handleSend}
                    className="text-white bg-cyan-600 p-2 rounded-full cursor-pointer"
                    disabled={loading}
                  >
                    {loading ? (
                      <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent" />
                    ) : (
                      <BsSoundwave size={20} />
                    )}
                  </button>
                </div>
              </div>
            </div>
          )}

          {selectedChat && (
            <div className="flex-1 flex flex-col justify-between w-full">
              <div
                className="flex-1 overflow-y-auto pr-2"
                style={{ maxHeight: "70vh" }}
              >
                <div className="space-y-4">
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
                        {msg.message === "Thinking..." ? (
                          <div className="flex items-center space-x-1 text-white/70 text-sm font-light tracking-wider">
                            <span>Thinking</span>
                            <span className="animate-bounce [animation-delay:0ms]">
                              .
                            </span>
                            <span className="animate-bounce [animation-delay:150ms]">
                              .
                            </span>
                            <span className="animate-bounce [animation-delay:300ms]">
                              .
                            </span>
                          </div>
                        ) : (
                          msg.message
                        )}

                        {msg.sender === "bot" && msg.data?.length > 0 && (
                          <div className="mt-3 overflow-x-auto rounded border border-white/10">
                            <table className="min-w-full table-auto text-left text-sm text-white bg-[#1B2332] rounded">
                              <thead className="bg-white/10 text-white uppercase text-xs">
                                <tr>
                                  {Object.keys(msg.data[0]).map((key) => (
                                    <th
                                      key={key}
                                      className="px-4 py-2 border-b border-white/10"
                                    >
                                      {key.replace(/_/g, " ")}
                                    </th>
                                  ))}
                                </tr>
                              </thead>
                              <tbody>
                                {msg.data.map((row, rIdx) => (
                                  <tr
                                    key={rIdx}
                                    className="hover:bg-white/5 transition"
                                  >
                                    {Object.values(row).map((val, cIdx) => (
                                      <td
                                        key={cIdx}
                                        className="px-4 py-2 border-b border-white/5"
                                      >
                                        {val}
                                      </td>
                                    ))}
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        )}
                        {msg.sender === "bot" && !msg.feedback && (
                          <div className="flex justify-end mt-2 space-x-2">
                            <button
                              onClick={() => sendFeedback(msg.id, "positive")}
                              title="Thumbs Up"
                              className="text-green-400 hover:text-green-600 text-xl cursor-pointer"
                            >
                              👍
                            </button>
                            <button
                              onClick={() => sendFeedback(msg.id, "negative")}
                              title="Thumbs Down"
                              className="text-red-400 hover:text-red-600 text-xl cursor-pointer"
                            >
                              👎
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                  <div ref={messagesEndRef} />
                </div>
              </div>

              {/* Input Area */}
              <div className="bg-[#1B2332]/80 rounded-2xl p-4 mt-4">
                <div className="flex items-center gap-2">
                  <textarea
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        handleSend();
                      }
                    }}
                    placeholder="Type here"
                    className="flex-1 bg-transparent outline-none text-white placeholder:text-white/50 px-3 py-3 text-base resize-none"
                    rows={1}
                  />
                  <button
                    onClick={handleSend}
                    className="text-white bg-cyan-600 p-2 rounded-full cursor-pointer"
                    disabled={loading}
                  >
                    {loading ? (
                      <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent" />
                    ) : (
                      <BsSoundwave size={20} />
                    )}
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
      {showDeleteModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-[#1B2332] border border-white/10 rounded-xl p-6 w-[300px] shadow-xl text-white text-center">
            <h3 className="text-lg font-semibold mb-3">Delete Chat</h3>
            <p className="text-sm text-white/70 mb-6">
              Are you sure you want to delete this chat? This action cannot be
              undone.
            </p>
            <div className="flex justify-center gap-4">
              <button
                onClick={() => setShowDeleteModal(false)}
                className="bg-white/10 hover:bg-white/20 px-4 py-2 rounded text-sm cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={confirmDelete}
                className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded text-sm cursor-pointer"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ChatPage;
