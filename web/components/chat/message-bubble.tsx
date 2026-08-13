// One message — user or assistant. The two variants look very different
// on purpose: user messages are right-aligned and quiet, assistant
// messages are left-aligned and surface the sources panel.

"use client";

import { motion } from "motion/react";
import { StreamingAnswer } from "./streaming-answer";
import type { Message } from "@/lib/types";

export function MessageBubble({ message }: { message: Message }) {
  if (message.role === "user") {
    return (
      <motion.div
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2, ease: "easeOut" }}
        className="flex justify-end"
      >
        <div className="max-w-prose rounded-lg bg-[var(--color-accent)] px-3 py-2 text-sm">
          {message.content.text}
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2, ease: "easeOut" }}
      className="flex justify-start"
    >
      <div className="max-w-prose">
        <StreamingAnswer message={message.content} />
      </div>
    </motion.div>
  );
}
