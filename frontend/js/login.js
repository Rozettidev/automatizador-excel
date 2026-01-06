document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("loginForm");
  if (!form) return;

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    // validação fake só pra fluxo
    const user = document.getElementById("username").value.trim();
    const pass = document.getElementById("password").value.trim();
    if (!user || !pass) return;

    // segue pro dashboard
    window.location.href = "/dashboard"; // caminho ABSOLUTO
  });
});
