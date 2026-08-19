const API_BASE = "/api";

let currentTeamId = "depor";
let teamsList = [];
let currentPlayers = [];
let currentMatches = [];
let currentMatchId = null;
let currentMatchDetails = null;
let tempMatchRoster = [];

// Initial Load
document.addEventListener("DOMContentLoaded", async () => {
  setupCSVDropzone();
  await loadTeams();
});

// Tab Switching
function showTab(tabName) {
  document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
  
  const targetBtn = Array.from(document.querySelectorAll('.tab-btn')).find(b => {
    const attr = b.getAttribute('onclick');
    return attr && attr.includes(tabName);
  });
  if (targetBtn) targetBtn.classList.add('active');
  
  const targetContent = document.getElementById(`tab-${tabName}`);
  if (targetContent) targetContent.classList.add('active');

  if (tabName === 'preview') {
    renderLivePreviews();
  }
}

// Teams Management
async function loadTeams() {
  try {
    const res = await fetch(`${API_BASE}/teams`);
    teamsList = await res.json();
    
    const select = document.getElementById("headerTeamSelect");
    select.innerHTML = teamsList.map(t => `<option value="${t.id}">${t.name}</option>`).join("");
    
    if (teamsList.length > 0) {
      currentTeamId = teamsList[0].id;
      select.value = currentTeamId;
      await loadTeamData();
    }
  } catch (err) {
    console.error("Error loading teams:", err);
  }
}

async function switchTeam(teamId) {
  currentTeamId = teamId;
  await loadTeamData();

  // Immediately re-render whichever tab is currently displayed
  const activeTab = document.querySelector('.tab-content.active');
  if (activeTab) {
    const tabName = activeTab.id.replace('tab-', '');
    if (tabName === 'preview') {
      await renderLivePreviews();
    } else if (tabName === 'plantilla') {
      renderPlayersTable();
    } else if (tabName === 'partidos') {
      if (currentMatchId) {
        await loadMatchTactics(currentMatchId);
      }
    } else if (tabName === 'exportar') {
      renderExportMatchesChecklist();
    }
  }
}

async function loadTeamData() {
  await Promise.all([loadPlayers(), loadMatches()]);
  renderExportMatchesChecklist();
}

// Players State & Filters
let playerSearchQuery = "";
let playerSelectedCategory = "";
let playerSortField = "name";
let playerSortDir = "asc";

function formatDateDDMMYYYY(dateStr) {
  if (!dateStr || typeof dateStr !== "string") return "-";
  const str = dateStr.trim();
  if (!str) return "-";

  // Check YYYY-MM-DD or YYYY/MM/DD
  const ymdMatch = str.match(/^(\d{4})[-/](\d{1,2})[-/](\d{1,2})/);
  if (ymdMatch) {
    const [, y, m, d] = ymdMatch;
    return `${d.padStart(2, "0")}/${m.padStart(2, "0")}/${y}`;
  }

  // Check DD-MM-YYYY or DD/MM/YYYY
  const dmyMatch = str.match(/^(\d{1,2})[-/](\d{1,2})[-/](\d{4})/);
  if (dmyMatch) {
    const [, d, m, y] = dmyMatch;
    return `${d.padStart(2, "0")}/${m.padStart(2, "0")}/${y}`;
  }

  // Date object fallback
  const d = new Date(str);
  if (!isNaN(d.getTime())) {
    const day = String(d.getDate()).padStart(2, "0");
    const month = String(d.getMonth() + 1).padStart(2, "0");
    const year = d.getFullYear();
    return `${day}/${month}/${year}`;
  }

  return str;
}

function parseDateForSort(dateStr) {
  if (!dateStr) return 0;
  const str = String(dateStr).trim();
  const ymdMatch = str.match(/^(\d{4})[-/](\d{1,2})[-/](\d{1,2})/);
  if (ymdMatch) {
    return new Date(`${ymdMatch[1]}-${ymdMatch[2].padStart(2, '0')}-${ymdMatch[3].padStart(2, '0')}`).getTime() || 0;
  }
  const dmyMatch = str.match(/^(\d{1,2})[-/](\d{1,2})[-/](\d{4})/);
  if (dmyMatch) {
    return new Date(`${dmyMatch[3]}-${dmyMatch[2].padStart(2, '0')}-${dmyMatch[1].padStart(2, '0')}`).getTime() || 0;
  }
  const d = new Date(str);
  return isNaN(d.getTime()) ? 0 : d.getTime();
}

// Players Management
async function loadPlayers() {
  try {
    const res = await fetch(`${API_BASE}/teams/${currentTeamId}/players`);
    currentPlayers = await res.json();
    renderPlayersTable();
  } catch (err) {
    console.error("Error loading players:", err);
  }
}

function renderPlayersTable() {
  const tbody = document.getElementById("playersTableBody");
  if (!tbody) return;

  // 1. Filter players
  const q = playerSearchQuery.toLowerCase().trim();
  const catFilter = playerSelectedCategory.toUpperCase().trim();

  let filtered = currentPlayers.filter(p => {
    // Category match
    if (catFilter) {
      const pCat = (p.derived_category || "").toUpperCase();
      if (!pCat.includes(catFilter)) return false;
    }

    // Text search match
    if (q) {
      const name = (p.name || "").toLowerCase();
      const pos = (p.detailed_position || "").toLowerCase();
      const cat = (p.derived_category || "").toLowerCase();
      const age = String(p.age || "").toLowerCase();
      const birthFormatted = formatDateDDMMYYYY(p.birthdate).toLowerCase();
      const birthRaw = (p.birthdate || "").toLowerCase();

      const matches = name.includes(q) || 
                      pos.includes(q) || 
                      cat.includes(q) || 
                      age.includes(q) || 
                      birthFormatted.includes(q) || 
                      birthRaw.includes(q);
      if (!matches) return false;
    }

    return true;
  });

  // 2. Sort players
  filtered.sort((a, b) => {
    let diff = 0;
    switch (playerSortField) {
      case "name":
        diff = (a.name || "").localeCompare(b.name || "", 'es', { sensitivity: 'base' });
        break;
      case "birthdate":
        diff = parseDateForSort(a.birthdate) - parseDateForSort(b.birthdate);
        break;
      case "age":
        diff = (a.age || 0) - (b.age || 0);
        break;
      case "detailed_position":
      case "position":
        diff = (a.detailed_position || "").localeCompare(b.detailed_position || "", 'es');
        break;
      case "derived_category":
        diff = (a.derived_category || "").localeCompare(b.derived_category || "", 'es');
        break;
      case "minutes_played":
      case "minutes":
        diff = (a.minutes_played || 0) - (b.minutes_played || 0);
        break;
      case "starts":
        diff = (a.starts || 0) - (b.starts || 0);
        break;
      case "goals":
        diff = (a.goals || 0) - (b.goals || 0);
        break;
      default:
        diff = (a.name || "").localeCompare(b.name || "", 'es');
    }
    return playerSortDir === "desc" ? -diff : diff;
  });

  // 3. Render HTML
  if (filtered.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="8" style="text-align: center; padding: 2.5rem 1rem; color: var(--text-muted); font-size: 0.95rem;">
          🔍 No se encontraron jugadores que coincidan con la búsqueda o filtro seleccionado.
          <br>
          <button class="btn btn-secondary" style="margin-top: 0.75rem; font-size: 0.8rem;" onclick="resetPlayersFilters()">Restablecer filtros</button>
        </td>
      </tr>
    `;
  } else {
    tbody.innerHTML = filtered.map(p => {
      const avatarHtml = p.photo_url 
        ? `<img src="${p.photo_url}" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover; border: 2px solid var(--navy-primary); box-shadow: 0 2px 4px rgba(0,0,0,0.12); cursor: pointer;" onclick="openPlayerCardModal('${p.id}')" title="Haz clic para ver la Ficha / Pasaporte del Jugador">`
        : `<div style="width: 40px; height: 40px; border-radius: 50%; background: #002060; color: white; display: flex; align-items: center; justify-content: center; font-size: 1.1rem; border: 2px solid #002060; cursor: pointer;" onclick="openPlayerCardModal('${p.id}')" title="Haz clic para ver la Ficha / Pasaporte del Jugador">👤</div>`;

      const metricsHtml = `
        <div style="font-size: 0.8rem; color: #1e293b; line-height: 1.3;">
          <span style="background: #e2e8f0; padding: 2px 6px; border-radius: 4px; font-weight: 700; color: #002060; font-size: 0.75rem;">26/27</span>
          <span style="margin-left: 4px;"><strong>${p.minutes_played || 0}'</strong> min | <strong>${p.starts || 0}</strong> part | <strong>${p.goals || 0}</strong> gol${(p.goals || 0) === 1 ? '' : 'es'}</span>
        </div>
      `;

      return `
        <tr>
          <td style="vertical-align: middle; width: 50px;">${avatarHtml}</td>
          <td style="font-weight: 700; color: var(--navy-primary); vertical-align: middle; cursor: pointer;" onclick="openPlayerCardModal('${p.id}')">${p.name}</td>
          <td style="vertical-align: middle;">${formatDateDDMMYYYY(p.birthdate)}</td>
          <td style="vertical-align: middle;"><strong>${p.age}</strong></td>
          <td style="vertical-align: middle;">${p.detailed_position}</td>
          <td style="vertical-align: middle;"><span class="badge badge-position">${p.derived_category}</span></td>
          <td style="vertical-align: middle;">${metricsHtml}</td>
          <td style="text-align: right; vertical-align: middle; white-space: nowrap;">
            <button class="btn btn-secondary" style="padding: 0.3rem 0.6rem; font-size: 0.78rem; margin-right: 4px;" onclick="openPlayerCardModal('${p.id}')">📋 Pasaporte</button>
            <button class="btn btn-danger" style="padding: 0.3rem 0.6rem; font-size: 0.78rem;" onclick="deletePlayer('${p.id}')">🗑️</button>
          </td>
        </tr>
      `;
    }).join("");
  }

  // 4. Update badges & UI controls
  updatePlayersFilterUI(filtered.length, currentPlayers.length);
}

function updatePlayersFilterUI(filteredCount, totalCount) {
  const badge = document.getElementById("playerCountBadge");
  if (badge) badge.innerText = `${totalCount} Jugadores`;

  const filteredBadge = document.getElementById("playerFilteredCount");
  if (filteredBadge) {
    filteredBadge.innerText = `${filteredCount} de ${totalCount}`;
    filteredBadge.style.color = filteredCount < totalCount ? "var(--navy-primary)" : "#475569";
    filteredBadge.style.fontWeight = filteredCount < totalCount ? "700" : "600";
    filteredBadge.style.background = filteredCount < totalCount ? "var(--pale-green)" : "#e2e8f0";
  }

  const clearBtn = document.getElementById("playerSearchClearBtn");
  if (clearBtn) {
    clearBtn.style.display = playerSearchQuery ? "block" : "none";
  }

  const dirIcon = document.getElementById("sortDirIcon");
  const dirLabel = document.getElementById("sortDirLabel");
  if (dirIcon && dirLabel) {
    if (playerSortDir === "asc") {
      dirIcon.innerText = "⬆️";
      dirLabel.innerText = "Asc";
    } else {
      dirIcon.innerText = "⬇️";
      dirLabel.innerText = "Desc";
    }
  }

  // Update header sort indicators & active classes
  const columns = ["name", "birthdate", "age", "detailed_position", "derived_category", "minutes_played"];
  columns.forEach(col => {
    const th = document.getElementById(`th-${col}`);
    const icon = document.getElementById(`sort-icon-${col}`);
    if (th && icon) {
      if (playerSortField === col || (col === 'detailed_position' && playerSortField === 'position') || (col === 'minutes_played' && (playerSortField === 'minutes' || playerSortField === 'starts' || playerSortField === 'goals'))) {
        th.classList.add("active-sort");
        icon.innerText = playerSortDir === "asc" ? "▲" : "▼";
      } else {
        th.classList.remove("active-sort");
        icon.innerText = "↕";
      }
    }
  });
}

function handlePlayerSearch(val) {
  playerSearchQuery = val;
  renderPlayersTable();
}

function clearPlayerSearch() {
  const input = document.getElementById("playerSearchInput");
  if (input) input.value = "";
  playerSearchQuery = "";
  renderPlayersTable();
}

function handleCategoryFilter(val) {
  playerSelectedCategory = val;
  renderPlayersTable();
}

function handleSortSelect(val) {
  const parts = val.split("_");
  const dir = parts.pop();
  const field = parts.join("_");
  playerSortField = field;
  playerSortDir = dir || "asc";
  renderPlayersTable();
}

function toggleSortDirection() {
  playerSortDir = playerSortDir === "asc" ? "desc" : "asc";
  syncSortSelectValue();
  renderPlayersTable();
}

function sortByColumn(col) {
  if (playerSortField === col) {
    playerSortDir = playerSortDir === "asc" ? "desc" : "asc";
  } else {
    playerSortField = col;
    if (col === "minutes_played" || col === "starts" || col === "goals") {
      playerSortDir = "desc";
    } else {
      playerSortDir = "asc";
    }
  }
  syncSortSelectValue();
  renderPlayersTable();
}

function syncSortSelectValue() {
  const select = document.getElementById("playerSortSelect");
  if (!select) return;
  const candidate = `${playerSortField}_${playerSortDir}`;
  const exists = Array.from(select.options).some(o => o.value === candidate);
  if (exists) {
    select.value = candidate;
  }
}

function resetPlayersFilters() {
  playerSearchQuery = "";
  playerSelectedCategory = "";
  playerSortField = "name";
  playerSortDir = "asc";

  const searchInput = document.getElementById("playerSearchInput");
  if (searchInput) searchInput.value = "";

  const catFilter = document.getElementById("playerCatFilter");
  if (catFilter) catFilter.value = "";

  const sortSelect = document.getElementById("playerSortSelect");
  if (sortSelect) sortSelect.value = "name_asc";

  renderPlayersTable();
}

function openPlayerCardModal(playerId) {
  const p = currentPlayers.find(x => x.id === playerId);
  if (!p) return;
  document.getElementById("cardPlayerModalId").value = p.id;
  document.getElementById("cardPlayerName").innerText = p.name;
  document.getElementById("cardPlayerPos").innerText = p.detailed_position;
  document.getElementById("cardPlayerAge").innerText = `${p.age} años`;
  document.getElementById("cardPlayerBirth").innerText = formatDateDDMMYYYY(p.birthdate);
  document.getElementById("cardStatMins").innerText = `${p.minutes_played || 0}'`;
  document.getElementById("cardStatApps").innerText = p.starts || 0;
  document.getElementById("cardStatGoals").innerText = p.goals || 0;
  document.getElementById("cardStatCards").innerText = `${p.yellow_cards || 0} / ${p.red_cards || 0}`;

  const img = document.getElementById("cardPlayerPhoto");
  const fallback = document.getElementById("cardPlayerFallback");
  if (p.photo_url) {
    img.src = p.photo_url;
    img.style.display = "block";
    fallback.style.display = "none";
  } else {
    img.src = "";
    img.style.display = "none";
    fallback.style.display = "block";
  }

  const seasonsBox = document.getElementById("cardPlayerSeasonsList");
  seasonsBox.innerText = p.seasons_data ? p.seasons_data : "No hay desglose histórico registrado para las últimas 3 temporadas.";
  document.getElementById("playerCardModal").classList.add("active");
}

function closePlayerCardModal() {
  document.getElementById("playerCardModal").classList.remove("active");
}

let selectedPhotoFile = null;

function openEditPlayerModal(playerId) {
  const p = currentPlayers.find(x => x.id === playerId);
  if (!p) return;

  selectedPhotoFile = null;
  document.getElementById("editPlayerId").value = p.id;
  document.getElementById("editPlayerName").value = p.name || "";
  document.getElementById("editPlayerBirthdate").value = p.birthdate || "";
  document.getElementById("editPlayerPosition").value = p.detailed_position || "";
  document.getElementById("editPlayerMin").value = p.minutes_played || 0;
  document.getElementById("editPlayerStarts").value = p.starts || 0;
  document.getElementById("editPlayerSubs").value = p.subs_in || 0;
  document.getElementById("editPlayerYellows").value = p.yellow_cards || 0;
  document.getElementById("editPlayerReds").value = p.red_cards || 0;
  document.getElementById("editPlayerGoals").value = p.goals || 0;
  document.getElementById("editPlayerSeasonsData").value = p.seasons_data || "";

  const img = document.getElementById("editPlayerPhotoImg");
  const fallback = document.getElementById("editPlayerPhotoFallback");
  if (p.photo_url) {
    img.src = p.photo_url;
    img.style.display = "block";
    fallback.style.display = "none";
  } else {
    img.src = "";
    img.style.display = "none";
    fallback.style.display = "block";
  }

  document.getElementById("editPlayerPhotoInput").value = "";
  document.getElementById("editPlayerModal").classList.add("active");
}

function closeEditPlayerModal() {
  document.getElementById("editPlayerModal").classList.remove("active");
}

async function importPlayerFromBeSoccer() {
  const urlInput = document.getElementById("editPlayerImportUrl");
  const btn = urlInput.nextElementSibling;
  const url = urlInput.value.trim();
  if (!url) {
    alert("Introduce una URL de BeSoccer válida");
    return;
  }

  const origText = btn.innerHTML;
  btn.innerHTML = "⏳ Importando...";
  btn.disabled = true;

  try {
    const res = await fetch(`${API_BASE}/scrape-player`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Error al importar");
    }

    const data = await res.json();
    
    // Fill fields
    if (data.name) document.getElementById("editPlayerName").value = data.name;
    if (data.birthdate) document.getElementById("editPlayerBirthdate").value = data.birthdate;
    if (data.detailed_position) document.getElementById("editPlayerPosition").value = data.detailed_position;
    
    if (data.stats) {
      document.getElementById("editPlayerMin").value = data.stats.minutes_played || 0;
      document.getElementById("editPlayerStarts").value = data.stats.starts || 0;
      document.getElementById("editPlayerSubs").value = data.stats.subs_in || 0;
      document.getElementById("editPlayerYellows").value = data.stats.yellow_cards || 0;
      document.getElementById("editPlayerReds").value = data.stats.red_cards || 0;
      document.getElementById("editPlayerGoals").value = data.stats.goals || 0;
    }
    
    if (data.seasons_data) {
      document.getElementById("editPlayerSeasonsData").value = data.seasons_data;
    }
    
    if (data.photo_url) {
      // Fetch photo and update preview
      const photoRes = await fetch(data.photo_url);
      const blob = await photoRes.blob();
      const file = new File([blob], "scraped_photo.jpg", { type: blob.type });
      
      // Simulate file selection
      const dataTransfer = new DataTransfer();
      dataTransfer.items.add(file);
      const fileInput = document.getElementById("editPlayerPhotoInput");
      fileInput.files = dataTransfer.files;
      
      // Update preview
      selectedPhotoFile = file;
      const img = document.getElementById("editPlayerPhotoImg");
      const fallback = document.getElementById("editPlayerPhotoFallback");
      img.src = data.photo_url;
      img.style.display = "block";
      fallback.style.display = "none";
    }

    alert("✅ Datos importados. Revisa y pulsa 'Guardar Cambios'");
  } catch (err) {
    alert("❌ Error: " + err.message);
  } finally {
    btn.innerHTML = origText;
    btn.disabled = false;
  }
}

function handlePlayerPhotoSelect(event) {
  if (event.target.files && event.target.files[0]) {
    selectedPhotoFile = event.target.files[0];
    const reader = new FileReader();
    reader.onload = (e) => {
      const img = document.getElementById("editPlayerPhotoImg");
      const fallback = document.getElementById("editPlayerPhotoFallback");
      img.src = e.target.result;
      img.style.display = "block";
      fallback.style.display = "none";
    };
    reader.readAsDataURL(selectedPhotoFile);
  }
}

async function submitSaveEditPlayer() {
  const playerId = document.getElementById("editPlayerId").value;
  if (!playerId) return;

  // 1. Upload photo if selected
  if (selectedPhotoFile) {
    const formData = new FormData();
    formData.append("file", selectedPhotoFile);
    try {
      await fetch(`${API_BASE}/players/${playerId}/photo`, {
        method: "POST",
        body: formData
      });
    } catch (err) {
      console.error("Error uploading photo:", err);
    }
  }

  // 2. Save info & stats
  const statsPayload = {
    minutes_played: parseInt(document.getElementById("editPlayerMin").value || 0),
    starts: parseInt(document.getElementById("editPlayerStarts").value || 0),
    subs_in: parseInt(document.getElementById("editPlayerSubs").value || 0),
    yellow_cards: parseInt(document.getElementById("editPlayerYellows").value || 0),
    red_cards: parseInt(document.getElementById("editPlayerReds").value || 0),
    goals: parseInt(document.getElementById("editPlayerGoals").value || 0),
    seasons_data: document.getElementById("editPlayerSeasonsData").value
  };

  const name = document.getElementById("editPlayerName").value;
  const birthdate = document.getElementById("editPlayerBirthdate").value;
  const position = document.getElementById("editPlayerPosition").value;

  try {
    await fetch(`${API_BASE}/players/${playerId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name,
        birthdate,
        detailed_position: position,
        team_id: currentTeamId
      })
    });

    await fetch(`${API_BASE}/players/${playerId}/stats`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(statsPayload)
    });

    closeEditPlayerModal();
    await loadPlayers();
  } catch (err) {
    alert("Error al guardar información del jugador");
  }
}

async function deletePlayer(playerId) {
  if (!confirm("¿Eliminar jugador de la plantilla?")) return;
  await fetch(`${API_BASE}/players/${playerId}`, { method: "DELETE" });
  await loadPlayers();
}

// Add Player Modal
function openAddPlayerModal() {
  document.getElementById("addPlayerModal").classList.add("active");
}

function closeAddPlayerModal() {
  document.getElementById("addPlayerModal").classList.remove("active");
}

async function submitAddPlayer() {
  const name = document.getElementById("newPlayerName").value.trim();
  const birthdate = document.getElementById("newPlayerBirthdate").value;
  const detailed_position = document.getElementById("newPlayerPos").value;

  if (!name) {
    alert("Por favor introduce el nombre del jugador");
    return;
  }

  await fetch(`${API_BASE}/teams/${currentTeamId}/players`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, birthdate, detailed_position, team_id: currentTeamId })
  });

  closeAddPlayerModal();
  document.getElementById("newPlayerName").value = "";
  await loadPlayers();
}

// Drag & Drop CSV Uploader
function setupCSVDropzone() {
  const dropzone = document.getElementById("csvDropzone");
  if (!dropzone) return;
  dropzone.addEventListener("click", () => document.getElementById("csvFileInput").click());
  dropzone.addEventListener("dragover", (e) => { e.preventDefault(); dropzone.classList.add("dragover"); });
  dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));
  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
    if (e.dataTransfer.files.length > 0) {
      uploadCSVFile(e.dataTransfer.files[0]);
    }
  });
}

function handleFileSelect(event) {
  if (event.target.files.length > 0) {
    uploadCSVFile(event.target.files[0]);
  }
}

async function uploadCSVFile(file) {
  const formData = new FormData();
  formData.append("file", file);

  try {
    const res = await fetch(`${API_BASE}/teams/${currentTeamId}/players/import-csv`, {
      method: "POST",
      body: formData
    });
    const data = await res.json();
    alert(`Importados con éxito ${data.imported_count} jugadores.`);
    await loadPlayers();
  } catch (err) {
    alert("Error al importar el archivo CSV/Excel");
  }
}

// BeSoccer Player Import
function openImportPlayerBeSoccerModal() {
  const urlInput = document.getElementById("importPlayerBeSoccerUrl");
  if (urlInput) urlInput.value = "";
  const st = document.getElementById("importPlayerBeSoccerStatus");
  if (st) { st.style.display = "none"; st.innerText = ""; }
  document.getElementById("importPlayerBeSoccerModal").classList.add("active");
}

function closeImportPlayerBeSoccerModal() {
  document.getElementById("importPlayerBeSoccerModal").classList.remove("active");
}

async function submitImportPlayerBeSoccer() {
  const urlInput = document.getElementById("importPlayerBeSoccerUrl");
  const url = (urlInput?.value || "").trim();
  const statusDiv = document.getElementById("importPlayerBeSoccerStatus");
  const submitBtn = document.getElementById("btnSubmitImportBeSoccerPlayer");
  
  if (!url) {
    alert("Por favor introduce el enlace de BeSoccer");
    return;
  }
  
  if (statusDiv) {
    statusDiv.style.display = "block";
    statusDiv.style.background = "#e0f2fe";
    statusDiv.style.color = "#0369a1";
    statusDiv.innerText = "⏳ Descargando datos y fotografía de BeSoccer...";
  }
  if (submitBtn) submitBtn.disabled = true;

  try {
    const res = await fetch(`${API_BASE}/teams/${currentTeamId}/players/import-besoccer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url })
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Error al importar jugador");
    }

    const created = await res.json();
    if (statusDiv) {
      statusDiv.style.background = "#dcfce7";
      statusDiv.style.color = "#15803d";
      statusDiv.innerText = `✓ ¡Jugador ${created.name} importado con éxito!`;
    }
    await loadPlayers();
    setTimeout(() => {
      closeImportPlayerBeSoccerModal();
      if (submitBtn) submitBtn.disabled = false;
    }, 1200);
  } catch (err) {
    if (statusDiv) {
      statusDiv.style.background = "#fee2e2";
      statusDiv.style.color = "#b91c1c";
      statusDiv.innerText = `✕ Error: ${err.message}`;
    }
    if (submitBtn) submitBtn.disabled = false;
  }
}

// Match Management (Add, Edit, Delete)
function onMatchCompetitionTypeChange(mode) {
  const compSelect = document.getElementById(mode === 'new' ? 'newMatchCompetitionType' : 'editMatchCompetitionType');
  const compInput = document.getElementById(mode === 'new' ? 'newMatchCompetition' : 'editMatchCompetition');
  const dayInput = document.getElementById(mode === 'new' ? 'newMatchDay' : 'editMatchDay');
  if (!compSelect || !compInput) return;
  const val = compSelect.value;
  if (val === 'LIGA') {
    if (!compInput.value || compInput.value === 'AMISTOSO' || compInput.value === 'COPA DEL REY') {
      compInput.value = 'LALIGA HYPERMOTION';
    }
    if (dayInput && !dayInput.value) dayInput.value = 'Jornada 1';
  } else if (val === 'AMISTOSO') {
    compInput.value = 'AMISTOSO';
    if (dayInput) dayInput.value = '';
  } else if (val === 'COPA') {
    compInput.value = 'COPA DEL REY';
    if (dayInput && !dayInput.value) dayInput.value = '1ª Ronda';
  }
}

function openAddMatchModal() {
  document.getElementById("newMatchOpponent").value = "";
  document.getElementById("newMatchDate").value = new Date().toISOString().split("T")[0];
  document.getElementById("newMatchCompetitionType").value = "LIGA";
  document.getElementById("newMatchCompetition").value = "LALIGA HYPERMOTION";
  document.getElementById("newMatchDay").value = "Jornada 1";
  document.getElementById("newMatchIsHome").value = "true";
  document.getElementById("newMatchResultType").value = "WIN";
  document.getElementById("newMatchHomeGoals").value = "2";
  document.getElementById("newMatchAwayGoals").value = "0";
  document.getElementById("newMatchPlayingTime").value = "90 Minutes";
  document.getElementById("newMatchCadence").value = "";
  document.getElementById("addMatchModal").classList.add("active");
}

function closeAddMatchModal() {
  document.getElementById("addMatchModal").classList.remove("active");
}

async function submitAddMatch() {
  const opponent = document.getElementById("newMatchOpponent").value.trim();
  if (!opponent) {
    alert("Por favor, introduce el nombre del equipo rival.");
    return;
  }

  const date = document.getElementById("newMatchDate").value || new Date().toISOString().split("T")[0];
  const match_type = document.getElementById("newMatchCompetitionType").value || "LIGA";
  const competition = document.getElementById("newMatchCompetition").value.trim() || (match_type === "LIGA" ? "LALIGA HYPERMOTION" : "AMISTOSO");
  const matchday = document.getElementById("newMatchDay").value.trim();
  const is_home = document.getElementById("newMatchIsHome").value === "true";
  const result_type = document.getElementById("newMatchResultType").value;
  const home_goals = parseInt(document.getElementById("newMatchHomeGoals").value) || 0;
  const away_goals = parseInt(document.getElementById("newMatchAwayGoals").value) || 0;
  const playing_time = document.getElementById("newMatchPlayingTime").value.trim() || "90 Minutes";
  const substitute_cadence = document.getElementById("newMatchCadence").value.trim();

  const payload = {
    team_id: currentTeamId,
    opponent: opponent,
    date: date,
    match_type: match_type,
    competition: competition,
    matchday: matchday,
    is_home: is_home,
    result_type: result_type,
    home_goals: home_goals,
    away_goals: away_goals,
    playing_time: playing_time,
    substitute_cadence: substitute_cadence
  };

  try {
    const res = await fetch(`${API_BASE}/matches`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const err = await res.json();
      alert(`Error al crear partido: ${err.detail || 'Error desconocido'}`);
      return;
    }

    const createdMatch = await res.json();
    closeAddMatchModal();
    
    await loadMatches();
    const select = document.getElementById("matchSelect");
    if (select) {
      select.value = createdMatch.id;
      await loadMatchTactics(createdMatch.id);
    }
    
    await renderLivePreviews();
    renderExportMatchesChecklist();

    alert(`✓ Partido frente a ${opponent} añadido con éxito.`);
  } catch (err) {
    console.error("Error creating match:", err);
    alert("Error de conexión al crear el partido.");
  }
}

function openEditMatchModal() {
  if (!currentMatchDetails || !currentMatchDetails.match) {
    alert("Selecciona un partido primero.");
    return;
  }
  const m = currentMatchDetails.match;
  document.getElementById("editMatchOpponent").value = m.opponent || "";
  document.getElementById("editMatchDate").value = m.date || "";
  document.getElementById("editMatchCompetitionType").value = m.match_type || (m.competition && m.competition.toUpperCase().includes("LALIGA") ? "LIGA" : "AMISTOSO");
  document.getElementById("editMatchCompetition").value = m.competition || "LALIGA HYPERMOTION";
  document.getElementById("editMatchDay").value = m.matchday || "";
  document.getElementById("editMatchIsHome").value = m.is_home ? "true" : "false";
  document.getElementById("editMatchResultType").value = m.result_type || "WIN";
  document.getElementById("editMatchHomeGoals").value = m.home_goals || 0;
  document.getElementById("editMatchAwayGoals").value = m.away_goals || 0;
  document.getElementById("editMatchPlayingTime").value = m.playing_time || "90 Minutes";
  document.getElementById("editMatchCadence").value = m.substitute_cadence || "";
  document.getElementById("editMatchModal").classList.add("active");
}

function closeEditMatchModal() {
  document.getElementById("editMatchModal").classList.remove("active");
}

async function submitEditMatch() {
  if (!currentMatchId) return;
  const opponent = document.getElementById("editMatchOpponent").value.trim();
  if (!opponent) {
    alert("Por favor, introduce el nombre del rival.");
    return;
  }

  const payload = {
    opponent: opponent,
    date: document.getElementById("editMatchDate").value,
    match_type: document.getElementById("editMatchCompetitionType").value,
    competition: document.getElementById("editMatchCompetition").value.trim(),
    matchday: document.getElementById("editMatchDay").value.trim(),
    is_home: document.getElementById("editMatchIsHome").value === "true",
    result_type: document.getElementById("editMatchResultType").value,
    home_goals: parseInt(document.getElementById("editMatchHomeGoals").value) || 0,
    away_goals: parseInt(document.getElementById("editMatchAwayGoals").value) || 0,
    playing_time: document.getElementById("editMatchPlayingTime").value.trim(),
    substitute_cadence: document.getElementById("editMatchCadence").value.trim()
  };

  try {
    const res = await fetch(`${API_BASE}/matches/${currentMatchId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      closeEditMatchModal();
      await loadMatches();
      const select = document.getElementById("matchSelect");
      if (select) select.value = currentMatchId;
      await loadMatchTactics(currentMatchId);
      await renderLivePreviews();
      renderExportMatchesChecklist();
      alert("✓ Datos del partido actualizados con éxito.");
    } else {
      alert("Error al actualizar los datos del partido.");
    }
  } catch (err) {
    console.error("Error updating match:", err);
    alert("Error de conexión al actualizar el partido.");
  }
}

async function deleteCurrentMatch() {
  if (!currentMatchId) {
    alert("No hay ningún partido seleccionado para eliminar.");
    return;
  }

  const currentMatch = currentMatches.find(m => m.id === currentMatchId);
  const matchName = currentMatch ? `${currentMatch.opponent} (${currentMatch.result_type})` : "este partido";

  if (!confirm(`¿Estás seguro de que deseas eliminar definitivamente el partido ${matchName}?`)) {
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/matches/${currentMatchId}`, {
      method: "DELETE"
    });

    if (res.ok) {
      alert("✓ Partido eliminado con éxito.");
      currentMatchId = null;
      currentMatchDetails = null;
      await loadMatches();
      await renderLivePreviews();
      renderExportMatchesChecklist();
    } else {
      const err = await res.json().catch(() => ({}));
      alert(`Error al eliminar el partido: ${err.detail || 'Error en el servidor'}`);
    }
  } catch (err) {
    console.error("Error deleting match:", err);
    alert("Error de conexión al eliminar el partido.");
  }
}

// Lineup Modal & Squad Selector
async function openManageLineupModal() {
  if (!currentMatchId) {
    alert("Selecciona un partido primero.");
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/matches/${currentMatchId}/squad_roster`);
    const data = await res.json();
    tempMatchRoster = data.roster;
    renderLineupRosterMatrix();
    document.getElementById("manageLineupModal").classList.add("active");
  } catch (err) {
    console.error("Error loading squad roster:", err);
    alert("Error al cargar la plantilla del partido.");
  }
}

function closeManageLineupModal() {
  document.getElementById("manageLineupModal").classList.remove("active");
}

function getTacticalCoordsForRole(role) {
  const roleCoords = {
    "GK": [0.50, 0.88],
    "LB": [0.18, 0.72],
    "LCB": [0.38, 0.77],
    "CB": [0.50, 0.77],
    "RCB": [0.62, 0.77],
    "RB": [0.82, 0.72],
    "DM": [0.50, 0.62],
    "LDM": [0.40, 0.62],
    "RDM": [0.60, 0.62],
    "LCM": [0.35, 0.50],
    "CM": [0.50, 0.50],
    "RCM": [0.65, 0.50],
    "CAM": [0.50, 0.38],
    "LW": [0.18, 0.28],
    "RW": [0.82, 0.28],
    "ST": [0.50, 0.16],
    "LST": [0.42, 0.16],
    "RST": [0.58, 0.16]
  };
  return roleCoords[role] || [0.50, 0.50];
}

function renderLineupRosterMatrix() {
  const container = document.getElementById("rosterMatrixContainer");
  if (!container) return;

  const startersCount = tempMatchRoster.filter(p => p.match_status === "STARTER").length;
  const badge = document.getElementById("lineupStartersCountBadge");
  if (badge) {
    badge.innerText = `${startersCount} / 11`;
    badge.style.background = startersCount === 11 ? "#059669" : (startersCount > 11 ? "#dc2626" : "#d97706");
  }

  const msg = document.getElementById("lineupValidationMessage");
  if (msg) {
    if (startersCount === 11) {
      msg.innerText = "✓ Once titular completo (11 jugadores seleccionados)";
      msg.style.color = "#059669";
    } else if (startersCount < 11) {
      msg.innerText = `Faltan ${11 - startersCount} titulares para completar el once`;
      msg.style.color = "#d97706";
    } else {
      msg.innerText = `Has seleccionado ${startersCount - 11} titulares de más (máximo 11)`;
      msg.style.color = "#dc2626";
    }
  }

  const roleOptions = [
    { value: "GK", label: "GK (Portero)" },
    { value: "LB", label: "LB (Lateral Izquierdo)" },
    { value: "LCB", label: "LCB (Central Izquierdo)" },
    { value: "CB", label: "CB (Central)" },
    { value: "RCB", label: "RCB (Central Derecho)" },
    { value: "RB", label: "RB (Lateral Derecho)" },
    { value: "DM", label: "DM (Pivote Defensivo)" },
    { value: "LCM", label: "LCM (Interior Izq)" },
    { value: "CM", label: "CM (Centrocampista)" },
    { value: "RCM", label: "RCM (Interior Dcho)" },
    { value: "CAM", label: "CAM (Mediapunta)" },
    { value: "LW", label: "LW (Extremo Izquierdo)" },
    { value: "RW", label: "RW (Extremo Derecho)" },
    { value: "ST", label: "ST (Delantero Centro)" }
  ];

  container.innerHTML = tempMatchRoster.map(p => {
    const isStarter = p.match_status === "STARTER";
    const isSub = p.match_status === "SUBSTITUTE";
    const isNone = p.match_status === "UNSELECTED";

    return `
      <div class="roster-player-row ${isStarter ? 'is-starter' : (isSub ? 'is-sub' : '')}">
        <div style="display: flex; align-items: center; gap: 0.75rem; flex: 1; min-width: 220px;">
          <div>
            <div style="font-weight: 700; color: var(--navy-primary); font-size: 0.88rem;">${p.name}</div>
            <div style="font-size: 0.75rem; color: var(--text-muted);">${p.detailed_position} • ${p.age} años</div>
          </div>
        </div>

        <!-- Status Pills -->
        <div style="display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap;">
          <div class="status-pill-group">
            <button class="status-pill ${isStarter ? 'active-starter' : ''}" onclick="setPlayerMatchStatus('${p.id}', 'STARTER')">⭐ Titular</button>
            <button class="status-pill ${isSub ? 'active-sub' : ''}" onclick="setPlayerMatchStatus('${p.id}', 'SUBSTITUTE')">🪑 Suplente</button>
            <button class="status-pill ${isNone ? 'active-none' : ''}" onclick="setPlayerMatchStatus('${p.id}', 'UNSELECTED')">⚪ Fuera</button>
          </div>

          <!-- Role Selector for Starters -->
          ${isStarter ? `
            <select class="form-control" style="font-size: 0.75rem; padding: 3px 6px; width: 145px;" onchange="setPlayerRole('${p.id}', this.value)">
              ${roleOptions.map(opt => `<option value="${opt.value}" ${p.field_position === opt.value ? 'selected' : ''}>${opt.label}</option>`).join("")}
            </select>
          ` : `<div style="width: 145px;"></div>`}

          <!-- Cards Controls -->
          <div style="display: flex; align-items: center; gap: 0.3rem;">
            <select class="form-control" style="font-size: 0.75rem; padding: 3px 6px; width: 95px;" onchange="setPlayerCardType('${p.id}', this.value)">
              <option value="NONE" ${(!p.has_yellow_card && !p.has_red_card) ? 'selected' : ''}>Sin Tarjeta</option>
              <option value="YELLOW" ${p.has_yellow_card ? 'selected' : ''}>🟨 Amarilla</option>
              <option value="RED" ${p.has_red_card ? 'selected' : ''}>🟥 Roja</option>
            </select>
            ${(p.has_yellow_card || p.has_red_card) ? `
              <input type="number" class="form-control" style="font-size: 0.75rem; padding: 3px 4px; width: 55px;" placeholder="Min" value="${p.card_minute || 35}" min="1" max="120" onchange="setPlayerCardMinute('${p.id}', this.value)" title="Minuto de la tarjeta">
            ` : ''}
          </div>
        </div>
      </div>
    `;
  }).join("");
}

function setPlayerMatchStatus(playerId, status) {
  const p = tempMatchRoster.find(x => x.id === playerId);
  if (!p) return;
  p.match_status = status;
  if (status === "STARTER" && (!p.field_position || p.field_position === "NONE" || p.field_position === "SUB")) {
    const pos = p.detailed_position.toLowerCase();
    if (pos.includes("portero")) p.field_position = "GK";
    else if (pos.includes("lateral") && pos.includes("izq")) p.field_position = "LB";
    else if (pos.includes("lateral") && pos.includes("dch")) p.field_position = "RB";
    else if (pos.includes("central")) p.field_position = "CB";
    else if (pos.includes("pivote")) p.field_position = "DM";
    else if (pos.includes("extremo") && pos.includes("izq")) p.field_position = "LW";
    else if (pos.includes("extremo") && pos.includes("dch")) p.field_position = "RW";
    else if (pos.includes("delantero")) p.field_position = "ST";
    else p.field_position = "CM";

    const coords = getTacticalCoordsForRole(p.field_position);
    p.grid_x = coords[0];
    p.grid_y = coords[1];
  }
  renderLineupRosterMatrix();
}

function setPlayerRole(playerId, role) {
  const p = tempMatchRoster.find(x => x.id === playerId);
  if (!p) return;
  p.field_position = role;
  const coords = getTacticalCoordsForRole(role);
  p.grid_x = coords[0];
  p.grid_y = coords[1];
  renderLineupRosterMatrix();
}

function setPlayerCardType(playerId, type) {
  const p = tempMatchRoster.find(x => x.id === playerId);
  if (!p) return;
  if (type === "YELLOW") {
    p.has_yellow_card = true;
    p.has_red_card = false;
    p.card_type = "YELLOW";
    p.card_minute = p.card_minute || 35;
  } else if (type === "RED") {
    p.has_yellow_card = false;
    p.has_red_card = true;
    p.card_type = "RED";
    p.card_minute = p.card_minute || 75;
  } else {
    p.has_yellow_card = false;
    p.has_red_card = false;
    p.card_type = null;
    p.card_minute = null;
  }
  renderLineupRosterMatrix();
}

function setPlayerCardMinute(playerId, min) {
  const p = tempMatchRoster.find(x => x.id === playerId);
  if (!p) return;
  p.card_minute = parseInt(min) || null;
}

function clearAllLineupSelections() {
  tempMatchRoster.forEach(p => {
    p.match_status = "UNSELECTED";
    p.has_yellow_card = false;
    p.has_red_card = false;
    p.card_minute = null;
  });
  renderLineupRosterMatrix();
}

function applyLineupPreset(preset) {
  clearAllLineupSelections();

  const gks = tempMatchRoster.filter(p => p.detailed_position.toLowerCase().includes("portero"));
  const lbs = tempMatchRoster.filter(p => p.detailed_position.toLowerCase().includes("lateral") && p.detailed_position.toLowerCase().includes("izq"));
  const rbs = tempMatchRoster.filter(p => p.detailed_position.toLowerCase().includes("lateral") && p.detailed_position.toLowerCase().includes("dch"));
  const cbs = tempMatchRoster.filter(p => p.detailed_position.toLowerCase().includes("central") && !lbs.includes(p) && !rbs.includes(p));
  const dms = tempMatchRoster.filter(p => p.detailed_position.toLowerCase().includes("pivote") || p.detailed_position.toLowerCase().includes("defensivo"));
  const cms = tempMatchRoster.filter(p => (p.detailed_position.toLowerCase().includes("medio") || p.detailed_position.toLowerCase().includes("interior")) && !dms.includes(p));
  const lws = tempMatchRoster.filter(p => p.detailed_position.toLowerCase().includes("extremo") && p.detailed_position.toLowerCase().includes("izq"));
  const rws = tempMatchRoster.filter(p => p.detailed_position.toLowerCase().includes("extremo") && p.detailed_position.toLowerCase().includes("dch"));
  const sts = tempMatchRoster.filter(p => p.detailed_position.toLowerCase().includes("delantero") || p.detailed_position.toLowerCase().includes("punta"));

  const starters = [];

  const addStarter = (player, role) => {
    if (!player || starters.includes(player)) return;
    player.match_status = "STARTER";
    player.field_position = role;
    const c = getTacticalCoordsForRole(role);
    player.grid_x = c[0];
    player.grid_y = c[1];
    starters.push(player);
  };

  // 1. GK
  if (gks.length > 0) addStarter(gks[0], "GK");

  if (preset === "4-3-3") {
    if (lbs.length > 0) addStarter(lbs[0], "LB");
    if (cbs.length > 0) addStarter(cbs[0], "LCB");
    if (cbs.length > 1) addStarter(cbs[1], "RCB");
    else if (cbs.length > 0 && tempMatchRoster.filter(p => p.detailed_position.toLowerCase().includes("defensa") && !starters.includes(p)).length > 0) {
      addStarter(tempMatchRoster.filter(p => p.detailed_position.toLowerCase().includes("defensa") && !starters.includes(p))[0], "RCB");
    }
    if (rbs.length > 0) addStarter(rbs[0], "RB");

    if (dms.length > 0) addStarter(dms[0], "DM");
    const avCms = cms.filter(p => !starters.includes(p));
    if (avCms.length > 0) addStarter(avCms[0], "LCM");
    if (avCms.length > 1) addStarter(avCms[1], "RCM");

    if (lws.length > 0) addStarter(lws[0], "LW");
    else if (sts.filter(p => !starters.includes(p)).length > 1) addStarter(sts.filter(p => !starters.includes(p))[0], "LW");

    const avSts = sts.filter(p => !starters.includes(p));
    if (avSts.length > 0) addStarter(avSts[0], "ST");

    if (rws.length > 0) addStarter(rws[0], "RW");
    else if (sts.filter(p => !starters.includes(p)).length > 0) addStarter(sts.filter(p => !starters.includes(p))[0], "RW");
  } else if (preset === "4-4-2") {
    if (lbs.length > 0) addStarter(lbs[0], "LB");
    if (cbs.length > 0) addStarter(cbs[0], "LCB");
    if (cbs.length > 1) addStarter(cbs[1], "RCB");
    if (rbs.length > 0) addStarter(rbs[0], "RB");

    if (lws.length > 0) addStarter(lws[0], "LW");
    const avCms = cms.filter(p => !starters.includes(p));
    if (avCms.length > 0) addStarter(avCms[0], "LCM");
    if (avCms.length > 1) addStarter(avCms[1], "RCM");
    if (rws.length > 0) addStarter(rws[0], "RW");

    const avSts = sts.filter(p => !starters.includes(p));
    if (avSts.length > 0) addStarter(avSts[0], "LST");
    if (avSts.length > 1) addStarter(avSts[1], "RST");
  } else if (preset === "3-5-2") {
    if (cbs.length > 0) addStarter(cbs[0], "LCB");
    if (cbs.length > 1) addStarter(cbs[1], "CB");
    if (cbs.length > 2) addStarter(cbs[2], "RCB");

    if (lbs.length > 0) addStarter(lbs[0], "LB");
    if (dms.length > 0) addStarter(dms[0], "DM");
    const avCms = cms.filter(p => !starters.includes(p));
    if (avCms.length > 0) addStarter(avCms[0], "LCM");
    if (avCms.length > 1) addStarter(avCms[1], "RCM");
    if (rbs.length > 0) addStarter(rbs[0], "RB");

    const avSts = sts.filter(p => !starters.includes(p));
    if (avSts.length > 0) addStarter(avSts[0], "LST");
    if (avSts.length > 1) addStarter(avSts[1], "RST");
  }

  // Fill up to 11 if needed
  tempMatchRoster.forEach(p => {
    if (starters.length < 11 && !starters.includes(p)) {
      addStarter(p, "CM");
    }
  });

  // Assign remaining players as SUBSTITUTES
  tempMatchRoster.forEach(p => {
    if (!starters.includes(p)) {
      p.match_status = "SUBSTITUTE";
    }
  });

  renderLineupRosterMatrix();
}

async function submitSaveLineup() {
  if (!currentMatchId) return;

  const starters = tempMatchRoster.filter(p => p.match_status === "STARTER").map(p => ({
    player_id: p.id,
    field_position: p.field_position || "POS",
    grid_x: p.grid_x || 0.5,
    grid_y: p.grid_y || 0.5,
    has_yellow_card: p.has_yellow_card,
    has_red_card: p.has_red_card,
    card_minute: p.card_minute,
    card_type: p.card_type,
    sub_out_minute: p.sub_out_minute
  }));

  const substitutes = tempMatchRoster.filter(p => p.match_status === "SUBSTITUTE").map(p => ({
    player_id: p.id,
    field_position: "SUB",
    has_yellow_card: p.has_yellow_card,
    has_red_card: p.has_red_card,
    card_minute: p.card_minute,
    card_type: p.card_type,
    sub_in_minute: p.sub_in_minute
  }));

  const subs_events = currentMatchDetails ? currentMatchDetails.substitutions : [];

  const payload = {
    starters: starters,
    substitutes: substitutes,
    substitutions: subs_events
  };

  try {
    const res = await fetch(`${API_BASE}/matches/${currentMatchId}/lineup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      closeManageLineupModal();
      await loadMatchTactics(currentMatchId);
      await renderLivePreviews();
      renderExportMatchesChecklist();
      alert(`✓ Convocatoria guardada: ${starters.length} titulares y ${substitutes.length} suplentes.`);
    } else {
      alert("Error al guardar la alineación.");
    }
  } catch (err) {
    console.error("Error saving lineup:", err);
    alert("Error de conexión al guardar la alineación.");
  }
}

// Format match labels with date, typology, jornada and score
function formatMatchLabel(m) {
  const dateStr = formatDateDDMMYYYY(m.date);
  let tipoStr = "";
  if (m.match_type === "LIGA" || (!m.match_type && m.competition && m.competition.toUpperCase().includes("LALIGA"))) {
    tipoStr = m.matchday ? `LIGA (${m.matchday})` : "LIGA";
  } else if (m.match_type === "COPA") {
    tipoStr = m.matchday ? `COPA (${m.matchday})` : "COPA";
  } else if (m.match_type === "AMISTOSO" || (!m.match_type && m.competition && m.competition.toUpperCase().includes("FRIENDLY"))) {
    tipoStr = "AMISTOSO";
  } else {
    tipoStr = m.match_type || m.competition || "PARTIDO";
    if (m.matchday) tipoStr += ` (${m.matchday})`;
  }
  const resultShort = m.result_type === "WIN" ? "V" : (m.result_type === "DRAW" ? "E" : "D");
  const score = `${m.home_goals}-${m.away_goals}`;
  return `📅 ${dateStr} | 🏆 ${tipoStr} | ${m.opponent} (${resultShort} ${score})`;
}

// Matches & Tactics
async function loadMatches() {
  try {
    const res = await fetch(`${API_BASE}/teams/${currentTeamId}/matches`);
    currentMatches = await res.json();
    
    const select = document.getElementById("matchSelect");
    if (!select) return;

    if (currentMatches.length === 0) {
      select.innerHTML = `<option value="">(Sin partidos registrados)</option>`;
      currentMatchId = null;
      currentMatchDetails = null;
      document.getElementById("tacticalPitchContainer").innerHTML = `<div style="color: white; text-align: center; padding-top: 150px; font-weight: 600;">No hay partidos creados para este equipo. Haz clic en "+ Nuevo Partido" para crear uno.</div>`;
      document.getElementById("substitutesListContainer").innerHTML = "";
      document.getElementById("substitutionsLogContainer").innerHTML = "";
      document.getElementById("cardsListContainer").innerHTML = "";
      document.getElementById("matchQuickSummary").innerHTML = "";
      return;
    }

    select.innerHTML = currentMatches.map(m => `<option value="${m.id}">${formatMatchLabel(m)}</option>`).join("");
    
    if (!currentMatchId || !currentMatches.some(m => m.id === currentMatchId)) {
      currentMatchId = currentMatches[0].id;
    }
    select.value = currentMatchId;
    await loadMatchTactics(currentMatchId);
  } catch (err) {
    console.error("Error loading matches:", err);
  }
}

async function loadMatchTactics(matchId) {
  if (!matchId) return;
  currentMatchId = matchId;
  try {
    const res = await fetch(`${API_BASE}/matches/${matchId}`);
    currentMatchDetails = await res.json();
    renderMatchQuickSummary();
    renderTacticalPitch();
    renderSubstitutesPanel();
    renderSubstitutionsLog();
    renderCardsList();
    renderGoalsList();
    populateSubDropdowns();
  } catch (err) {
    console.error("Error loading match tactics:", err);
  }
}

function renderMatchQuickSummary() {
  const container = document.getElementById("matchQuickSummary");
  if (!container || !currentMatchDetails) return;
  const m = currentMatchDetails.match;
  const resultClass = m.result_type === "WIN" ? "badge-success" : (m.result_type === "DRAW" ? "badge-warning" : "badge-danger");
  const resultText = m.result_type === "WIN" ? "Victoria" : (m.result_type === "DRAW" ? "Empate" : "Derrota");
  const dateFormatted = formatDateDDMMYYYY(m.date);
  
  let typeBadge = "";
  if (m.match_type === "LIGA" || (!m.match_type && m.competition && m.competition.toUpperCase().includes("LALIGA"))) {
    typeBadge = `🏆 LIGA ${m.matchday ? '• ' + m.matchday : ''}`;
  } else if (m.match_type === "COPA") {
    typeBadge = `🏆 COPA ${m.matchday ? '• ' + m.matchday : ''}`;
  } else if (m.match_type === "AMISTOSO" || (!m.match_type && m.competition && m.competition.toUpperCase().includes("FRIENDLY"))) {
    typeBadge = `⚽ AMISTOSO`;
  } else {
    typeBadge = `🏆 ${m.match_type || m.competition} ${m.matchday ? '• ' + m.matchday : ''}`;
  }

  container.innerHTML = `
    <span class="badge ${resultClass}" style="font-weight: 700;">${resultText} ${m.home_goals} - ${m.away_goals}</span>
    <span class="badge" style="background: #e2e8f0; color: var(--navy-primary); font-weight: 700;">📅 ${dateFormatted}</span>
    <span class="badge" style="background: var(--peach-accent); color: var(--navy-primary); font-weight: 700; border: 1px solid var(--peach-border);">${typeBadge}</span>
    <span class="badge" style="background: #e2e8f0; color: var(--navy-primary); font-weight: 600;">⏱️ ${m.playing_time || '90 Min'}</span>
  `;
}



function renderTacticalPitch() {
  const container = document.getElementById("tacticalPitchContainer");
  if (!container || !currentMatchDetails) return;

  const starters = currentMatchDetails.starters;
  const substitutes = currentMatchDetails.substitutes || [];
  const playersMap = currentMatchDetails.players_map;
  const subsEvents = currentMatchDetails.substitutions;
  const subbedOutMap = {};
  subsEvents.forEach(se => subbedOutMap[se.player_out_id] = se.minute);

  // Incoming substitutes for sideline display
  const incomingSubs = subsEvents.map(s => {
    const pObj = playersMap[s.player_in_id] || currentPlayers.find(x => x.id === s.player_in_id) || { id: s.player_in_id, name: 'Suplente' };
    const subDetails = substitutes.find(sub => sub.player_id === s.player_in_id) || {};
    return {
      id: s.player_in_id,
      name: pObj.name,
      photo_url: pObj.photo_url,
      minute: s.minute,
      has_yellow_card: subDetails.has_yellow_card,
      has_red_card: subDetails.has_red_card,
      card_minute: subDetails.card_minute,
      goals: subDetails.goals || 0
    };
  });

  let sidelineHtml = "";
  if (incomingSubs.length > 0) {
    sidelineHtml = `
      <div class="pitch-sideline-subs">
        <div class="pitch-sideline-subs-title">▲ ENTRADAS</div>
        ${incomingSubs.map(sub => {
          const photoContent = sub.photo_url 
            ? `<img src="${sub.photo_url}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%;">`
            : `<span style="font-size: 0.75rem; color: white;">👤</span>`;
          
          let badgesHtml = `<div class="event-badge sub-in-badge">▲ ${sub.minute}'</div>`;
          if (sub.has_red_card) {
            badgesHtml += `<div class="yellow-card-badge" style="background-color: #ef4444; border-color: #b91c1c; left: -5px; right: auto;"></div>`;
          } else if (sub.has_yellow_card) {
            badgesHtml += `<div class="yellow-card-badge" style="left: -5px; right: auto;"></div>`;
          }
          if (sub.goals && sub.goals > 0) {
            badgesHtml += `<div class="event-badge goal-badge" style="right: -6px; top: -6px;">⚽${sub.goals > 1 ? ' ' + sub.goals : ''}</div>`;
          }

          return `
            <div class="sideline-sub-card" onclick="openPlayerCardModal('${sub.id}')" title="${sub.name} (Entró en min ${sub.minute}')">
              <div class="player-photo-circle" style="width: 32px; height: 32px;">
                ${photoContent}
                ${badgesHtml}
              </div>
              <div class="player-name-pill" style="font-size: 0.65rem; padding: 1px 5px; max-width: 80px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${sub.name}</div>
            </div>
          `;
        }).join("")}
      </div>
    `;
  }

  container.innerHTML = `
    <div class="pitch-svg-canvas" id="tacticalEditorPitchCanvas">
      ${starters.map(st => {
        const p = playersMap[st.player_id] || { name: 'Jugador' };
        const subMin = subbedOutMap[st.player_id] || st.sub_out_minute;
        
        let badgesHtml = "";
        if (st.goals && st.goals > 0) {
          badgesHtml += `<div class="event-badge goal-badge">${st.goals}⚽</div>`;
        }
        if (subMin) {
          badgesHtml += `<div class="event-badge sub-out-badge">${subMin}'</div>`;
        }
        if (st.has_red_card) {
          badgesHtml += `<div class="yellow-card-badge" style="background-color: #ef4444; border-color: #b91c1c;"></div>`;
        } else if (st.has_yellow_card) {
          badgesHtml += `<div class="yellow-card-badge"></div>`;
        }
        
        const leftPct = (st.grid_x * 100).toFixed(1);
        const topPct = (st.grid_y * 100).toFixed(1);
        
        const photoContent = (p && p.photo_url) 
          ? `<img src="${p.photo_url}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%;">`
          : `<span style="font-size: 1rem; color: white;">👤</span>`;
          
        return `
          <div class="pitch-player-box" data-player-id="${st.player_id}" data-player-name="${p.name}" style="left: ${leftPct}%; top: ${topPct}%;" title="Arrastra para mover en el campo">
            <div class="player-photo-circle">
              ${photoContent}
              ${badgesHtml}
            </div>
            <div class="player-name-pill">${p.name}</div>
          </div>
        `;
      }).join("")}
      ${sidelineHtml}
    </div>
  `;

  const canvas = document.getElementById("tacticalEditorPitchCanvas");
  if (canvas) attachPitchDragListeners(canvas, false);
}

function renderSubstitutesPanel() {
  const container = document.getElementById("substitutesListContainer");
  if (!container || !currentMatchDetails) return;

  const substitutes = currentMatchDetails.substitutes;
  const playersMap = currentMatchDetails.players_map;
  const subbedInMap = {};
  currentMatchDetails.substitutions.forEach(se => subbedInMap[se.player_in_id] = se.minute);

  const badge = document.getElementById("subsCountBadge");
  if (badge) badge.innerText = substitutes.length;

  if (substitutes.length === 0) {
    container.innerHTML = `<div style="color: var(--text-muted); font-size: 0.8rem; font-style: italic;">No hay suplentes en la convocatoria.</div>`;
    return;
  }

  container.innerHTML = substitutes.map(sub => {
    const p = playersMap[sub.player_id] || { name: 'Suplente' };
    const min = subbedInMap[sub.player_id] || sub.sub_in_minute;

    let cardHtml = "";
    if (sub.has_red_card) {
      cardHtml = ` <span class="card-badge-pill card-red">${sub.card_minute ? sub.card_minute + '’ ' : ''}🟥</span>`;
    } else if (sub.has_yellow_card) {
      cardHtml = ` <span class="card-badge-pill card-yellow">${sub.card_minute ? sub.card_minute + '’ ' : ''}🟨</span>`;
    }

    let goalHtml = "";
    if (sub.goals && sub.goals > 0) {
      goalHtml = ` <span style="font-weight: 800; color: #1e40af; font-size: 0.78rem;">⚽${sub.goals > 1 ? ' ' + sub.goals : ''}</span>`;
    }

    if (min) {
      return `<div style="color: #00994c; font-weight: 700; margin-bottom: 4px; display: flex; align-items: center; justify-content: space-between; gap: 4px;"><span>▲ ${p.name}${goalHtml}${cardHtml}</span><span class="sub-min-tag">${min}’</span></div>`;
    }
    return `<div style="color: var(--navy-primary); margin-bottom: 4px; display: flex; align-items: center; gap: 4px;">• ${p.name}${goalHtml}${cardHtml}</div>`;
  }).join("");
}

function renderSubstitutionsLog() {
  const container = document.getElementById("substitutionsLogContainer");
  if (!container || !currentMatchDetails) return;

  const subsEvents = currentMatchDetails.substitutions;
  const playersMap = currentMatchDetails.players_map;
  const substitutes = currentMatchDetails.substitutes || [];
  const starters = currentMatchDetails.starters || [];

  const badge = document.getElementById("subsDoneCountBadge");
  if (badge) badge.innerText = subsEvents.length;

  if (subsEvents.length === 0) {
    container.innerHTML = `<div style="color: var(--text-muted); font-size: 0.8rem; font-style: italic;">Sin sustituciones registradas.</div>`;
    return;
  }

  container.innerHTML = subsEvents.map((ev, idx) => {
    const pOut = playersMap[ev.player_out_id] || { name: 'Sale' };
    const pIn = playersMap[ev.player_in_id] || { name: 'Entra' };
    
    const subInDetails = substitutes.find(s => s.player_id === ev.player_in_id) || {};
    const stOutDetails = starters.find(s => s.player_id === ev.player_out_id) || {};

    let inBadges = "";
    if (subInDetails.goals && subInDetails.goals > 0) inBadges += ` ⚽${subInDetails.goals > 1 ? ' ' + subInDetails.goals : ''}`;
    if (subInDetails.has_red_card) inBadges += ` 🟥${subInDetails.card_minute ? ' ' + subInDetails.card_minute + '\'' : ''}`;
    else if (subInDetails.has_yellow_card) inBadges += ` 🟨${subInDetails.card_minute ? ' ' + subInDetails.card_minute + '\'' : ''}`;

    let outBadges = "";
    if (stOutDetails.goals && stOutDetails.goals > 0) outBadges += ` ⚽${stOutDetails.goals > 1 ? ' ' + stOutDetails.goals : ''}`;
    if (stOutDetails.has_red_card) outBadges += ` 🟥`;
    else if (stOutDetails.has_yellow_card) outBadges += ` 🟨`;

    return `
      <div class="sub-event-card">
        <div style="flex: 1;">
          <span style="font-weight: 700; color: var(--navy-primary);">${ev.minute}’</span> 
          <span style="color: #00994c; font-weight: 600;">🔺 ${pIn.name}${inBadges}</span> 
          <span style="color: var(--text-muted); font-size: 0.75rem;">por</span> 
          <span style="color: #dc2626; font-weight: 600;">🔻 ${pOut.name}${outBadges}</span>
        </div>
        <button class="btn btn-secondary" style="padding: 2px 6px; font-size: 0.72rem; color: #dc2626;" onclick="deleteSubstitutionEvent(${idx})" title="Deshacer este cambio">🗑️</button>
      </div>
    `;
  }).join("");
}

function renderCardsList() {
  const container = document.getElementById("cardsListContainer");
  if (!container || !currentMatchDetails) return;

  const starters = currentMatchDetails.starters;
  const substitutes = currentMatchDetails.substitutes;
  const playersMap = currentMatchDetails.players_map;

  const carded = [];
  [...starters, ...substitutes].forEach(entry => {
    if (entry.has_yellow_card || entry.has_red_card) {
      const p = playersMap[entry.player_id] || { name: 'Jugador' };
      carded.push({
        player_id: entry.player_id,
        name: p.name,
        is_red: entry.has_red_card,
        minute: entry.card_minute
      });
    }
  });

  if (carded.length === 0) {
    container.innerHTML = `<div style="color: var(--text-muted); font-size: 0.8rem; font-style: italic;">Sin tarjetas registradas.</div>`;
    return;
  }

  container.innerHTML = carded.map(c => `
    <div style="display: flex; justify-content: space-between; align-items: center; background: #f8fafc; padding: 4px 8px; border-radius: 4px; border: 1px solid #e2e8f0; margin-bottom: 4px;">
      <div>
        <span class="card-badge-pill ${c.is_red ? 'card-red' : 'card-yellow'}">${c.is_red ? '🟥 Roja' : '🟨 Amarilla'}</span>
        <strong style="color: var(--navy-primary); font-size: 0.8rem; margin-left: 4px;">${c.name}</strong>
        ${c.minute ? `<span style="color: var(--text-muted); font-size: 0.75rem;">(Min ${c.minute}’)</span>` : ''}
      </div>
      <button class="btn btn-secondary" style="padding: 1px 5px; font-size: 0.7rem; color: #dc2626;" onclick="removeCardFromPlayer('${c.player_id}')" title="Quitar tarjeta">✕</button>
    </div>
  `).join("");
}

function renderGoalsList() {
  const container = document.getElementById("goalsListContainer");
  if (!container || !currentMatchDetails) return;

  const starters = currentMatchDetails.starters;
  const substitutes = currentMatchDetails.substitutes;
  const playersMap = currentMatchDetails.players_map;

  const goalScorers = [];
  [...starters, ...substitutes].forEach(entry => {
    if (entry.goals && entry.goals > 0) {
      const p = playersMap[entry.player_id] || { name: 'Jugador' };
      goalScorers.push({
        player_id: entry.player_id,
        name: p.name,
        goals: entry.goals
      });
    }
  });

  if (goalScorers.length === 0) {
    container.innerHTML = `<div style="color: var(--text-muted); font-size: 0.8rem; font-style: italic;">Sin goles registrados.</div>`;
    return;
  }

  container.innerHTML = goalScorers.map(g => `
    <div style="display: flex; justify-content: space-between; align-items: center; background: #f8fafc; padding: 4px 8px; border-radius: 4px; border: 1px solid #e2e8f0; margin-bottom: 4px;">
      <div>
        <span style="font-size: 0.85rem;">⚽</span>
        <strong style="color: var(--navy-primary); font-size: 0.8rem; margin-left: 4px;">${g.name}</strong>
        <span style="color: var(--text-muted); font-size: 0.75rem; margin-left: 4px;">(${g.goals} gol${g.goals > 1 ? 'es' : ''})</span>
      </div>
      <button class="btn btn-secondary" style="padding: 1px 5px; font-size: 0.7rem; color: #dc2626;" onclick="removeGoalFromPlayer('${g.player_id}')" title="Quitar goles">✕</button>
    </div>
  `).join("");
}

function populateSubDropdowns() {
  if (!currentMatchDetails) return;
  const starters = currentMatchDetails.starters;
  const substitutes = currentMatchDetails.substitutes;
  const playersMap = currentMatchDetails.players_map;

  const subOutSelect = document.getElementById("subOutSelect");
  if (subOutSelect) {
    subOutSelect.innerHTML = starters.map(st => {
      const p = playersMap[st.player_id] || { name: 'Jugador' };
      return `<option value="${st.player_id}">${p.name}</option>`;
    }).join("");
  }

  const subInSelect = document.getElementById("subInSelect");
  if (subInSelect) {
    subInSelect.innerHTML = substitutes.map(sub => {
      const p = playersMap[sub.player_id] || { name: 'Jugador' };
      return `<option value="${sub.player_id}">${p.name}</option>`;
    }).join("");
  }

  const cardSelect = document.getElementById("cardPlayerSelect");
  if (cardSelect) {
    const allMatchPlayers = [...starters, ...substitutes];
    cardSelect.innerHTML = allMatchPlayers.map(entry => {
      const p = playersMap[entry.player_id] || { name: 'Jugador' };
      return `<option value="${entry.player_id}">${p.name} (${entry.is_starter ? 'Titular' : 'Suplente'})</option>`;
    }).join("");
  }
  const goalSelect = document.getElementById("goalPlayerSelect");
  if (goalSelect) {
    const allMatchPlayers = [...starters, ...substitutes];
    goalSelect.innerHTML = allMatchPlayers.map(entry => {
      const p = playersMap[entry.player_id] || { name: 'Jugador' };
      return `<option value="${entry.player_id}">${p.name} (${entry.is_starter ? 'Titular' : 'Suplente'})</option>`;
    }).join("");
  }
}

async function addGoalToPlayer() {
  const playerId = document.getElementById("goalPlayerSelect").value;
  const goalsToAdd = parseInt(document.getElementById("goalAmountInput").value) || 1;

  if (!playerId || !currentMatchDetails) return;

  const starters = currentMatchDetails.starters.map(s => {
    if (s.player_id === playerId) {
      return { ...s, goals: (s.goals || 0) + goalsToAdd };
    }
    return s;
  });

  const substitutes = currentMatchDetails.substitutes.map(s => {
    if (s.player_id === playerId) {
      return { ...s, goals: (s.goals || 0) + goalsToAdd };
    }
    return s;
  });

  const payload = {
    starters: starters,
    substitutes: substitutes,
    substitutions: currentMatchDetails.substitutions
  };

  try {
    await fetch(`${API_BASE}/matches/${currentMatchId}/lineup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    await loadMatchTactics(currentMatchId);
    await renderLivePreviews();
  } catch (err) {
    console.error("Error adding goal:", err);
  }
}

async function removeGoalFromPlayer(playerId) {
  if (!currentMatchDetails) return;

  const starters = currentMatchDetails.starters.map(s => {
    if (s.player_id === playerId) {
      return { ...s, goals: 0 };
    }
    return s;
  });

  const substitutes = currentMatchDetails.substitutes.map(s => {
    if (s.player_id === playerId) {
      return { ...s, goals: 0 };
    }
    return s;
  });

  const payload = {
    starters: starters,
    substitutes: substitutes,
    substitutions: currentMatchDetails.substitutions
  };

  try {
    await fetch(`${API_BASE}/matches/${currentMatchId}/lineup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    await loadMatchTactics(currentMatchId);
    await renderLivePreviews();
  } catch (err) {
    console.error("Error removing goal:", err);
  }
}

async function addSubstitutionEvent() {
  const player_out_id = document.getElementById("subOutSelect").value;
  const player_in_id = document.getElementById("subInSelect").value;
  const minute = parseInt(document.getElementById("subMinuteInput").value) || 65;

  if (!player_out_id || !player_in_id) {
    alert("Debes seleccionar el jugador que sale y el jugador que entra.");
    return;
  }

  if (!currentMatchDetails) return;

  const currentSubs = currentMatchDetails.substitutions.map(s => ({
    player_out_id: s.player_out_id,
    player_in_id: s.player_in_id,
    minute: s.minute
  }));

  currentSubs.push({ player_out_id, player_in_id, minute });

  const payload = {
    starters: currentMatchDetails.starters,
    substitutes: currentMatchDetails.substitutes,
    substitutions: currentSubs
  };

  try {
    await fetch(`${API_BASE}/matches/${currentMatchId}/lineup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    await loadMatchTactics(currentMatchId);
    await renderLivePreviews();
  } catch (err) {
    console.error("Error adding substitution:", err);
  }
}

async function deleteSubstitutionEvent(index) {
  if (!currentMatchDetails) return;
  const currentSubs = currentMatchDetails.substitutions.map(s => ({
    player_out_id: s.player_out_id,
    player_in_id: s.player_in_id,
    minute: s.minute
  }));

  currentSubs.splice(index, 1);

  const payload = {
    starters: currentMatchDetails.starters,
    substitutes: currentMatchDetails.substitutes,
    substitutions: currentSubs
  };

  try {
    await fetch(`${API_BASE}/matches/${currentMatchId}/lineup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    await loadMatchTactics(currentMatchId);
    await renderLivePreviews();
  } catch (err) {
    console.error("Error deleting substitution:", err);
  }
}

async function addCardToPlayer() {
  const playerId = document.getElementById("cardPlayerSelect").value;
  const cardType = document.getElementById("cardTypeSelect").value;
  const minute = parseInt(document.getElementById("cardMinuteInput").value) || 35;

  if (!playerId || !currentMatchDetails) return;

  const starters = currentMatchDetails.starters.map(s => {
    if (s.player_id === playerId) {
      return {
        ...s,
        has_yellow_card: cardType === "YELLOW" || cardType === "DOUBLE_YELLOW",
        has_red_card: cardType === "RED" || cardType === "DOUBLE_YELLOW",
        card_minute: minute,
        card_type: cardType
      };
    }
    return s;
  });

  const substitutes = currentMatchDetails.substitutes.map(s => {
    if (s.player_id === playerId) {
      return {
        ...s,
        has_yellow_card: cardType === "YELLOW" || cardType === "DOUBLE_YELLOW",
        has_red_card: cardType === "RED" || cardType === "DOUBLE_YELLOW",
        card_minute: minute,
        card_type: cardType
      };
    }
    return s;
  });

  const payload = {
    starters: starters,
    substitutes: substitutes,
    substitutions: currentMatchDetails.substitutions
  };

  try {
    await fetch(`${API_BASE}/matches/${currentMatchId}/lineup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    await loadMatchTactics(currentMatchId);
    await renderLivePreviews();
  } catch (err) {
    console.error("Error adding card:", err);
  }
}

async function removeCardFromPlayer(playerId) {
  if (!currentMatchDetails) return;

  const starters = currentMatchDetails.starters.map(s => {
    if (s.player_id === playerId) {
      return { ...s, has_yellow_card: false, has_red_card: false, card_minute: null, card_type: null };
    }
    return s;
  });

  const substitutes = currentMatchDetails.substitutes.map(s => {
    if (s.player_id === playerId) {
      return { ...s, has_yellow_card: false, has_red_card: false, card_minute: null, card_type: null };
    }
    return s;
  });

  const payload = {
    starters: starters,
    substitutes: substitutes,
    substitutions: currentMatchDetails.substitutions
  };

  try {
    await fetch(`${API_BASE}/matches/${currentMatchId}/lineup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    await loadMatchTactics(currentMatchId);
    await renderLivePreviews();
  } catch (err) {
    console.error("Error removing card:", err);
  }
}

// Drag & Drop Pitch Engine
let isDraggingPitchBox = false;
let currentDraggedEl = null;
let currentPitchCanvas = null;
let dragStartX = 0;
let dragStartY = 0;
let initialElemLeft = 0;
let initialElemTop = 0;

function attachPitchDragListeners(pitchCanvasEl, isSquadPitch = false) {
  const playerBoxes = pitchCanvasEl.querySelectorAll(".pitch-player-box");
  
  playerBoxes.forEach(box => {
    box.addEventListener("pointerdown", (e) => {
      e.preventDefault();
      e.stopPropagation();
      isDraggingPitchBox = true;
      currentDraggedEl = box;
      currentPitchCanvas = pitchCanvasEl;
      
      try { box.setPointerCapture(e.pointerId); } catch(err) {}
      box.classList.add("dragging");
      
      dragStartX = e.clientX;
      dragStartY = e.clientY;
      
      const styleLeft = parseFloat(box.style.left) || 50;
      const styleTop = parseFloat(box.style.top) || 50;
      initialElemLeft = styleLeft;
      initialElemTop = styleTop;
    });

    box.addEventListener("pointermove", (e) => {
      if (!isDraggingPitchBox || currentDraggedEl !== box) return;
      e.preventDefault();

      const rect = pitchCanvasEl.getBoundingClientRect();
      const deltaX = e.clientX - dragStartX;
      const deltaY = e.clientY - dragStartY;

      const deltaXPct = (deltaX / rect.width) * 100;
      const deltaYPct = (deltaY / rect.height) * 100;

      let leftPct = initialElemLeft + deltaXPct;
      let topPct = initialElemTop + deltaYPct;

      leftPct = Math.max(5, Math.min(95, leftPct));
      topPct = Math.max(5, Math.min(95, topPct));

      box.style.left = `${leftPct.toFixed(2)}%`;
      box.style.top = `${topPct.toFixed(2)}%`;
    });

    const finishDrag = async (e) => {
      if (!isDraggingPitchBox || currentDraggedEl !== box) return;
      isDraggingPitchBox = false;
      box.classList.remove("dragging");
      try { box.releasePointerCapture(e.pointerId); } catch(err) {}

      const rect = pitchCanvasEl.getBoundingClientRect();
      let leftPct = ((e.clientX - rect.left) / rect.width) * 100;
      let topPct = ((e.clientY - rect.top) / rect.height) * 100;
      leftPct = Math.max(5, Math.min(95, leftPct));
      topPct = Math.max(5, Math.min(95, topPct));

      const pitch_u = parseFloat((leftPct / 100.0).toFixed(3));
      const pitch_v = parseFloat((topPct / 100.0).toFixed(3));

      const playerId = box.getAttribute("data-player-id");
      const playerName = box.getAttribute("data-player-name") || "Jugador";

      if (isSquadPitch && playerId) {
        await savePlayerPitchPosition(playerId, pitch_u, pitch_v, playerName);
      } else if (!isSquadPitch && playerId && currentMatchId) {
        await saveMatchStarterPosition(currentMatchId, playerId, pitch_u, pitch_v, playerName);
      }

      currentDraggedEl = null;
      currentPitchCanvas = null;
    };

    box.addEventListener("pointerup", finishDrag);
    box.addEventListener("pointercancel", finishDrag);
  });
}

function showPitchToast(pitchContainer, message) {
  const existing = pitchContainer.querySelectorAll(".pitch-toast");
  existing.forEach(t => t.remove());

  const toast = document.createElement("div");
  toast.className = "pitch-toast";
  toast.innerText = message;
  pitchContainer.appendChild(toast);
  setTimeout(() => toast.remove(), 2100);
}

async function savePlayerPitchPosition(playerId, pitch_u, pitch_v, playerName) {
  try {
    const res = await fetch(`${API_BASE}/players/${playerId}/pitch_position`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pitch_x: pitch_u, pitch_y: pitch_v })
    });
    if (res.ok) {
      const container = document.getElementById("prevPitchBContainer");
      if (container) showPitchToast(container, `✓ Posición guardada: ${playerName}`);
    }
  } catch (err) {
    console.error("Error saving position:", err);
  }
}

async function saveMatchStarterPosition(matchId, playerId, grid_x, grid_y, playerName) {
  try {
    const res = await fetch(`${API_BASE}/matches/${matchId}/lineup_positions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify([{ player_id: playerId, grid_x: grid_x, grid_y: grid_y }])
    });
    if (res.ok) {
      const container = document.getElementById("prevPitchCContainer");
      if (container) showPitchToast(container, `✓ Alineación guardada: ${playerName}`);
    }
  } catch (err) {
    console.error("Error saving lineup position:", err);
  }
}

async function resetTacticalPitchPositions() {
  if (!confirm("¿Deseas restablecer las posiciones a la formación táctica original?")) return;
  try {
    const res = await fetch(`${API_BASE}/teams/${currentTeamId}/reset_pitch_positions`, {
      method: "POST"
    });
    if (res.ok) {
      const container = document.getElementById("prevPitchBContainer");
      if (container) showPitchToast(container, "⚽ Formación táctica restablecida");
      await renderLivePreviews();
    }
  } catch (err) {
    alert("Error al restablecer posiciones");
  }
}

// Live Slide Previews
async function renderLivePreviews() {
  try {
    // Slide A Preview
    const resA = await fetch(`${API_BASE}/preview/demographic/${currentTeamId}`);
    const dataA = await resA.json();
    document.getElementById("prevTitleA").innerText = `${dataA.team.name} SQUAD DEMOGRAPHIC`;
    document.getElementById("prevKpiA").innerText = `TOTAL PLAYERS: ${dataA.players.length}`;
    document.getElementById("prevFooterA").innerText = `${dataA.team.club_name} | ${dataA.team.season} | MEDICAL & SPORTS SCIENCE DEPARTMENT`;
    renderDemographicPreviewTable(dataA.players);

    // Slide B Preview
    const resB = await fetch(`${API_BASE}/preview/squad-pitch/${currentTeamId}`);
    const dataB = await resB.json();
    document.getElementById("prevTitleB").innerText = `${dataB.team.name}`;
    document.getElementById("prevKpiB").innerText = `NUMERO DE JUGADORES: ${dataB.boxes.length} JUGADORES`;
    renderSquadPitchPreview(dataB.boxes, dataB.all_pitch_players || []);
    renderInjuredPlayers(dataB.injured || []);
    renderExtraPitchPlayers(dataB.extra_pitch_players || []);
    populateGlobalDropdowns(dataB.extra_pitch_players || []);

    // Slide C Preview - populate match selector and use previewMatchId
    populatePreviewMatchSelect();
    const matchIdForPreview = previewMatchId || currentMatchId;
    if (matchIdForPreview) {
      const resC = await fetch(`${API_BASE}/preview/match/${matchIdForPreview}`);
      const dataC = await resC.json();
      document.getElementById("prevTitleC").innerText = `${dataC.match.opponent} v DEPORTIVO (${dataC.match.result_type} ${dataC.match.home_goals}-${dataC.match.away_goals})`;
      document.getElementById("prevKpiC").innerText = `TOTAL NUMBER OF SUBSTITUTIONS: ${dataC.substitutions.length}`;
      renderMatchPreview(dataC);
    }
  } catch (err) {
    console.error("Error loading live previews:", err);
  }
}

function renderDemographicPreviewTable(players) {
  const table = document.getElementById("prevDemographicTable");
  if (!table) return;
  const categories = ["Porteros", "Centrales", "Laterales", "Mediocentros", "Int/Extremos", "Delanteros"];
  const bands = [
    { label: "30+", test: a => a >= 30, color: "#1e3a8a" },
    { label: "26-29", test: a => a >= 26 && a <= 29, color: "#1d4ed8" },
    { label: "22-25", test: a => a >= 22 && a <= 25, color: "#2563eb" },
    { label: "U21", test: a => a <= 21, color: "#0284c7" }
  ];

  let html = `
    <thead>
      <tr>
        <th style="width: 90px; text-align: center;">Edad</th>
        ${categories.map(c => `<th style="text-align: center;">${c}</th>`).join("")}
        <th style="width: 80px; text-align: center; background: #002060;">TOTAL</th>
      </tr>
    </thead>
    <tbody>
  `;

  bands.forEach(b => {
    const bandPlayers = players.filter(p => b.test(p.age));
    html += `<tr>
      <td style="font-weight: 800; text-align: center; color: white; background: ${b.color}; font-size: 0.88rem; vertical-align: middle; border-radius: 4px;">${b.label}</td>`;
    categories.forEach(cat => {
      const matched = bandPlayers.filter(p => p.derived_category === cat);
      html += `<td style="vertical-align: middle; padding: 6px 8px;">`;
      if (matched.length === 0) {
        html += `<span style="color: #cbd5e1; font-size: 0.75rem; font-style: italic;">-</span>`;
      } else {
        html += `<div style="display: flex; flex-direction: column; gap: 4px; width: 100%;">`;
        matched.forEach(p => {
          html += `<div style="display: flex; justify-content: space-between; align-items: center; width: 100%; padding: 4px 8px; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 0.82rem; box-shadow: 0 1px 2px rgba(0,0,0,0.04);"><span style="font-weight: 600; color: #0f172a;">${p.name}</span><span style="font-weight: 700; color: #475569; font-size: 0.76rem;">(${p.age})</span></div>`;
        });
        html += `</div>`;
      }
      html += `</td>`;
    });
    html += `<td style="text-align: center; font-weight: 700; color: #002060; vertical-align: middle; background: #f1f5f9;">${bandPlayers.length}</td>`;
    html += `</tr>`;
  });

  // Calculate totals and average ages for each category
  const catTotals = [];
  const catAvgs = [];

  categories.forEach(cat => {
    const catP = players.filter(p => p.derived_category === cat);
    const count = catP.length;
    catTotals.push(count);
    if (count > 0) {
      const avg = catP.reduce((sum, p) => sum + p.age, 0) / count;
      catAvgs.push(avg.toFixed(1).replace(".", ","));
    } else {
      catAvgs.push("0,0");
    }
  });

  const totalPlayersCount = players.length;
  const overallAvgAge = totalPlayersCount > 0 
    ? (players.reduce((sum, p) => sum + p.age, 0) / totalPlayersCount).toFixed(1).replace(".", ",")
    : "0,0";

  // Add TOTALS Row
  html += `
    <tr style="border-top: 2px solid #002060;">
      <td style="font-weight: 800; text-align: center; color: white; background: #002060; font-size: 0.85rem; padding: 8px 4px;">TOTALS</td>
      ${catTotals.map(t => `<td style="text-align: center; font-weight: 800; color: #002060; background: #d9ead3; font-size: 0.95rem; padding: 8px 4px;">${t}</td>`).join("")}
      <td style="text-align: center; font-weight: 800; color: white; background: #002060; font-size: 0.95rem; padding: 8px 4px;">${totalPlayersCount}</td>
    </tr>
  `;

  // Add MEDIA EDAD Row
  html += `
    <tr>
      <td style="font-weight: 800; text-align: center; color: white; background: #002060; font-size: 0.82rem; padding: 8px 4px;">MEDIA EDAD</td>
      ${catAvgs.map(a => `<td style="text-align: center; font-weight: 800; color: #002060; background: #f8fafc; font-size: 0.9rem; padding: 8px 4px;">${a}</td>`).join("")}
      <td style="text-align: center; font-weight: 800; color: white; background: #002060; font-size: 0.9rem; padding: 8px 4px;">${overallAvgAge}</td>
    </tr>
  `;

  html += `</tbody>`;
  table.innerHTML = html;
}

function renderSquadPitchPreview(boxes, allPitchPlayers = []) {
  const container = document.getElementById("prevPitchBContainer");
  if (!container) return;
  container.innerHTML = `
    <div style="display: flex; justify-content: center; width: 100%; padding: 10px 0;">
      <div class="pitch-svg-canvas wide-slide-pitch" id="squadPitchCanvas">
        ${boxes.map(b => {
          const pObj = (allPitchPlayers && allPitchPlayers.find(x => x.id === b.id)) ||
                       currentPlayers.find(x => x.id === b.id) ||
                       allGlobalPlayersCache.find(x => x.id === b.id);
          const photoContent = (pObj && pObj.photo_url) 
            ? `<img src="${pObj.photo_url}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%;">`
            : `<span style="font-size: 1rem; color: white;">👤</span>`;
          const leftPct = (b.u * 100).toFixed(2);
          const topPct = (b.v * 100).toFixed(2);
          return `
            <div class="pitch-player-box squad-player-box" data-player-id="${b.id}" data-player-name="${b.label}" style="left: ${leftPct}%; top: ${topPct}%;" title="Haz clic para ver Pasaporte del Jugador (o arrastra para reubicar)">
              <div class="player-photo-circle" style="cursor: pointer;" onclick="openPlayerCardModal('${b.id}')">
                ${photoContent}
              </div>
              <div class="player-name-pill" style="cursor: pointer;" onclick="openPlayerCardModal('${b.id}')">${b.label}</div>
            </div>`;
        }).join("")}
      </div>
    </div>
  `;

  const canvas = document.getElementById("squadPitchCanvas");
  if (canvas) attachPitchDragListeners(canvas, true);
}

function renderMatchPreview(data, targetContainerId = "prevPitchCContainer", targetSubListId = "prevSubListC", targetSubLogId = "prevSubLogC") {
  // 1. Center Pitch
  const pitchContainer = document.getElementById(targetContainerId);
  if (!pitchContainer) return;
  const boxes = data.starter_boxes;
  const canvasId = targetContainerId === "prevPitchCContainer" ? "matchPitchCanvas" : `matchPitchCanvas_${targetContainerId}`;

  // Extract incoming substitutes for sideline display
  const incomingSubs = (data.substitutions || []).map(s => {
    const pObj = (data.players_map && data.players_map[s.player_in_id]) || currentPlayers.find(x => x.id === s.player_in_id) || { id: s.player_in_id, name: 'Suplente' };
    const subDetails = (data.substitutes || []).find(sub => sub.player_id === s.player_in_id) || {};
    return {
      id: s.player_in_id,
      name: pObj.name,
      photo_url: pObj.photo_url,
      minute: s.minute,
      has_yellow_card: subDetails.has_yellow_card,
      has_red_card: subDetails.has_red_card,
      card_minute: subDetails.card_minute,
      goals: subDetails.goals || 0
    };
  });

  let sidelineHtml = "";
  if (incomingSubs.length > 0) {
    sidelineHtml = `
      <div class="pitch-sideline-subs">
        <div class="pitch-sideline-subs-title">▲ ENTRADAS</div>
        ${incomingSubs.map(sub => {
          const photoContent = sub.photo_url 
            ? `<img src="${sub.photo_url}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%;">`
            : `<span style="font-size: 0.75rem; color: white;">👤</span>`;
          
          let badgesHtml = `<div class="event-badge sub-in-badge">▲ ${sub.minute}'</div>`;
          if (sub.has_red_card) {
            badgesHtml += `<div class="yellow-card-badge" style="background-color: #ef4444; border-color: #b91c1c; left: -5px; right: auto;"></div>`;
          } else if (sub.has_yellow_card) {
            badgesHtml += `<div class="yellow-card-badge" style="left: -5px; right: auto;"></div>`;
          }
          if (sub.goals && sub.goals > 0) {
            badgesHtml += `<div class="event-badge goal-badge" style="right: -6px; top: -6px;">⚽${sub.goals > 1 ? ' ' + sub.goals : ''}</div>`;
          }

          return `
            <div class="sideline-sub-card" onclick="openPlayerCardModal('${sub.id}')" title="${sub.name} (Entró en min ${sub.minute}')">
              <div class="player-photo-circle" style="width: 32px; height: 32px;">
                ${photoContent}
                ${badgesHtml}
              </div>
              <div class="player-name-pill" style="font-size: 0.65rem; padding: 1px 5px; max-width: 80px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${sub.name}</div>
            </div>
          `;
        }).join("")}
      </div>
    `;
  }

  pitchContainer.innerHTML = `
    <div style="display: flex; justify-content: center; width: 100%;">
      <div class="pitch-svg-canvas" id="${canvasId}">
        ${boxes.map(b => {
          let badgesHtml = "";
          const startersList = data.starters || (currentMatchDetails ? currentMatchDetails.starters : []);
          const st = startersList.find(s => s.player_id === b.id);
          if (st) {
              const subbedOutMap = {};
              (data.substitutions || []).forEach(se => subbedOutMap[se.player_out_id] = se.minute);
              const subMin = subbedOutMap[st.player_id] || st.sub_out_minute;
              
              if (subMin) {
                badgesHtml += `<div class="event-badge sub-out-badge">${subMin}'</div>`;
              }
              if (st.has_red_card) {
                badgesHtml += `<div class="yellow-card-badge" style="background-color: #ef4444; border-color: #b91c1c; left: -5px; right: auto;"></div>`;
              } else if (st.has_yellow_card) {
                badgesHtml += `<div class="yellow-card-badge" style="left: -5px; right: auto;"></div>`;
              }
              
              if (st.goals && st.goals > 0) {
                badgesHtml += `<div class="event-badge goal-badge">⚽${st.goals > 1 ? ' '+st.goals : ''}</div>`;
              }
          }
          
          const pObj = (data.players_map && data.players_map[b.id]) || currentPlayers.find(x => x.id === b.id);
          const photoContent = (pObj && pObj.photo_url) 
            ? `<img src="${pObj.photo_url}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%;">`
            : `<span style="font-size: 1rem; color: white;">👤</span>`;

          const leftPct = (b.u * 100).toFixed(1);
          const topPct = (b.v * 100).toFixed(1);
          return `
            <div class="pitch-player-box" data-player-id="${b.id}" data-player-name="${b.label}" style="left: ${leftPct}%; top: ${topPct}%;" title="Haz clic para ver Pasaporte del Jugador (o arrastra para reubicar)">
              <div class="player-photo-circle" style="cursor: pointer;" onclick="openPlayerCardModal('${b.id}')">
                ${photoContent}
                ${badgesHtml}
              </div>
              <div class="player-name-pill" style="cursor: pointer;" onclick="openPlayerCardModal('${b.id}')">${b.label}</div>
            </div>
          `;
        }).join("")}
        ${sidelineHtml}
      </div>
    </div>
  `;

  const matchCanvas = document.getElementById(canvasId);
  if (matchCanvas) attachPitchDragListeners(matchCanvas, false);

  // 2. Left Panel: Substitutes
  const subContainer = document.getElementById(targetSubListId);
  if (subContainer) {
    const subbedInMap = {};
    (data.substitutions || []).forEach(s => subbedInMap[s.player_in_id] = s.minute);

    let subHtml = `
      <div style="font-weight: 800; color: var(--navy-primary); font-size: 0.9rem; margin-bottom: 10px; padding-bottom: 6px; border-bottom: 2px solid var(--gold-accent); display: flex; justify-content: space-between; align-items: center;">
        <span>CONVOCADOS</span>
        <span class="badge" style="background: var(--navy-primary); color: white; font-size: 0.75rem; font-weight: 700;">${(data.substitutes || []).length}</span>
      </div>
      <div style="display: flex; flex-direction: column; gap: 4px;">
    `;
    (data.substitutes || []).forEach(sub => {
      const p = (data.players_map && data.players_map[sub.player_id]) || { name: 'Suplente' };
      const min = subbedInMap[sub.player_id];
      
      let extraBadges = "";
      if (sub.goals && sub.goals > 0) {
        extraBadges += ` <span style="font-size: 0.72rem; color: #1e40af; font-weight: 800;">⚽${sub.goals > 1 ? ' ' + sub.goals : ''}</span>`;
      }
      if (sub.has_red_card) {
        extraBadges += ` <span class="card-badge-pill card-red" style="font-size: 0.65rem;">${sub.card_minute ? sub.card_minute + '’ ' : ''}🟥</span>`;
      } else if (sub.has_yellow_card) {
        extraBadges += ` <span class="card-badge-pill card-yellow" style="font-size: 0.65rem;">${sub.card_minute ? sub.card_minute + '’ ' : ''}🟨</span>`;
      }

      if (min) {
        subHtml += `
          <div class="sub-list-item is-subbed-in" style="display: flex; justify-content: space-between; align-items: center;">
            <span style="color: #059669; font-weight: 800;">▲ ${p.name}${extraBadges}</span>
            <span class="sub-min-tag">${min}’</span>
          </div>`;
      } else {
        subHtml += `
          <div class="sub-list-item" style="display: flex; justify-content: space-between; align-items: center;">
            <span>• ${p.name}${extraBadges}</span>
          </div>`;
      }
    });
    subHtml += `</div>`;
    subContainer.innerHTML = subHtml;
  }

  // 3. Right Panel: Substitutions Log & Cadence
  const logContainer = document.getElementById(targetSubLogId);
  if (logContainer) {
    const m = data.match;
    const subs = data.substitutions || [];
    let logHtml = `
      <div class="match-info-card-header">
        <div style="font-weight: 800; color: var(--navy-primary); font-size: 0.85rem; margin-bottom: 2px;">⏱️ ${m.playing_time || '90 Minutes'}</div>
        <div style="font-size: 0.75rem; font-weight: 600; color: #475569;">${m.substitute_cadence || '1 Cadence: 1 x 4'}</div>
        <div style="font-size: 0.78rem; font-weight: 700; color: var(--navy-primary); margin-top: 4px;">Cambios Realizados: ${subs.length}</div>
      </div>
      <div style="font-weight: 800; color: var(--navy-primary); font-size: 0.85rem; margin-top: 10px; margin-bottom: 8px; padding-bottom: 4px; border-bottom: 2px solid var(--gold-accent);">
        HISTORIAL DE CAMBIOS
      </div>
      <div style="display: flex; flex-direction: column; gap: 6px; max-height: 480px; overflow-y: auto;">
    `;

    if (subs.length === 0) {
      logHtml += `<div style="color: #94a3b8; font-style: italic; font-size: 0.8rem; text-align: center; padding: 12px 0;">Sin cambios realizados</div>`;
    } else {
      subs.forEach((ev, idx) => {
        const pOut = (data.players_map && data.players_map[ev.player_out_id]) || { name: 'Sale' };
        const pIn = (data.players_map && data.players_map[ev.player_in_id]) || { name: 'Entra' };
        
        const subInDetails = (data.substitutes || []).find(s => s.player_id === ev.player_in_id) || {};
        const stOutDetails = (data.starters || []).find(s => s.player_id === ev.player_out_id) || {};

        let inBadges = "";
        if (subInDetails.goals && subInDetails.goals > 0) inBadges += ` ⚽${subInDetails.goals > 1 ? ' ' + subInDetails.goals : ''}`;
        if (subInDetails.has_red_card) inBadges += ` 🟥${subInDetails.card_minute ? ' ' + subInDetails.card_minute + '\'' : ''}`;
        else if (subInDetails.has_yellow_card) inBadges += ` 🟨${subInDetails.card_minute ? ' ' + subInDetails.card_minute + '\'' : ''}`;

        let outBadges = "";
        if (stOutDetails.goals && stOutDetails.goals > 0) outBadges += ` ⚽${stOutDetails.goals > 1 ? ' ' + stOutDetails.goals : ''}`;
        if (stOutDetails.has_red_card) outBadges += ` 🟥`;
        else if (stOutDetails.has_yellow_card) outBadges += ` 🟨`;

        logHtml += `
          <div class="sub-log-timeline-item">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 3px;">
              <span style="font-weight: 800; color: var(--navy-primary); font-size: 0.78rem;">Cambio #${idx + 1}</span>
              <span class="sub-min-tag" style="background: var(--navy-primary); color: white;">${ev.minute}’</span>
            </div>
            <div style="font-size: 0.76rem; display: flex; flex-direction: column; gap: 2px;">
              <span style="color: #059669; font-weight: 700;">▲ Entra: ${pIn.name}${inBadges}</span>
              <span style="color: #dc2626; font-weight: 700;">▼ Sale: ${pOut.name}${outBadges}</span>
            </div>
          </div>
        `;
      });
    }
    logHtml += `</div>`;
    logContainer.innerHTML = logHtml;
  }
}

// ===== MULTI-SLIDE C MATCH REPORTS IN PREVIEW =====
let extraPreviewMatchReports = [];

function addExtraSlideCPreviewReport() {
  if (!currentMatches || currentMatches.length === 0) {
    alert("No hay partidos disponibles para añadir.");
    return;
  }
  const reportId = "extra_c_" + Date.now();
  const existingIds = new Set([previewMatchId, ...extraPreviewMatchReports.map(r => r.matchId)]);
  const availableMatch = currentMatches.find(m => !existingIds.has(m.id)) || currentMatches[0];
  
  extraPreviewMatchReports.push({ id: reportId, matchId: availableMatch.id });
  renderExtraSlideCReports();
}

function removeExtraSlideCPreviewReport(reportId) {
  extraPreviewMatchReports = extraPreviewMatchReports.filter(r => r.id !== reportId);
  renderExtraSlideCReports();
}

async function switchExtraPreviewMatch(reportId, matchId) {
  const rep = extraPreviewMatchReports.find(r => r.id === reportId);
  if (rep) {
    rep.matchId = matchId;
    await renderSingleExtraSlideCReport(rep);
  }
}

async function renderExtraSlideCReports() {
  const container = document.getElementById("extraSlideCReportsContainer");
  if (!container) return;

  if (extraPreviewMatchReports.length === 0) {
    container.innerHTML = "";
    return;
  }

  container.innerHTML = extraPreviewMatchReports.map((rep, idx) => `
    <div class="preview-slide-card" id="slideCard_${rep.id}">
      <div class="slide-header-bar">
        <div>
          <p style="font-size: 0.8rem; font-weight: 700; color: var(--navy-primary);">Diapositiva C (Informe Adicional #${idx + 1})</p>
          <h2 class="slide-title-navy" id="prevTitle_${rep.id}">MATCH REPORT</h2>
        </div>
        <div style="display: flex; gap: 0.75rem; align-items: center; flex-wrap: wrap;">
          <div style="display: flex; align-items: center; gap: 0.5rem; background: #f8fafc; padding: 4px 8px; border-radius: 4px; border: 1px solid #cbd5e1;">
            <span style="font-size: 0.75rem; font-weight: 600; color: var(--navy-primary);">Partido:</span>
            <select id="select_${rep.id}" class="form-control" style="font-size: 0.75rem; padding: 2px 4px; max-width: 320px;" onchange="switchExtraPreviewMatch('${rep.id}', this.value)">
              ${currentMatches.map(m => `<option value="${m.id}" ${m.id === rep.matchId ? 'selected' : ''}>${formatMatchLabel(m)}</option>`).join("")}
            </select>
          </div>
          <div class="slide-kpi-box" id="prevKpi_${rep.id}">TOTAL NUMBER OF SUBSTITUTIONS: 0</div>
          <button class="btn btn-secondary" style="padding: 2px 8px; font-size: 0.75rem; color: #dc2626; border-color: #fca5a5;" onclick="removeExtraSlideCPreviewReport('${rep.id}')" title="Quitar este informe de la vista previa">✕ Quitar</button>
        </div>
      </div>

      <div class="slide-c-content-grid">
        <div style="background-color: var(--peach-accent); padding: 0.75rem; border-radius: 6px; font-size: 0.8rem;" id="prevSubList_${rep.id}"></div>
        <div class="pitch-container" id="prevPitch_${rep.id}" style="min-height: 400px;"></div>
        <div style="padding: 0.75rem; font-size: 0.8rem;" id="prevSubLog_${rep.id}"></div>
      </div>

      <div class="slide-footer-gold">CLUB | SEASON | MEDICAL & SPORTS SCIENCE DEPARTMENT</div>
    </div>
  `).join("");

  for (const rep of extraPreviewMatchReports) {
    await renderSingleExtraSlideCReport(rep);
  }
}

async function renderSingleExtraSlideCReport(rep) {
  try {
    const res = await fetch(`${API_BASE}/preview/match/${rep.matchId}`);
    if (!res.ok) return;
    const data = await res.json();
    
    const titleEl = document.getElementById(`prevTitle_${rep.id}`);
    if (titleEl) titleEl.innerText = `${data.match.opponent} v DEPORTIVO (${data.match.result_type} ${data.match.home_goals}-${data.match.away_goals})`;
    
    const kpiEl = document.getElementById(`prevKpi_${rep.id}`);
    if (kpiEl) kpiEl.innerText = `TOTAL NUMBER OF SUBSTITUTIONS: ${data.substitutions.length}`;
    
    renderMatchPreview(data, `prevPitch_${rep.id}`, `prevSubList_${rep.id}`, `prevSubLog_${rep.id}`);
  } catch(e) {
    console.error("Error rendering extra slide report:", e);
  }
}

async function importMatchFromUrl() {
  if (!currentMatchId) {
    alert("Por favor, selecciona o crea un partido primero.");
    return;
  }
  
  const urlInput = document.getElementById("importUrlInput");
  const url = urlInput.value.trim();
  if (!url) {
    alert("Por favor, pega el enlace de BeSoccer primero.");
    return;
  }

  const btn = document.getElementById("importUrlBtn");
  const originalText = btn.innerHTML;
  btn.innerHTML = `⏳ Importando...`;
  btn.disabled = true;

  try {
    const doImport = async (createUnknowns = false, ignoreUnknowns = false) => {
      return await fetch(`/api/matches/${currentMatchId}/import`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url, create_unknowns: createUnknowns, ignore_unknowns: ignoreUnknowns })
      });
    };

    let response = await doImport();

    if (response.ok) {
      const data = await response.json();
      if (data.status === "pending_creation") {
        const msg = "Se detectaron jugadores que no están en el equipo:\n\n- " + data.unknown_players.join("\n- ") + "\n\n¿Deseas crearlos y añadirlos al equipo?\n(Aceptar = Sí, Cancelar = Ignorarlos)";
        if (confirm(msg)) {
          response = await doImport(true, false);
        } else {
          response = await doImport(false, true);
        }
        
        if (!response.ok) {
          const err = await response.json();
          alert("Error al importar: " + (err.detail || "URL inválida"));
          return;
        }
      }
      
      alert("¡Partido importado con éxito! Recargando alineaciones...");
      await loadMatchTactics(currentMatchId);
      urlInput.value = "";
    } else {
      const err = await response.json();
      alert("Error al importar: " + (err.detail || "URL inválida"));
    }
  } catch (err) {
    console.error("Import error:", err);
    alert("Error de conexión al importar.");
  } finally {
    btn.innerHTML = originalText;
    btn.disabled = false;
  }
}

// Export checklist & action
// ===== SLIDE VISIBILITY TOGGLES =====
function toggleSlideVisibility(slide, visible) {
  const containerMap = { 'A': 'slideAContainer', 'B': 'slideBContainer', 'C': 'slideCContainer' };
  const container = document.getElementById(containerMap[slide]);
  if (container) {
    container.style.display = visible ? '' : 'none';
  }
}

// ===== PREVIEW MATCH SELECTOR =====
let previewMatchId = null;

function populatePreviewMatchSelect() {
  const select = document.getElementById("previewMatchSelect");
  if (!select) return;
  if (!currentMatches || currentMatches.length === 0) {
    select.innerHTML = `<option value="">(Sin partidos)</option>`;
    previewMatchId = null;
    return;
  }
  select.innerHTML = currentMatches.map(m => `<option value="${m.id}">${formatMatchLabel(m)}</option>`).join("");
  // Default to the currently selected match or the first one
  if (previewMatchId && currentMatches.some(m => m.id === previewMatchId)) {
    select.value = previewMatchId;
  } else if (currentMatchId && currentMatches.some(m => m.id === currentMatchId)) {
    select.value = currentMatchId;
    previewMatchId = currentMatchId;
  } else {
    previewMatchId = currentMatches[0].id;
    select.value = previewMatchId;
  }
}

async function switchPreviewMatch(matchId) {
  if (!matchId) return;
  previewMatchId = matchId;
  try {
    const resC = await fetch(`${API_BASE}/preview/match/${matchId}`);
    const dataC = await resC.json();
    document.getElementById("prevTitleC").innerText = `${dataC.match.opponent} v DEPORTIVO (${dataC.match.result_type} ${dataC.match.home_goals}-${dataC.match.away_goals})`;
    document.getElementById("prevKpiC").innerText = `TOTAL NUMBER OF SUBSTITUTIONS: ${dataC.substitutions.length}`;
    renderMatchPreview(dataC);
  } catch (err) {
    console.error("Error loading preview match:", err);
  }
}

// ===== EXPORT MATCHES CHECKLIST =====
function renderExportMatchesChecklist() {
  const container = document.getElementById("exportMatchesChecklist");
  if (!container) return;
  if (!currentMatches || currentMatches.length === 0) {
    container.innerHTML = `<span style="color: var(--text-muted); font-size: 0.85rem;">No hay partidos creados para este equipo.</span>`;
    updateToggleAllButton();
    return;
  }
  container.innerHTML = currentMatches.map(m => `
    <div style="margin-bottom: 6px;">
      <label style="display: flex; align-items: center; gap: 6px; font-size: 0.85rem; cursor: pointer;">
        <input type="checkbox" value="${m.id}" checked onchange="updateToggleAllButton()">
        <span>${formatMatchLabel(m)}</span>
      </label>
    </div>
  `).join("");
  updateToggleAllButton();
}

function toggleAllExportMatches() {
  const checkboxes = document.querySelectorAll("#exportMatchesChecklist input[type='checkbox']");
  const allChecked = Array.from(checkboxes).every(cb => cb.checked);
  checkboxes.forEach(cb => cb.checked = !allChecked);
  updateToggleAllButton();
}

function updateToggleAllButton() {
  const btn = document.getElementById("toggleAllMatchesBtn");
  if (!btn) return;
  const checkboxes = document.querySelectorAll("#exportMatchesChecklist input[type='checkbox']");
  const allChecked = checkboxes.length > 0 && Array.from(checkboxes).every(cb => cb.checked);
  if (allChecked) {
    btn.innerHTML = "☑️ Deseleccionar Todos";
  } else {
    btn.innerHTML = "✅ Seleccionar Todos";
  }
}

async function triggerExport(format, allTeams = false) {
  const selectedMatchIds = Array.from(document.querySelectorAll("#exportMatchesChecklist input:checked")).map(cb => cb.value);
  
  const payload = {
    team_id: currentTeamId,
    match_ids: selectedMatchIds,
    all_teams: allTeams
  };

  const endpoint = format === 'pdf' ? '/export/pdf' : '/export/pptx';
  const mimeType = format === 'pdf' ? 'application/pdf' : 'application/vnd.openxmlformats-officedocument.presentationml.presentation';
  const defaultFilename = allTeams ? `Full_Club_Analysis_Player.${format}` : `${currentTeamId}_Analysis_Player.${format}`;

  try {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!res.ok) throw new Error("Export failed");

    let filename = defaultFilename;
    const disposition = res.headers.get("Content-Disposition");
    if (disposition && disposition.includes("filename=")) {
      const match = disposition.match(/filename="?([^"]+)"?/);
      if (match && match[1]) filename = match[1];
    }

    const rawBlob = await res.blob();
    const typedBlob = new Blob([rawBlob], { type: mimeType });
    const url = window.URL.createObjectURL(typedBlob);
    
    const a = document.createElement("a");
    a.style.display = "none";
    a.href = url;
    a.setAttribute("download", filename);
    document.body.appendChild(a);
    a.click();
    
    setTimeout(() => {
      if (a.parentNode) document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    }, 500);
  } catch (err) {
    console.error("Export error, falling back to direct GET URL:", err);
    const getUrl = `${API_BASE}${endpoint}?team_id=${encodeURIComponent(currentTeamId)}&all_teams=${allTeams ? 'true' : 'false'}`;
    window.location.href = getUrl;
  }
}

// Lesionados and Extra Pitch Players Logic
let allGlobalPlayersCache = [];
let currentInjuredPlayersCache = [];

// Extra Pitch (Filial / Juvenil) Players Logic
function renderExtraPitchPlayers(extraPlayers) {
  const list = document.getElementById("extraPitchPlayersList");
  const countBadge = document.getElementById("extraPitchCountBadge");
  const sidebarTitle = document.getElementById("extraPitchSidebarTitle");
  
  if (sidebarTitle) {
    if (currentTeamId === 'depor') sidebarTitle.innerText = "🌟 FILIAL (FABRIL)";
    else if (currentTeamId === 'fabril') sidebarTitle.innerText = "🌟 JUVENIL A";
    else sidebarTitle.innerText = "🌟 FILIAL / OTROS";
  }

  if (countBadge) countBadge.innerText = (extraPlayers ? extraPlayers.length : 0);
  if (!list) return;

  if (!extraPlayers || extraPlayers.length === 0) {
    list.innerHTML = `<div style="color: rgba(255,255,255,0.45); font-size: 0.75rem; font-style: italic; text-align: center; padding: 1.5rem 0;">Sin jugadores incorporados.</div>`;
    return;
  }

  list.innerHTML = extraPlayers.map(p => {
    const photoContent = p.photo_url 
      ? `<img src="${p.photo_url}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%;">`
      : `<span style="font-size: 0.85rem; color: white;">👤</span>`;
    const teamBadgeColor = p.team_id === 'fabril' ? '#002060' : '#16a34a';
    const teamBadgeText = (p.team_id === 'fabril' ? 'FABRIL' : (p.team_id === 'juvenil_a' ? 'JUVENIL A' : p.team_id || '')).toUpperCase();

    return `
      <div class="extra-player-card">
        <div style="display: flex; align-items: center; gap: 8px; overflow: hidden; flex: 1;">
          <div style="width: 28px; height: 28px; border-radius: 50%; overflow: hidden; background: #334155; border: 1px solid rgba(255,255,255,0.3); flex-shrink: 0; display: flex; align-items: center; justify-content: center;">
            ${photoContent}
          </div>
          <div style="display: flex; flex-direction: column; overflow: hidden;">
            <div style="font-weight: 700; color: white; font-size: 0.78rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${p.name}</div>
            <div style="display: flex; gap: 4px; align-items: center;">
              <span class="badge" style="background: ${teamBadgeColor}; color: white; font-size: 0.6rem; padding: 1px 4px; font-weight: 700;">${teamBadgeText}</span>
              <span style="color: #94a3b8; font-size: 0.68rem; white-space: nowrap;">${p.detailed_position}</span>
            </div>
          </div>
        </div>
        <button class="btn btn-secondary" style="padding: 2px 6px; font-size: 0.7rem; background: rgba(239, 68, 68, 0.25); color: #fca5a5; border: none; cursor: pointer;" onclick="removeExtraPlayerFromPitch('${p.id}')" title="Retirar del campograma">✕</button>
      </div>
    `;
  }).join("");
}

async function removeExtraPlayerFromPitch(playerId) {
  try {
    const res = await fetch(`${API_BASE}/players/${playerId}/pitch-position`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pitch_x: null, pitch_y: null, extra_pitch_team_id: null })
    });
    if (res.ok) {
      await renderLivePreviews();
    }
  } catch (e) {
    console.error("Error removing extra player:", e);
  }
}

async function populateGlobalDropdowns(currentExtraPlayers = []) {
  try {
    const res = await fetch(`${API_BASE}/players/all`);
    const allPlayers = await res.json();
    allGlobalPlayersCache = allPlayers;
    
    const extraSelect = document.getElementById("extraPitchPlayerSelect");
    if (!extraSelect) return;

    // Filter available external players according to strict hierarchy rules:
    // 1. If currentTeamId === 'depor': ONLY players from 'fabril'
    // 2. If currentTeamId === 'fabril': ONLY players from 'juvenil_a'
    // 3. If currentTeamId === 'penafiel': NONE
    let eligiblePlayers = [];
    if (currentTeamId === "depor") {
      eligiblePlayers = allPlayers.filter(p => p.team_id === "fabril");
    } else if (currentTeamId === "fabril") {
      eligiblePlayers = allPlayers.filter(p => p.team_id === "juvenil_a");
    } else {
      eligiblePlayers = [];
    }

    // Exclude players already on this team's pitch
    const extraIds = new Set((currentExtraPlayers || []).map(p => p.id));
    const available = eligiblePlayers.filter(p => !extraIds.has(p.id) && p.extra_pitch_team_id !== currentTeamId);

    if (available.length === 0) {
      extraSelect.innerHTML = `<option value="">-- Sin jugadores disponibles --</option>`;
      extraSelect.disabled = true;
    } else {
      extraSelect.disabled = false;
      const options = available.map(p => `<option value="${p.id}">${p.name} (${p.detailed_position})</option>`);
      extraSelect.innerHTML = `<option value="">-- Seleccionar jugador --</option>` + options.join("");
    }
  } catch(e) {
    console.error("Error fetching all players", e);
  }
}

async function addExtraPlayerToPitch() {
  const select = document.getElementById("extraPitchPlayerSelect");
  const playerId = select ? select.value : "";
  if (!playerId) {
    alert("Por favor selecciona un jugador para incorporar.");
    return;
  }
  
  try {
    const res = await fetch(`${API_BASE}/players/${playerId}/pitch-position`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pitch_x: 0.5, pitch_y: 0.5, extra_pitch_team_id: currentTeamId })
    });
    if (res.ok) {
      await renderLivePreviews();
    }
  } catch(e) {
    console.error("Error adding extra player:", e);
  }
}

// Medical & Injury Modal Logic
function openAddInjuryModal() {
  const select = document.getElementById("injuryPlayerSelect");
  if (!select) return;
  
  const availablePlayers = allGlobalPlayersCache.length > 0 ? allGlobalPlayersCache : currentPlayers;
  select.innerHTML = availablePlayers.map(p => `<option value="${p.id}">${p.name} (${p.team_id || currentTeamId} - ${p.detailed_position})</option>`).join("");
  select.disabled = false;

  document.getElementById("injuryModalPlayerId").value = "";
  document.getElementById("injuryDescription").value = "";
  document.getElementById("injuryReturnTime").value = "";
  document.getElementById("injuryPhase").value = "Fase 1: Reposo / Fisioterapia";
  
  const recoverBtn = document.getElementById("btnRecoverPlayer");
  if (recoverBtn) recoverBtn.style.display = "none";
  
  document.getElementById("injuryModal").classList.add("active");
}

function openEditInjuryModal(playerId) {
  const p = currentInjuredPlayersCache.find(x => x.id === playerId) || allGlobalPlayersCache.find(x => x.id === playerId) || currentPlayers.find(x => x.id === playerId);
  if (!p) return;
  
  const select = document.getElementById("injuryPlayerSelect");
  if (select) {
    select.innerHTML = `<option value="${p.id}" selected>${p.name} (${p.team_id || currentTeamId} - ${p.detailed_position})</option>`;
    select.disabled = true;
  }
  
  document.getElementById("injuryModalPlayerId").value = p.id;
  document.getElementById("injuryDescription").value = p.injury_description || "";
  document.getElementById("injuryReturnTime").value = p.injury_return_time || "";
  document.getElementById("injuryPhase").value = p.injury_phase || "Fase 1: Reposo / Fisioterapia";
  
  const recoverBtn = document.getElementById("btnRecoverPlayer");
  if (recoverBtn) recoverBtn.style.display = "inline-flex";
  
  document.getElementById("injuryModal").classList.add("active");
}

function closeInjuryModal() {
  document.getElementById("injuryModal").classList.remove("active");
}

async function submitSaveInjury() {
  const select = document.getElementById("injuryPlayerSelect");
  const hiddenId = document.getElementById("injuryModalPlayerId").value;
  const playerId = hiddenId || (select ? select.value : "");
  
  if (!playerId) {
    alert("Por favor selecciona un jugador.");
    return;
  }

  const desc = document.getElementById("injuryDescription").value.trim();
  const returnTime = document.getElementById("injuryReturnTime").value.trim();
  const phase = document.getElementById("injuryPhase").value;

  try {
    const res = await fetch(`${API_BASE}/players/${playerId}/injured`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        is_injured: true,
        injury_description: desc,
        injury_return_time: returnTime,
        injury_phase: phase
      })
    });

    if (res.ok) {
      closeInjuryModal();
      await renderLivePreviews();
    } else {
      alert("Error al guardar la lesión.");
    }
  } catch (err) {
    console.error("Error saving injury:", err);
    alert("Error de conexión al registrar la lesión.");
  }
}

async function submitRecoverPlayer() {
  const hiddenId = document.getElementById("injuryModalPlayerId").value;
  if (!hiddenId) return;
  
  if (!confirm("¿Dar de alta médica a este jugador y reincorporarlo al campo?")) return;
  
  try {
    const res = await fetch(`${API_BASE}/players/${hiddenId}/injured`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ is_injured: false })
    });
    if (res.ok) {
      closeInjuryModal();
      await renderLivePreviews();
    }
  } catch (err) {
    console.error("Error recovering player:", err);
  }
}

async function recoverPlayerDirect(playerId) {
  if (!confirm("¿Dar de alta médica a este jugador?")) return;
  try {
    const res = await fetch(`${API_BASE}/players/${playerId}/injured`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ is_injured: false })
    });
    if (res.ok) {
      await renderLivePreviews();
    }
  } catch (err) {
    console.error("Error recovering player:", err);
  }
}

function renderInjuredPlayers(injuredPlayers) {
  currentInjuredPlayersCache = injuredPlayers || [];
  const list = document.getElementById("injuredPlayersList");
  if (!list) return;
  
  if (!injuredPlayers || injuredPlayers.length === 0) {
    list.innerHTML = `<div style="color: rgba(255,255,255,0.45); font-size: 0.75rem; font-style: italic; text-align: center; padding: 1.5rem 0;">Sin lesionados registrados.</div>`;
    return;
  }

  const phaseColors = {
    "Fase 1: Reposo / Fisioterapia": "#dc2626",
    "Fase 2: Readaptación en Campo": "#ea580c",
    "Fase 3: Parcial con Grupo": "#ca8a04",
    "Fase 4: Alta Médica / Competición": "#16a34a"
  };
  
  list.innerHTML = injuredPlayers.map(p => {
    const phase = p.injury_phase || "Fase 1: Reposo / Fisioterapia";
    const phaseBg = phaseColors[phase] || "#dc2626";
    const desc = p.injury_description || "Diagnóstico no especificado";
    const time = p.injury_return_time || "Tiempo pendiente";

    return `
      <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(255, 255, 255, 0.15); border-radius: 6px; padding: 8px; display: flex; flex-direction: column; gap: 4px; box-shadow: 0 2px 5px rgba(0,0,0,0.25);">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 4px;">
          <div style="font-weight: 700; color: white; font-size: 0.8rem; display: flex; align-items: center; gap: 4px;">
            <span>🩹</span>
            <span>${p.name}</span>
          </div>
          <div style="display: flex; gap: 3px;">
            <button class="btn btn-secondary" style="padding: 1px 5px; font-size: 0.65rem; background: rgba(255,255,255,0.12); color: white; border: none;" onclick="openEditInjuryModal('${p.id}')" title="Editar detalles de lesión">✏️</button>
            <button class="btn btn-secondary" style="padding: 1px 5px; font-size: 0.65rem; background: rgba(22, 163, 74, 0.35); color: #86efac; border: none;" onclick="recoverPlayerDirect('${p.id}')" title="Dar alta médica">✅</button>
          </div>
        </div>
        <div style="font-size: 0.72rem; color: #cbd5e1; font-weight: 500; line-height: 1.2;">${desc}</div>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 3px; border-top: 1px dashed rgba(255,255,255,0.1); padding-top: 3px;">
          <span class="badge" style="background: ${phaseBg}; color: white; font-size: 0.65rem; padding: 2px 6px; font-weight: 700; border-radius: 3px;">${phase.split(':')[0]}</span>
          <span style="font-size: 0.7rem; color: #fbbf24; font-weight: 600;">⏳ ${time}</span>
        </div>
      </div>
    `;
  }).join("");
}
