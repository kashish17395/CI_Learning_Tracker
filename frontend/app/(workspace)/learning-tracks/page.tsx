import { requireUser } from "@/lib/server-auth";
import { TrackList } from "@/components/learning/track-list";
export default async function LearningTracksPage() {
  await requireUser(true);
  return <TrackList />;
}
