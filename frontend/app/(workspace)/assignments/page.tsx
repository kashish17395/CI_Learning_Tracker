import { requireUser } from "@/lib/server-auth";
import { AssignmentList } from "@/components/learning/assignment-list";
export default async function AssignmentsPage({
  searchParams,
}: {
  searchParams: Promise<{
    create?: string;
    employee?: string;
    status?: string;
  }>;
}) {
  await requireUser(true);
  const p = await searchParams;
  return (
    <AssignmentList
      create={p.create === "1"}
      employee={p.employee}
      initialStatus={p.status}
    />
  );
}
