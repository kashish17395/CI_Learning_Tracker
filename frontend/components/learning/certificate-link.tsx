"use client";
import { useState, type ReactNode } from "react";
import { downloadCertificate } from "@/services/api";
import type { Certificate } from "@/types";

export function CertificateLink({
  certificate,
  className,
  children,
}: {
  certificate: Pick<Certificate, "id" | "original_filename">;
  className?: string;
  children?: ReactNode;
}) {
  const [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  return (
    <>
      <a
        href={`/api/v1/certificates/${certificate.id}/download`}
        className={className}
        aria-busy={busy}
        onClick={async (event) => {
          event.preventDefault();
          if (busy) return;
          setBusy(true);
          setError("");
          try {
            await downloadCertificate(
              certificate.id,
              certificate.original_filename,
            );
          } catch (failure) {
            setError((failure as Error).message);
          } finally {
            setBusy(false);
          }
        }}
      >
        {children || certificate.original_filename}
      </a>
      {error && (
        <span
          role="alert"
          style={{ display: "block", color: "#a13e36", fontSize: 12 }}
        >
          {error}
        </span>
      )}
    </>
  );
}
