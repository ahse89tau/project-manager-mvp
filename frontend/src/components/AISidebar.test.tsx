import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AISidebar } from "@/components/AISidebar";
import { sendAIMessage } from "@/lib/api";

vi.mock("@/lib/api", () => ({
  sendAIMessage: vi.fn(),
}));

beforeAll(() => {
  window.HTMLElement.prototype.scrollIntoView = vi.fn();
});

const sendAIMessageMock = vi.mocked(sendAIMessage);

const defaultProps = {
  isOpen: true,
  onClose: vi.fn(),
  onBoardUpdated: vi.fn(),
};

describe("AISidebar", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("renders nothing when closed", () => {
    render(<AISidebar {...defaultProps} isOpen={false} />);
    expect(screen.queryByRole("complementary")).not.toBeInTheDocument();
  });

  it("shows empty state prompt when open with no messages", () => {
    render(<AISidebar {...defaultProps} />);
    expect(
      screen.getByText(/ask me to add, move, or edit cards/i)
    ).toBeInTheDocument();
  });

  it("calls onClose when close button is clicked", async () => {
    const onClose = vi.fn();
    render(<AISidebar {...defaultProps} onClose={onClose} />);
    await userEvent.click(screen.getByRole("button", { name: /close ai sidebar/i }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("sends a message and displays the assistant response", async () => {
    sendAIMessageMock.mockResolvedValueOnce({
      assistantMessage: "Done! I added the card.",
      applyBoardUpdate: false,
      boardUpdated: false,
    });

    render(<AISidebar {...defaultProps} />);

    const textarea = screen.getByRole("textbox", { name: /message/i });
    await userEvent.type(textarea, "Add a card");
    await userEvent.click(screen.getByRole("button", { name: /send message/i }));

    await waitFor(() => {
      expect(screen.getByText("Add a card")).toBeInTheDocument();
      expect(screen.getByText("Done! I added the card.")).toBeInTheDocument();
    });

    expect(sendAIMessageMock).toHaveBeenCalledWith("Add a card", []);
  });

  it("sends message on Enter key", async () => {
    sendAIMessageMock.mockResolvedValueOnce({
      assistantMessage: "Got it.",
      applyBoardUpdate: false,
      boardUpdated: false,
    });

    render(<AISidebar {...defaultProps} />);

    const textarea = screen.getByRole("textbox", { name: /message/i });
    await userEvent.type(textarea, "Move card to Done{Enter}");

    await waitFor(() => {
      expect(sendAIMessageMock).toHaveBeenCalledTimes(1);
    });
  });

  it("does not send on Shift+Enter", async () => {
    render(<AISidebar {...defaultProps} />);

    const textarea = screen.getByRole("textbox", { name: /message/i });
    await userEvent.type(textarea, "Hello{Shift>}{Enter}{/Shift}");

    expect(sendAIMessageMock).not.toHaveBeenCalled();
  });

  it("calls onBoardUpdated when the AI reports a board mutation", async () => {
    const onBoardUpdated = vi.fn();
    sendAIMessageMock.mockResolvedValueOnce({
      assistantMessage: "Card moved.",
      applyBoardUpdate: true,
      boardUpdated: true,
    });

    render(<AISidebar {...defaultProps} onBoardUpdated={onBoardUpdated} />);

    await userEvent.type(
      screen.getByRole("textbox", { name: /message/i }),
      "Move card"
    );
    await userEvent.click(screen.getByRole("button", { name: /send message/i }));

    await waitFor(() => {
      expect(onBoardUpdated).toHaveBeenCalledTimes(1);
    });
  });

  it("does not call onBoardUpdated when no board mutation occurred", async () => {
    const onBoardUpdated = vi.fn();
    sendAIMessageMock.mockResolvedValueOnce({
      assistantMessage: "Looks good!",
      applyBoardUpdate: false,
      boardUpdated: false,
    });

    render(<AISidebar {...defaultProps} onBoardUpdated={onBoardUpdated} />);

    await userEvent.type(
      screen.getByRole("textbox", { name: /message/i }),
      "How many cards are there?"
    );
    await userEvent.click(screen.getByRole("button", { name: /send message/i }));

    await waitFor(() => {
      expect(screen.getByText("Looks good!")).toBeInTheDocument();
    });
    expect(onBoardUpdated).not.toHaveBeenCalled();
  });

  it("shows error and removes optimistic message when request fails", async () => {
    sendAIMessageMock.mockRejectedValueOnce(new Error("network error"));

    render(<AISidebar {...defaultProps} />);

    await userEvent.type(
      screen.getByRole("textbox", { name: /message/i }),
      "Do something"
    );
    await userEvent.click(screen.getByRole("button", { name: /send message/i }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(
        "Failed to get a response. Please try again."
      );
    });

    expect(screen.queryByText("Do something")).not.toBeInTheDocument();
  });

  it("passes conversation history to subsequent messages", async () => {
    sendAIMessageMock
      .mockResolvedValueOnce({
        assistantMessage: "First reply.",
        applyBoardUpdate: false,
        boardUpdated: false,
      })
      .mockResolvedValueOnce({
        assistantMessage: "Second reply.",
        applyBoardUpdate: false,
        boardUpdated: false,
      });

    render(<AISidebar {...defaultProps} />);

    const textarea = screen.getByRole("textbox", { name: /message/i });

    await userEvent.type(textarea, "First message");
    await userEvent.click(screen.getByRole("button", { name: /send message/i }));
    await waitFor(() => {
      expect(screen.getByText("First reply.")).toBeInTheDocument();
    });

    await userEvent.type(textarea, "Second message");
    await userEvent.click(screen.getByRole("button", { name: /send message/i }));
    await waitFor(() => {
      expect(screen.getByText("Second reply.")).toBeInTheDocument();
    });

    expect(sendAIMessageMock).toHaveBeenNthCalledWith(2, "Second message", [
      { role: "user", content: "First message" },
      { role: "assistant", content: "First reply." },
    ]);
  });
});
