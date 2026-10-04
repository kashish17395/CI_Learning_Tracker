import { requireUser } from "@/lib/server-auth";
import { Shell } from "@/components/layout/shell";
export default async function WorkspaceLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const user = await requireUser();
  return <Shell user={user}>{children}</Shell>;
}
