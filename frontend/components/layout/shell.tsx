"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";
import {
  BookOpen,
  LayoutDashboard,
  Users,
  Library,
  Route,
  ClipboardList,
  Award,
  LogOut,
  Menu,
  X,
  ChevronRight,
  ShieldCheck,
  History,
} from "lucide-react";
import { api } from "@/services/api";
import { ToastProvider } from "@/components/ui";
import type { User } from "@/types";
import type { ReactNode } from "react";

const managerNav = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/employees", label: "Employees", icon: Users },
  { href: "/courses", label: "Courses", icon: Library },
  { href: "/learning-tracks", label: "Learning tracks", icon: Route },
  { href: "/assignments", label: "Assignments", icon: ClipboardList },
  { href: "/certificates", label: "Certificates", icon: Award },
  { href: "/audit", label: "Audit history", icon: History },
];
const employeeNav = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/my-learning", label: "My learning", icon: BookOpen },
  { href: "/certificates", label: "Certificates", icon: Award },
];

export function Shell({ user, children }: { user: User; children: ReactNode }) {
  const path = usePathname(),
    router = useRouter();
  const [open, setOpen] = useState(false);
  const [error, setError] = useState("");
  const nav = user.role === "MANAGER" ? managerNav : employeeNav;
  const active = nav.find((n) => path.startsWith(n.href));
  return (
    <ToastProvider>
      <div className="app-shell">
        <aside className={"sidebar " + (open ? "sidebar-open" : "")}>
          <Link href="/dashboard" className="brand">
            <span className="brand-icon">
              <BookOpen size={23} />
            </span>
            <span>
              learning<span className="brand-suffix">space</span>
              <small>PEOPLE & DEVELOPMENT</small>
            </span>
          </Link>
          <button
            className="mobile-close icon-btn"
            aria-label="Close navigation"
            onClick={() => setOpen(false)}
          >
            <X />
          </button>
          <div className="nav-label">WORKSPACE</div>
          <nav aria-label="Main navigation">
            {nav.map((n) => (
              <Link
                key={n.href}
                href={n.href}
                onClick={() => setOpen(false)}
                className={path.startsWith(n.href) ? "active" : ""}
                aria-current={path.startsWith(n.href) ? "page" : undefined}
              >
                <n.icon size={19} />
                {n.label}
                {path.startsWith(n.href) && (
                  <ChevronRight size={16} className="nav-chevron" />
                )}
              </Link>
            ))}
          </nav>
          <div className="sidebar-bottom">
            <div className="access-card">
              <ShieldCheck size={19} />
              <div>
                {user.role === "MANAGER"
                  ? "Manager workspace"
                  : "Employee workspace"}
                <small>Learning & development</small>
              </div>
            </div>
            <div className="user-card">
              <span className="avatar">
                {user.name
                  .split(" ")
                  .map((n) => n[0])
                  .slice(0, 2)
                  .join("")}
              </span>
              <div>
                <strong>{user.name}</strong>
                <small>{user.email}</small>
              </div>
            </div>
            <button
              className="logout"
              onClick={async () => {
                try {
                  await api("/auth/logout", { method: "POST" });
                  router.replace("/login");
                  router.refresh();
                } catch (e) {
                  setError((e as Error).message);
                }
              }}
            >
              <LogOut size={17} />
              Sign out
            </button>
            {error && <small role="alert">{error}</small>}
          </div>
        </aside>
        {open && (
          <button
            className="sidebar-overlay"
            aria-label="Close navigation"
            onClick={() => setOpen(false)}
          />
        )}
        <div className="main-shell">
          <header className="topbar">
            <div className="breadcrumb">
              <button
                className="mobile-menu icon-btn"
                aria-label="Open navigation"
                onClick={() => setOpen(true)}
              >
                <Menu />
              </button>
              <span>Workspace</span>
              <ChevronRight size={14} />
              <strong>{active?.label || "Learning details"}</strong>
            </div>
            <div className="topbar-right">
              <span className="role-chip">
                {user.role === "MANAGER" ? "Manager" : "Employee"}
              </span>
              <span className="avatar small">{user.name[0]}</span>
            </div>
          </header>
          <main className="main-content">{children}</main>
          <footer className="footer">
            Learning space <span>Build capability. Track progress.</span>
          </footer>
        </div>
      </div>
    </ToastProvider>
  );
}
