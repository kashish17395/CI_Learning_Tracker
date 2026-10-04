"use client";
import Link from "next/link";
import { useState } from "react";
import { Plus, Pencil, UserRound } from "lucide-react";
import { useResource } from "@/hooks/use-resource";
import { patch, post, query } from "@/services/api";
import {
  Confirm,
  Dialog,
  Empty,
  ErrorState,
  Field,
  Loading,
  PageHeading,
  Pagination,
  SearchInput,
  useToast,
} from "@/components/ui";
import type { Employee, Page } from "@/types";

export function EmployeeList() {
  const [search, setSearch] = useState(""),
    [department, setDepartment] = useState(""),
    [active, setActive] = useState(""),
    [page, setPage] = useState(1);
  const [edit, setEdit] = useState<Employee | null | undefined>(undefined),
    [confirm, setConfirm] = useState<Employee | null>(null);
  const toast = useToast();
  const resource = useResource<Page<Employee>>(
    "/employees" + query({ search, department, active, page }),
  );
  return (
    <>
      <PageHeading
        eyebrow="PEOPLE & DEVELOPMENT"
        title="Employees"
        description="Maintain your team and their learning history."
        action={
          <button className="btn" onClick={() => setEdit(null)}>
            <Plus size={17} />
            Add employee
          </button>
        }
      />
      <section className="panel">
        <div className="filter-bar">
          <SearchInput
            value={search}
            onChange={(v) => {
              setSearch(v);
              setPage(1);
            }}
            placeholder="Search name, code or department…"
          />
          <input
            aria-label="Filter department"
            placeholder="All departments"
            value={department}
            onChange={(e) => {
              setDepartment(e.target.value);
              setPage(1);
            }}
          />
          <select
            aria-label="Account status"
            value={active}
            onChange={(e) => {
              setActive(e.target.value);
              setPage(1);
            }}
          >
            <option value="">All accounts</option>
            <option value="true">Active</option>
            <option value="false">Inactive</option>
          </select>
        </div>
        {resource.error ? (
          <ErrorState message={resource.error} retry={resource.reload} />
        ) : resource.loading ? (
          <Loading />
        ) : !resource.data?.items.length ? (
          <Empty
            title="Create your first employee"
            detail="Employee accounts give your team access to their assigned learning."
          />
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Employee</th>
                  <th>Department</th>
                  <th>Designation / team</th>
                  <th>Account</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {resource.data.items.map((e) => (
                  <tr key={e.id}>
                    <td>
                      <Link className="person-cell" href={"/employees/" + e.id}>
                        <span className="avatar">
                          {e.name
                            .split(" ")
                            .map((w) => w[0])
                            .slice(0, 2)
                            .join("")}
                        </span>
                        <span>
                          <strong className="cell-title">{e.name}</strong>
                          <span className="cell-subtitle">
                            {e.employee_code} · {e.email}
                          </span>
                        </span>
                      </Link>
                    </td>
                    <td>{e.department || "—"}</td>
                    <td>
                      {e.designation || "—"}
                      <span className="cell-subtitle">{e.team_name}</span>
                    </td>
                    <td>
                      <span
                        className={
                          "badge " +
                          (e.is_active
                            ? "status-completed"
                            : "status-cancelled")
                        }
                      >
                        {e.is_active ? "Active" : "Inactive"}
                      </span>
                    </td>
                    <td>
                      <div className="badge-group">
                        <button
                          className="icon-btn"
                          aria-label={"Edit " + e.name}
                          onClick={() => setEdit(e)}
                        >
                          <Pencil size={15} />
                        </button>
                        <button
                          className="btn compact secondary"
                          onClick={() => setConfirm(e)}
                        >
                          {e.is_active ? "Deactivate" : "Activate"}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {resource.data && (
          <Pagination
            page={page}
            total={resource.data.total}
            onChange={setPage}
          />
        )}
      </section>
      {edit !== undefined && (
        <EmployeeForm
          employee={edit}
          onClose={() => setEdit(undefined)}
          onSaved={() => {
            setEdit(undefined);
            resource.reload();
            toast("Employee saved");
          }}
        />
      )}
      {confirm && (
        <Confirm
          title={
            confirm.is_active ? "Deactivate employee?" : "Activate employee?"
          }
          detail={
            confirm.is_active
              ? `${confirm.name} will lose account access. Learning history will remain available.`
              : `Restore account access for ${confirm.name}.`
          }
          onClose={() => setConfirm(null)}
          onConfirm={async () => {
            await patch("/employees/" + confirm.id, {
              is_active: !confirm.is_active,
            });
            resource.reload();
            toast("Account status updated");
          }}
        />
      )}
    </>
  );
}
function EmployeeForm({
  employee,
  onClose,
  onSaved,
}: {
  employee: Employee | null;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const teams = useResource<Page<{ id: string; name: string }>>(
    "/teams?page_size=100",
  );
  return (
    <Dialog
      title={employee ? "Edit employee" : "Add employee"}
      onClose={onClose}
    >
      <form
        onSubmit={async (e) => {
          e.preventDefault();
          setError("");
          setBusy(true);
          const f = new FormData(e.currentTarget);
          const values = {
            name: f.get("name"),
            employee_code: f.get("employee_code"),
            email: f.get("email"),
            department: f.get("department"),
            designation: f.get("designation"),
            team_id: f.get("team_id") || null,
            ...(!employee ? { password: f.get("password") } : {}),
          };
          try {
            if (employee) await patch("/employees/" + employee.id, values);
            else await post("/employees", values);
            onSaved();
          } catch (err) {
            setError((err as Error).message);
          } finally {
            setBusy(false);
          }
        }}
      >
        <div className="form-grid">
          <Field label="Full name">
            <input
              name="name"
              defaultValue={employee?.name}
              required
              maxLength={150}
              autoComplete="name"
            />
          </Field>
          <Field label="Employee code">
            <input
              name="employee_code"
              defaultValue={employee?.employee_code}
              required
              maxLength={64}
            />
          </Field>
        </div>
        <Field label="Work email">
          <input
            name="email"
            type="email"
            defaultValue={employee?.email}
            required
            maxLength={254}
          />
        </Field>
        {!employee && (
          <Field
            label="Initial password"
            hint="At least 12 characters. Share through a secure channel."
          >
            <input
              name="password"
              type="password"
              required
              minLength={12}
              maxLength={256}
              autoComplete="new-password"
            />
          </Field>
        )}
        <div className="form-grid">
          <Field label="Department">
            <input
              name="department"
              defaultValue={employee?.department}
              maxLength={150}
            />
          </Field>
          <Field label="Designation">
            <input
              name="designation"
              defaultValue={employee?.designation}
              maxLength={150}
            />
          </Field>
        </div>
        <Field label="Team">
          <select name="team_id" defaultValue={employee?.team_id || ""}>
            <option value="">No team</option>
            {teams.data?.items.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
        </Field>
        {error && <ErrorState message={error} />}
        <div className="form-actions">
          <button
            type="button"
            className="btn secondary"
            disabled={busy}
            onClick={onClose}
          >
            Cancel
          </button>
          <button className="btn" disabled={busy}>
            {busy ? "Saving…" : "Save employee"}
          </button>
        </div>
      </form>
    </Dialog>
  );
}
