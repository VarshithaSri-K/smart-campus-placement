document.addEventListener("DOMContentLoaded", loadAllJobs);

async function loadAllJobs() {
  const container = document.getElementById("jobs-list");
  try {
    const me = await apiFetch("/api/auth/me");
    const isStudent = me.authenticated && me.user.role === "student";
    const data = await apiFetch("/api/jobs?status=open");
    if (!data.jobs.length) {
      container.innerHTML = `<div class="empty-state">No open positions at the moment.</div>`;
      return;
    }
    container.innerHTML = data.jobs.map((job) => renderJobCard(job, isStudent)).join("");
    if (isStudent) {
      container.querySelectorAll(".apply-btn").forEach((btn) => {
        btn.addEventListener("click", async () => {
          try {
            await apiFetch(`/api/applications/jobs/${btn.dataset.job}`, { method: "POST" });
            showAlert("Application submitted successfully!", "success");
            loadAllJobs();
          } catch (err) {
            showAlert(err.message);
          }
        });
      });
    }
  } catch (err) {
    container.innerHTML = `<div class="empty-state">Could not load job listings.</div>`;
  }
}

function renderJobCard(job, isStudent) {
  const scoreBadge = isStudent && job.match_score !== undefined
    ? `<div class="score-badge">${job.match_score}% match</div>` : "";
  const applyBtn = isStudent
    ? `<button class="btn ${job.eligible ? "btn-primary" : "btn-secondary"} btn-sm apply-btn" data-job="${job.id}" ${job.eligible ? "" : "disabled"}>
         ${job.eligible ? "Apply Now" : "Not Eligible"}
       </button>${!job.eligible ? `<span class="muted">${escapeHtml(job.eligibility_reason || "")}</span>` : ""}`
    : "";
  const branches = job.allowed_branches ? job.allowed_branches.split(",").map(b => b.trim()).filter(Boolean) : [];
  const skills = job.required_skills ? job.required_skills.split(",").map(s => s.trim()).filter(Boolean) : [];

  return `
    <div class="job-card">
      <div class="top-row">
        <div>
          <h3>${escapeHtml(job.title)}</h3>
          <div class="company">${escapeHtml(job.company_name)} · ${escapeHtml(job.location || "")}</div>
        </div>
        ${scoreBadge}
      </div>
      <div class="meta">
        <span class="tag">${escapeHtml(job.job_type)}</span>
        ${job.package_lpa ? `<span class="tag">${job.package_lpa} LPA</span>` : ""}
        <span class="tag">Min CGPA: ${job.min_cgpa}</span>
        <span class="tag">Deadline: ${fmtDate(job.deadline)}</span>
        ${branches.length ? `<span class="tag">${branches.join(", ")}</span>` : `<span class="tag">All branches</span>`}
      </div>
      ${skills.length ? `<div class="meta">${skills.map(s => `<span class="tag orange">${escapeHtml(s)}</span>`).join("")}</div>` : ""}
      <p class="desc">${escapeHtml(job.description || "")}</p>
      <div class="actions">${applyBtn}</div>
    </div>
  `;
}
