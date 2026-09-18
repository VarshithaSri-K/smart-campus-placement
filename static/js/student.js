document.addEventListener("DOMContentLoaded", async () => {
  setupTabs();
  await loadBranchOptions();
  await loadProfile();
  loadRecommendations();
  loadApplications();

  document.getElementById("profile-form").addEventListener("submit", saveProfile);
  document.getElementById("skill-form").addEventListener("submit", addSkill);
});

function setupTabs() {
  const buttons = document.querySelectorAll(".tab-btn");
  buttons.forEach((btn) => {
    btn.addEventListener("click", () => {
      buttons.forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById(`panel-${btn.dataset.tab}`).classList.add("active");
    });
  });
}

async function loadBranchOptions() {
  try {
    const data = await apiFetch("/api/auth/branches");
    document.getElementById("p-branch").innerHTML = data.branches
      .map((b) => `<option value="${b}">${b}</option>`).join("");
  } catch (e) { /* ignore */ }
}

async function loadProfile() {
  try {
    const s = await apiFetch("/api/students/me");
    document.getElementById("p-name").value = s.name || "";
    document.getElementById("p-cgpa").value = s.cgpa ?? "";
    document.getElementById("p-backlogs").value = s.backlogs ?? 0;
    document.getElementById("p-phone").value = s.phone || "";
    document.getElementById("p-resume").value = s.resume_link || "";
    document.getElementById("p-branch").value = s.branch;
    renderSkills(s.skills || []);
  } catch (err) {
    showAlert(err.message);
  }
}

function renderSkills(skills) {
  const levelLabel = { 1: "Beginner", 2: "Intermediate", 3: "Advanced" };
  const container = document.getElementById("skills-list");
  if (!skills.length) {
    container.innerHTML = `<p class="muted">No skills added yet. Add skills to get better job matches.</p>`;
    return;
  }
  container.innerHTML = skills.map((s) => `
    <span class="skill-chip">
      ${escapeHtml(s.name)} · ${levelLabel[s.proficiency] || ""}
      <button data-skill="${escapeHtml(s.name)}" class="remove-skill-btn">&times;</button>
    </span>
  `).join("");
  container.querySelectorAll(".remove-skill-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      try {
        await apiFetch(`/api/students/me/skills/${encodeURIComponent(btn.dataset.skill)}`, { method: "DELETE" });
        loadProfile();
        loadRecommendations();
      } catch (err) {
        showAlert(err.message);
      }
    });
  });
}

async function saveProfile(e) {
  e.preventDefault();
  const payload = {
    name: document.getElementById("p-name").value.trim(),
    branch: document.getElementById("p-branch").value,
    cgpa: document.getElementById("p-cgpa").value,
    backlogs: document.getElementById("p-backlogs").value,
    phone: document.getElementById("p-phone").value.trim(),
    resume_link: document.getElementById("p-resume").value.trim(),
  };
  try {
    await apiFetch("/api/students/me", { method: "PUT", body: JSON.stringify(payload) });
    showAlert("Profile updated successfully", "success");
    loadRecommendations();
  } catch (err) {
    showAlert(err.message);
  }
}

async function addSkill(e) {
  e.preventDefault();
  const name = document.getElementById("skill-name").value.trim();
  const proficiency = document.getElementById("skill-level").value;
  if (!name) return;
  try {
    await apiFetch("/api/students/me/skills", {
      method: "POST",
      body: JSON.stringify({ name, proficiency }),
    });
    document.getElementById("skill-name").value = "";
    loadProfile();
    loadRecommendations();
  } catch (err) {
    showAlert(err.message);
  }
}

async function loadRecommendations() {
  const container = document.getElementById("recommend-list");
  try {
    const data = await apiFetch("/api/jobs/recommendations");
    if (!data.recommendations.length) {
      container.innerHTML = `<div class="empty-state">No open jobs to recommend right now. Check back soon.</div>`;
      return;
    }
    container.innerHTML = data.recommendations.map((r) => jobCardHtml(r.job, r.match_score, r.eligible, r.eligibility_reason)).join("");
    attachApplyHandlers(container);
  } catch (err) {
    container.innerHTML = `<div class="empty-state">Could not load recommendations.</div>`;
  }
}

async function loadApplications() {
  const container = document.getElementById("applications-list");
  try {
    const data = await apiFetch("/api/applications/me");
    if (!data.applications.length) {
      container.innerHTML = `<div class="empty-state">You haven't applied to any jobs yet.</div>`;
      return;
    }
    container.innerHTML = data.applications.map((a) => `
      <div class="job-card">
        <div class="top-row">
          <div>
            <h3>${escapeHtml(a.job.title)}</h3>
            <div class="company">${escapeHtml(a.job.company_name)} · ${escapeHtml(a.job.location || "")}</div>
          </div>
          <span class="status-pill status-${a.status}">${a.status}</span>
        </div>
        <div class="meta">
          <span class="tag">Match score: ${a.match_score}%</span>
          <span class="tag">Applied ${fmtDate(a.applied_at)}</span>
        </div>
        <div class="actions">
          ${a.status === "Applied" ? `<button class="btn btn-danger btn-sm" data-id="${a.id}" onclick="withdrawApplication(${a.id})">Withdraw</button>` : ""}
        </div>
      </div>
    `).join("");
  } catch (err) {
    container.innerHTML = `<div class="empty-state">Could not load applications.</div>`;
  }
}

async function withdrawApplication(id) {
  if (!confirm("Withdraw this application?")) return;
  try {
    await apiFetch(`/api/applications/${id}`, { method: "DELETE" });
    loadApplications();
    loadRecommendations();
  } catch (err) {
    showAlert(err.message);
  }
}

function jobCardHtml(job, score, eligible, reason) {
  const color = scoreColor(score);
  return `
    <div class="job-card">
      <div class="top-row">
        <div>
          <h3>${escapeHtml(job.title)}</h3>
          <div class="company">${escapeHtml(job.company_name)} · ${escapeHtml(job.location || "")}</div>
        </div>
        <div class="score-badge">${score}% match</div>
      </div>
      <div class="meta">
        <span class="tag">${escapeHtml(job.job_type)}</span>
        ${job.package_lpa ? `<span class="tag">${job.package_lpa} LPA</span>` : ""}
        <span class="tag ${color}">${eligible ? "Eligible" : "Not eligible"}</span>
        <span class="tag">Deadline: ${fmtDate(job.deadline)}</span>
      </div>
      <p class="desc">${escapeHtml((job.description || "").slice(0, 180))}${(job.description || "").length > 180 ? "…" : ""}</p>
      <div class="actions">
        <button class="btn ${eligible ? "btn-primary" : "btn-secondary"} btn-sm apply-btn" data-job="${job.id}" ${eligible ? "" : "disabled"}>
          ${eligible ? "Apply Now" : "Not Eligible"}
        </button>
        ${!eligible ? `<span class="muted">${escapeHtml(reason || "")}</span>` : ""}
      </div>
    </div>
  `;
}

function attachApplyHandlers(container) {
  container.querySelectorAll(".apply-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      try {
        await apiFetch(`/api/applications/jobs/${btn.dataset.job}`, { method: "POST" });
        showAlert("Application submitted successfully!", "success");
        loadRecommendations();
        loadApplications();
      } catch (err) {
        showAlert(err.message);
      }
    });
  });
}
