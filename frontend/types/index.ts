export type Role = "MANAGER" | "EMPLOYEE";
export type Status = "NOT_STARTED" | "ENROLLED" | "IN_PROGRESS" | "COMPLETED";
export interface User {
  id: string;
  name: string;
  email: string;
  role: Role;
  employee_id: string | null;
}
export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}
export interface Employee {
  id: string;
  employee_code: string;
  name: string;
  email: string;
  department: string;
  designation: string;
  team_id: string | null;
  team_name: string | null;
  is_active: boolean;
}
export interface Course {
  id: string;
  course_code: string;
  name: string;
  description: string;
  category: string;
  provider: string;
  estimated_duration_minutes: number | null;
  is_active: boolean;
}
export interface Track {
  id: string;
  name: string;
  description: string;
  is_active: boolean;
  courses: (Course & { sequence_order: number })[];
}
export interface Certificate {
  id: string;
  learning_attempt_id: string;
  original_filename: string;
  content_type: string;
  file_size: number;
  uploaded_at: string;
  employee_name?: string;
  course_name?: string;
}
export interface Context {
  id: string;
  target_date: string | null;
  track_id: string | null;
  track_name: string | null;
  is_mandatory: boolean;
}
export interface Attempt {
  id: string;
  employee_id: string;
  employee_name: string;
  department: string;
  course_id: string;
  course: Course;
  status: Status;
  version: number;
  started_on: string;
  target_date: string | null;
  completion_date: string | null;
  overdue: boolean;
  employee_can_update: boolean;
  employee_can_complete: boolean;
  certificate_required: boolean;
  certificates: Certificate[];
  assignments: Context[];
  created_at: string;
  retired_at: string | null;
}
export interface Assignment {
  id: string;
  employee_id: string;
  employee_name: string;
  name: string;
  course_id: string | null;
  learning_track_id: string | null;
  assigned_at: string;
  target_date: string | null;
  status: Status;
  version: number;
  overdue: boolean;
  completion_date: string | null;
  cancelled_at: string | null;
  employee_can_update: boolean;
  employee_can_complete: boolean;
  certificate_required: boolean;
  is_mandatory: boolean;
  courses: Attempt[];
}
export interface Summary {
  assigned: number;
  completed: number;
  in_progress: number;
  enrolled: number;
  pending: number;
  overdue: number;
  completion_percentage: number | null;
  total_employees?: number;
  total_assignments?: number;
}
export interface EmployeeProgress extends Summary {
  employee_id: string;
  name: string;
  department: string;
}
export interface CourseProgress extends Summary {
  course_id: string;
  name: string;
}
export interface Dashboard {
  summary: Summary;
  employees: EmployeeProgress[];
  courses: CourseProgress[];
  upcoming: Attempt[];
  overdue: Attempt[];
  capability_gaps: CourseProgress[];
  priority_development: Attempt[];
}
export interface Audit {
  id: string;
  action: string;
  entity_type: string;
  entity_id: string;
  actor_user_id: string;
  details: Record<string, unknown>;
  created_at: string;
}
