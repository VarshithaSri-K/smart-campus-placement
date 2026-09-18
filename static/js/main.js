// ---------- Shared helpers used across all pages ----------

async function apiFetch(url, options = {}) {
  const opts = Object.assign({ credentials: "same-origin" }, options);
  opts.headers = Object.assign({ "Content-Type": "application/json" }, options.headers || {});
  const res = await fetch(url, opts);
  let data = null;
  try { data = await res.json(); } catch (e) { /* no body */ }
  if (!res.ok) {
    const err = new Error((data && data.error) || `Request failed (${res.status})`);
    err.status = res.status;
    err.data = data;
    throw err;
  }
  return data;
}

function showAlert(message, type = "error") {
  const box = document.getElementById("alert-box");
  if (!box) { alert(message); return; }
  box.innerHTML = `<div class="alert alert-${type === "error" ? "error" : "success"}">${escapeHtml(message)}</div>`;
  window.scrollTo({ top: 0, behavior: "smooth" });
  setTimeout(() => { box.innerHTML = ""; }, 5000);
}

function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}

function fmtDate(iso) {
  if (!iso) return "No deadline";
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

function scoreColor(score) {
  if (score >= 75) return "green";
  if (score >= 50) return "orange";
  return "red";
}

// ---------- Nav bar ----------
async function renderNav() {
  const nav = document.getElementById("nav-links");
  if (!nav) return;
  try {
    const me = await apiFetch("/api/auth/me");
    if (!me.authenticated) {
      nav.innerHTML = `<a href="/login">Sign In</a><a href="/register">Register</a>`;
      return;
    }
    if (me.user.role === "admin") {
      nav.innerHTML = `
        <a href="/admin">Dashboard</a>
        <a href="/jobs">Browse Jobs</a>
        <span class="muted" style="margin-left:16px">${escapeHtml(me.user.name)}</span>
        <a href="#" id="logout-link">Logout</a>`;
    } else {
      nav.innerHTML = `
        <a href="/dashboard">Dashboard</a>
        <a href="/jobs">Browse Jobs</a>
        <span class="muted" style="margin-left:16px">${escapeHtml(me.user.name)}</span>
        <a href="#" id="logout-link">Logout</a>`;
    }
    const logoutLink = document.getElementById("logout-link");
    if (logoutLink) {
      logoutLink.addEventListener("click", async (e) => {
        e.preventDefault();
        await apiFetch("/api/auth/logout", { method: "POST" });
        window.location.href = "/";
      });
    }
  } catch (e) {
    nav.innerHTML = `<a href="/login">Sign In</a><a href="/register">Register</a>`;
  }
}

document.addEventListener("DOMContentLoaded", renderNav);
