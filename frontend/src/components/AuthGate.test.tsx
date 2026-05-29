import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AuthGate } from "@/components/AuthGate";

vi.mock("@/components/KanbanBoard", () => ({
  KanbanBoard: () => <div data-testid="kanban-board">Board</div>,
}));

const mockJsonResponse = (body: unknown, ok = true) =>
  ({
    ok,
    json: vi.fn().mockResolvedValue(body),
  }) as unknown as Response;

describe("AuthGate", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("shows the login form when unauthenticated", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(mockJsonResponse({ authenticated: false }));

    render(<AuthGate />);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /kanban studio/i })).toBeInTheDocument();
    });
    expect(screen.getByRole("button", { name: /sign in/i })).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith("/api/auth/session", {
      credentials: "include",
    });
  });

  it("shows an error when login fails", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(mockJsonResponse({ authenticated: false }))
      .mockResolvedValueOnce(mockJsonResponse({ detail: "Invalid username or password" }, false));

    render(<AuthGate />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /sign in/i })).toBeInTheDocument();
    });

    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Invalid username or password");
    });
  });

  it("logs in successfully and supports logout", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(mockJsonResponse({ authenticated: false }))
      .mockResolvedValueOnce(mockJsonResponse({ authenticated: true }))
      .mockResolvedValueOnce(mockJsonResponse({ authenticated: false }));

    render(<AuthGate />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /sign in/i })).toBeInTheDocument();
    });

    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByTestId("kanban-board")).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /log out/i })).toBeInTheDocument();
    });

    await userEvent.click(screen.getByRole("button", { name: /log out/i }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /sign in/i })).toBeInTheDocument();
    });
  });
});
