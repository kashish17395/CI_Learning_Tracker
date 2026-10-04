"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  BookOpen,
  ShieldCheck,
  Layers3,
  TrendingUp,
  Award,
  Eye,
  EyeOff,
} from "lucide-react";
import { post } from "@/services/api";
import { ErrorState, Field } from "@/components/ui";
export default function LoginPage() {
  const router = useRouter();
  const [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [visible, setVisible] = useState(false),
    [ready, setReady] = useState(false);
  useEffect(() => setReady(true), []);
  return (
    <div className="login-page">
      <section className="login-story">
        <div className="login-brand">
          <BookOpen size={30} />
          learning space
        </div>
        <div className="login-story-content">
          <div className="eyebrow">LEARNING & DEVELOPMENT</div>
          <h1>
            A clearer path
            <br />
            to what’s next.
          </h1>
          <p>
            Bring learning plans, team progress and completion evidence into one
            shared workspace.
          </p>
          <div className="login-features">
            <div>
              <Layers3 />
              <span>Structured learning tracks</span>
            </div>
            <div>
              <TrendingUp />
              <span>Progress you can see</span>
            </div>
            <div>
              <Award />
              <span>Every achievement recorded</span>
            </div>
          </div>
        </div>
        <div className="login-foot">
          Build capability, one course at a time.
        </div>
      </section>
      <section className="login-form-side">
        <div className="login-form">
          <span className="login-emblem">
            <BookOpen size={27} />
          </span>
          <h2>Welcome back</h2>
          <p className="muted">Sign in to your learning workspace.</p>
          <form
            method="post"
            action="/api/v1/auth/login"
            onSubmit={async (e) => {
              e.preventDefault();
              if (!ready) return;
              setBusy(true);
              setError("");
              const f = new FormData(e.currentTarget);
              try {
                await post("/auth/login", {
                  email: f.get("email"),
                  password: f.get("password"),
                });
                router.replace("/dashboard");
                router.refresh();
              } catch (err) {
                setError((err as Error).message);
              } finally {
                setBusy(false);
              }
            }}
          >
            <Field label="Work email">
              <input
                name="email"
                type="email"
                placeholder="you@company.com"
                autoComplete="username"
                required
                maxLength={254}
              />
            </Field>
            <Field label="Password">
              <div className="password-input">
                <input
                  name="password"
                  type={visible ? "text" : "password"}
                  placeholder="Enter your password"
                  autoComplete="current-password"
                  required
                  maxLength={256}
                />
                <button
                  type="button"
                  aria-label={visible ? "Hide password" : "Show password"}
                  onClick={() => setVisible((v) => !v)}
                >
                  {visible ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </Field>
            {error && <ErrorState message={error} />}
            <button className="btn login-submit" disabled={busy || !ready}>
              {busy ? "Signing in…" : "Sign in"}
            </button>
          </form>
          <div className="login-help">
            <ShieldCheck size={17} />
            <span>
              Access is managed by your organization.
              <br />
              Contact your manager if you need an account.
            </span>
          </div>
        </div>
        <small className="login-copyright">
          Learning Tracker · Internal company portal
        </small>
      </section>
    </div>
  );
}
