document.addEventListener('DOMContentLoaded', function () {
  // ===== Config =====
  const API_BASE = "http://127.0.0.1:5000";

  // ===== DOM =====
  const uploadForm      = document.getElementById('upload-form');
  const fileUpload      = document.getElementById('file-upload');
  const textInput       = document.getElementById('text-input');
  const dataViewCard    = document.getElementById('data-view-card');
  const issuesCard      = document.getElementById('issues-card');
  const tableHeader     = document.getElementById('table-header');
  const tableBody       = document.getElementById('table-body');
  const issuesCount     = document.getElementById('issues-count');
  const issuesList      = document.getElementById('issues-list');
  const fixAllBtn       = document.getElementById('fix-all-btn');
  const downloadBtn     = document.getElementById('download-btn');
  const saveServerBtn   = document.getElementById('save-server-btn');

  // ===== State =====
  let currentData = null;        // array de objetos (linhas)
  let currentIssues = [];        // lista de problemas vindos do backend
  let appliedCorrections = [];   // correções aplicadas no UI
  let currentColumns = [];       // cabeçalhos/ordem das colunas

  const hasSuggestion = (v) => v !== null && v !== undefined;

  // ===== Submit =====
  uploadForm.addEventListener('submit', async function (e) {
    e.preventDefault();

    const file = fileUpload.files[0];
    const text = textInput.value.trim();

    if (!file && !text) {
      alert('Por favor, selecione um arquivo ou cole dados no campo de texto.');
      return;
    }

    try {
      const formData = new FormData();
      if (file) {
        formData.append('file', file);
      } else {
        formData.append('data', text);
      }

      const response = await fetch(`${API_BASE}/api/analyze`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(`Erro ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();

      currentData    = result.data || [];
      currentIssues  = result.issues || [];
      currentColumns = Array.isArray(result.columns) && result.columns.length
        ? result.columns
        : (currentData.length ? Object.keys(currentData[0]) : []);

      appliedCorrections = [];

      displayData(currentData, currentColumns);
      displayIssues(currentIssues);

      dataViewCard.classList.remove('d-none');
      issuesCard.classList.remove('d-none');

      fixAllBtn.disabled    = currentIssues.length === 0;
      downloadBtn.disabled  = true;
      saveServerBtn.disabled = true;
    } catch (error) {
      console.error('Erro ao analisar dados:', error);
      alert(`Erro ao analisar dados: ${error.message}`);
    }
  });

  // ===== Render table =====
  function displayData(data, columns) {
    tableHeader.innerHTML = '';
    tableBody.innerHTML = '';

    // header
    columns.forEach(col => {
      const th = document.createElement('th');
      th.textContent = col;
      tableHeader.appendChild(th);
    });

    // body
    data.forEach((row, rowIndex) => {
      const tr = document.createElement('tr');
      columns.forEach((col, colIndex) => {
        const td = document.createElement('td');
        const val = row && col in row ? row[col] : '';
        td.textContent = val ?? '';
        td.dataset.row = String(rowIndex);
        td.dataset.col = String(colIndex);
        tr.appendChild(td);
      });
      tableBody.appendChild(tr);
    });
  }

  // ===== Render issues =====
  function displayIssues(issues) {
    issuesList.innerHTML = '';
    issuesCount.textContent = `${issues.length} problemas encontrados`;

    issues.forEach((issue, index) => {
      const item = document.createElement('div');
      item.className = 'list-group-item issue-item';
      item.dataset.index = String(index);

      let badgeClass = 'bg-warning';
      switch (issue.issue_type) {
        case 'date_format':   badgeClass = 'bg-info';    break;
        case 'invalid_cpf':
        case 'invalid_cnpj':  badgeClass = 'bg-danger';  break;
        case 'cpf_format':
        case 'cnpj_format':   badgeClass = 'bg-warning'; break;
        case 'text_case':     badgeClass = 'bg-primary'; break;
        case 'number_format': badgeClass = 'bg-success'; break;
      }

      const showFixButton = hasSuggestion(issue.suggested_value);

      item.innerHTML = `
        <div class="d-flex justify-content-between align-items-center">
          <div>
            <strong>Linha ${Number(issue.row) + 1}, Coluna ${issue.column_name ?? issue.column}</strong>
            <span class="badge ${badgeClass}">${getIssueTypeName(issue.issue_type)}</span>
          </div>
          ${showFixButton ? '<button class="btn btn-sm btn-outline-primary fix-btn">Corrigir</button>' : ''}
        </div>
        <div class="mt-1">${issue.description ?? ''}</div>
        <div class="mt-1">
          <small>Valor atual: <code>${safeStr(issue.value)}</code></small>
          ${showFixButton ? `<small class="ms-2">Sugestão: <code>${safeStr(issue.suggested_value)}</code></small>` : ''}
        </div>
      `;

      item.addEventListener('mouseenter', () => highlightCell(issue.row, issue.column));
      item.addEventListener('mouseleave', () => unhighlightCells());

      const fixBtn = item.querySelector('.fix-btn');
      if (fixBtn) fixBtn.addEventListener('click', () => applyCorrection(issue, index));

      issuesList.appendChild(item);
    });

    fixAllBtn.disabled = issues.length === 0 || issues.every(i => !hasSuggestion(i.suggested_value));
  }

  function safeStr(v) {
    if (v === null || v === undefined) return '';
    return String(v);
  }

  // ===== Highlights =====
  function highlightCell(row, col) {
    unhighlightCells();
    const cell = document.querySelector(`td[data-row="${row}"][data-col="${col}"]`);
    if (cell) cell.classList.add('highlight-cell');
  }

  function unhighlightCells() {
    document.querySelectorAll('.highlight-cell').forEach(c => c.classList.remove('highlight-cell'));
  }

  // ===== Apply single correction =====
  function applyCorrection(issue, issueIndex) {
    const cell = document.querySelector(`td[data-row="${issue.row}"][data-col="${issue.column}"]`);
    if (cell && hasSuggestion(issue.suggested_value)) {
      cell.textContent = issue.suggested_value;
      cell.classList.add('corrected-cell');
    }

    const colName = currentColumns[issue.column];
    if (colName) {
      if (currentData[issue.row]) {
        currentData[issue.row][colName] = issue.suggested_value;
      }
    }

    appliedCorrections.push({
      row: issue.row,
      column: issue.column,
      column_name: colName ?? issue.column_name,
      old_value: issue.value,
      new_value: issue.suggested_value
    });

    // remove da lista e redesenha
    currentIssues.splice(issueIndex, 1);
    displayIssues(currentIssues);

    downloadBtn.disabled = false;
    saveServerBtn.disabled = false;
  }

  // ===== Fix all =====
  fixAllBtn.addEventListener('click', () => {
    if (!currentIssues.length) return;

    currentIssues.forEach(issue => {
      if (!hasSuggestion(issue.suggested_value)) return;

      const cell = document.querySelector(`td[data-row="${issue.row}"][data-col="${issue.column}"]`);
      if (cell) {
        cell.textContent = issue.suggested_value;
        cell.classList.add('corrected-cell');
      }

      const colName = currentColumns[issue.column];
      if (colName && currentData[issue.row]) {
        currentData[issue.row][colName] = issue.suggested_value;
      }

      appliedCorrections.push({
        row: issue.row,
        column: issue.column,
        column_name: colName ?? issue.column_name,
        old_value: issue.value,
        new_value: issue.suggested_value
      });
    });

    // mantém apenas os que não tinham sugestão
    currentIssues = currentIssues.filter(i => !hasSuggestion(i.suggested_value));
    displayIssues(currentIssues);

    downloadBtn.disabled = false;
    saveServerBtn.disabled = false;
  });

  // ===== Download CSV =====
  downloadBtn.addEventListener('click', () => {
    if (!currentData || !currentData.length) return;

    const cols = currentColumns.length ? currentColumns : Object.keys(currentData[0]);
    let csv = cols.join(',') + '\n';

    currentData.forEach(row => {
      const values = cols.map(col => {
        const value = row[col];
        if (value === null || value === undefined) return '';
        const s = String(value);
        return (s.includes(',') || s.includes('"') || s.includes('\n'))
          ? `"${s.replace(/"/g, '""')}"`
          : s;
      });
      csv += values.join(',') + '\n';
    });

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href = url;
    a.download = 'dados_corrigidos.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  });

  // ===== Save to server (aplicar no backend) =====
  saveServerBtn.addEventListener('click', async () => {
    try {
      const res = await fetch(`${API_BASE}/api/apply_corrections`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          data: currentData,
          corrections: appliedCorrections.map(c => ({
            row: c.row,
            column: c.column,
            column_name: c.column_name,
            suggested_value: c.new_value
          })),
          columns: currentColumns
        })
      });

      if (!res.ok) throw new Error(await res.text());
      const json = await res.json();
      currentData = json.corrected_data;
      alert('Correções aplicadas no servidor com sucesso!');
    } catch (e) {
      alert('Falha ao aplicar correções no servidor: ' + e.message);
    }
  });

  // ===== Helpers =====
  function getIssueTypeName(issueType) {
    switch (issueType) {
      case 'date_format':   return 'Data';
      case 'invalid_cpf':   return 'CPF Inválido';
      case 'invalid_cnpj':  return 'CNPJ Inválido';
      case 'cpf_format':    return 'Formato CPF';
      case 'cnpj_format':   return 'Formato CNPJ';
      case 'text_case':     return 'Texto';
      case 'number_format': return 'Número';
      default:              return issueType || '';
    }
  }
});
