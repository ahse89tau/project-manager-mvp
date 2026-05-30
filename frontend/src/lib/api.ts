import type { BoardData } from "@/lib/kanban";

export type AIChatMessage = { role: string; content: string };

export type AIChatResponse = {
  assistantMessage: string;
  applyBoardUpdate: boolean;
  boardUpdated: boolean;
};

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

const defaultErrorMessage = "Request failed. Please try again.";

const getErrorMessage = async (response: Response): Promise<string> => {
  try {
    const payload = await response.json();
    if (typeof payload?.detail === "string" && payload.detail.trim()) {
      return payload.detail;
    }
  } catch {
    return defaultErrorMessage;
  }

  return defaultErrorMessage;
};

const withAuth = (init?: RequestInit): RequestInit => ({
  ...init,
  credentials: "include",
});

export const fetchBoard = async (): Promise<BoardData> => {
  const response = await fetch("/api/board", withAuth());
  if (!response.ok) {
    throw new ApiError(await getErrorMessage(response), response.status);
  }
  return (await response.json()) as BoardData;
};

export const saveBoard = async (board: BoardData): Promise<BoardData> => {
  const response = await fetch(
    "/api/board",
    withAuth({
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(board),
    })
  );

  if (!response.ok) {
    throw new ApiError(await getErrorMessage(response), response.status);
  }

  const payload = (await response.json()) as {
    saved: boolean;
    board: BoardData;
  };

  return payload.board;
};

export const sendAIMessage = async (
  message: string,
  history: AIChatMessage[]
): Promise<AIChatResponse> => {
  const response = await fetch(
    "/api/ai/chat",
    withAuth({
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, history }),
    })
  );

  if (!response.ok) {
    throw new ApiError(await getErrorMessage(response), response.status);
  }

  return (await response.json()) as AIChatResponse;
};
