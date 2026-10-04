import { requireUser } from "@/lib/server-auth";
import { DashboardView } from "@/components/dashboard/dashboard-view";
export default async function DashboardPage() {
  const user = await requireUser();
  return <DashboardView user={user} />;
}
