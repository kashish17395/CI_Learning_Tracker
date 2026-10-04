"use client";
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
} from "@/components/ui";
import type { Audit, Page } from "@/types";
export function AuditList() {
  const [search, setSearch] = useState(""),
    [page, setPage] = useState(1);
  const r = useResource<Page<Audit>>("/audit-logs" + query({ search, page }));
  return (
    <>
      <PageHeading
        eyebrow="ACCOUNTABILITY"
        title="Audit history"
        description="Recorded changes to employees, learning plans, progress and evidence."
      />
      <section className="panel">
        <div className="filter-bar">
          <SearchInput
            value={search}
            onChange={(v) => {
              setSearch(v);
              setPage(1);
            }}
            placeholder="Search action or record type…"
          />
        </div>
        {r.error ? (
          <ErrorState message={r.error} retry={r.reload} />
        ) : r.loading ? (
          <Loading />
        ) : !r.data?.items.length ? (
          <Empty title="No matching audit events" />
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Action</th>
                  <th>Record type</th>
                  <th>Actor</th>
                  <th>When</th>
                  <th>Details</th>
                </tr>
              </thead>
              <tbody>
                {r.data.items.map((a) => (
                  <tr key={a.id}>
                    <td className="cell-title">
                      {a.action.toLowerCase().replaceAll("_", " ")}
                    </td>
                    <td>
                      {a.entity_type.replaceAll("_", " ")}
                      <span className="cell-subtitle">
                        {a.entity_id.slice(0, 8)}
                      </span>
                    </td>
                    <td>{a.actor_user_id.slice(0, 8)}</td>
                    <td>
                      {dateLabel(a.created_at)}
                      <span className="cell-subtitle">
                        {new Date(a.created_at).toLocaleTimeString("en-IN")}
                      </span>
                    </td>
                    <td>
                      <details>
                        <summary className="text-btn">View details</summary>
                        <pre
                          style={{
                            fontSize: 11,
                            whiteSpace: "pre-wrap",
                            maxWidth: 300,
                          }}
                        >
                          {JSON.stringify(a.details, null, 2)}
                        </pre>
                      </details>
                    </td>
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
    </>
  );
}
