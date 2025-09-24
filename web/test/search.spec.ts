import { test, expect } from "@playwright/test";

test("search returns results and navigates", async ({ page }) => {
    await page.goto("http://localhost:3000/search");
    await page.getByPlaceholder("Search documents").fill("Incoterms");
    await page.keyboard.press("Enter");
    await page.waitForTimeout(500);
    const first = page.getByRole("link", { name: /Document #/ }).first();
    await expect(first).toBeVisible();
    await first.click();
    await expect(page.getByText("Document #")).toBeVisible();
});
