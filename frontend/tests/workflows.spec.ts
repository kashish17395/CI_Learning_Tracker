import { test, expect } from "@playwright/test";

test("manager assigns a track and employee completes learning with evidence", async ({
  page,
}) => {
  const password = process.env.TEST_BOOTSTRAP_PASSWORD!;
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/employees");
  await expect(page).toHaveURL(/\/login$/);
  await page.getByLabel("Work email").fill("manager@example.com");
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Team learning dashboard" }),
  ).toBeVisible();
  await page.getByRole("link", { name: "Employees", exact: true }).click();
  await page.getByRole("button", { name: "Add employee" }).click();
  const employee = page.getByRole("dialog");
  await employee.getByLabel("Full name").fill("Asha Rao");
  await employee.getByLabel("Employee code").fill("ENG-101");
  await employee.getByLabel("Work email").fill("asha@example.com");
  await employee.getByLabel("Initial password").fill(password);
  await employee.getByLabel("Department").fill("Engineering");
  await employee.getByLabel("Designation").fill("Software Engineer");
  await employee.getByRole("button", { name: "Save employee" }).click();
  await expect(
    page.getByRole("table").getByText("Asha Rao", { exact: true }),
  ).toBeVisible();
  await page.getByRole("link", { name: "Courses", exact: true }).click();
  await page
    .getByRole("button", { name: "Create course", exact: true })
    .click();
  const course = page.getByRole("dialog");
  await course.getByLabel("Course code").fill("GIT-101");
  await course.getByLabel("Course name").fill("Git Essentials");
  await course.getByLabel("Category").fill("Engineering");
  await course
    .getByLabel("Description")
    .fill("Learn branches, commits and collaborative code review.");
  await course.getByLabel("Estimated duration (minutes)").fill("90");
  await course.getByRole("button", { name: "Save course" }).click();
  await expect(
    page.getByRole("heading", { name: "Git Essentials" }),
  ).toBeVisible();
  await page
    .getByRole("link", { name: "Learning tracks", exact: true })
    .click();
  await page.getByRole("button", { name: "Create track" }).click();
  const track = page.getByRole("dialog");
  await track.getByLabel("Track name").fill("Engineering Foundations");
  await track
    .getByLabel("Add a course")
    .selectOption({ label: "Git Essentials · GIT-101" });
  await track.getByRole("button", { name: "Save track" }).click();
  await expect(
    page.getByRole("heading", { name: "Engineering Foundations" }),
  ).toBeVisible();
  await page.getByRole("link", { name: "Assignments", exact: true }).click();
  await page
    .getByRole("button", { name: "Assign learning", exact: true })
    .click();
  const assignment = page.getByRole("dialog");
  await assignment
    .getByRole("combobox", { name: "Employee", exact: true })
    .selectOption({ label: "Asha Rao · ENG-101" });
  await assignment
    .getByRole("combobox", { name: "Assignment type", exact: true })
    .selectOption("track");
  await assignment
    .getByRole("combobox", { name: "Learning track", exact: true })
    .selectOption({ label: "Engineering Foundations" });
  await assignment.getByLabel("Certificate required for completion").check();
  await assignment
    .getByRole("button", { name: "Assign learning", exact: true })
    .click();
  await expect(
    page.getByRole("link", { name: "Engineering Foundations", exact: true }),
  ).toBeVisible();
  await page.getByRole("link", { name: "Dashboard", exact: true }).click();
  await expect(
    page.getByRole("table").getByText("Asha Rao", { exact: true }),
  ).toBeVisible();
  await page.screenshot({
    path: "test-results/manager-dashboard.png",
    fullPage: true,
  });
  await page.getByRole("button", { name: "Sign out" }).click();
  await expect(page).toHaveURL(/\/login$/);
  await page.getByLabel("Work email").fill("asha@example.com");
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Welcome, Asha" }),
  ).toBeVisible();
  await page
    .getByRole("navigation")
    .getByRole("link", { name: "My learning", exact: true })
    .click();
  await page.getByRole("link", { name: "Git Essentials", exact: true }).click();
  await page
    .getByRole("combobox", { name: "Status", exact: true })
    .selectOption("IN_PROGRESS");
  await page.getByRole("button", { name: "Save progress" }).click();
  await expect(
    page.getByRole("status").filter({ hasText: "Learning progress saved" }),
  ).toBeVisible();
  const png = Buffer.from(
    "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAIAAAACUFjqAAAAFklEQVR4nGP8//8/A27AhEeOYeRKAwCl4wMRx3ocVQAAAABJRU5ErkJggg==",
    "base64",
  );
  await page.getByLabel("Upload certificate").setInputFiles({
    name: "certificate.png",
    mimeType: "image/png",
    buffer: png,
  });
  await page.getByRole("button", { name: "Upload evidence" }).click();
  await expect(
    page.getByRole("link", { name: /certificate.png/ }),
  ).toBeVisible();
  await page
    .getByRole("combobox", { name: "Status", exact: true })
    .selectOption("COMPLETED");
  const today = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Calcutta",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date());
  await page.getByLabel("Completion date").fill(today);
  await page.getByRole("button", { name: "Save progress" }).click();
  await expect(
    page.getByText(
      "This course is completed. Your manager can make corrections.",
    ),
  ).toBeVisible();
  await page.getByRole("link", { name: "Certificates", exact: true }).click();
  await expect(
    page.getByText("certificate.png", { exact: true }),
  ).toBeVisible();
  await page.context().clearCookies({ name: "lt_access" });
  const downloaded = page.waitForEvent("download");
  await page.getByRole("link", { name: "Download", exact: true }).click();
  expect((await downloaded).suggestedFilename()).toBe("certificate.png");
  expect(
    (await page.context().cookies()).some(
      (cookie) => cookie.name === "lt_access",
    ),
  ).toBe(true);
  await page.goto("/employees");
  await expect(page).toHaveURL(/\/my-learning$/);
  await page.setViewportSize({ width: 375, height: 812 });
  await page.getByRole("button", { name: "Open navigation" }).click();
  await expect(page.getByRole("navigation")).toBeVisible();
  await page
    .getByRole("navigation")
    .getByRole("link", { name: "Dashboard", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Welcome, Asha" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Course progress", exact: true }),
  ).toBeVisible();
  await expect(page.getByText("100%", { exact: true }).first()).toBeVisible();
  await page.screenshot({
    path: "test-results/employee-mobile.png",
    fullPage: true,
  });
  expect(errors).toEqual([]);
});
