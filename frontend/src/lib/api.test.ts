import { ApiError, fetchBoard, saveBoard, sendAIMessage } from "@/lib/api";
import { initialData } from "@/lib/kanban";

const mockJsonResponse = (body: unknown, ok = true, status = 200) =>
  ({
    ok,
    status,
    json: vi.fn().mockResolvedValue(body),
  }) as unknown as Response;

describe("api client", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("fetchBoard requests board with auth credentials", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(mockJsonResponse(initialData));

    const board = await fetchBoard();

    expect(fetchMock).toHaveBeenCalledWith("/api/board", {
      credentials: "include",
    });
    expect(board).toEqual(initialData);
  });

  it("fetchBoard throws ApiError with backend detail", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      mockJsonResponse({ detail: "Authentication required" }, false, 401)
    );

    await expect(fetchBoard()).rejects.toMatchObject<ApiError>({
      name: "ApiError",
      status: 401,
      message: "Authentication required",
    });
  });

  it("saveBoard sends board payload and returns saved board", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(mockJsonResponse({ saved: true, board: initialData }));

    const board = await saveBoard(initialData);

    expect(fetchMock).toHaveBeenCalledWith("/api/board", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(initialData),
      credentials: "include",
    });
    expect(board).toEqual(initialData);
  });

  it("saveBoard throws ApiError when save fails", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      mockJsonResponse({ detail: "invalid board" }, false, 422)
    );

    await expect(saveBoard(initialData)).rejects.toMatchObject<ApiError>({
      name: "ApiError",
      status: 422,
      message: "invalid board",
    });
  });

  it("sendAIMessage sends message and history with auth credentials", async () => {
    const aiResponse = {
      assistantMessage: "Done.",
      applyBoardUpdate: false,
      boardUpdated: false,
    };
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(mockJsonResponse(aiResponse));

    const history = [{ role: "user", content: "previous" }];
    const result = await sendAIMessage("new message", history);

    expect(fetchMock).toHaveBeenCalledWith("/api/ai/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: "new message", history }),
      credentials: "include",
    });
    expect(result).toEqual(aiResponse);
  });

  it("sendAIMessage throws ApiError when request fails", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      mockJsonResponse({ detail: "AI unavailable" }, false, 503)
    );

    await expect(sendAIMessage("hello", [])).rejects.toMatchObject<ApiError>({
      name: "ApiError",
      status: 503,
      message: "AI unavailable",
    });
  });
});
