"use client";
import Link from "next/link";
import { useState } from "react";
import { Award, ChevronLeft, Upload } from "lucide-react";
import { useResource } from "@/hooks/use-resource";
import { api, patch } from "@/services/api";
import {
  dateLabel,
  ErrorState,
  Field,
  Loading,
  PageHeading,
  StatusBadge,
  useToast,
} from "@/components/ui";
import type { Attempt, Status, User } from "@/types";
import { CertificateLink } from "@/components/learning/certificate-link";
export function LearningDetail({ id, user }: { id: string; user: User }) {
  const r = useResource<Attempt>("/completions/" + id),
    toast = useToast();
  const [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [uploading, setUploading] = useState(false),
    [status, setStatus] = useState<Status | "">("");
  if (r.error) return <ErrorState message={r.error} retry={r.reload} />;
  if (!r.data) return <Loading />;
  const a = r.data,
    manager = user.role === "MANAGER",
    canUpdate = manager || a.employee_can_update,
    canComplete = manager || a.employee_can_complete;
  const hasContext = a.assignments.length > 0 && !a.retired_at,
    mayEdit = hasContext && canUpdate && (manager || a.status !== "COMPLETED");
  return (
    <>
      <Link
        className="back-link"
        href={manager ? "/employees/" + a.employee_id : "/my-learning"}
      >
        <ChevronLeft size={16} />
        {manager ? "Employee learning" : "My learning"}
      </Link>
      <PageHeading
        eyebrow={a.course.course_code}
        title={a.course.name}
        description={
          manager
            ? `Learning progress for ${a.employee_name}`
            : a.course.provider || "Assigned course"
        }
        action={<StatusBadge status={a.status} overdue={a.overdue} />}
      />
      <div className="detail-grid">
        <div className="section-stack">
          <section className="panel">
            <div className="panel-heading">
              <h2>Course information</h2>
              <span className="badge">{a.course.category || "General"}</span>
            </div>
            <div className="panel-body">
              <p className="description-text">
                {a.course.description || "No description provided."}
              </p>
              <dl className="detail-list" style={{ marginTop: 25 }}>
                <div>
                  <dt>Assigned date</dt>
                  <dd>{dateLabel(a.created_at)}</dd>
                </div>
                <div>
                  <dt>Target date</dt>
                  <dd>{dateLabel(a.target_date)}</dd>
                </div>
                <div>
                  <dt>Estimated duration</dt>
                  <dd>
                    {a.course.estimated_duration_minutes == null
                      ? "Not specified"
                      : a.course.estimated_duration_minutes + " minutes"}
                  </dd>
                </div>
                <div>
                  <dt>Completion date</dt>
                  <dd>{dateLabel(a.completion_date)}</dd>
                </div>
              </dl>
            </div>
          </section>
          <section className="panel">
            <div className="panel-heading">
              <h2>Assignment context</h2>
            </div>
            <div className="panel-body">
              {a.assignments.length ? (
                a.assignments.map((c) => (
                  <div className="deadline-item" key={c.id}>
                    <div className="deadline-info">
                      <strong>
                        {c.track_name || "Individual course assignment"}
                      </strong>
                      <small>
                        Target: {dateLabel(c.target_date)}
                        {c.is_mandatory ? " · Mandatory" : ""}
                      </small>
                    </div>
                    {manager && (
                      <Link className="text-btn" href={"/assignments/" + c.id}>
                        View assignment
                      </Link>
                    )}
                  </div>
                ))
              ) : (
                <p className="muted">
                  This learning has no active assignments.
                </p>
              )}
            </div>
            <div className="panel-note">
              Progress is shared across active assignments for this learning
              attempt.
            </div>
          </section>
          <section className="panel">
            <div className="panel-heading">
              <h2>Certificates & evidence</h2>
              <Award size={20} className="muted" />
            </div>
            <div className="panel-body">
              <p className="muted">
                {a.certificate_required
                  ? "A certificate is required before completion."
                  : "You can attach evidence of your learning."}
              </p>
              <div className="evidence-list">
                {a.certificates.map((c) => (
                  <CertificateLink
                    className="evidence-item"
                    key={c.id}
                    certificate={c}
                  >
                    <Award size={19} />
                    <span>
                      {c.original_filename}
                      <small
                        style={{ display: "block", color: "var(--muted)" }}
                      >
                        {dateLabel(c.uploaded_at)} ·{" "}
                        {Math.ceil(c.file_size / 1024)} KB
                      </small>
                    </span>
                  </CertificateLink>
                ))}
              </div>
              {hasContext && canUpdate && (
                <form
                  onSubmit={async (e) => {
                    e.preventDefault();
                    const form = e.currentTarget;
                    const f = new FormData(form);
                    f.set("attempt_id", a.id);
                    setUploading(true);
                    setError("");
                    try {
                      await api("/certificates", { method: "POST", body: f });
                      form.reset();
                      r.reload();
                      toast("Certificate uploaded");
                    } catch (err) {
                      setError((err as Error).message);
                    } finally {
                      setUploading(false);
                    }
                  }}
                >
                  <Field
                    label="Upload certificate"
                    hint="PDF, PNG or JPEG · Maximum 10 MiB"
                  >
                    <input
                      name="file"
                      type="file"
                      accept=".pdf,.png,.jpg,.jpeg"
                      required
                    />
                  </Field>
                  <button className="btn secondary" disabled={uploading}>
                    <Upload size={16} />
                    {uploading ? "Uploading…" : "Upload evidence"}
                  </button>
                </form>
              )}
            </div>
          </section>
        </div>
        <section className="panel" style={{ alignSelf: "start" }}>
          <div className="panel-heading">
            <h2>{manager ? "Manage progress" : "Update your progress"}</h2>
          </div>
          <div className="panel-body">
            {mayEdit ? (
              <form
                onSubmit={async (e) => {
                  e.preventDefault();
                  const f = new FormData(e.currentTarget);
                  setBusy(true);
                  setError("");
                  try {
                    await patch("/completions/" + id, {
                      status: f.get("status"),
                      version: a.version,
                      completion_date:
                        f.get("status") === "COMPLETED"
                          ? f.get("completion_date") || null
                          : null,
                      reason: manager ? f.get("reason") : null,
                    });
                    setStatus("");
                    r.reload();
                    toast("Learning progress saved");
                  } catch (err) {
                    setError((err as Error).message);
                  } finally {
                    setBusy(false);
                  }
                }}
              >
                <Field label="Status">
                  <select
                    name="status"
                    value={status || a.status}
                    onChange={(e) => setStatus(e.target.value as Status)}
                  >
                    {(
                      [
                        "NOT_STARTED",
                        "ENROLLED",
                        "IN_PROGRESS",
                        "COMPLETED",
                      ] as Status[]
                    )
                      .filter(
                        (s) =>
                          (manager ||
                            [
                              "NOT_STARTED",
                              "ENROLLED",
                              "IN_PROGRESS",
                              "COMPLETED",
                            ].indexOf(s) >=
                              [
                                "NOT_STARTED",
                                "ENROLLED",
                                "IN_PROGRESS",
                                "COMPLETED",
                              ].indexOf(a.status)) &&
                          (s !== "COMPLETED" || canComplete),
                      )
                      .map((s) => (
                        <option value={s} key={s}>
                          {s.toLowerCase().replaceAll("_", " ")}
                        </option>
                      ))}
                  </select>
                </Field>
                {(status || a.status) === "COMPLETED" && (
                  <Field label="Completion date">
                    <input
                      name="completion_date"
                      type="date"
                      min={a.started_on}
                      defaultValue={a.completion_date || ""}
                      required
                    />
                  </Field>
                )}
                {manager && (
                  <Field label="Reason for change">
                    <textarea
                      name="reason"
                      required
                      minLength={3}
                      maxLength={2000}
                    />
                  </Field>
                )}
                <p className="muted" style={{ fontSize: 12, marginBottom: 18 }}>
                  {a.certificate_required
                    ? "Upload evidence before submitting completion."
                    : "Your progress will update every assignment linked to this attempt."}
                </p>
                <button
                  className="btn"
                  style={{ width: "100%" }}
                  disabled={busy}
                >
                  {busy ? "Saving…" : "Save progress"}
                </button>
              </form>
            ) : (
              <p className="muted">
                {a.status === "COMPLETED"
                  ? "This course is completed. Your manager can make corrections."
                  : "Progress for this learning is managed by your manager."}
              </p>
            )}
            {error && <ErrorState message={error} />}
          </div>
        </section>
      </div>
    </>
  );
}
