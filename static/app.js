(() => {
  const $ = (id) => document.getElementById(id);

  const beforePhoto = $("beforePhoto");
  const afterPhoto = $("afterPhoto");
  const analyzeBtn = $("analyze");
  const compareBtn = $("compare");

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

  function setError(id, message) {
    const el = $(id);
    if (!message) {
      el.hidden = true;
      el.textContent = "";
      return;
    }
    el.hidden = false;
    el.textContent = message;
  }

  function showPhoto(input, chosenId, dropId, nameId, previewId) {
    const file = input.files?.[0];
    if (!file) return;
    const preview = $(previewId);
    if (preview.src) URL.revokeObjectURL(preview.src);
    preview.src = URL.createObjectURL(file);
    $(nameId).textContent = file.name;
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

  beforePhoto.addEventListener("change", () => {
    showPhoto(beforePhoto, "beforeChosen", "beforeDrop", "beforeFileName", "beforePreview");
    analyzeBtn.disabled = !beforePhoto.files?.[0];
    compareBtn.disabled = !(afterPhoto.files?.[0] && analysisData && beforePhoto.files?.[0]);
  });

  afterPhoto.addEventListener("change", () => {
    showPhoto(afterPhoto, "afterChosen", "afterDrop", "afterFileName", "afterPreview");
    compareBtn.disabled = !(afterPhoto.files?.[0] && analysisData && beforePhoto.files?.[0]);
  });

  analyzeBtn.addEventListener("click", async () => {
    const file = beforePhoto.files?.[0];
    if (!file) return;

    analyzeBtn.disabled = true;
    setError("analyzeError", "");
    $("analyzeWait").hidden = false;
    analyzeWait.start();

    const body = new FormData();
    body.append("image", file);
    body.append("room_hint", $("room").value);
    body.append("time_budget", $("budget").value);

    try {
      const response = await fetch("/api/analyze", { method: "POST", body });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Could not build a checklist from that photo.");

      analysisData = data;
      taskState = data.tasks.map((task) => ({ ...task, done: false, compare: null }));
      $("roomTitle").textContent = data.room_type;
      $("summary").textContent = data.summary;
      $("planMeta").textContent = `${data.tasks.length} tasks · about ${data.estimated_total_minutes} min`;
      $("cautions").innerHTML = data.cautions?.length
        ? `<div class="caution"><b>Before you start</b>${data.cautions.map((item) => `<p>${esc(item)}</p>`).join("")}</div>`
        : "";
      $("startPanel").classList.add("has-plan");
      $("startHeading").textContent = "Before photo";
      renderTasks();
      $("results").hidden = false;
      $("afterSection").hidden = false;
      $("comparison").hidden = true;
      compareBtn.disabled = !afterPhoto.files?.[0];
      $("results").scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (error) {
      setError("analyzeError", error.message || "Analysis failed.");
    } finally {
      analyzeWait.stop();
      $("analyzeWait").hidden = true;
      analyzeBtn.disabled = !beforePhoto.files?.[0];
    }
  });

  compareBtn.addEventListener("click", async () => {
    const before = beforePhoto.files?.[0];
    const after = afterPhoto.files?.[0];
    if (!before || !after || !analysisData) return;

    compareBtn.disabled = true;
    setError("compareError", "");
    $("compareWait").hidden = false;
    compareWait.start();

    const body = new FormData();
    body.append("before_image", before);
    body.append("after_image", after);
    body.append("room_type", analysisData.room_type || "room");
    body.append("tasks_json", JSON.stringify(analysisData.tasks));

    try {
      const response = await fetch("/api/compare", { method: "POST", body });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Could not compare those photos.");

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
      setError("compareError", error.message || "Comparison failed.");
    } finally {
      compareWait.stop();
      $("compareWait").hidden = true;
      compareBtn.disabled = !(afterPhoto.files?.[0] && analysisData && beforePhoto.files?.[0]);
    }
  });

  renderWorkSummary();
})();
