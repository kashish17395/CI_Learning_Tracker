"use client";
import Link from "next/link";
import { useState } from "react";
import { useResource } from "@/hooks/use-resource";
import { query } from "@/services/api";
import {
  dateLabel,
  Empty,
  ErrorState,
  Loading,
  PageHeading,
  Pagination,
  SearchInput,
  StatusBadge,
} from "@/components/ui";
import type { Attempt, Page } from "@/types";
import { CertificateLink } from "@/components/learning/certificate-link";
export function MyLearning() {
  const [search, setSearch] = useState(""),
    [status, setStatus] = useState(""),
    [history, setHistory] = useState(false),
    [page, setPage] = useState(1),
    [from, setFrom] = useState(""),
    [to, setTo] = useState(""),
    [track, setTrack] = useState("");
  const r = useResource<Page<Attempt>>(
    "/my-learning" +
      query({
        search,
        status,
        history,
        page,
        target_from: from,
        target_to: to,
        track_id: track,
      }),
  );
  const options = useResource<{ tracks: { id: string; name: string }[] }>(
    "/my-learning/options",
  );
  const tracks = options.data?.tracks.map((t) => [t.id, t.name]) || [];
  return (
    <>
      <PageHeading
        eyebrow="YOUR DEVELOPMENT"
        title="My learning"
        description="Every course, learning path and achievement in one place."
      />
      <section className="panel">
        <div className="filter-bar">
          <SearchInput
            value={search}
            onChange={(v) => {
              setSearch(v);
              setPage(1);
            }}
            placeholder="Search your courses…"
          />
          <select
            aria-label="Learning status"
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
            aria-label="Learning track"
            value={track}
            onChange={(e) => {
              setTrack(e.target.value);
              setPage(1);
            }}
          >
            <option value="">All tracks</option>
            {tracks.map(([id, name]) => (
              <option value={id} key={id}>
                {name}
              </option>
            ))}
          </select>
          <label className="date-filter">
            From
            <input
              aria-label="Target date from"
              type="date"
              value={from}
              onChange={(e) => {
                setFrom(e.target.value);
                setPage(1);
              }}
            />
          </label>
          <label className="date-filter">
            To
            <input
              aria-label="Target date to"
              type="date"
              value={to}
              onChange={(e) => {
                setTo(e.target.value);
                setPage(1);
              }}
            />
          </label>
          <label className="checkbox-row" style={{ margin: 0 }}>
            <input
              type="checkbox"
              checked={history}
              onChange={(e) => {
                setHistory(e.target.checked);
                setPage(1);
              }}
            />
            Include history
          </label>
        </div>
        {r.error ? (
          <ErrorState message={r.error} retry={r.reload} />
        ) : r.loading ? (
          <Loading />
        ) : r.data?.items.length ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Course</th>
                  <th>Learning track</th>
                  <th>Assigned date</th>
                  <th>Target date</th>
                  <th>Status</th>
                  <th>Completion</th>
                  <th>Certificate</th>
                </tr>
              </thead>
              <tbody>
                {r.data.items.map((a) => (
                  <tr key={a.id}>
                    <td>
                      <Link className="text-btn" href={"/my-learning/" + a.id}>
                        {a.course.name}
                      </Link>
                      <span className="cell-subtitle">
                        {a.course.course_code}
                      </span>
                    </td>
                    <td>
                      {a.assignments
                        .map((c) => c.track_name)
                        .filter(Boolean)
                        .join(", ") || "Individual course"}
                    </td>
                    <td>{dateLabel(a.created_at)}</td>
                    <td>{dateLabel(a.target_date)}</td>
                    <td>
                      <StatusBadge status={a.status} overdue={a.overdue} />
                    </td>
                    <td>{dateLabel(a.completion_date)}</td>
                    <td>
                      {a.certificates.length ? (
                        <CertificateLink
                          className="text-btn"
                          certificate={a.certificates[0]}
                        >
                          {a.certificates.length} files
                        </CertificateLink>
                      ) : (
                        "—"
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <Empty
            title="No matching learning"
            detail="Your manager’s assigned courses and tracks appear here."
          />
        )}
        {r.data && (
          <Pagination page={page} total={r.data.total} onChange={setPage} />
        )}
      </section>
    </>
  );
}
