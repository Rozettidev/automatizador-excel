const logOut = document.getElementById("logOutput");
const btnRun = document.getElementById("autoBtn");
const btnExport = document.getElementById("exportBtn");
const btnClear = document.getElementById("clearLog");
const statusTxt = document.getElementById("statusText");
const fill = document.getElementById("progressFill");
const kpiProcessed = document.getElementById("kpiProcessed");
const kpiErrors = document.getElementById("kpiErrors");
const kpiLastRun = document.getElementById("kpiLastRun");
const fileInput = document.getElementById("fileInput");

let processed = 0;
let errors = 0;

// --------- Automatizar Modelo (simulação visual) ---------
btnRun.addEventListener("click", () => {
  statusTxt.textContent = "Processando…";
  fill.style.width = "0%";
  addLog("[ZYNTRA] Iniciando sequência de automação…");

  pipeline([
    () => addLog("• Analisando modelo de planilha…"),
    () => progressTo(25),
    () => addLog("• Detectando inconsistências…"),
    () => progressTo(45),
    () => addLog("• Corrigindo formatação e tipos…"),
    () => progressTo(70),
    () => addLog("• Aplicando regras de normalização…"),
    () => progressTo(88),
    () => addLog("• Gerando relatório final…"),
    () => progressTo(100),
  ], () => {
    processed += 1;
    const happenedError = Math.random() < 0.18;
    if (happenedError) {
      errors += 1;
      addLog("[ZYNTRA] Processo concluído com alertas.", "warn");
      statusTxt.textContent = "Concluído com alertas.";
    } else {
      addLog("[ZYNTRA] Processo concluído com sucesso.", "ok");
      statusTxt.textContent = "Automatização completa.";
    }
    kpiProcessed.textContent = processed;
    kpiErrors.textContent = errors;
    kpiLastRun.textContent = new Date().toLocaleTimeString();
  });
});

// --------- Exportar Log ---------
btnExport.addEventListener("click", () => {
  const blob = new Blob(
    [Array.from(logOut.querySelectorAll(".log-line")).map(l => l.textContent).join("\n")],
    { type: "text/plain;charset=utf-8" }
  );
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = `zyntra_log_${Date.now()}.txt`;
  document.body.appendChild(a); a.click(); a.remove();
  URL.revokeObjectURL(url);
});

// --------- Limpar Log ---------
btnClear.addEventListener("click", () => {
  logOut.innerHTML = "";
  addLog("[ZYNTRA] Log limpo.");
});

// --------- Importar -> /upload -> /correct ---------
fileInput.addEventListener("change", async (event) => {
  const file = event.target.files?.[0];
  if (!file) return;

  addLog(`[ZYNTRA] Planilha carregada: ${file.name}`);
  statusTxt.textContent = "Validando planilha…";
  progressTo(15);

  const formData = new FormData();
  formData.append("file", file);

  try {
    // 1) Upload
    const res = await fetch("/upload", { method: "POST", body: formData });
    const data = await res.json();

    if (!res.ok || data.error) {
      addLog(`❌ Erro no upload: ${data.error || res.statusText}`, "warn");
      statusTxt.textContent = "Erro no upload.";
      return;
    }

    addLog(`✅ Upload concluído: ${file.name}`);
    addLog(`Detectados ${data.issues.length} possíveis problemas.`);
    progressTo(55);

    // 2) Corrigir
    const corrRes = await fetch("/correct", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ filename: data.filename }),
    });

    if (!corrRes.ok) {
      addLog("❌ Erro ao corrigir o arquivo.", "warn");
      statusTxt.textContent = "Erro na correção.";
      return;
    }

    const blob = await corrRes.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `corrigido_${file.name}`;
    a.click();
    URL.revokeObjectURL(url);

    progressTo(100);
    statusTxt.textContent = "Pronto para download.";
    addLog("📦 Correções aplicadas e download iniciado!", "ok");
  } catch (err) {
    addLog(`⚠️ Falha ao comunicar com o servidor: ${err.message}`, "warn");
  }
});

// ---------- Helpers ----------
function addLog(msg, level) {
  const div = document.createElement("div");
  div.className = "log-line" + (level ? ` log-${level}` : "");
  div.textContent = `[${new Date().toLocaleTimeString()}] ${msg}`;
  logOut.appendChild(div);
  logOut.scrollTop = logOut.scrollHeight;
}
function progressTo(pct) { fill.style.width = pct + "%"; }
function pipeline(steps, done) {
  let i = 0;
  function next() {
    if (i >= steps.length) { done(); return; }
    steps[i++]();
    setTimeout(next, 600);
  }
  next();
}
