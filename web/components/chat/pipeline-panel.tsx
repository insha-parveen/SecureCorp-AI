"use client";

// PipelinePanel — DEPRECATED alias. The /chat right rail now mounts
// <SecureCorpPipelineLive> directly (the branching, technically-accurate
// pipeline). This thin wrapper is kept only so any stray import keeps
// compiling; it forwards to the live pipeline. Prefer importing
// SecureCorpPipelineLive directly. Safe to delete once no imports remain.

import { SecureCorpPipelineLive } from "@/components/pipeline/securecorp-pipeline-live";

export function PipelinePanel() {
  return <SecureCorpPipelineLive />;
}
