"use client";
import { useState } from "react";
import { BookOpen, Plus, Clock3 } from "lucide-react";
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
import type { Course, Page } from "@/types";
export function CourseList() {
  const [search, setSearch] = useState(""),
    [active, setActive] = useState(""),
    [category, setCategory] = useState(""),
    [page, setPage] = useState(1),
    [edit, setEdit] = useState<Course | null | undefined>(undefined),
    [confirm, setConfirm] = useState<Course | null>(null);
  const toast = useToast();
  const r = useResource<Page<Course>>(
    "/courses" + query({ search, active, category, page }),
  );
  return (
    <>
      <PageHeading
        eyebrow="LEARNING CATALOG"
        title="Courses"
        description="The building blocks of every learning plan."
        action={
          <button className="btn" onClick={() => setEdit(null)}>
            <Plus size={17} />
            Create course
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
            placeholder="Search courses, providers or codes…"
          />
          <input
            placeholder="All categories"
            aria-label="Category filter"
            value={category}
            onChange={(e) => {
              setCategory(e.target.value);
              setPage(1);
            }}
          />
          <select
            aria-label="Course status"
            value={active}
            onChange={(e) => {
              setActive(e.target.value);
              setPage(1);
            }}
          >
            <option value="">All courses</option>
            <option value="true">Active</option>
            <option value="false">Inactive</option>
          </select>
        </div>
        {r.error ? (
          <ErrorState message={r.error} retry={r.reload} />
        ) : r.loading ? (
          <Loading />
        ) : !r.data?.items.length ? (
          <Empty
            title="Build your course catalog"
            detail="Create courses that can be assigned individually or grouped into learning tracks."
          />
        ) : (
          <div className="course-grid">
            {r.data.items.map((c) => (
              <article className="course-card" key={c.id}>
                <div
                  style={{ display: "flex", justifyContent: "space-between" }}
                >
                  <span className="course-card-icon">
                    <BookOpen size={21} />
                  </span>
                  <span
                    className={
                      "badge " +
                      (c.is_active ? "status-completed" : "status-cancelled")
                    }
                    style={{ height: 24 }}
                  >
                    {c.is_active ? "Active" : "Inactive"}
                  </span>
                </div>
                <span className="cell-subtitle">
                  {c.course_code} · {c.category || "General"}
                </span>
                <h3>{c.name}</h3>
                <p>{c.description || "No course description yet."}</p>
                <span className="cell-subtitle">
                  {c.provider || "Internal learning"}
                </span>
                <div className="course-card-bottom">
                  <span
                    style={{ display: "flex", alignItems: "center", gap: 5 }}
                  >
                    <Clock3 size={14} />
                    {c.estimated_duration_minutes == null
                      ? "Duration not set"
                      : `${c.estimated_duration_minutes} min`}
                  </span>
                  <button className="text-btn" onClick={() => setEdit(c)}>
                    Edit course
                  </button>
                </div>
                <button
                  className="text-btn"
                  style={{
                    alignSelf: "flex-start",
                    fontSize: 11,
                    marginTop: 8,
                    color: "var(--muted)",
                  }}
                  onClick={() => setConfirm(c)}
                >
                  {c.is_active ? "Deactivate" : "Activate"}
                </button>
              </article>
            ))}
          </div>
        )}
        {r.data && (
          <Pagination page={page} total={r.data.total} onChange={setPage} />
        )}
      </section>
      {edit !== undefined && (
        <CourseForm
          course={edit}
          onClose={() => setEdit(undefined)}
          onSaved={() => {
            setEdit(undefined);
            r.reload();
            toast("Course saved");
          }}
        />
      )}
      {confirm && (
        <Confirm
          title={confirm.is_active ? "Deactivate course?" : "Activate course?"}
          detail={
            confirm.is_active
              ? "Existing assignments and historical completions will remain available. New assignments will be blocked."
              : "Make this course available for new assignments."
          }
          onClose={() => setConfirm(null)}
          onConfirm={async () => {
            await patch("/courses/" + confirm.id, {
              is_active: !confirm.is_active,
            });
            r.reload();
            toast("Course status updated");
          }}
        />
      )}
    </>
  );
}
function CourseForm({
  course,
  onClose,
  onSaved,
}: {
  course: Course | null;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  return (
    <Dialog title={course ? "Edit course" : "Create course"} onClose={onClose}>
      <form
        onSubmit={async (e) => {
          e.preventDefault();
          setBusy(true);
          setError("");
          const f = new FormData(e.currentTarget);
          const values = {
            course_code: f.get("course_code"),
            name: f.get("name"),
            description: f.get("description"),
            category: f.get("category"),
            provider: f.get("provider"),
            estimated_duration_minutes: f.get("duration")
              ? Number(f.get("duration"))
              : null,
          };
          try {
            if (course) await patch("/courses/" + course.id, values);
            else await post("/courses", values);
            onSaved();
          } catch (err) {
            setError((err as Error).message);
          } finally {
            setBusy(false);
          }
        }}
      >
        <div className="form-grid">
          <Field label="Course code">
            <input
              name="course_code"
              defaultValue={course?.course_code}
              required
              maxLength={64}
            />
          </Field>
          <Field label="Category">
            <input
              name="category"
              defaultValue={course?.category}
              maxLength={100}
            />
          </Field>
        </div>
        <Field label="Course name">
          <input
            name="name"
            defaultValue={course?.name}
            required
            maxLength={200}
          />
        </Field>
        <Field label="Description">
          <textarea
            name="description"
            defaultValue={course?.description}
            maxLength={10000}
          />
        </Field>
        <div className="form-grid">
          <Field label="Provider">
            <input
              name="provider"
              defaultValue={course?.provider}
              maxLength={150}
            />
          </Field>
          <Field label="Estimated duration (minutes)">
            <input
              name="duration"
              type="number"
              min={0}
              step={1}
              defaultValue={course?.estimated_duration_minutes ?? ""}
            />
          </Field>
        </div>
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
            {busy ? "Saving…" : "Save course"}
          </button>
        </div>
      </form>
    </Dialog>
  );
}
