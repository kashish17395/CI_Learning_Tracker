import { requireUser } from "@/lib/server-auth";
import { CourseList } from "@/components/courses/course-list";
export default async function CoursesPage() {
  await requireUser(true);
  return <CourseList />;
}
