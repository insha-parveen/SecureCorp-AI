// /dashboard — legacy route. The authenticated home is now the chat (/chat),
// so anything pointing at /dashboard is redirected there. Kept as a route so
// existing links / bookmarks don't 404.

import { redirect } from "next/navigation";

export default function DashboardPage() {
  redirect("/chat");
}
