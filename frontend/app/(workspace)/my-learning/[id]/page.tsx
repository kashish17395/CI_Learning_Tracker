import { requireUser } from "@/lib/server-auth";
import { LearningDetail } from "@/components/learning/learning-detail";
export default async function LearningPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const user = await requireUser();
  return <LearningDetail id={(await params).id} user={user} />;
}
