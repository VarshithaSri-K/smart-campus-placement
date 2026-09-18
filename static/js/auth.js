document.addEventListener("DOMContentLoaded", () => {
  const loginForm = document.getElementById("login-form");
  const registerForm = document.getElementById("register-form");

  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const email = document.getElementById("email").value.trim();
      const password = document.getElementById("password").value;
      try {
        const res = await apiFetch("/api/auth/login", {
          method: "POST",
          body: JSON.stringify({ email, password }),
        });
        window.location.href = res.user.role === "admin" ? "/admin" : "/dashboard";
      } catch (err) {
        showAlert(err.message);
      }
    });
  }

  if (registerForm) {
    loadBranches();
    registerForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const payload = {
        name: document.getElementById("name").value.trim(),
        roll_no: document.getElementById("roll_no").value.trim(),
        email: document.getElementById("email").value.trim(),
        phone: document.getElementById("phone").value.trim(),
        branch: document.getElementById("branch").value,
        batch_year: document.getElementById("batch_year").value,
        cgpa: document.getElementById("cgpa").value,
        backlogs: document.getElementById("backlogs").value || 0,
        password: document.getElementById("password").value,
      };
      try {
        await apiFetch("/api/auth/register", { method: "POST", body: JSON.stringify(payload) });
        window.location.href = "/dashboard";
      } catch (err) {
        showAlert(err.message);
      }
    });
  }
});

async function loadBranches() {
  try {
    const data = await apiFetch("/api/auth/branches");
    const select = document.getElementById("branch");
    select.innerHTML = data.branches.map((b) => `<option value="${b}">${b}</option>`).join("");
  } catch (e) { /* ignore */ }
}
