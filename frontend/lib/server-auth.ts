import "server-only";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import type { User } from "@/types";

export async function requireUser(manager = false): Promise<User> {
  const jar = await cookies();
  const backend = process.env.BACKEND_URL || "http://127.0.0.1:8000";
  let response: Response;
  try {
    response = await fetch(backend + "/api/v1/auth/me", {
      headers: { cookie: jar.toString() },
      cache: "no-store",
    });
  } catch {
    throw new Error(
      "The learning service is unavailable. Check the backend connection.",
    );
  }
  if (!response.ok) {
    if (response.status === 401 && jar.has("lt_refresh")) redirect("/session");
    if (response.status === 401) redirect("/login");
    throw new Error("Unable to validate your session");
  }
  const user: User = await response.json();
  if (manager && user.role !== "MANAGER") redirect("/my-learning");
  return user;
}
