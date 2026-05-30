import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { KanbanBoard } from "@/components/KanbanBoard";
import { fetchBoard, saveBoard } from "@/lib/api";
import { initialData, type BoardData } from "@/lib/kanban";

vi.mock("@/lib/api", () => ({
  fetchBoard: vi.fn(),
  saveBoard: vi.fn(),
}));

const fetchBoardMock = vi.mocked(fetchBoard);
const saveBoardMock = vi.mocked(saveBoard);

const cloneBoard = (board: BoardData): BoardData => structuredClone(board);
const getFirstColumn = () => screen.getAllByTestId(/column-/i)[0];

describe("KanbanBoard", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    fetchBoardMock.mockResolvedValue(cloneBoard(initialData));
    saveBoardMock.mockImplementation(async (board) => board);
  });

  it("loads and renders board columns from the backend", async () => {
    render(<KanbanBoard />);

    await waitFor(() => {
      expect(screen.getAllByTestId(/column-/i)).toHaveLength(5);
    });

    expect(fetchBoardMock).toHaveBeenCalledTimes(1);
  });

  it("shows load error and allows retry", async () => {
    fetchBoardMock
      .mockRejectedValueOnce(new Error("network"))
      .mockResolvedValueOnce(cloneBoard(initialData));

    render(<KanbanBoard />);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Unable to load board. Please try again.");
    });

    await userEvent.click(screen.getByRole("button", { name: /retry/i }));

    await waitFor(() => {
      expect(screen.getAllByTestId(/column-/i)).toHaveLength(5);
    });

    expect(fetchBoardMock).toHaveBeenCalledTimes(2);
  });

  it("persists column rename on blur", async () => {
    render(<KanbanBoard />);

    await waitFor(() => {
      expect(screen.getAllByTestId(/column-/i)).toHaveLength(5);
    });

    const column = getFirstColumn();
    const input = within(column).getByLabelText("Column title");

    await userEvent.clear(input);
    await userEvent.type(input, "New Name");
    expect(saveBoardMock).not.toHaveBeenCalled();

    await userEvent.tab();

    await waitFor(() => {
      expect(saveBoardMock).toHaveBeenCalledTimes(1);
    });

    const savedBoard = saveBoardMock.mock.calls[0][0];
    expect(savedBoard.columns[0].title).toBe("New Name");
  });

  it("adds and removes a card while persisting board updates", async () => {
    render(<KanbanBoard />);

    await waitFor(() => {
      expect(screen.getAllByTestId(/column-/i)).toHaveLength(5);
    });

    const column = getFirstColumn();
    const addButton = within(column).getByRole("button", {
      name: /add a card/i,
    });

    await userEvent.click(addButton);
    await userEvent.type(within(column).getByPlaceholderText(/card title/i), "New card");
    await userEvent.type(within(column).getByPlaceholderText(/details/i), "Notes");
    await userEvent.click(within(column).getByRole("button", { name: /add card/i }));

    await waitFor(() => {
      expect(within(column).getByText("New card")).toBeInTheDocument();
      expect(saveBoardMock).toHaveBeenCalled();
    });

    const deleteButton = within(column).getByRole("button", {
      name: /delete new card/i,
    });
    await userEvent.click(deleteButton);

    await waitFor(() => {
      expect(within(column).queryByText("New card")).not.toBeInTheDocument();
      expect(saveBoardMock.mock.calls.length).toBeGreaterThanOrEqual(2);
    });
  });

  it("shows save errors and supports retry", async () => {
    saveBoardMock.mockRejectedValueOnce(new Error("save failed"));

    render(<KanbanBoard />);

    await waitFor(() => {
      expect(screen.getAllByTestId(/column-/i)).toHaveLength(5);
    });

    const column = getFirstColumn();
    await userEvent.click(within(column).getByRole("button", { name: /add a card/i }));
    await userEvent.type(within(column).getByPlaceholderText(/card title/i), "Unsaved card");
    await userEvent.click(within(column).getByRole("button", { name: /add card/i }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(
        "Could not save board changes. Please retry."
      );
    });

    await userEvent.click(screen.getByRole("button", { name: /retry save/i }));

    await waitFor(() => {
      expect(saveBoardMock.mock.calls.length).toBeGreaterThanOrEqual(2);
    });
  });
});
