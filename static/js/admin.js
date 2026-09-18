document.addEventListener("DOMContentLoaded", () => {
  setupTabs();
  loadStats();
  loadAdminJobs();
  loadStudents();
  setupJobModal();
  setupCandidatesModal();

  document.getElementById("app-job-filter").addEventListener("change", loadApplications);
  document.getElementById("app-status-filter").addEventListener("change", loadApplications);
});

function setupTabs() {
  const buttons = document.querySelectorAll(".tab-btn");
  buttons.forEach((btn) => {
    btn.addEventListener("click", () => {
      buttons.forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById(`panel-${btn.dataset.tab}`).classList.add("active");
      if (btn.dataset.tab === "applications") loadApplications();
    });
  });
}

async function loadStats() {
  try {
    const s = await apiFetch("/api/admin/stats");
    const grid = document.getElementById("stats-grid");
    grid.innerHTML = `
      ${statBox(s.total_students, "Students")}
      ${statBox(s.total_jobs, "Job Postings")}
      ${statBox(s.open_jobs, "Open Jobs")}
      ${statBox(s.total_applications, "Applications")}
      ${statBox(s.selected, "Selected")}
    `;
  } catch (err) {
    showAlert(err.message);
  }
}
function statBox(num, label) {
  return `<div class="stat-box"><div class="num">${num}</div><div class="label">${label}</div></div>`;
}

// ---------- Job Postings ----------

async function loadAdminJobs() {
  const container = document.getElementById("admin-jobs-list");
  const filterSelect = document.getElementById("app-job-filter");
  try {
    const data = await apiFetch("/api/jobs?status=all");
    if (!data.jobs.length) {
      container.innerHTML = `<div class="empty-state">No jobs posted yet. Click "New Job Posting" to add one.</div>`;
    } else {
      container.innerHTML = data.jobs.map(adminJobCardHtml).join("");
      attachJobActionHandlers(container);
    }
    filterSelect.innerHTML = `<option value="">All jobs</option>` +
      data.jobs.map((j) => `<option value="${j.id}">${escapeHtml(j.title)} - ${escapeHtml(j.company_name)}</option>`).join("");
  } catch (err) {
    container.innerHTML = `<div class="empty-state">Could not load jobs.</div>`;
  }
}

function adminJobCardHtml(job) {
  const statusTag = job.status === "open" ? `<span class="tag green">Open</span>` : `<span class="tag red">Closed</span>`;
  return `
    <div class="job-card">
      <div class="top-row">
        <div>
          <h3>${escapeHtml(job.title)}</h3>
          <div class="company">${escapeHtml(job.company_name)} · ${escapeHtml(job.location || "")}</div>
        </div>
        ${statusTag}
      </div>
      <div class="meta">
        <span class="tag">${escapeHtml(job.job_type)}</span>
        ${job.package_lpa ? `<span class="tag">${job.package_lpa} LPA</span>` : ""}
        <span class="tag">Min CGPA ${job.min_cgpa}</span>
        <span class="tag">Deadline: ${fmtDate(job.deadline)}</span>
      </div>
      <div class="actions">
        <button class="btn btn-secondary btn-sm view-candidates-btn" data-id="${job.id}" data-title="${escapeHtml(job.title)}">View Ranked Candidates</button>
        <button class="btn btn-secondary btn-sm toggle-status-btn" data-id="${job.id}" data-status="${job.status}">
          ${job.status === "open" ? "Close Job" : "Reopen Job"}
        </button>
        <button class="btn btn-danger btn-sm delete-job-btn" data-id="${job.id}">Delete</button>
      </div>
    </div>
  `;
}

function attachJobActionHandlers(container) {
  container.querySelectorAll(".toggle-status-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const newStatus = btn.dataset.status === "open" ? "closed" : "open";
      try {
        await apiFetch(`/api/jobs/${btn.dataset.id}`, { method: "PUT", body: JSON.stringify({ status: newStatus }) });
        loadAdminJobs();
        loadStats();
      } catch (err) { showAlert(err.message); }
    });
  });
  container.querySelectorAll(".delete-job-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      if (!confirm("Delete this job posting? This also removes its applications.")) return;
      try {
        await apiFetch(`/api/jobs/${btn.dataset.id}`, { method: "DELETE" });
        loadAdminJobs();
        loadStats();
      } catch (err) { showAlert(err.message); }
    });
  });
  container.querySelectorAll(".view-candidates-btn").forEach((btn) => {
    btn.addEventListener("click", () => openCandidatesModal(btn.dataset.id, btn.dataset.title));
  });
}

function setupJobModal() {
  const overlay = document.getElementById("job-modal-overlay");
  document.getElementById("new-job-btn").addEventListener("click", () => overlay.classList.add("open"));
  document.getElementById("job-modal-close").addEventListener("click", () => overlay.classList.remove("open"));
  overlay.addEventListener("click", (e) => { if (e.target === overlay) overlay.classList.remove("open"); });

  document.getElementById("job-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = {
      title: document.getElementById("j-title").value.trim(),
      company_name: document.getElementById("j-company").value.trim(),
      job_type: document.getElementById("j-type").value,
      location: document.getElementById("j-location").value.trim(),
      package_lpa: document.getElementById("j-package").value || null,
      deadline: document.getElementById("j-deadline").value || null,
      min_cgpa: document.getElementById("j-mincgpa").value || 0,
      max_backlogs: document.getElementById("j-maxbacklogs").value || 0,
      allowed_branches: document.getElementById("j-branches").value.split(",").map(s => s.trim()).filter(Boolean),
      required_skills: document.getElementById("j-skills").value.split(",").map(s => s.trim()).filter(Boolean),
      description: document.getElementById("j-description").value.trim(),
    };
    try {
      await apiFetch("/api/jobs", { method: "POST", body: JSON.stringify(payload) });
      overlay.classList.remove("open");
      e.target.reset();
      showAlert("Job posted successfully", "success");
      loadAdminJobs();
      loadStats();
    } catch (err) {
      showAlert(err.message);
    }
  });
}

// ---------- Candidate ranking modal ----------

function setupCandidatesModal() {
  const overlay = document.getElementById("candidates-modal-overlay");
  document.getElementById("candidates-modal-close").addEventListener("click", () => overlay.classList.remove("open"));
  overlay.addEventListener("click", (e) => { if (e.target === overlay) overlay.classList.remove("open"); });
}

async function openCandidatesModal(jobId, title) {
  const overlay = document.getElementById("candidates-modal-overlay");
  document.getElementById("candidates-modal-title").textContent = `Ranked Candidates — ${title}`;
  const list = document.getElementById("candidates-list");
  list.innerHTML = `<p class="muted">Loading...</p>`;
  overlay.classList.add("open");
  try {
    const data = await apiFetch(`/api/jobs/${jobId}/candidates`);
    if (!data.candidates.length) {
      list.innerHTML = `<div class="empty-state">No students in the system yet.</div>`;
      return;
    }
    list.innerHTML = `<table><thead><tr><th>Rank</th><th>Student</th><th>Branch</th><th>CGPA</th><th>Score</th><th>Eligible</th></tr></thead><tbody>` +
      data.candidates.map((c, i) => `
        <tr>
          <td>${i + 1}</td>
          <td>${escapeHtml(c.student.name)} <div class="muted">${escapeHtml(c.student.roll_no)}</div></td>
          <td>${escapeHtml(c.student.branch)}</td>
          <td>${c.student.cgpa}</td>
          <td><strong>${c.match_score}%</strong></td>
          <td>${c.eligible ? '<span class="tag green">Yes</span>' : `<span class="tag red">No</span>`}</td>
        </tr>
      `).join("") + `</tbody></table>`;
  } catch (err) {
    list.innerHTML = `<div class="empty-state">Could not load candidates.</div>`;
  }
}

// ---------- Applications ----------

async function loadApplications() {
  const container = document.getElementById("admin-applications-list");
  const jobId = document.getElementById("app-job-filter").value;
  const status = document.getElementById("app-status-filter").value;
  const params = new URLSearchParams();
  if (jobId) params.set("job_id", jobId);
  if (status) params.set("status", status);
  try {
    const data = await apiFetch(`/api/applications?${params.toString()}`);
    if (!data.applications.length) {
      container.innerHTML = `<div class="empty-state">No applications match this filter.</div>`;
      return;
    }
    container.innerHTML = `<table><thead><tr><th>Student</th><th>Job</th><th>Score</th><th>Status</th><th></th></tr></thead><tbody>` +
      data.applications.map((a) => `
        <tr>
          <td>${escapeHtml(a.student.name)}<div class="muted">${escapeHtml(a.student.roll_no)}</div></td>
          <td>${escapeHtml(a.job.title)}<div class="muted">${escapeHtml(a.job.company_name)}</div></td>
          <td><strong>${a.match_score}%</strong></td>
          <td><span class="status-pill status-${a.status}">${a.status}</span></td>
          <td>
            <select data-id="${a.id}" class="status-select">
              <option ${a.status === "Applied" ? "selected" : ""}>Applied</option>
              <option ${a.status === "Shortlisted" ? "selected" : ""}>Shortlisted</option>
              <option ${a.status === "Interview" ? "selected" : ""}>Interview</option>
              <option ${a.status === "Rejected" ? "selected" : ""}>Rejected</option>
              <option ${a.status === "Selected" ? "selected" : ""}>Selected</option>
            </select>
          </td>
        </tr>
      `).join("") + `</tbody></table>`;

    container.querySelectorAll(".status-select").forEach((sel) => {
      sel.addEventListener("change", async () => {
        try {
          await apiFetch(`/api/applications/${sel.dataset.id}/status`, {
            method: "PUT",
            body: JSON.stringify({ status: sel.value }),
          });
          showAlert("Status updated", "success");
          loadStats();
        } catch (err) {
          showAlert(err.message);
        }
      });
    });
  } catch (err) {
    container.innerHTML = `<div class="empty-state">Could not load applications.</div>`;
  }
}

// ---------- Students directory ----------

async function loadStudents() {
  const container = document.getElementById("admin-students-list");
  try {
    const data = await apiFetch("/api/students");
    if (!data.students.length) {
      container.innerHTML = `<div class="empty-state">No students registered yet.</div>`;
      return;
    }
    container.innerHTML = `<table><thead><tr><th>Name</th><th>Roll No</th><th>Branch</th><th>CGPA</th><th>Backlogs</th><th>Skills</th></tr></thead><tbody>` +
      data.students.map((s) => `
        <tr>
          <td>${escapeHtml(s.name)}<div class="muted">${escapeHtml(s.email)}</div></td>
          <td>${escapeHtml(s.roll_no)}</td>
          <td>${escapeHtml(s.branch)}</td>
          <td>${s.cgpa}</td>
          <td>${s.backlogs}</td>
          <td>${(s.skills || []).map(sk => `<span class="tag">${escapeHtml(sk.name)}</span>`).join(" ")}</td>
        </tr>
      `).join("") + `</tbody></table>`;
  } catch (err) {
    container.innerHTML = `<div class="empty-state">Could not load students.</div>`;
  }
}
