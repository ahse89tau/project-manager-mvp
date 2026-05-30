import { expect, test, type Page } from "@playwright/test";

type BoardCard = {
  id: string;
  title: string;
  details: string;
};

type BoardColumn = {
  id: string;
  title: string;
  cardIds: string[];
};

type BoardData = {
  columns: BoardColumn[];
  cards: Record<string, BoardCard>;
};

const seedBoard = (): BoardData => ({
  columns: [
    { id: "col-backlog", title: "Backlog", cardIds: ["card-1", "card-2"] },
    { id: "col-discovery", title: "Discovery", cardIds: ["card-3"] },
    { id: "col-progress", title: "In Progress", cardIds: ["card-4", "card-5"] },
    { id: "col-review", title: "Review", cardIds: ["card-6"] },
    { id: "col-done", title: "Done", cardIds: ["card-7", "card-8"] },
  ],
  cards: {
    "card-1": {
      id: "card-1",
      title: "Align roadmap themes",
      details: "Draft quarterly themes with impact statements and metrics.",
    },
    "card-2": {
      id: "card-2",
      title: "Gather customer signals",
      details: "Review support tags, sales notes, and churn feedback.",
    },
    "card-3": {
      id: "card-3",
      title: "Prototype analytics view",
      details: "Sketch initial dashboard layout and key drill-downs.",
    },
    "card-4": {
      id: "card-4",
      title: "Refine status language",
      details: "Standardize column labels and tone across the board.",
    },
    "card-5": {
      id: "card-5",
      title: "Design card layout",
      details: "Add hierarchy and spacing for scanning dense lists.",
    },
    "card-6": {
      id: "card-6",
      title: "QA micro-interactions",
      details: "Verify hover, focus, and loading states.",
    },
    "card-7": {
      id: "card-7",
      title: "Ship marketing page",
      details: "Final copy approved and asset pack delivered.",
    },
    "card-8": {
      id: "card-8",
      title: "Close onboarding sprint",
      details: "Document release notes and share internally.",
    },
  },
});

const mockBackend = async (page: Page) => {
  let authenticated = false;
  let board = seedBoard();

  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());

    if (url.pathname === "/api/auth/session" && request.method() === "GET") {
      await route.fulfill({ json: { authenticated } });
      return;
    }

    if (url.pathname === "/api/auth/login" && request.method() === "POST") {
      const payload = request.postDataJSON() as { username?: string; password?: string };
      const isValid = payload.username === "user" && payload.password === "password";
      if (!isValid) {
        await route.fulfill({ status: 401, json: { detail: "Invalid username or password" } });
        return;
      }

      authenticated = true;
      await route.fulfill({ json: { authenticated: true } });
      return;
    }

    if (url.pathname === "/api/auth/logout" && request.method() === "POST") {
      authenticated = false;
      await route.fulfill({ json: { authenticated: false } });
      return;
    }

    if (!authenticated) {
      await route.fulfill({ status: 401, json: { detail: "Authentication required" } });
      return;
    }

    if (url.pathname === "/api/board" && request.method() === "GET") {
      await route.fulfill({ json: board });
      return;
    }

    if (url.pathname === "/api/board" && request.method() === "PUT") {
      const payload = request.postDataJSON() as BoardData;
      board = payload;
      await route.fulfill({ json: { saved: true, board } });
      return;
    }

    await route.fallback();
  });
};

const login = async (page: Page) => {
  await page.goto("/");
  await expect(page.getByRole("button", { name: /sign in/i })).toBeVisible();
  await page.getByRole("button", { name: /sign in/i }).click();
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(5);
};

test.beforeEach(async ({ page }) => {
  await mockBackend(page);
});

test("loads the kanban board", async ({ page }) => {
  await login(page);
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(5);
});

test("persists an added card after reload", async ({ page }) => {
  await login(page);

  const firstColumn = page.locator('[data-testid^="column-"]').first();
  await firstColumn.getByRole("button", { name: /add a card/i }).click();
  await firstColumn.getByPlaceholder("Card title").fill("Playwright card");
  await firstColumn.getByPlaceholder("Details").fill("Added via e2e.");
  await firstColumn.getByRole("button", { name: /add card/i }).click();
  await expect(firstColumn.getByText("Playwright card")).toBeVisible();

  await page.reload();
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(5);
  await expect(firstColumn.getByText("Playwright card")).toBeVisible();
});

test("persists a renamed column after reload", async ({ page }) => {
  await login(page);

  const firstColumn = page.locator('[data-testid^="column-"]').first();
  const titleInput = firstColumn.getByLabel("Column title");

  await titleInput.fill("Ideas");
  await titleInput.blur();

  await expect(firstColumn.getByLabel("Column title")).toHaveValue("Ideas");

  await page.reload();
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(5);
  await expect(firstColumn.getByLabel("Column title")).toHaveValue("Ideas");
});
