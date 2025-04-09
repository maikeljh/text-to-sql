import { useState } from "react";
import { useNavigate } from "react-router-dom";

function LoginPage() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const handleLogin = async () => {
    // const res = await fetch("http://localhost:8000/login", {
    //   method: "POST",
    //   headers: { "Content-Type": "application/json" },
    //   body: JSON.stringify({ username, password }),
    // });

    // const data = await res.json();

    // if (res.ok) {
    //   localStorage.setItem("user_id", data.user_id);
    //   navigate("/chat");
    // } else {
    //   alert(data.detail || "Login failed");
    // }
    navigate("/chat");
  };

  return (
    <div
      className="min-h-screen bg-cover bg-center flex items-center justify-center"
      style={{ backgroundImage: "url('/login.png')" }}
    >
      <div className="bg-white/10 backdrop-blur-md rounded-xl p-8 shadow-lg w-full max-w-md border border-white/20 z-10">
        <h2 className="text-white text-2xl font-semibold text-center mb-2">
          Welcome to Chatbot
        </h2>
        <p className="text-gray-300 text-sm text-center mb-6">
          Enter your credentials to log in.
        </p>

        <div className="space-y-4">
          <div>
            <label className="block text-white text-sm mb-1">Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Type here"
              className="w-full px-4 py-2 rounded bg-white/10 text-white border border-white/20 focus:outline-none focus:ring-2 focus:ring-indigo-400"
            />
          </div>
          <div>
            <label className="block text-white text-sm mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Type here"
              className="w-full px-4 py-2 rounded bg-white/10 text-white border border-white/20 focus:outline-none focus:ring-2 focus:ring-indigo-400"
            />
          </div>
          <button
            onClick={handleLogin}
            className="w-full bg-white text-gray-900 font-semibold py-2 rounded hover:bg-gray-200 transition cursor-pointer"
          >
            Login
          </button>
        </div>
      </div>
    </div>
  );
}

export default LoginPage;
