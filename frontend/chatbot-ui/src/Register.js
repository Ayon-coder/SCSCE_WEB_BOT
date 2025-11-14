import React, { useState } from "react";
import axios from "axios";

export default function Register() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [msg, setMsg] = useState("");

  const handleRegister = async (e) => {
    e.preventDefault();
    try {
      const res = await axios.post("http://localhost:5000/register", {
        name,
        email,
        password
      });
      setMsg("✅ " + res.data.message);
    } catch (err) {
      setMsg("❌ " + (err.response?.data?.error || "Registration failed"));
    }
  };

  return (
    <div className="flex flex-col items-center mt-24">
      <h2 className="text-xl font-semibold mb-4">Create Account</h2>

      <form onSubmit={handleRegister} className="flex flex-col w-64">
        <input
          type="text"
          placeholder="Full Name"
          className="border p-2 mb-2 rounded"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />

        <input
          type="email"
          placeholder="Email"
          className="border p-2 mb-2 rounded"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />

        <input
          type="password"
          placeholder="Password"
          className="border p-2 mb-2 rounded"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />

        <button className="bg-blue-500 text-white py-2 rounded hover:bg-blue-600">
          Register
        </button>
      </form>

      {msg && <p className="mt-3">{msg}</p>}
    </div>
  );
}
