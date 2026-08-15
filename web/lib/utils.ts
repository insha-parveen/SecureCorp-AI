// Tailwind class-name combiner. Tiny on purpose — we don't pull in
// `tailwind-variants` for one helper.

import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
