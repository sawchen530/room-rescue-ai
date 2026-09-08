(() => {
  const $ = (id) => document.getElementById(id);

  const beforePhoto = $("beforePhoto");
  const afterPhoto = $("afterPhoto");
  const analyzeBtn = $("analyze");
  const compareBtn = $("compare");
  const REQUEST_TIMEOUT_MS = 95000;

  const ANALYZE_STEPS = [
    "Looking at the photo…",
    "Noting what’s actually visible…",
    "Drafting the checklist…",
    "Estimating time and supplies…",
    "Sorting by what to handle first…",
  ];

  const COMPARE_STEPS = [
    "Comparing the two photos…",
    "Checking each task against the new picture…",
    "Marking only what the photo can confirm…",
    "Writing the leftover list…",
  ];

  const STORE_KEY = "roomRescueWork";

  let analysisData = null;
  let taskState = [];

  function loadWork() {
    try {
      const raw = JSON.parse(localStorage.getItem(STORE_KEY) || "null");
      if (raw && typeof raw === "object") {
        return {
          rooms: Number(raw.rooms) || 0,
          verified: Number(raw.verified) || 0,
          streak: Number(raw.streak) || 0,
          lastDay: raw.lastDay || null,
        };
      }
    } catch {
      /* ignore broken storage */
    }
    return { rooms: 0, verified: 0, streak: 0, lastDay: null };
  }

  let work = loadWork();

  function saveWork() {
    localStorage.setItem(STORE_KEY, JSON.stringify(work));
  }

  function recordVerifiedWork(count, roomFinished) {
    if (count <= 0 && !roomFinished) return;
    const today = new Date().toISOString().slice(0, 10);
    if (work.lastDay !== today) {
      const yesterday = new Date(Date.now() - 86400000).toISOString().slice(0, 10);
      work.streak = work.lastDay === yesterday ? (work.streak || 0) + 1 : 1;
      work.lastDay = today;
    }
    work.verified += count;
    if (roomFinished) work.rooms += 1;
    saveWork();
    renderWorkSummary();
  }

  function renderWorkSummary() {
    const el = $("workSummary");
    const parts = [];
    if (work.rooms) parts.push(work.rooms === 1 ? "1 room finished" : `${work.rooms} rooms finished`);
    if (work.verified) parts.push(work.verified === 1 ? "1 task verified" : `${work.verified} tasks verified`);
    if (work.streak >= 2) parts.push(`${work.streak}-day streak`);
    if (!parts.length) {
      el.hidden = true;
      el.textContent = "";
      return;
    }
    el.hidden = false;
    el.textContent = parts.join(" · ");
  }

  function esc(value) {
    return String(value ?? "").replace(/[&<>"']/g, (ch) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#039;",
    }[ch]));
  }

  function setError(boxId, textId, message) {
    const box = $(boxId);
    const el = $(textId);
    if (!message) {
      box.hidden = true;
      el.textContent = "";
      return;
    }
    box.hidden = false;
    el.textContent = message;
  }

  function friendlyStatusMessage(status, detail) {
    if (status === 413) return detail || "That photo is too large. Please use one under 12 MB.";
    if (status === 415) return detail || "Please use a JPG, PNG, WebP, or HEIC photo.";
    if (status === 408 || status === 504) return detail || "The photo check took too long. Please try again.";
    if (status === 502 || status === 503) {
      return detail || "The photo check is temporarily unavailable. Please try again in a moment.";
    }
    if (status >= 500) return detail || "Something went wrong on our side. Please try again.";
    return detail || "Something went wrong. Please try again.";
  }

  function friendlyNetworkError(error) {
    if (error?.name === "AbortError") {
      return "The photo check took too long. Please try again.";
    }
    if (error?.name === "TypeError" || /failed to fetch|networkerror|load failed/i.test(error?.message || "")) {
      return "We couldn’t reach Room Rescue. Check your connection and try again.";
    }
    return error?.message || "Something went wrong. Please try again.";
  }

  async function postForm(url, body) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
    try {
      const response = await fetch(url, { method: "POST", body, signal: controller.signal });
      const raw = await response.text();
      let data = {};
      if (raw) {
        try {
          data = JSON.parse(raw);
        } catch {
          if (!response.ok) throw new Error(friendlyStatusMessage(response.status));
          throw new Error("The server sent an unexpected response. Please try again.");
        }
      }
      if (!response.ok) {
        const detail = typeof data.detail === "string" ? data.detail : "";
        throw new Error(friendlyStatusMessage(response.status, detail));
      }
      return data;
    } finally {
      clearTimeout(timer);
    }
  }

  function bindDropzone(drop, input) {
    ["dragenter", "dragover"].forEach((type) => {
      drop.addEventListener(type, (event) => {
        event.preventDefault();
        drop.classList.add("is-dragover");
      });
    });
    ["dragleave", "dragend"].forEach((type) => {
      drop.addEventListener(type, (event) => {
        event.preventDefault();
        drop.classList.remove("is-dragover");
      });
    });
    drop.addEventListener("drop", (event) => {
      event.preventDefault();
      drop.classList.remove("is-dragover");
      const file = event.dataTransfer?.files?.[0];
      if (!file) return;
      const transfer = new DataTransfer();
      transfer.items.add(file);
      input.files = transfer.files;
      input.dispatchEvent(new Event("change", { bubbles: true }));
    });
    drop.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        input.click();
      }
    });
  }

  function showPhoto(input, chosenId, dropId, nameId, previewId, fallbackId, noteId, readyNote) {
    const file = input.files?.[0];
    if (!file) return;
    const preview = $(previewId);
    const fallback = $(fallbackId);
    const note = $(noteId);
    if (preview.src) URL.revokeObjectURL(preview.src);
    preview.hidden = true;
    fallback.hidden = true;
    fallback.textContent = /\.hei[cf]$/i.test(file.name) ? "HEIC" : "Photo";

    const objectUrl = URL.createObjectURL(file);
    preview.onload = () => {
      preview.hidden = false;
      fallback.hidden = true;
      note.textContent = readyNote;
    };
    preview.onerror = () => {
      URL.revokeObjectURL(objectUrl);
      preview.removeAttribute("src");
      preview.hidden = true;
      fallback.hidden = false;
      note.textContent = "This phone format may not preview here, but we can still analyze it.";
    };
    preview.src = objectUrl;
    $(nameId).textContent = file.name || "Photo selected";
    $(dropId).hidden = true;
    $(chosenId).hidden = false;
  }

  function createWaiter(barId, textId, steps) {
    let timer = null;
    let started = 0;

    function tick() {
      const elapsed = Date.now() - started;
      const pct = Math.min(90, 8 + elapsed / 220);
      $(barId).style.width = `${pct}%`;
      const step = Math.min(steps.length - 1, Math.floor(elapsed / 2800));
      $(textId).textContent = steps[step];
    }

    return {
      start() {
        started = Date.now();
        $(barId).style.width = "8%";
        $(textId).textContent = steps[0];
        clearInterval(timer);
        timer = setInterval(tick, 400);
      },
      stop() {
        clearInterval(timer);
        timer = null;
        $(barId).style.width = "100%";
      },
    };
  }

  const analyzeWait = createWaiter("analyzeBar", "analyzeWaitText", ANALYZE_STEPS);
  const compareWait = createWaiter("compareBar", "compareWaitText", COMPARE_STEPS);

  function updateManualProgress() {
    const done = taskState.filter((task) => task.done).length;
    const pct = taskState.length ? Math.round((done / taskState.length) * 100) : 0;
    $("manualProgressText").textContent = `${done} of ${taskState.length} checked`;
    $("manualPct").textContent = `${pct}%`;
    $("manualProgressBar").style.width = `${pct}%`;
  }

  function compareClass(status) {
    if (status === "Completed") return "done";
    if (status === "Partially Done") return "partial";
    return "open";
  }

  function renderTasks() {
    const root = $("tasks");
    root.innerHTML = "";
    $("emptyTasks").hidden = taskState.length > 0;
    taskState.forEach((task, index) => {
      const row = document.createElement("article");
      row.className = "task" + (task.done ? " done" : "");
      const prioClass = task.priority === "High" ? "high" : task.priority === "Medium" ? "med" : "low";
      const compare = task.compare
        ? `<p class="compare-note ${compareClass(task.compare.status)}"><b>${esc(task.compare.status)}</b> — ${esc(task.compare.evidence)}${task.compare.status !== "Completed" ? `<br>Next: ${esc(task.compare.next_step)}` : ""}</p>`
        : "";
      const supplies = task.supplies?.length
        ? `<p class="task-supplies"><span>Need:</span> ${task.supplies.map(esc).join(", ")}</p>`
        : "";
      row.innerHTML = `
        <input type="checkbox" ${task.done ? "checked" : ""} aria-label="${esc(task.title)}">
        <div>
          <div class="task-title">${esc(task.title)}</div>
          <div class="task-meta">
            <span class="prio ${prioClass}">${esc(task.priority)}</span>
            <span>${esc(task.category)}</span>
            <span>${task.minutes} min</span>
            ${task.diy_level ? `<span>${esc(task.diy_level)}</span>` : ""}
          </div>
          <p class="task-reason">${esc(task.reason)}</p>
          ${supplies}
          ${compare}
        </div>`;
      row.querySelector("input").addEventListener("change", (event) => {
        taskState[index].done = event.target.checked;
        renderTasks();
      });
      root.appendChild(row);
    });
    updateManualProgress();
  }

  function completenessLabel(percent) {
    if (percent === 100) return "Finished";
    if (percent >= 75) return "Mostly done";
    if (percent >= 50) return "Halfway";
    if (percent >= 25) return "Started";
    return "Just started";
  }

  function checklistMarkdown() {
    if (!analysisData) return "";
    const lines = [
      `# ${analysisData.room_type || "Room"} checklist`,
      "",
      analysisData.summary || "",
      "",
      `About ${analysisData.estimated_total_minutes} minutes · ${taskState.length} tasks`,
      "",
    ];
    if (analysisData.cautions?.length) {
      lines.push("## Before you start", "");
      analysisData.cautions.forEach((item) => lines.push(`- ${item}`));
      lines.push("");
    }
    lines.push("## Tasks", "");
    taskState.forEach((task) => {
      const mark = task.done ? "x" : " ";
      lines.push(`- [${mark}] ${task.title}`);
      lines.push(`  ${task.priority} · ${task.category} · ${task.minutes} min${task.diy_level ? ` · ${task.diy_level}` : ""}`);
      if (task.reason) lines.push(`  ${task.reason}`);
      if (task.supplies?.length) lines.push(`  Need: ${task.supplies.join(", ")}`);
      if (task.compare) {
        lines.push(`  Photo check: ${task.compare.status} — ${task.compare.evidence}`);
        if (task.compare.status !== "Completed") lines.push(`  Next: ${task.compare.next_step}`);
      }
      lines.push("");
    });
    lines.push("_Saved from Room Rescue. Photos aren’t kept on our servers._", "");
    return lines.join("\n");
  }

  function saveChecklist() {
    if (!analysisData) return;
    const blob = new Blob([checklistMarkdown()], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    const slug = String(analysisData.room_type || "room").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "room";
    link.href = url;
    link.download = `${slug}-checklist.md`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  function resetRoom() {
    analysisData = null;
    taskState = [];
    $("startPanel").classList.remove("has-plan");
    $("startHeading").textContent = "Start with a photo";
    $("results").hidden = true;
    $("afterSection").hidden = true;
    $("comparison").hidden = true;
    $("finishedNote").hidden = true;
    delete $("finishedNote").dataset.counted;
    $("emptyTasks").hidden = true;
    $("tasks").innerHTML = "";
    compareBtn.disabled = true;
    $("photo").scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function syncButtons() {
    analyzeBtn.disabled = !beforePhoto.files?.[0];
    compareBtn.disabled = !(afterPhoto.files?.[0] && analysisData && beforePhoto.files?.[0]);
  }

  bindDropzone($("beforeDrop"), beforePhoto);
  bindDropzone($("afterDrop"), afterPhoto);

  beforePhoto.addEventListener("change", () => {
    showPhoto(
      beforePhoto,
      "beforeChosen",
      "beforeDrop",
      "beforeFileName",
      "beforePreview",
      "beforeFallback",
      "beforePhotoNote",
      "Use the same angle later for a progress check."
    );
    syncButtons();
  });

  afterPhoto.addEventListener("change", () => {
    showPhoto(
      afterPhoto,
      "afterChosen",
      "afterDrop",
      "afterFileName",
      "afterPreview",
      "afterFallback",
      "afterPhotoNote",
      "Hidden areas stay open until a later photo."
    );
    syncButtons();
  });

  async function runAnalyze() {
    const file = beforePhoto.files?.[0];
    if (!file) return;

    analyzeBtn.disabled = true;
    setError("analyzeErrorBox", "analyzeError", "");
    $("analyzeWait").hidden = false;
    analyzeWait.start();

    const body = new FormData();
    body.append("image", file);
    body.append("room_hint", $("room").value);
    body.append("time_budget", $("budget").value);

    try {
      const data = await postForm("/api/analyze", body);
      analysisData = data;
      taskState = (data.tasks || []).map((task) => ({ ...task, done: false, compare: null }));
      $("roomTitle").textContent = data.room_type;
      $("summary").textContent = data.summary;
      $("planMeta").textContent = `${taskState.length} tasks · about ${data.estimated_total_minutes} min`;
      $("cautions").innerHTML = data.cautions?.length
        ? `<div class="caution"><b>Before you start</b>${data.cautions.map((item) => `<p>${esc(item)}</p>`).join("")}</div>`
        : "";
      $("startPanel").classList.add("has-plan");
      $("startHeading").textContent = "Before photo";
      renderTasks();
      $("results").hidden = false;
      $("afterSection").hidden = false;
      $("comparison").hidden = true;
      $("results").scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (error) {
      setError("analyzeErrorBox", "analyzeError", friendlyNetworkError(error));
    } finally {
      analyzeWait.stop();
      $("analyzeWait").hidden = true;
      syncButtons();
    }
  }

  async function runCompare() {
    const before = beforePhoto.files?.[0];
    const after = afterPhoto.files?.[0];
    if (!before || !after || !analysisData) return;

    compareBtn.disabled = true;
    setError("compareErrorBox", "compareError", "");
    $("compareWait").hidden = false;
    compareWait.start();

    const body = new FormData();
    body.append("before_image", before);
    body.append("after_image", after);
    body.append("room_type", analysisData.room_type || "room");
    body.append("tasks_json", JSON.stringify(analysisData.tasks));

    try {
      const data = await postForm("/api/compare", body);
      const byTitle = new Map(data.task_results.map((item) => [item.title.trim().toLowerCase(), item]));
      let newlyVerified = 0;
      taskState = taskState.map((task) => {
        const found = byTitle.get(task.title.trim().toLowerCase()) || null;
        const justCompleted = found?.status === "Completed" && task.compare?.status !== "Completed";
        if (justCompleted) newlyVerified += 1;
        return {
          ...task,
          done: found ? found.status === "Completed" : task.done,
          compare: found,
        };
      });

      const finished = data.completed_percentage === 100;
      const alreadyCounted = $("finishedNote").dataset.counted === "1";
      recordVerifiedWork(newlyVerified, finished && !alreadyCounted);
      if (finished) $("finishedNote").dataset.counted = "1";

      renderTasks();
      $("comparison").hidden = false;
      $("compareSummary").textContent = data.summary;
      $("kpiPercent").textContent = `${data.completed_percentage}%`;
      $("kpiDone").textContent = data.completed_tasks;
      $("kpiRemaining").textContent = data.total_tasks - data.completed_tasks;
      $("compareProgressBar").style.width = `${data.completed_percentage}%`;
      $("reportHeadline").textContent = finished ? "This room looks finished" : "What the photos show";
      $("reportMeta").textContent = completenessLabel(data.completed_percentage);
      $("encouragement").textContent = data.encouragement || "";
      $("successes").innerHTML = (data.successes?.length ? data.successes : ["Visible progress is recorded above."])
        .map((item) => `<li>${esc(item)}</li>`).join("");
      $("failures").innerHTML = (data.failures?.length ? data.failures : ["Nothing major left in the photo."])
        .map((item) => `<li>${esc(item)}</li>`).join("");
      $("nextAction").textContent = data.next_action || "";
      $("remainingTasksWrap").innerHTML = data.remaining_tasks?.length
        ? `<p class="note"><b>Still open</b><br>${data.remaining_tasks.map(esc).join("<br>")}</p>`
        : "";
      $("finishedNote").hidden = !finished;
      $("comparison").scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (error) {
      setError("compareErrorBox", "compareError", friendlyNetworkError(error));
    } finally {
      compareWait.stop();
      $("compareWait").hidden = true;
      syncButtons();
    }
  }

  analyzeBtn.addEventListener("click", runAnalyze);
  compareBtn.addEventListener("click", runCompare);
  $("analyzeRetry").addEventListener("click", runAnalyze);
  $("compareRetry").addEventListener("click", runCompare);
  $("saveChecklist").addEventListener("click", saveChecklist);
  $("printChecklist").addEventListener("click", () => window.print());
  $("newRoom").addEventListener("click", resetRoom);

  if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
      navigator.serviceWorker.register("/sw.js").catch(() => {
        /* installability is optional */
      });
    });
  }

  renderWorkSummary();
})();
