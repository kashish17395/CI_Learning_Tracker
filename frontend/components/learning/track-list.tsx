"use client";
import { useState } from "react";
import { ArrowDown, ArrowUp, Plus, Route, X } from "lucide-react";
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
import type { Course, Page, Track } from "@/types";
export function TrackList() {
  const [search, setSearch] = useState(""),
    [active, setActive] = useState(""),
    [page, setPage] = useState(1),
    [edit, setEdit] = useState<Track | null | undefined>(undefined),
    [confirm, setConfirm] = useState<Track | null>(null);
  const toast = useToast();
  const r = useResource<Page<Track>>(
    "/learning-tracks" + query({ search, active, page }),
  );
  return (
    <>
      <PageHeading
        eyebrow="STRUCTURED DEVELOPMENT"
        title="Learning tracks"
        description="Turn individual courses into a clear path for growth."
        action={
          <button className="btn" onClick={() => setEdit(null)}>
            <Plus size={17} />
            Create track
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
            placeholder="Search learning tracks…"
          />
          <select
            aria-label="Track status"
            value={active}
            onChange={(e) => {
              setActive(e.target.value);
              setPage(1);
            }}
          >
            <option value="">All tracks</option>
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
            title="Create a learning path"
            detail="Group courses into an ordered track for a role or capability."
          />
        ) : (
          <div className="course-grid">
            {r.data.items.map((t) => (
              <article className="course-card" key={t.id}>
                <div
                  style={{ display: "flex", justifyContent: "space-between" }}
                >
                  <span className="course-card-icon">
                    <Route size={21} />
                  </span>
                  <span
                    className={
                      "badge " +
                      (t.is_active ? "status-completed" : "status-cancelled")
                    }
                    style={{ height: 24 }}
                  >
                    {t.is_active ? "Active" : "Inactive"}
                  </span>
                </div>
                <h3>{t.name}</h3>
                <p>
                  {t.description ||
                    "A structured collection of learning courses."}
                </p>
                <div className="ordered-courses">
                  {t.courses.slice(0, 4).map((c, i) => (
                    <div className="ordered-course" key={c.id}>
                      <span className="order-number">{i + 1}</span>
                      <span style={{ fontSize: 12 }}>{c.name}</span>
                    </div>
                  ))}
                  {t.courses.length > 4 && (
                    <small className="muted">
                      +{t.courses.length - 4} more courses
                    </small>
                  )}
                </div>
                <div className="course-card-bottom">
                  <span>{t.courses.length} courses</span>
                  <button className="text-btn" onClick={() => setEdit(t)}>
                    Edit track
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
                  onClick={() => setConfirm(t)}
                >
                  {t.is_active ? "Deactivate" : "Activate"}
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
        <TrackForm
          track={edit}
          onClose={() => setEdit(undefined)}
          onSaved={() => {
            setEdit(undefined);
            r.reload();
            toast("Learning track saved");
          }}
        />
      )}
      {confirm && (
        <Confirm
          title={confirm.is_active ? "Deactivate track?" : "Activate track?"}
          detail="Existing assignments retain their captured courses and learning history."
          onClose={() => setConfirm(null)}
          onConfirm={async () => {
            await patch("/learning-tracks/" + confirm.id, {
              is_active: !confirm.is_active,
            });
            r.reload();
            toast("Track status updated");
          }}
        />
      )}
    </>
  );
}
function TrackForm({
  track,
  onClose,
  onSaved,
}: {
  track: Track | null;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [selected, setSelected] = useState<Course[]>(track?.courses || []),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [search, setSearch] = useState("");
  const courses = useResource<Page<Course>>(
    "/courses" + query({ active: true, page_size: 100, search }),
  );
  const move = (index: number, delta: number) => {
    const next = [...selected];
    [next[index], next[index + delta]] = [next[index + delta], next[index]];
    setSelected(next);
  };
  return (
    <Dialog
      title={track ? "Edit learning track" : "Create learning track"}
      onClose={onClose}
    >
      <form
        onSubmit={async (e) => {
          e.preventDefault();
          if (!selected.length) {
            setError("Add at least one course");
            return;
          }
          setBusy(true);
          setError("");
          const f = new FormData(e.currentTarget),
            fields = { name: f.get("name"), description: f.get("description") },
            course_ids = selected.map((c) => c.id);
          try {
            if (track) {
              await patch("/learning-tracks/" + track.id, {
                ...fields,
                course_ids,
              });
            } else await post("/learning-tracks", { ...fields, course_ids });
            onSaved();
          } catch (err) {
            setError((err as Error).message);
          } finally {
            setBusy(false);
          }
        }}
      >
        <Field label="Track name">
          <input
            name="name"
            defaultValue={track?.name}
            required
            maxLength={200}
          />
        </Field>
        <Field label="Description">
          <textarea
            name="description"
            defaultValue={track?.description}
            maxLength={10000}
          />
        </Field>
        <Field label="Find courses">
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search your course catalog"
          />
        </Field>
        <Field label="Add a course">
          <select
            value=""
            onChange={(e) => {
              const course = courses.data?.items.find(
                (c) => c.id === e.target.value,
              );
              if (course) setSelected([...selected, course]);
            }}
          >
            <option value="">Select a course…</option>
            {courses.data?.items
              .filter((c) => !selected.some((s) => s.id === c.id))
              .map((c) => (
                <option value={c.id} key={c.id}>
                  {c.name} · {c.course_code}
                </option>
              ))}
          </select>
        </Field>
        {courses.error && (
          <ErrorState message={courses.error} retry={courses.reload} />
        )}
        <div className="ordered-courses">
          {selected.map((c, i) => (
            <div className="ordered-course" key={c.id}>
              <span className="order-number">{i + 1}</span>
              <span>{c.name}</span>
              <button
                type="button"
                className="icon-btn"
                aria-label={"Move " + c.name + " up"}
                disabled={i === 0}
                onClick={() => move(i, -1)}
              >
                <ArrowUp size={14} />
              </button>
              <button
                type="button"
                className="icon-btn"
                aria-label={"Move " + c.name + " down"}
                disabled={i === selected.length - 1}
                onClick={() => move(i, 1)}
              >
                <ArrowDown size={14} />
              </button>
              <button
                type="button"
                className="icon-btn"
                aria-label={"Remove " + c.name}
                onClick={() =>
                  setSelected(selected.filter((s) => s.id !== c.id))
                }
              >
                <X size={14} />
              </button>
            </div>
          ))}
        </div>
        <small className="muted">
          Changes apply to future assignments. Existing assignments keep their
          course list.
        </small>
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
            {busy ? "Saving…" : "Save track"}
          </button>
        </div>
      </form>
    </Dialog>
  );
}
