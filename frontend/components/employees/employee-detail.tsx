"use client";
import Link from "next/link";
import { useState } from "react";
import { ChevronLeft, Plus } from "lucide-react";
import { useResource } from "@/hooks/use-resource";
import { query } from "@/services/api";
import {
  dateLabel,
  Empty,
  ErrorState,
  Loading,
  PageHeading,
  Pagination,
  StatusBadge,
} from "@/components/ui";
import type { Attempt, Employee, Page } from "@/types";
export function EmployeeDetail({ id }: { id: string }) {
  const employee = useResource<Employee>("/employees/" + id);
  const [page, setPage] = useState(1);
  const history = useResource<Page<Attempt>>(
    "/employees/" + id + "/learning" + query({ page }),
  );
  if (employee.error)
    return <ErrorState message={employee.error} retry={employee.reload} />;
  if (!employee.data) return <Loading />;
  const e = employee.data;
  return (
    <>
      <Link className="back-link" href="/employees">
        <ChevronLeft size={16} />
        Employees
      </Link>
      <PageHeading
        eyebrow={e.employee_code}
        title={e.name}
        description={`${e.designation || "Employee"} · ${e.department || "No department"}`}
        action={
          <Link className="btn" href={"/assignments?create=1&employee=" + id}>
            <Plus size={17} />
            Assign learning
          </Link>
        }
      />
      <div className="section-stack">
        <section className="panel">
          <div className="panel-heading">
            <h2>Employee profile</h2>
            <span
              className={
                "badge " +
                (e.is_active ? "status-completed" : "status-cancelled")
              }
            >
              {e.is_active ? "Active" : "Inactive"}
            </span>
          </div>
          <div className="panel-body">
            <dl className="detail-list">
              <div>
                <dt>Email</dt>
                <dd>{e.email}</dd>
              </div>
              <div>
                <dt>Team</dt>
                <dd>{e.team_name || "Unassigned"}</dd>
              </div>
            </dl>
          </div>
        </section>
        <section className="panel">
          <div className="panel-heading">
            <div>
              <h2>Learning history</h2>
              <p>Includes completed and retired attempts</p>
            </div>
          </div>
          {history.error ? (
            <ErrorState message={history.error} retry={history.reload} />
          ) : history.loading ? (
            <Loading />
          ) : history.data?.items.length ? (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Course</th>
                    <th>Status</th>
                    <th>Target date</th>
                    <th>Completion date</th>
                    <th>Evidence</th>
                  </tr>
                </thead>
                <tbody>
                  {history.data.items.map((a) => (
                    <tr key={a.id}>
                      <td>
                        <Link
                          className="text-btn"
                          href={"/my-learning/" + a.id}
                        >
                          {a.course.name}
                        </Link>
                        <span className="cell-subtitle">
                          {a.course.course_code}
                          {a.retired_at ? " · Retired" : ""}
                        </span>
                      </td>
                      <td>
                        <StatusBadge status={a.status} overdue={a.overdue} />
                      </td>
                      <td>{dateLabel(a.target_date)}</td>
                      <td>{dateLabel(a.completion_date)}</td>
                      <td>{a.certificates.length} files</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <Empty
              title="No learning assigned"
              detail="Assign a course or learning track to get started."
            />
          )}
          {history.data && (
            <Pagination
              page={page}
              total={history.data.total}
              onChange={setPage}
            />
          )}
        </section>
      </div>
    </>
  );
}
