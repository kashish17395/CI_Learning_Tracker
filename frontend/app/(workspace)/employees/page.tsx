import { requireUser } from "@/lib/server-auth";
import { EmployeeList } from "@/components/employees/employee-list";
export default async function EmployeesPage() {
  await requireUser(true);
  return <EmployeeList />;
}
