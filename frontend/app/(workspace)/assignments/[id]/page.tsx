import { requireUser } from "@/lib/server-auth";
import { AssignmentDetail } from "@/components/learning/assignment-detail";
export default async function AssignmentPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  await requireUser(true);
  return <AssignmentDetail id={(await params).id} />;
}
