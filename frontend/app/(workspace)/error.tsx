"use client";
import { ErrorState } from "@/components/ui";
export default function ErrorPage({
  reset,
}: {
  error: Error;
  reset: () => void;
}) {
  return (
    <ErrorState
      message="This page could not load. Check that the learning service is running."
      retry={reset}
    />
  );
}
