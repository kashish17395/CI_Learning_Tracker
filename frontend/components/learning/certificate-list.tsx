"use client";
import { useState } from "react";
import { Download, FileText } from "lucide-react";
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
import type { Certificate, Page } from "@/types";
import { CertificateLink } from "@/components/learning/certificate-link";
export function CertificateList() {
  const [search, setSearch] = useState(""),
    [page, setPage] = useState(1);
  const r = useResource<Page<Certificate>>(
    "/certificates" + query({ search, page }),
  );
  return (
    <>
      <PageHeading
        eyebrow="COMPLETION EVIDENCE"
        title="Certificates"
        description="Securely stored evidence of learning and achievement."
      />
      <section className="panel">
        <div className="filter-bar">
          <SearchInput
            value={search}
            onChange={(v) => {
              setSearch(v);
              setPage(1);
            }}
            placeholder="Search certificate filenames…"
          />
        </div>
        {r.error ? (
          <ErrorState message={r.error} retry={r.reload} />
        ) : r.loading ? (
          <Loading />
        ) : !r.data?.items.length ? (
          <Empty
            title="No certificates yet"
            detail="Upload a certificate from a course’s learning detail page."
          />
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Certificate</th>
                  <th>Employee</th>
                  <th>Course</th>
                  <th>Uploaded</th>
                  <th>Size</th>
                  <th>Download</th>
                </tr>
              </thead>
              <tbody>
                {r.data.items.map((c) => (
                  <tr key={c.id}>
                    <td>
                      <div className="person-cell">
                        <span className="avatar">
                          <FileText size={17} />
                        </span>
                        <span className="cell-title">
                          {c.original_filename}
                        </span>
                      </div>
                    </td>
                    <td>{c.employee_name}</td>
                    <td>{c.course_name}</td>
                    <td>{dateLabel(c.uploaded_at)}</td>
                    <td>{Math.ceil(c.file_size / 1024)} KB</td>
                    <td>
                      <CertificateLink
                        certificate={c}
                        className="btn compact secondary"
                      >
                        <Download size={14} />
                        Download
                      </CertificateLink>
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
