"use client";

import React from "react";
import { Plus, MessageSquare } from "lucide-react";

interface SidebarProps {
  threads: string[];
  activeThreadId: string | null;
  onSelectThread: (id: string) => void;
  onCreateThread: () => void;
}

export default function Sidebar({
  threads,
  activeThreadId,
  onSelectThread,
  onCreateThread,
}: SidebarProps) {
  // Sort threads so the most recently accessed/active stays recognizable,
  // or simply keep reverse order of creation
  const sortedThreads = [...threads].reverse();

  return (
    <aside className="w-80 h-full glass-panel flex flex-col border-r border-[rgba(255,255,255,0.06)] select-none">
      {/* App Header */}
      <div className="p-6 border-b border-[rgba(255,255,255,0.06)]">
        <h1 className="text-xl font-bold bg-gradient-to-r from-indigo-400 via-purple-400 to-fuchsia-400 bg-clip-text text-transparent tracking-wide">
          AI Chat Space
        </h1>
        <p className="text-xs text-gray-500 mt-1">LangGraph & Gemini Workspace</p>
      </div>

      {/* Create New Chat Button */}
      <div className="p-4">
        <button
          onClick={onCreateThread}
          className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl bg-gradient-to-r from-indigo-600 via-indigo-500 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-semibold text-sm transition-all duration-300 hover:shadow-[0_0_15px_rgba(99,102,241,0.4)] hover:scale-[1.02] active:scale-[0.98] cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          <span>New Chat</span>
        </button>
      </div>

      {/* Conversation Thread History List */}
      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-1.5">
        <div className="px-3 mb-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
          Conversations
        </div>
        {sortedThreads.length === 0 ? (
          <div className="px-3 py-8 text-center text-sm text-gray-500">
            No active threads. Click 'New Chat' to get started.
          </div>
        ) : (
          sortedThreads.map((id) => {
            const isActive = activeThreadId === id;
            const shortId = id.substring(0, 8);
            return (
              <button
                key={id}
                onClick={() => onSelectThread(id)}
                className={`w-full flex items-center gap-3 px-3 py-3 rounded-xl transition-all duration-200 text-left cursor-pointer border ${
                  isActive
                    ? "bg-[rgba(99,102,241,0.15)] text-indigo-300 border-[rgba(99,102,241,0.25)] shadow-[0_0_10px_rgba(99,102,241,0.1)]"
                    : "text-gray-400 hover:bg-[rgba(255,255,255,0.03)] hover:text-[#f3f4f6] border-transparent"
                }`}
              >
                <MessageSquare
                  className={`w-4.5 h-4.5 shrink-0 ${isActive ? "text-indigo-400" : "text-gray-500"}`}
                />
                <span className="text-sm font-medium truncate">Chat {shortId}</span>
              </button>
            );
          })
        )}
      </div>
    </aside>
  );
}
