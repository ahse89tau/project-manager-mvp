"use client";

import { useEffect, useRef, useState } from "react";
import { sendAIMessage, type AIChatMessage } from "@/lib/api";

type UIMessage = AIChatMessage & { id: string };

type Props = {
  isOpen: boolean;
  onClose: () => void;
  onBoardUpdated: () => void;
};

export const AISidebar = ({ isOpen, onClose, onBoardUpdated }: Props) => {
  const [messages, setMessages] = useState<UIMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (isOpen) {
      inputRef.current?.focus();
    }
  }, [isOpen]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || isLoading) return;

    const history: AIChatMessage[] = messages.map(({ role, content }) => ({ role, content }));
    setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: "user", content: text }]);
    setInput("");
    setIsLoading(true);
    setError("");

    try {
      const response = await sendAIMessage(text, history);
      setMessages((prev) => [
        ...prev,
        { id: crypto.randomUUID(), role: "assistant", content: response.assistantMessage },
      ]);
      if (response.boardUpdated) {
        onBoardUpdated();
      }
    } catch {
      setError("Failed to get a response. Please try again.");
      setMessages((prev) => prev.slice(0, -1));
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void handleSend();
    }
  };

  if (!isOpen) return null;

  return (
    <>
      <div
        className="fixed inset-0 z-40 bg-black/20 lg:hidden"
        onClick={onClose}
        aria-hidden="true"
      />

      <aside
        aria-label="AI assistant"
        className="fixed right-0 top-0 z-50 flex h-full w-full flex-col border-l border-[var(--stroke)] bg-white shadow-[var(--shadow)] lg:w-96"
      >
        <div className="flex items-center justify-between border-b border-[var(--stroke)] px-5 py-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.25em] text-[var(--gray-text)]">
              AI Assistant
            </p>
            <h2 className="mt-1 font-display text-lg font-semibold text-[var(--navy-dark)]">
              Kanban AI
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close AI sidebar"
            className="rounded-full p-2 text-[var(--gray-text)] transition hover:bg-[var(--surface)] hover:text-[var(--navy-dark)]"
          >
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
              <path
                d="M2 2l14 14M16 2L2 16"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
              />
            </svg>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-4 py-4">
          {messages.length === 0 && !isLoading && (
            <p className="text-center text-sm text-[var(--gray-text)]">
              Ask me to add, move, or edit cards on your board.
            </p>
          )}

          <div className="flex flex-col gap-3">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                    msg.role === "user"
                      ? "bg-[var(--primary-blue)] text-white"
                      : "border border-[var(--stroke)] bg-[var(--surface)] text-[var(--navy-dark)]"
                  }`}
                >
                  {msg.content}
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="flex justify-start">
                <div
                  aria-label="AI is thinking"
                  className="rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-4 py-3"
                >
                  <div className="flex gap-1">
                    <span
                      className="h-2 w-2 animate-bounce rounded-full bg-[var(--gray-text)]"
                      style={{ animationDelay: "0ms" }}
                    />
                    <span
                      className="h-2 w-2 animate-bounce rounded-full bg-[var(--gray-text)]"
                      style={{ animationDelay: "150ms" }}
                    />
                    <span
                      className="h-2 w-2 animate-bounce rounded-full bg-[var(--gray-text)]"
                      style={{ animationDelay: "300ms" }}
                    />
                  </div>
                </div>
              </div>
            )}

            {error && (
              <p
                role="alert"
                className="text-center text-xs text-[var(--secondary-purple)]"
              >
                {error}
              </p>
            )}
          </div>

          <div ref={messagesEndRef} />
        </div>

        <div className="border-t border-[var(--stroke)] p-4">
          <div className="flex gap-2">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask to add, move, or edit cards..."
              rows={2}
              aria-label="Message"
              disabled={isLoading}
              className="flex-1 resize-none rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-4 py-3 text-sm text-[var(--navy-dark)] placeholder:text-[var(--gray-text)] focus:outline-none focus:ring-2 focus:ring-[var(--primary-blue)] disabled:opacity-50"
            />
            <button
              type="button"
              onClick={() => void handleSend()}
              disabled={!input.trim() || isLoading}
              aria-label="Send message"
              className="self-end rounded-full bg-[var(--primary-blue)] p-3 text-white transition hover:opacity-90 disabled:opacity-40"
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                <path d="M14 8L2 2l2 6-2 6 12-6z" fill="currentColor" />
              </svg>
            </button>
          </div>
          <p className="mt-2 text-[10px] text-[var(--gray-text)]">
            Enter to send · Shift+Enter for new line
          </p>
        </div>
      </aside>
    </>
  );
};
