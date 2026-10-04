"use client";
import Link from "next/link";
import { useState } from "react";
import {
  Users,
  ClipboardList,
  CheckCircle2,
  Clock3,
  Plus,
  AlertTriangle,
  BookOpen,
  TrendingUp,
  CalendarDays,
} from "lucide-react";
import { useResource } from "@/hooks/use-resource";
import { query } from "@/services/api";
import {
  dateLabel,
  Empty,
  ErrorState,
  Loading,
  PageHeading,
  ProgressBar,
  StatusBadge,
} from "@/components/ui";
import type { Course, Dashboard, Employee, Page, Track, User } from "@/types";

export function DashboardView({ user }: { user: User }) {
  const manager = user.role === "MANAGER";
  const [department, setDepartment] = useState("");
  const [employee, setEmployee] = useState(""),
    [course, setCourse] = useState(""),
    [track, setTrack] = useState(""),
    [status, setStatus] = useState(""),
    [from, setFrom] = useState(""),
    [to, setTo] = useState("");
  const employees = useResource<Page<Employee>>(
    "/employees?page_size=100",
    manager,
  );
  const courses = useResource<Page<Course>>("/courses?page_size=100", manager);
  const tracks = useResource<Page<Track>>(
    "/learning-tracks?page_size=100",
    manager,
  );
  const { data, error, loading, reload } = useResource<Dashboard>(
    (manager ? "/dashboard/manager" : "/dashboard/me") +
      query({
        department,
        employee_id: employee,
        course_id: course,
        track_id: track,
        status,
        target_from: from,
        target_to: to,
      }),
  );
  return (
    <>
      <PageHeading
        eyebrow="LEARNING OVERVIEW"
        title={
          manager
            ? "Team learning dashboard"
            : `Welcome, ${user.name.split(" ")[0]}`
        }
        description={
          manager
            ? "A shared view of progress, priorities and team development."
            : "Your next steps, achievements and learning priorities."
        }
        action={
          <Link
            className="btn"
            href={manager ? "/assignments?create=1" : "/my-learning"}
          >
            {manager ? <Plus size={17} /> : <BookOpen size={17} />}{" "}
            {manager ? "Assign learning" : "My learning"}
          </Link>
        }
      />
      {manager && (
        <section className="panel" style={{ marginBottom: 24 }}>
          <div className="filter-bar">
            <select
              aria-label="Filter employee"
              value={employee}
              onChange={(e) => setEmployee(e.target.value)}
            >
              <option value="">All employees</option>
              {employees.data?.items?.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.name}
                </option>
              ))}
            </select>
            <input
              aria-label="Filter department"
              placeholder="All departments"
              value={department}
              onChange={(e) => setDepartment(e.target.value)}
            />
            <select
              aria-label="Filter course"
              value={course}
              onChange={(e) => setCourse(e.target.value)}
            >
              <option value="">All courses</option>
              {courses.data?.items.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
            <select
              aria-label="Filter learning track"
              value={track}
              onChange={(e) => setTrack(e.target.value)}
            >
              <option value="">All tracks</option>
              {tracks.data?.items.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name}
                </option>
              ))}
            </select>
            <select
              aria-label="Filter status"
              value={status}
              onChange={(e) => setStatus(e.target.value)}
            >
              <option value="">All statuses</option>
              <option value="NOT_STARTED">Not started</option>
              <option value="ENROLLED">Enrolled</option>
              <option value="IN_PROGRESS">In progress</option>
              <option value="COMPLETED">Completed</option>
              <option value="OVERDUE">Overdue</option>
            </select>
            <label className="date-filter">
              From
              <input
                aria-label="Target date from"
                type="date"
                value={from}
                onChange={(e) => setFrom(e.target.value)}
              />
            </label>
            <label className="date-filter">
              To
              <input
                aria-label="Target date to"
                type="date"
                value={to}
                onChange={(e) => setTo(e.target.value)}
              />
            </label>
          </div>
        </section>
      )}
      {error ? (
        <ErrorState message={error} retry={reload} />
      ) : loading || !data ? (
        <Loading />
      ) : (
        <>
          <div className={"stats-grid " + (!manager ? "five" : "")}>
            {(manager
              ? [
                  {
                    label: "Active employees",
                    value: data.summary.total_employees,
                    caption: "Across your organization",
                    icon: Users,
                  },
                  {
                    label: "Learning assignments",
                    value: data.summary.total_assignments,
                    caption: `${data.summary.assigned} assigned courses`,
                    icon: ClipboardList,
                  },
                  {
                    label: "Course completion",
                    value:
                      data.summary.completion_percentage == null
                        ? "—"
                        : data.summary.completion_percentage + "%",
                    caption: `${data.summary.completed} courses completed`,
                    icon: CheckCircle2,
                    featured: true,
                  },
                  {
                    label: "Overdue learning",
                    value: data.summary.overdue,
                    caption: "Requires your attention",
                    icon: Clock3,
                  },
                ]
              : [
                  {
                    label: "Assigned courses",
                    value: data.summary.assigned,
                    caption: "Your current learning plan",
                    icon: BookOpen,
                  },
                  {
                    label: "Completed",
                    value: data.summary.completed,
                    caption: "Achievements recorded",
                    icon: CheckCircle2,
                    featured: true,
                  },
                  {
                    label: "In progress",
                    value: data.summary.in_progress,
                    caption: `${data.summary.enrolled} additional courses enrolled`,
                    icon: TrendingUp,
                  },
                  {
                    label: "Pending",
                    value: data.summary.pending,
                    caption: "Ready for your next step",
                    icon: ClipboardList,
                  },
                  {
                    label: "Overdue",
                    value: data.summary.overdue,
                    caption: "Learning needing attention",
                    icon: Clock3,
                  },
                ]
            ).map((s) => (
              <div
                key={s.label}
                className={
                  "stat-card " +
                  ("featured" in s && s.featured ? "featured" : "")
                }
              >
                <div className="stat-top">
                  <span>{s.label}</span>
                  <span className="stat-icon">
                    <s.icon size={18} />
                  </span>
                </div>
                <div className="stat-number">{s.value}</div>
                <div className="stat-caption">{s.caption}</div>
              </div>
            ))}
          </div>
          <div className="dashboard-grid">
            <section className="panel">
              <div className="panel-heading">
                <div>
                  <h2>Learning status</h2>
                  <p>Assigned courses · overdue overlaps status</p>
                </div>
                <span className="count-chip">
                  {data.summary.assigned} courses
                </span>
              </div>
              <Distribution data={data} />
            </section>
            <section className="panel">
              <div className="panel-heading">
                <div>
                  <h2>Upcoming target dates</h2>
                  <p>Keep the next milestones in view</p>
                </div>
                <CalendarDays size={19} className="muted" />
              </div>
              <div className="panel-body">
                {data.upcoming.length ? (
                  data.upcoming.slice(0, 3).map((a) => (
                    <Link
                      href={"/my-learning/" + a.id}
                      key={a.id}
                      className="deadline-item"
                    >
                      <div className="date-tile">
                        {new Date(
                          a.target_date + "T12:00:00",
                        ).toLocaleDateString("en", { month: "short" })}
                        <strong>
                          {new Date(a.target_date + "T12:00:00").getDate()}
                        </strong>
                      </div>
                      <div className="deadline-info">
                        <strong>{a.course.name}</strong>
                        <small>
                          {manager
                            ? a.employee_name
                            : a.course.provider || "Assigned learning"}
                        </small>
                      </div>
                      <StatusBadge status={a.status} />
                    </Link>
                  ))
                ) : (
                  <Empty
                    title="No upcoming deadlines"
                    detail="Assignments with target dates will appear here."
                  />
                )}
              </div>
            </section>
          </div>
          {manager && (
            <section className="panel" style={{ marginBottom: 24 }}>
              <div className="panel-heading">
                <div>
                  <h2>
                    Team progress
                    <span className="count-chip">
                      {data.employees.length} employees
                    </span>
                  </h2>
                  <p>Completion and outstanding learning by employee</p>
                </div>
                <Link className="text-btn" href="/employees">
                  View employees
                </Link>
              </div>
              {data.employees.length ? (
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Employee</th>
                        <th>Assigned</th>
                        <th>Completed</th>
                        <th>In progress</th>
                        <th>Pending</th>
                        <th>Overdue</th>
                        <th>Completion</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.employees.map((e) => (
                        <tr key={e.employee_id}>
                          <td>
                            <Link
                              href={"/employees/" + e.employee_id}
                              className="person-cell"
                            >
                              <span className="avatar">
                                {e.name
                                  .split(" ")
                                  .map((w) => w[0])
                                  .slice(0, 2)
                                  .join("")}
                              </span>
                              <span>
                                <strong className="cell-title">{e.name}</strong>
                                <span className="cell-subtitle">
                                  {e.department || "No department"}
                                </span>
                              </span>
                            </Link>
                          </td>
                          <td>{e.assigned}</td>
                          <td>{e.completed}</td>
                          <td>
                            {e.in_progress}
                            <span className="cell-subtitle">
                              {e.enrolled} enrolled
                            </span>
                          </td>
                          <td>{e.pending}</td>
                          <td>
                            {e.overdue ? (
                              <span className="badge status-overdue">
                                {e.overdue} overdue
                              </span>
                            ) : (
                              "—"
                            )}
                          </td>
                          <td>
                            <ProgressBar value={e.completion_percentage} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <Empty
                  title="Your team starts here"
                  detail="Create employee accounts, then assign their first learning plan."
                />
              )}
            </section>
          )}
          <div className="dashboard-grid">
            <section className="panel">
              <div className="panel-heading">
                <div>
                  <h2>
                    {manager
                      ? "Development priorities"
                      : "Learning needing attention"}
                  </h2>
                  <p>
                    {manager
                      ? "Courses with outstanding team learning"
                      : "Start with your overdue courses"}
                  </p>
                </div>
                <TrendingUp size={19} className="muted" />
              </div>
              <div className="panel-body">
                {manager ? (
                  data.capability_gaps.length ? (
                    <div className="attention-list">
                      {data.capability_gaps.slice(0, 5).map((c) => (
                        <div className="attention-item" key={c.course_id}>
                          <div>
                            <h3>{c.name}</h3>
                            <p>
                              {c.assigned - c.completed} outstanding ·{" "}
                              {c.overdue} overdue
                            </p>
                          </div>
                          <ProgressBar value={c.completion_percentage} />
                        </div>
                      ))}
                    </div>
                  ) : (
                    <Empty title="No outstanding course requirements" />
                  )
                ) : data.overdue.length ? (
                  data.overdue.slice(0, 5).map((a) => (
                    <Link
                      className="deadline-item"
                      key={a.id}
                      href={"/my-learning/" + a.id}
                    >
                      <AlertTriangle size={20} color="#ba6b40" />
                      <div className="deadline-info">
                        <strong>{a.course.name}</strong>
                        <small>Due {dateLabel(a.target_date)}</small>
                      </div>
                      <span className="badge status-overdue">Overdue</span>
                    </Link>
                  ))
                ) : (
                  <Empty
                    title="You’re up to date"
                    detail="No assigned courses are overdue."
                  />
                )}
              </div>
              {manager && (
                <div className="panel-note">
                  Outstanding learning indicates development work to follow up.
                </div>
              )}
            </section>
            <section className="panel">
              <div className="panel-heading">
                <div>
                  <h2>
                    {manager ? "Priority overdue learning" : "Course progress"}
                  </h2>
                  <p>
                    {manager
                      ? "Mandatory learning requiring follow-up"
                      : "Your completion across assigned courses"}
                  </p>
                </div>
                <Link
                  className="text-btn"
                  href={
                    manager ? "/assignments?status=OVERDUE" : "/my-learning"
                  }
                >
                  View all
                </Link>
              </div>
              <div className="panel-body">
                {manager ? (
                  data.priority_development.length ? (
                    data.priority_development.slice(0, 4).map((a) => (
                      <Link
                        key={a.id}
                        className="deadline-item"
                        href={"/my-learning/" + a.id}
                      >
                        <span className="avatar small">
                          {a.employee_name[0]}
                        </span>
                        <div className="deadline-info">
                          <strong>{a.employee_name}</strong>
                          <small>
                            {a.course.name} · {dateLabel(a.target_date)}
                          </small>
                        </div>
                        <span className="badge status-overdue">Overdue</span>
                      </Link>
                    ))
                  ) : (
                    <Empty title="No mandatory learning overdue" />
                  )
                ) : (
                  <div className="attention-list">
                    {data.courses.length ? (
                      data.courses.map((c) => (
                        <div className="attention-item" key={c.course_id}>
                          <h3>{c.name}</h3>
                          <ProgressBar value={c.completion_percentage} />
                        </div>
                      ))
                    ) : (
                      <Empty
                        title="Your learning plan is empty"
                        detail="Your manager will assign courses and tracks."
                      />
                    )}
                  </div>
                )}
              </div>
            </section>
          </div>
        </>
      )}
    </>
  );
}
function Distribution({ data }: { data: Dashboard }) {
  const s = data.summary,
    total = s.assigned || 1;
  const values = [
    { name: "Completed", value: s.completed, color: "#4F2D7F" },
    { name: "In progress", value: s.in_progress, color: "#9e82c0" },
    { name: "Enrolled", value: s.enrolled, color: "#bbb0cd" },
    { name: "Pending", value: s.pending, color: "#DEDAD6" },
  ];
  let offset = 0;
  const stops = values.map((v) => {
    const start = offset;
    offset += (v.value / total) * 100;
    return `${v.color} ${start}% ${offset}%`;
  });
  return (
    <div className="distribution">
      <div
        className="donut"
        role="img"
        aria-label={values.map((v) => `${v.name}: ${v.value}`).join(", ")}
        style={{
          background: s.assigned
            ? `conic-gradient(${stops.join(",")})`
            : "#DEDAD6",
        }}
      >
        <div className="donut-hole">
          <strong>
            {s.completion_percentage == null
              ? "—"
              : s.completion_percentage + "%"}
          </strong>
          <span>completion rate</span>
        </div>
      </div>
      <div className="chart-legend">
        {values.map((v) => (
          <div className="legend-row" key={v.name}>
            <span className="legend-dot" style={{ background: v.color }} />
            {v.name}
            <strong>{v.value}</strong>
          </div>
        ))}
        <div
          className="legend-row"
          style={{ borderTop: "1px solid var(--border)", paddingTop: 12 }}
        >
          <span className="legend-dot" style={{ background: "#e5ae87" }} />
          Overdue<strong>{s.overdue}</strong>
        </div>
      </div>
    </div>
  );
}
