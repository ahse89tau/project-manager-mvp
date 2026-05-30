"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  closestCorners,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import { KanbanColumn } from "@/components/KanbanColumn";
import { KanbanCardPreview } from "@/components/KanbanCardPreview";
import { AISidebar } from "@/components/AISidebar";
import { fetchBoard, saveBoard } from "@/lib/api";
import { createId, moveCard, type BoardData } from "@/lib/kanban";

const loadErrorMessage = "Unable to load board. Please try again.";
const saveErrorMessage = "Could not save board changes. Please retry.";

export const KanbanBoard = () => {
  const [board, setBoard] = useState<BoardData | null>(null);
  const [activeCardId, setActiveCardId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState("");
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  const pendingSaveCount = useRef(0);
  const latestBoardRef = useRef<BoardData | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 6 },
    })
  );

  const loadBoard = useCallback(async (silent = false) => {
    if (!silent) setIsLoading(true);
    setLoadError("");

    try {
      const nextBoard = await fetchBoard();
      setBoard(nextBoard);
      latestBoardRef.current = nextBoard;
    } catch {
      setLoadError(loadErrorMessage);
    } finally {
      if (!silent) setIsLoading(false);
    }
  }, []);

  const persistBoard = useCallback(async (nextBoard: BoardData) => {
    pendingSaveCount.current += 1;
    setIsSaving(true);
    setSaveError("");

    try {
      await saveBoard(nextBoard);
    } catch {
      setSaveError(saveErrorMessage);
    } finally {
      pendingSaveCount.current -= 1;
      if (pendingSaveCount.current <= 0) {
        pendingSaveCount.current = 0;
        setIsSaving(false);
      }
    }
  }, []);

  useEffect(() => {
    void loadBoard();
  }, [loadBoard]);

  const applyBoardUpdate = useCallback(
    (updater: (prev: BoardData) => BoardData, persist = true) => {
      setBoard((prev) => {
        if (!prev) {
          return prev;
        }

        const nextBoard = updater(prev);
        latestBoardRef.current = nextBoard;

        if (persist) {
          void persistBoard(nextBoard);
        }

        return nextBoard;
      });
    },
    [persistBoard]
  );

  const cardsById = useMemo(() => board?.cards ?? {}, [board?.cards]);

  const handleDragStart = (event: DragStartEvent) => {
    setActiveCardId(event.active.id as string);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveCardId(null);

    if (!board || !over || active.id === over.id) {
      return;
    }

    applyBoardUpdate((prev) => ({
      ...prev,
      columns: moveCard(prev.columns, active.id as string, over.id as string),
    }));
  };

  const handleRenameColumn = (columnId: string, title: string) => {
    applyBoardUpdate(
      (prev) => ({
        ...prev,
        columns: prev.columns.map((column) =>
          column.id === columnId ? { ...column, title } : column
        ),
      }),
      false
    );
  };

  const handleRenameColumnCommit = (columnId: string) => {
    applyBoardUpdate((prev) => ({
      ...prev,
      columns: prev.columns.map((column) => {
        if (column.id !== columnId) {
          return column;
        }

        const nextTitle = column.title.trim();
        return {
          ...column,
          title: nextTitle || "Untitled",
        };
      }),
    }));
  };

  const handleAddCard = (columnId: string, title: string, details: string) => {
    const id = createId("card");
    applyBoardUpdate((prev) => ({
      ...prev,
      cards: {
        ...prev.cards,
        [id]: { id, title, details: details || "No details yet." },
      },
      columns: prev.columns.map((column) =>
        column.id === columnId
          ? { ...column, cardIds: [...column.cardIds, id] }
          : column
      ),
    }));
  };

  const handleDeleteCard = (columnId: string, cardId: string) => {
    applyBoardUpdate((prev) => ({
      ...prev,
      cards: Object.fromEntries(
        Object.entries(prev.cards).filter(([id]) => id !== cardId)
      ),
      columns: prev.columns.map((column) =>
        column.id === columnId
          ? {
              ...column,
              cardIds: column.cardIds.filter((id) => id !== cardId),
            }
          : column
      ),
    }));
  };

  const handleRetrySave = () => {
    if (latestBoardRef.current) {
      void persistBoard(latestBoardRef.current);
    }
  };

  if (isLoading) {
    return (
      <main className="grid min-h-screen place-items-center px-6 py-8">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
          Loading board...
        </p>
      </main>
    );
  }

  if (!board) {
    return (
      <main className="grid min-h-screen place-items-center px-6 py-8">
        <section className="w-full max-w-lg rounded-3xl border border-[var(--stroke)] bg-white p-8 shadow-[var(--shadow)]">
          <h1 className="font-display text-3xl text-[var(--navy-dark)]">Kanban Studio</h1>
          <p className="mt-3 text-sm text-[var(--gray-text)]" role="alert">
            {loadError || loadErrorMessage}
          </p>
          <button
            type="button"
            onClick={() => void loadBoard()}
            className="mt-6 rounded-full bg-[var(--secondary-purple)] px-4 py-2 text-sm font-semibold text-white transition hover:opacity-95"
          >
            Retry
          </button>
        </section>
      </main>
    );
  }

  const activeCard = activeCardId ? cardsById[activeCardId] : null;

  return (
    <div className="relative">
      <div className="pointer-events-none absolute left-0 top-0 h-[420px] w-[420px] -translate-x-1/3 -translate-y-1/3 rounded-full bg-[radial-gradient(circle,_rgba(32,157,215,0.25)_0%,_rgba(32,157,215,0.05)_55%,_transparent_70%)]" />
      <div className="pointer-events-none absolute bottom-0 right-0 h-[520px] w-[520px] translate-x-1/4 translate-y-1/4 rounded-full bg-[radial-gradient(circle,_rgba(117,57,145,0.18)_0%,_rgba(117,57,145,0.05)_55%,_transparent_75%)]" />

      <main className="relative mx-auto flex min-h-screen max-w-[1500px] flex-col gap-10 px-6 pb-16 pt-12">
        <header className="flex flex-col gap-6 rounded-[32px] border border-[var(--stroke)] bg-white/80 p-8 shadow-[var(--shadow)] backdrop-blur">
          <div className="flex flex-wrap items-start justify-between gap-6">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[var(--gray-text)]">
                Single Board Kanban
              </p>
              <h1 className="mt-3 font-display text-4xl font-semibold text-[var(--navy-dark)]">
                Kanban Studio
              </h1>
              <p className="mt-3 max-w-xl text-sm leading-6 text-[var(--gray-text)]">
                Keep momentum visible. Rename columns, drag cards between stages,
                and capture quick notes without getting buried in settings.
              </p>
            </div>
            <div className="flex items-start gap-3">
              <button
                type="button"
                onClick={() => setIsSidebarOpen(true)}
                className="flex items-center gap-2 rounded-full border border-[var(--secondary-purple)] bg-white px-4 py-2.5 text-xs font-semibold uppercase tracking-[0.2em] text-[var(--secondary-purple)] transition hover:bg-[var(--secondary-purple)] hover:text-white"
              >
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                  <path
                    d="M7 1C3.69 1 1 3.46 1 6.5c0 1.25.45 2.4 1.2 3.3L1.5 12l2.4-.9A6.2 6.2 0 007 12c3.31 0 6-2.46 6-5.5S10.31 1 7 1z"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinejoin="round"
                    fill="none"
                  />
                </svg>
                Ask AI
              </button>
              <div className="rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-5 py-4">
              <p className="text-xs font-semibold uppercase tracking-[0.25em] text-[var(--gray-text)]">
                Focus
              </p>
              <p className="mt-2 text-lg font-semibold text-[var(--primary-blue)]">
                One board. Five columns. Zero clutter.
              </p>
              {isSaving ? (
                <p className="mt-2 text-xs font-semibold uppercase tracking-[0.2em] text-[var(--primary-blue)]">
                  Saving changes...
                </p>
              ) : null}
              {saveError ? (
                <div className="mt-2">
                  <p className="text-xs font-semibold text-[var(--secondary-purple)]" role="alert">
                    {saveError}
                  </p>
                  <button
                    type="button"
                    onClick={handleRetrySave}
                    className="mt-2 rounded-full border border-[var(--secondary-purple)] px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-[var(--secondary-purple)]"
                  >
                    Retry save
                  </button>
                </div>
              ) : null}
              </div>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-4">
            {board.columns.map((column) => (
              <div
                key={column.id}
                className="flex items-center gap-2 rounded-full border border-[var(--stroke)] px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-[var(--navy-dark)]"
              >
                <span className="h-2 w-2 rounded-full bg-[var(--accent-yellow)]" />
                {column.title}
              </div>
            ))}
          </div>
        </header>

        <DndContext
          sensors={sensors}
          collisionDetection={closestCorners}
          onDragStart={handleDragStart}
          onDragEnd={handleDragEnd}
        >
          <section className="grid gap-6 lg:grid-cols-5">
            {board.columns.map((column) => (
              <KanbanColumn
                key={column.id}
                column={column}
                cards={column.cardIds.map((cardId) => board.cards[cardId])}
                onRename={handleRenameColumn}
                onRenameCommit={handleRenameColumnCommit}
                onAddCard={handleAddCard}
                onDeleteCard={handleDeleteCard}
              />
            ))}
          </section>
          <DragOverlay>
            {activeCard ? (
              <div className="w-[260px]">
                <KanbanCardPreview card={activeCard} />
              </div>
            ) : null}
          </DragOverlay>
        </DndContext>
      </main>

      <AISidebar
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        onBoardUpdated={() => void loadBoard(true)}
      />
    </div>
  );
};
