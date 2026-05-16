let tasks = [];
let filter = "all";

// ---- API helpers ----
async function api(path, method = "GET", body = null) {
  const opts = { method, headers: {} };
  if (body !== null) {
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(body);
  }
  const res = await fetch(path, opts);
  if (res.status === 204) return null;
  return res.json();
}

// ---- Toast ----
let toastTimer = null;
function showToast(msg) {
  let el = document.getElementById("toast");
  if (!el) {
    el = document.createElement("div");
    el.id = "toast";
    document.body.appendChild(el);
  }
  el.textContent = msg;
  el.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove("show"), 2500);
}

// ---- Render ----
function render() {
  const list = document.getElementById("task-list");
  const empty = document.getElementById("empty-msg");
  const tpl = document.getElementById("tpl-task");
  list.innerHTML = "";

  const visible = tasks.filter(t =>
    filter === "all" || t.status === filter
  );

  if (visible.length === 0) {
    empty.classList.remove("hidden");
    return;
  }
  empty.classList.add("hidden");

  visible.forEach(task => {
    const clone = tpl.content.cloneNode(true);
    const li = clone.querySelector(".task-item");
    if (task.status === "done") li.classList.add("done");

    const cb = clone.querySelector(".task-check");
    cb.checked = task.status === "done";
    cb.addEventListener("change", () => toggleTask(task.id, cb.checked));

    clone.querySelector(".task-title").textContent = task.title;
    clone.querySelector(".delete-btn").addEventListener("click", () => deleteTask(task.id));

    list.appendChild(clone);
  });
}

// ---- Actions ----
async function loadTasks() {
  tasks = await api("/api/tasks");
  render();
}

async function addTask(title) {
  const result = await api("/api/tasks", "POST", { title });
  if (result?.error) { showToast(result.error); return; }
  tasks.push(result);
  render();
}

async function toggleTask(id, done) {
  const status = done ? "done" : "todo";
  const result = await api(`/api/tasks/${encodeURIComponent(id)}`, "PATCH", { status });
  if (result?.error) { showToast(result.error); return; }
  tasks = tasks.map(t => t.id === id ? result : t);
  render();
}

async function deleteTask(id) {
  await api(`/api/tasks/${encodeURIComponent(id)}`, "DELETE");
  tasks = tasks.filter(t => t.id !== id);
  render();
}

// ---- Settings ----
async function openSettings() {
  const panel = document.getElementById("settings-panel");
  const settings = await api("/api/settings");
  document.getElementById("input-dir").value = settings.tasks_dir;
  panel.classList.toggle("hidden");
}

async function saveSettings() {
  const dir = document.getElementById("input-dir").value.trim();
  const result = await api("/api/settings", "POST", { tasks_dir: dir });
  if (result?.error) { showToast(result.error); return; }
  document.getElementById("settings-panel").classList.add("hidden");
  showToast("設定を保存しました");
  await loadTasks();
}

// ---- Event listeners ----
document.addEventListener("DOMContentLoaded", () => {
  loadTasks();

  document.getElementById("form-add").addEventListener("submit", async e => {
    e.preventDefault();
    const input = document.getElementById("input-title");
    const title = input.value.trim();
    if (!title) return;
    input.value = "";
    await addTask(title);
  });

  document.getElementById("btn-settings").addEventListener("click", openSettings);
  document.getElementById("btn-save-settings").addEventListener("click", saveSettings);
  document.getElementById("btn-cancel-settings").addEventListener("click", () => {
    document.getElementById("settings-panel").classList.add("hidden");
  });

  document.querySelectorAll(".tab").forEach(tab => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      filter = tab.dataset.filter;
      render();
    });
  });
});
