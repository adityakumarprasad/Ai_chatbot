"use client";

import React, { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Wrench, ChevronDown, ChevronUp, CheckCircle, Paperclip, Loader, FileText } from "lucide-react";

export interface Message {
  role: "user" | "assistant" | "tool";
  content: string;
  name?: string;
}

export interface ToolExecution {
  id?: string;
  name: string;
  content?: string;
  status: "running" | "complete";
}

interface ChatWindowProps {
  activeThreadId: string | null;
  messages: Message[];
  activeTools: ToolExecution[];
  streamingMessage: string;
  isSending: boolean;
  onSendMessage: (text: string) => void;
  activeDoc: {
    files: { filename: string; documents: number; chunks: number }[];
    total_documents: number;
    total_chunks: number;
  } | null;
  onUploadFile: (file: File) => void;
  isUploading: boolean;
}

export default function ChatWindow({
  activeThreadId,
  messages,
  activeTools,
  streamingMessage,
  isSending,
  onSendMessage,
  activeDoc,
  onUploadFile,
  isUploading,
}: ChatWindowProps) {
  const [inputValue, setInputValue] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom on new messages or tools
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, activeTools, streamingMessage]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || isSending || isUploading) return;
    onSendMessage(inputValue);
    setInputValue("");
  };

  // Helper component to render collapsible tool cards
  const ToolCard = ({ name, content, status }: { name: string; content?: string; status: string }) => {
    const [isOpen, setIsOpen] = useState(false);
    const isComplete = status === "complete";
    
    return (
      <div className="w-full my-2 rounded-xl border border-[rgba(255,255,255,0.06)] bg-[rgba(255,255,255,0.02)] overflow-hidden animate-slide-up">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="w-full flex items-center justify-between px-4 py-3 cursor-pointer select-none hover:bg-[rgba(255,255,255,0.02)] transition-colors"
        >
          <div className="flex items-center gap-2.5">
            {isComplete ? (
              <CheckCircle className="w-4.5 h-4.5 text-emerald-400 shrink-0" />
            ) : (
              <Wrench className="w-4.5 h-4.5 text-indigo-400 animate-spin shrink-0" />
            )}
            <span className="text-xs font-semibold tracking-wider font-mono text-gray-300">
              {name.toUpperCase()}
            </span>
            <span className={`text-[10px] px-2 py-0.5 rounded-full font-semibold ${
              isComplete 
                ? "bg-emerald-500/10 text-emerald-400" 
                : "bg-indigo-500/10 text-indigo-400 animate-pulse"
            }`}>
              {status}
            </span>
          </div>
          {isOpen ? (
            <ChevronUp className="w-4 h-4 text-gray-500" />
          ) : (
            <ChevronDown className="w-4 h-4 text-gray-500" />
          )}
        </button>
        {isOpen && (
          <div className="px-4 pb-4 border-t border-[rgba(255,255,255,0.04)] bg-[rgba(0,0,0,0.2)]">
            <pre className="text-xs font-mono text-gray-400 whitespace-pre-wrap mt-3 overflow-x-auto leading-relaxed">
              {content || (isComplete ? "Executed successfully." : "Running tool call...")}
            </pre>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="flex-1 h-full flex flex-col bg-[#070913]">
      {/* Thread Header */}
      <div className="h-16 border-b border-[rgba(255,255,255,0.06)] px-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-3 h-3 rounded-full bg-indigo-500 shadow-[0_0_10px_rgba(99,102,241,0.6)] animate-pulse" />
          <span className="text-sm font-semibold tracking-wide text-gray-200">
            {activeThreadId ? `Chat Session: ${activeThreadId.substring(0, 8)}` : "Select a thread"}
          </span>
        </div>

        {/* Active Document Status Badge */}
        {activeDoc && activeDoc.files.length > 0 && (
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-emerald-500/20 bg-emerald-500/10 text-emerald-400 text-xs font-medium animate-slide-up">
            <FileText className="w-3.5 h-3.5 shrink-0" />
            <span>{activeDoc.files.length} Document(s) active</span>
          </div>
        )}
      </div>

      {/* Main Container */}
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
        {!activeThreadId ? (
          /* Empty Dashboard State */
          <div className="h-full flex flex-col justify-center items-center text-center max-w-2xl mx-auto space-y-8 select-none">
            <div className="space-y-3">
              <div className="w-16 h-16 rounded-3xl bg-indigo-600/10 flex items-center justify-center border border-indigo-500/20 mx-auto text-indigo-400">
                <Bot className="w-8 h-8 animate-pulse-glow" />
              </div>
              <h2 className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-indigo-300 via-purple-300 to-fuchsia-300 bg-clip-text text-transparent">
                Refactored AI Chat Space
              </h2>
              <p className="text-sm text-gray-400 max-w-md mx-auto leading-relaxed">
                Welcome to your modular workspace powered by FastAPI, PostgreSQL, LangGraph, and Google Gemini.
              </p>
            </div>

            {/* Grid of Capabilities */}
            <div className="grid grid-cols-2 gap-4 w-full text-left">
              <div className="glass-card p-5 rounded-2xl">
                <h3 className="text-sm font-bold text-indigo-400 mb-1">Google Gemini AI</h3>
                <p className="text-xs text-gray-500 leading-relaxed">
                  Leverages Gemini 1.5/2.5 for high-speed reasoning, message streaming, and context summarization.
                </p>
              </div>

              <div className="glass-card p-5 rounded-2xl">
                <h3 className="text-sm font-bold text-purple-400 mb-1">GitHub MCP Server</h3>
                <p className="text-xs text-gray-500 leading-relaxed">
                  FastMCP server exposing repository searches, issue creation, and file commits via secure stdio.
                </p>
              </div>

              <div className="glass-card p-5 rounded-2xl">
                <h3 className="text-sm font-bold text-fuchsia-400 mb-1">LangGraph & Postgres</h3>
                <p className="text-xs text-gray-500 leading-relaxed">
                  Robust state machines with Postgres checkpointers to keep persistent chat history across reboots.
                </p>
              </div>

              <div className="glass-card p-5 rounded-2xl">
                <h3 className="text-sm font-bold text-emerald-400 mb-1">RAG Document Q&A</h3>
                <p className="text-xs text-gray-500 leading-relaxed">
                  Upload PDF files to query details. Uses local FAISS databases and Gemini embeddings to retrieve contexts.
                </p>
              </div>
            </div>

            <div className="text-xs text-gray-600 flex items-center gap-1.5 justify-center">
              <span>Select or create a thread in the sidebar to initialize the AI.</span>
            </div>
          </div>
        ) : (
          /* Conversation stream */
          <div className="max-w-3xl mx-auto space-y-6">
            {messages.map((msg, index) => {
              if (msg.role === "tool") {
                // Historical tool calls
                return (
                  <ToolCard
                    key={`hist-tool-${index}`}
                    name={msg.name || "tool"}
                    content={msg.content}
                    status="complete"
                  />
                );
              }

              const isUser = msg.role === "user";
              return (
                <div
                  key={`msg-${index}`}
                  className={`flex gap-4 max-w-full ${isUser ? "flex-row-reverse" : "flex-row"} animate-slide-up`}
                >
                  {/* Profile icon */}
                  <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 border ${
                    isUser 
                      ? "bg-indigo-500/10 border-indigo-500/20 text-indigo-400" 
                      : "bg-white/5 border-white/10 text-gray-400"
                  }`}>
                    {isUser ? <User className="w-5 h-5" /> : <Bot className="w-5 h-5" />}
                  </div>

                  {/* Message Bubble */}
                  <div className={`rounded-2xl px-5 py-3.5 max-w-[75%] border text-sm leading-relaxed whitespace-pre-wrap break-words ${
                    isUser
                      ? "bg-indigo-500/15 border-indigo-500/20 text-indigo-100"
                      : "bg-white/5 border-white/10 text-gray-200"
                  }`}>
                    {msg.content}
                  </div>
                </div>
              );
            })}

            {/* Active streaming tools */}
            {activeTools.map((tool, idx) => (
              <ToolCard
                key={`active-tool-${idx}`}
                name={tool.name}
                content={tool.content}
                status={tool.status}
              />
            ))}

            {/* Active streaming text from assistant */}
            {streamingMessage && (
              <div className="flex gap-4 max-w-full flex-row animate-slide-up">
                <div className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0 border bg-white/5 border-white/10 text-gray-400">
                  <Bot className="w-5 h-5" />
                </div>
                <div className="rounded-2xl px-5 py-3.5 max-w-[75%] border bg-white/5 border-white/10 text-sm leading-relaxed whitespace-pre-wrap break-words text-gray-200">
                  {streamingMessage}
                </div>
              </div>
            )}

            {/* AI thinking/typing bubble */}
            {isSending && !streamingMessage && activeTools.length === 0 && (
              <div className="flex gap-4 max-w-full flex-row animate-slide-up">
                <div className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0 border bg-white/5 border-white/10 text-gray-400">
                  <Bot className="w-5 h-5" />
                </div>
                <div className="rounded-2xl px-5 py-4 border bg-white/5 border-white/10 flex items-center gap-1.5 justify-center w-24">
                  <span className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce" style={{ animationDelay: "0ms" }}></span>
                  <span className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce" style={{ animationDelay: "150ms" }}></span>
                  <span className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce" style={{ animationDelay: "300ms" }}></span>
                </div>
              </div>
            )}

            {/* Empty space at the end of messages */}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input controls */}
      {activeThreadId && (
        <div className="p-6 border-t border-[rgba(255,255,255,0.06)] bg-[rgba(7,9,19,0.3)]">
          
          {/* Active Document Attachment Previews */}
          {activeDoc && activeDoc.files.length > 0 && (
            <div className="max-w-3xl mx-auto flex flex-wrap gap-2.5 mb-4 animate-slide-up select-none">
              {activeDoc.files.map((file, idx) => (
                <div key={idx} className="flex items-center gap-3 px-3.5 py-2.5 rounded-xl border border-emerald-500/20 bg-emerald-500/5 text-emerald-300 text-xs font-medium w-fit">
                  <FileText className="w-4.5 h-4.5 text-emerald-400 shrink-0" />
                  <div className="flex flex-col">
                    <span className="font-bold truncate max-w-[160px] text-gray-200">{file.filename}</span>
                    <span className="text-[10px] text-emerald-400/80 mt-0.5">{file.documents} pages</span>
                  </div>
                </div>
              ))}
            </div>
          )}

          <form onSubmit={handleSubmit} className="max-w-3xl mx-auto relative flex items-center gap-3">
            
            {/* Hidden Input selector for PDF file sharing */}
            <input
              type="file"
              ref={fileInputRef}
              accept=".pdf"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) {
                  onUploadFile(file);
                }
              }}
              className="hidden"
            />

            {/* Paperclip upload trigger */}
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploading || isSending}
              className="w-12 h-12 rounded-2xl bg-white/5 hover:bg-white/10 text-gray-400 hover:text-gray-200 border border-[rgba(255,255,255,0.08)] flex items-center justify-center transition-all cursor-pointer disabled:opacity-50 shrink-0"
              title="Upload PDF document for RAG search"
            >
              {isUploading ? (
                <Loader className="w-5 h-5 animate-spin text-indigo-400" />
              ) : (
                <Paperclip className="w-5 h-5" />
              )}
            </button>

            {/* Input message bar */}
            <div className="relative flex-1">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                disabled={isSending || isUploading}
                placeholder={
                  isUploading
                    ? "Parsing document details..."
                    : isSending
                      ? "AI is reasoning..."
                      : activeDoc
                        ? "Ask about the document..."
                        : "Message or upload a PDF..."
                }
                className="w-full py-4 pl-5 pr-14 rounded-2xl bg-white/5 hover:bg-white/8 focus:bg-white/8 border border-[rgba(255,255,255,0.08)] focus:border-indigo-500/50 text-gray-200 placeholder-gray-500 text-sm outline-none transition-all duration-300 disabled:opacity-50"
              />
              <button
                type="submit"
                disabled={!inputValue.trim() || isSending || isUploading}
                className="absolute right-3.5 top-3 w-10 h-10 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white flex items-center justify-center transition-all duration-200 disabled:opacity-30 disabled:hover:bg-indigo-600 cursor-pointer"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>

          </form>
        </div>
      )}
    </div>
  );
}
