import { requireUser } from "@/lib/server-auth";
import { EmployeeDetail } from "@/components/employees/employee-detail";
export default async function EmployeePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  await requireUser(true);
  return <EmployeeDetail id={(await params).id} />;
}
