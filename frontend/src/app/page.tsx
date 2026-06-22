"use client";

import React, { useState, useEffect, useCallback } from "react";
import Sidebar from "@/components/Sidebar";
import ChatWindow, { Message, ToolExecution } from "@/components/ChatWindow";

const BACKEND_URL = "http://localhost:8000";

export default function Home() {
  const [threads, setThreads] = useState<string[]>([]);
  const [activeThreadId, setActiveThreadId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  
  // Streaming states
  const [activeTools, setActiveTools] = useState<ToolExecution[]>([]);
  const [streamingMessage, setStreamingMessage] = useState<string>("");
  const [isSending, setIsSending] = useState<boolean>(false);

  // 1. Fetch thread history from Postgres via FastAPI
  const loadHistory = useCallback(async (threadId: string) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/threads/${threadId}/messages`);
      if (response.ok) {
        const data = await response.json();
        setMessages(data.messages || []);
      } else {
        console.error("Failed to load history:", response.statusText);
      }
    } catch (err) {
      console.error("Network error loading thread history:", err);
    }
  }, []);

  // 2. Fetch all thread IDs on initial render
  const fetchThreads = useCallback(async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/threads`);
      if (response.ok) {
        const data = await response.json();
        setThreads(data.threads || []);
      }
    } catch (err) {
      console.error("Failed to fetch threads:", err);
    }
  }, []);

  useEffect(() => {
    fetchThreads();
  }, [fetchThreads]);

  // Load history whenever activeThreadId changes
  useEffect(() => {
    if (activeThreadId) {
      loadHistory(activeThreadId);
    } else {
      setMessages([]);
    }
  }, [activeThreadId, loadHistory]);

  // 3. Create a new thread ID
  const handleCreateThread = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/threads`, {
        method: "POST",
      });
      if (response.ok) {
        const data = await response.json();
        const newId = data.thread_id;
        setThreads((prev) => [...prev, newId]);
        setActiveThreadId(newId);
      }
    } catch (err) {
      console.error("Failed to create new thread:", err);
    }
  };

  // 4. Handle sending queries and parsing Server-Sent Events (SSE)
  const handleSendMessage = async (text: string) => {
    if (!text.trim() || !activeThreadId) return;

    // Instantly append user's bubble to chat list
    const userMsg: Message = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setIsSending(true);
    setStreamingMessage("");
    setActiveTools([]);

    try {
      // Connect to FastAPI SSE stream
      const response = await fetch(`${BACKEND_URL}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: text,
          thread_id: activeThreadId,
        }),
      });

      if (!response.ok) {
        throw new Error(`Server returned code ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      if (!reader) return;

      let buffer = "";
      let activeAssistantText = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        
        // Parse SSE double newline delimiter
        const parts = buffer.split("\n\n");
        buffer = parts.pop() || "";

        for (const part of parts) {
          if (!part.trim()) continue;

          const lines = part.split("\n");
          let eventName = "";
          let eventData = "";

          for (const line of lines) {
            if (line.startsWith("event: ")) {
              eventName = line.slice(7).trim();
            } else if (line.startsWith("data: ")) {
              eventData = line.slice(6).trim();
            }
          }

          if (eventData) {
            try {
              const data = JSON.parse(eventData);

              if (eventName === "message") {
                // Update streaming response
                activeAssistantText += data.content;
                setStreamingMessage(activeAssistantText);
              } else if (eventName === "tool_start") {
                // Add tool card in 'running' state
                setActiveTools((prev) => [
                  ...prev,
                  {
                    id: data.id,
                    name: data.name,
                    status: "running",
                  },
                ]);
              } else if (eventName === "tool") {
                // Update tool card to complete
                setActiveTools((prev) =>
                  prev.map((t) =>
                    t.name === data.name
                      ? { ...t, status: "complete", content: data.content }
                      : t
                  )
                );
              } else if (eventName === "error") {
                console.error("AI Error:", data.detail);
                setMessages((prev) => [
                  ...prev,
                  { role: "assistant", content: `Error: ${data.detail}` },
                ]);
              }
            } catch (jsonErr) {
              console.error("JSON parse error on SSE payload:", jsonErr);
            }
          }
        }
      }

      // Re-fetch historical messages to show formatted tool call cards and settled text
      await loadHistory(activeThreadId);
    } catch (err: any) {
      console.error("API communications failure:", err);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Connection failed: ${err.message}. Make sure the FastAPI backend is running.`,
        },
      ]);
    } finally {
      setIsSending(false);
      setStreamingMessage("");
      setActiveTools([]);
    }
  };

  return (
    <main className="flex h-screen w-screen overflow-hidden bg-[#070913]">
      <Sidebar
        threads={threads}
        activeThreadId={activeThreadId}
        onSelectThread={setActiveThreadId}
        onCreateThread={handleCreateThread}
      />
      <ChatWindow
        activeThreadId={activeThreadId}
        messages={messages}
        activeTools={activeTools}
        streamingMessage={streamingMessage}
        isSending={isSending}
        onSendMessage={handleSendMessage}
      />
    </main>
  );
}
