import { requireUser } from "@/lib/server-auth";
import { AuditList } from "@/components/learning/audit-list";
export default async function AuditPage() {
  await requireUser(true);
  return <AuditList />;
}
