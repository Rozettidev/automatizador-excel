// Splash -> Login (2s)
document.addEventListener("DOMContentLoaded", () => {
  const boot = document.querySelector(".boot-screen");
  if (!boot) return;

  setTimeout(() => {
    boot.style.transition = "opacity 0.8s ease";
    boot.style.opacity = "0";
  }, 1500);

  setTimeout(() => {
    window.location.href = "/login"; // caminho ABSOLUTO
  }, 2000);
});
