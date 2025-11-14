import React, { useState, useEffect } from "react";

function Chat() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);

  const user_id = localStorage.getItem("user_id");
  const user_name = localStorage.getItem("user_name");

  // Add welcome message only once
  useEffect(() => {
    if (user_name) {
      setMessages([
        {
          sender: "bot",
          text: `👋 Welcome back, ${user_name}! How can I help you today?`
        }
      ]);
    }
  }, [user_name]);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMsg = { sender: "user", text: input };
    setMessages((prev) => [...prev, userMsg]);

    const res = await fetch("http://127.0.0.1:5000/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: user_id,
        name: user_name,     // ✅ sending name to backend
        message: input
      }),
    });

    const data = await res.json();

    const botMsg = { sender: "bot", text: data.reply || data.error };
    setMessages((prev) => [...prev, botMsg]);

    setInput("");
  };

  return (
    <div className="flex flex-col h-screen bg-gray-100">
      <header className="bg-indigo-600 text-white p-4 text-center font-semibold">
        SCCSE Chatbot
      </header>

      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`p-3 rounded-lg ${
              msg.sender === "user"
                ? "bg-indigo-200 self-end text-right"
                : "bg-white self-start shadow"
            }`}
          >
            {msg.text}
          </div>
        ))}
      </div>

      <div className="p-4 bg-white flex">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          className="flex-1 border rounded-l-lg px-3 py-2"
          placeholder="Ask something..."
        />
        <button
          onClick={sendMessage}
          className="bg-indigo-600 text-white px-4 py-2 rounded-r-lg"
        >
          Send
        </button>
      </div>
    </div>
  );
}

export default Chat;
