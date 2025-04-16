import { useState } from "react";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { FiEye, FiEyeOff } from "react-icons/fi";

function LoginPage() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const handleLogin = async () => {
    try {
      const res = await fetch(
        import.meta.env.VITE_API_BASE_URL + "/auth/login",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username, password }),
        }
      );

      const data = await res.json();

      if (res.ok) {
        localStorage.setItem("user_id", data.user_id);
        localStorage.setItem("token", data.access_token);
        toast.success("Login successful");
        navigate("/chat");
      } else {
        toast.error(data.detail || "Login failed");
      }
    } catch (err) {
      console.error("Login error:", err);
      toast.error("Something went wrong");
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") handleLogin();
  };

  return (
    <div
      className="min-h-screen bg-cover bg-center flex items-center justify-center"
      style={{ backgroundImage: "url('/login.png')" }}
    >
      <div className="bg-white/10 backdrop-blur-md rounded-xl p-8 shadow-lg w-full max-w-md border border-white/20 z-10">
        <h2 className="text-white text-2xl font-semibold text-center mb-2">
          Welcome to SQL Chatbot
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
              onKeyDown={handleKeyDown}
              placeholder="Type here"
              className="w-full px-4 py-2 rounded bg-white/10 text-white border border-white/20 focus:outline-none focus:ring-2 focus:ring-indigo-400"
            />
          </div>
          <div>
            <label className="block text-white text-sm mb-1">Password</label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type here"
                className="w-full px-4 py-2 pr-10 rounded bg-white/10 text-white border border-white/20 focus:outline-none focus:ring-2 focus:ring-indigo-400"
              />
              <button
                type="button"
                onClick={() => setShowPassword((prev) => !prev)}
                className="absolute right-3 top-2.5 text-white/70 cursor-pointer"
              >
                {showPassword ? <FiEyeOff size={18} /> : <FiEye size={18} />}
              </button>
            </div>
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
