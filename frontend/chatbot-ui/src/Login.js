import React, { useState } from "react";
import axios from "axios";
import { useNavigate, Link } from "react-router-dom";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [msg, setMsg] = useState("");
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();

    setMsg(""); // Clear previous error

    try {
      const res = await axios.post("http://localhost:5000/login", {
        email: email.trim(),
        password: password.trim(),
      });

      if (res.status === 200) {
        // Save user info
        localStorage.setItem("user_id", res.data.user_id);
        localStorage.setItem("user_name", res.data.name);

        // Redirect
        navigate("/chat");
      }
    } catch (err) {
      setMsg("❌ Invalid email or password");
    }
  };

  return (
    <div className="flex flex-col items-center mt-24">
      <h2 className="text-xl font-semibold mb-4">Login</h2>

      <form onSubmit={handleLogin} className="flex flex-col w-64">
        <input
          type="email"
          placeholder="Email"
          className="border p-2 mb-2 rounded"
          value={email}
          onChange={(e) => {
            setEmail(e.target.value);
            setMsg("");
          }}
        />

        <input
          type="password"
          placeholder="Password"
          className="border p-2 mb-2 rounded"
          value={password}
          onChange={(e) => {
            setPassword(e.target.value);
            setMsg("");
          }}
        />

        <button className="bg-green-500 text-white py-2 rounded hover:bg-green-600">
          Login
        </button>
      </form>

      {msg && <p className="text-red-500 mt-3">{msg}</p>}

      <p className="mt-4 text-sm">
        Don’t have an account?{" "}
        <Link to="/register" className="text-blue-500 hover:underline">
          Create one
        </Link>
      </p>
    </div>
  );
}
