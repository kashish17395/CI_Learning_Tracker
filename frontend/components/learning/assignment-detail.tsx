"use client";
import Link from "next/link";
import { useState } from "react";
import { ChevronLeft, Pencil } from "lucide-react";
import { useResource } from "@/hooks/use-resource";
import { patch } from "@/services/api";
import {
  dateLabel,
  Dialog,
  ErrorState,
  Field,
  Loading,
  PageHeading,
  StatusBadge,
  useToast,
} from "@/components/ui";
import type { Assignment } from "@/types";
export function AssignmentDetail({ id }: { id: string }) {
  const r = useResource<Assignment>("/assignments/" + id);
  const [edit, setEdit] = useState(false);
  const toast = useToast();
  if (r.error) return <ErrorState message={r.error} retry={r.reload} />;
  if (!r.data) return <Loading />;
  const a = r.data;
  return (
    <>
      <Link className="back-link" href="/assignments">
        <ChevronLeft size={16} />
        Assignments
      </Link>
      <PageHeading
        eyebrow={
          a.learning_track_id
            ? "LEARNING TRACK ASSIGNMENT"
            : "COURSE ASSIGNMENT"
        }
        title={a.name}
        description={"Assigned to " + a.employee_name}
        action={
          !a.cancelled_at && (
            <button className="btn secondary" onClick={() => setEdit(true)}>
              <Pencil size={16} />
              Manage assignment
            </button>
          )
        }
      />
      <div className="section-stack">
        <section className="panel">
          <div className="panel-heading">
            <h2>Assignment details</h2>
            <StatusBadge
              status={a.cancelled_at ? "CANCELLED" : a.status}
              overdue={a.overdue}
            />
          </div>
          <div className="panel-body">
            <dl className="detail-list">
              <div>
                <dt>Assigned date</dt>
                <dd>{dateLabel(a.assigned_at)}</dd>
              </div>
              <div>
                <dt>Target date</dt>
                <dd>{dateLabel(a.target_date)}</dd>
              </div>
              <div>
                <dt>Evidence policy</dt>
                <dd>
                  {a.certificate_required
                    ? "Certificate required"
                    : "Certificate optional"}
                </dd>
              </div>
              <div>
                <dt>Completion</dt>
                <dd>{dateLabel(a.completion_date)}</dd>
              </div>
              <div>
                <dt>Employee progress</dt>
                <dd>
                  {a.employee_can_update ? "Allowed" : "Manager controlled"}
                </dd>
              </div>
              <div>
                <dt>Employee completion</dt>
                <dd>
                  {a.employee_can_complete ? "Allowed" : "Manager controlled"}
                </dd>
              </div>
            </dl>
          </div>
        </section>
        <section className="panel">
          <div className="panel-heading">
            <div>
              <h2>Assigned courses</h2>
              <p>Courses included when this assignment was created</p>
            </div>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Sequence</th>
                  <th>Course</th>
                  <th>Status</th>
                  <th>Completion date</th>
                  <th>Certificates</th>
                </tr>
              </thead>
              <tbody>
                {a.courses.map((c, i) => (
                  <tr key={c.id}>
                    <td>{i + 1}</td>
                    <td>
                      <Link className="text-btn" href={"/my-learning/" + c.id}>
                        {c.course.name}
                      </Link>
                      <span className="cell-subtitle">
                        {c.course.course_code}
                      </span>
                    </td>
                    <td>
                      <StatusBadge status={c.status} overdue={c.overdue} />
                    </td>
                    <td>{dateLabel(c.completion_date)}</td>
                    <td>{c.certificates.length} files</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>
      {edit && (
        <ManageAssignment
          assignment={a}
          onClose={() => setEdit(false)}
          onSaved={() => {
            setEdit(false);
            r.reload();
            toast("Assignment updated");
          }}
        />
      )}
    </>
  );
}
function ManageAssignment({
  assignment: a,
  onClose,
  onSaved,
}: {
  assignment: Assignment;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [cancel, setCancel] = useState(false);
  return (
    <Dialog title="Manage assignment" onClose={onClose}>
      <form
        onSubmit={async (e) => {
          e.preventDefault();
          setError("");
          setBusy(true);
          const f = new FormData(e.currentTarget);
          try {
            await patch("/assignments/" + a.id, {
              version: a.version,
              target_date: f.get("target_date") || null,
              employee_can_update: f.has("update"),
              employee_can_complete: f.has("complete"),
              certificate_required: f.has("certificate"),
              is_mandatory: f.has("mandatory"),
              cancel,
              reason: f.get("reason"),
            });
            onSaved();
          } catch (err) {
            setError((err as Error).message);
          } finally {
            setBusy(false);
          }
        }}
      >
        <Field label="Target date">
          <input
            name="target_date"
            type="date"
            defaultValue={a.target_date || ""}
          />
        </Field>
        <label className="checkbox-row">
          <input
            name="update"
            type="checkbox"
            defaultChecked={a.employee_can_update}
          />
          Employee can update progress
        </label>
        <label className="checkbox-row">
          <input
            name="complete"
            type="checkbox"
            defaultChecked={a.employee_can_complete}
          />
          Employee can record completion
        </label>
        <label className="checkbox-row">
          <input
            name="certificate"
            type="checkbox"
            defaultChecked={a.certificate_required}
          />
          Require certificate
        </label>
        <label className="checkbox-row">
          <input
            name="mandatory"
            type="checkbox"
            defaultChecked={a.is_mandatory}
          />
          Mandatory learning
        </label>
        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={cancel}
            onChange={(e) => setCancel(e.target.checked)}
          />
          Cancel this assignment
        </label>
        {cancel && (
          <p className="muted">
            Cancellation preserves learning history and shared course progress.
          </p>
        )}
        <Field label="Reason for change">
          <textarea name="reason" required minLength={3} maxLength={2000} />
        </Field>
        {error && <ErrorState message={error} />}
        <div className="form-actions">
          <button
            type="button"
            className="btn secondary"
            disabled={busy}
            onClick={onClose}
          >
            Keep current assignment
          </button>
          <button className="btn" disabled={busy}>
            {busy
              ? "Saving…"
              : cancel
                ? "Confirm cancellation"
                : "Save changes"}
          </button>
        </div>
      </form>
    </Dialog>
  );
}
