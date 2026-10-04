"use client";
import Link from "next/link";
import { useState } from "react";
import { Plus } from "lucide-react";
import { useResource } from "@/hooks/use-resource";
import { post, query } from "@/services/api";
import {
  dateLabel,
  Dialog,
  Empty,
  ErrorState,
  Field,
  Loading,
  PageHeading,
  Pagination,
  SearchInput,
  StatusBadge,
  useToast,
} from "@/components/ui";
import type { Assignment, Course, Employee, Page, Track } from "@/types";

export function AssignmentList({
  create = false,
  employee = "",
  initialStatus = "",
}: {
  create?: boolean;
  employee?: string;
  initialStatus?: string;
}) {
  const [show, setShow] = useState(create),
    [search, setSearch] = useState(""),
    [status, setStatus] = useState(initialStatus),
    [page, setPage] = useState(1),
    [targetFrom, setTargetFrom] = useState(""),
    [targetTo, setTargetTo] = useState(""),
    [cancelled, setCancelled] = useState(false),
    [employeeId, setEmployeeId] = useState(employee),
    [courseId, setCourseId] = useState(""),
    [trackId, setTrackId] = useState("");
  const toast = useToast();
  const employees = useResource<Page<Employee>>("/employees?page_size=100");
  const courses = useResource<Page<Course>>("/courses?page_size=100");
  const tracks = useResource<Page<Track>>("/learning-tracks?page_size=100");
  const r = useResource<Page<Assignment>>(
    "/assignments" +
      query({
        search,
        status,
        page,
        employee_id: employeeId,
        course_id: courseId,
        track_id: trackId,
        target_from: targetFrom,
        target_to: targetTo,
        include_cancelled: cancelled,
      }),
  );
  return (
    <>
      <PageHeading
        eyebrow="LEARNING PLANS"
        title="Assignments"
        description="Connect people with courses and structured learning paths."
        action={
          <button className="btn" onClick={() => setShow(true)}>
            <Plus size={17} />
            Assign learning
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
            placeholder="Search employee or learning…"
          />
          <select
            aria-label="Assignment status"
            value={status}
            onChange={(e) => {
              setStatus(e.target.value);
              setPage(1);
            }}
          >
            <option value="">All statuses</option>
            <option value="NOT_STARTED">Not started</option>
            <option value="ENROLLED">Enrolled</option>
            <option value="IN_PROGRESS">In progress</option>
            <option value="COMPLETED">Completed</option>
            <option value="OVERDUE">Overdue</option>
          </select>
          <select
            aria-label="Employee filter"
            value={employeeId}
            onChange={(e) => {
              setEmployeeId(e.target.value);
              setPage(1);
            }}
          >
            <option value="">All employees</option>
            {employees.data?.items.map((e) => (
              <option key={e.id} value={e.id}>
                {e.name}
              </option>
            ))}
          </select>
          <select
            aria-label="Course filter"
            value={courseId}
            onChange={(e) => {
              setCourseId(e.target.value);
              setPage(1);
            }}
          >
            <option value="">All courses</option>
            {courses.data?.items.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
          <select
            aria-label="Track filter"
            value={trackId}
            onChange={(e) => {
              setTrackId(e.target.value);
              setPage(1);
            }}
          >
            <option value="">All tracks</option>
            {tracks.data?.items.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
          <label className="date-filter">
            From
            <input
              aria-label="Target date from"
              type="date"
              value={targetFrom}
              onChange={(e) => {
                setTargetFrom(e.target.value);
                setPage(1);
              }}
            />
          </label>
          <label className="date-filter">
            To
            <input
              aria-label="Target date to"
              type="date"
              value={targetTo}
              onChange={(e) => {
                setTargetTo(e.target.value);
                setPage(1);
              }}
            />
          </label>
          <label className="checkbox-row" style={{ margin: 0 }}>
            <input
              type="checkbox"
              checked={cancelled}
              onChange={(e) => setCancelled(e.target.checked)}
            />
            Include cancelled
          </label>
        </div>
        {r.error ? (
          <ErrorState message={r.error} retry={r.reload} />
        ) : r.loading ? (
          <Loading />
        ) : !r.data?.items.length ? (
          <Empty
            title="No matching assignments"
            detail="Assign a course or track to start a learning plan."
          />
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Employee</th>
                  <th>Assigned learning</th>
                  <th>Assigned date</th>
                  <th>Target date</th>
                  <th>Status</th>
                  <th>Completed</th>
                </tr>
              </thead>
              <tbody>
                {r.data.items.map((a) => (
                  <tr key={a.id}>
                    <td>
                      <Link
                        href={"/employees/" + a.employee_id}
                        className="cell-title"
                      >
                        {a.employee_name}
                      </Link>
                    </td>
                    <td>
                      <Link href={"/assignments/" + a.id} className="text-btn">
                        {a.name}
                      </Link>
                      <span className="cell-subtitle">
                        {a.learning_track_id
                          ? "Learning track"
                          : "Individual course"}{" "}
                        · {a.courses.length} courses
                        {a.is_mandatory ? " · Mandatory" : ""}
                      </span>
                    </td>
                    <td>{dateLabel(a.assigned_at)}</td>
                    <td>{dateLabel(a.target_date)}</td>
                    <td>
                      <StatusBadge
                        status={a.cancelled_at ? "CANCELLED" : a.status}
                        overdue={a.overdue}
                      />
                    </td>
                    <td>{dateLabel(a.completion_date)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {r.data && (
          <Pagination page={page} total={r.data.total} onChange={setPage} />
        )}
      </section>
      {show && (
        <AssignmentForm
          employee={employee}
          onClose={() => setShow(false)}
          onSaved={() => {
            setShow(false);
            r.reload();
            toast("Learning assigned");
          }}
        />
      )}
    </>
  );
}
function AssignmentForm({
  employee,
  onClose,
  onSaved,
}: {
  employee: string;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [kind, setKind] = useState("course"),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [employeeSearch, setEmployeeSearch] = useState(""),
    [learningSearch, setLearningSearch] = useState("");
  const employees = useResource<Page<Employee>>(
    "/employees" +
      query({ active: true, page_size: 100, search: employeeSearch }),
  );
  const courses = useResource<Page<Course>>(
    "/courses" +
      query({ active: true, page_size: 100, search: learningSearch }),
  );
  const tracks = useResource<Page<Track>>(
    "/learning-tracks" +
      query({ active: true, page_size: 100, search: learningSearch }),
  );
  return (
    <Dialog title="Assign learning" onClose={onClose}>
      <form
        onSubmit={async (e) => {
          e.preventDefault();
          setBusy(true);
          setError("");
          const f = new FormData(e.currentTarget);
          try {
            await post("/assignments", {
              employee_id: f.get("employee_id"),
              course_id: kind === "course" ? f.get("target") : null,
              learning_track_id: kind === "track" ? f.get("target") : null,
              target_date: f.get("target_date") || null,
              employee_can_update: f.has("can_update"),
              employee_can_complete: f.has("can_complete"),
              certificate_required: f.has("certificate"),
              is_mandatory: f.has("mandatory"),
            });
            onSaved();
          } catch (err) {
            setError((err as Error).message);
          } finally {
            setBusy(false);
          }
        }}
      >
        <Field label="Find an employee">
          <input
            value={employeeSearch}
            onChange={(e) => setEmployeeSearch(e.target.value)}
            placeholder="Search name or employee code"
          />
        </Field>
        <Field label="Employee">
          <select name="employee_id" defaultValue={employee} required>
            <option value="">Select employee…</option>
            {employees.data?.items.map((e) => (
              <option key={e.id} value={e.id}>
                {e.name} · {e.employee_code}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Assignment type">
          <select
            value={kind}
            onChange={(e) => {
              setKind(e.target.value);
              setLearningSearch("");
            }}
          >
            <option value="course">Individual course</option>
            <option value="track">Learning track</option>
          </select>
        </Field>
        <Field label="Find learning">
          <input
            value={learningSearch}
            onChange={(e) => setLearningSearch(e.target.value)}
            placeholder="Search courses or tracks"
          />
        </Field>
        <Field label={kind === "course" ? "Course" : "Learning track"}>
          <select
            name="target"
            key={kind + learningSearch}
            required
            defaultValue=""
          >
            <option value="">Select {kind}…</option>
            {(kind === "course"
              ? courses.data?.items
              : tracks.data?.items
            )?.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Target completion date">
          <input name="target_date" type="date" />
        </Field>
        <label className="checkbox-row">
          <input name="can_update" type="checkbox" defaultChecked />
          Employee can update progress
        </label>
        <label className="checkbox-row">
          <input name="can_complete" type="checkbox" defaultChecked />
          Employee can record completion
        </label>
        <label className="checkbox-row">
          <input name="certificate" type="checkbox" />
          Certificate required for completion
        </label>
        <label className="checkbox-row">
          <input name="mandatory" type="checkbox" />
          Mandatory learning
        </label>
        <small className="muted">
          Unfinished courses already assigned to this employee share progress
          and evidence. Completed courses start a new attempt.
        </small>
        {[employees.error, courses.error, tracks.error, error]
          .filter(Boolean)
          .map((e, i) => (
            <ErrorState key={i} message={e} />
          ))}
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
            {busy ? "Assigning…" : "Assign learning"}
          </button>
        </div>
      </form>
    </Dialog>
  );
}
