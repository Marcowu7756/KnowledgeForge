(() => {
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

  let lastComposeDraftPath = "";
  let accessLane = "general";

  const LANE_HINTS = {
    general: "public / internal · 不含 SETV / Factor / AShare",
    proprietary: "含 restricted · SETV / FactorLib / AShareLib · 默认不可外发",
  };

  function setAccessLane(lane) {
    accessLane = lane === "proprietary" ? "proprietary" : "general";
    $$(".lane-btn").forEach((btn) => {
      btn.classList.toggle("active", btn.getAttribute("data-lane") === accessLane);
    });
    const hint = $("#lane-hint");
    if (hint) hint.textContent = LANE_HINTS[accessLane];
    const retrieveLane = $("#retrieve-lane");
    const composeLane = $("#compose-lane");
    if (retrieveLane) retrieveLane.value = accessLane;
    if (composeLane) composeLane.value = accessLane;
    document.body.dataset.accessLane = accessLane;
    const title = $("#knowledge-lane-title");
    if (title) {
      title.textContent =
        accessLane === "proprietary" ? "知识库 · 专有资产" : "知识库 · 通用";
    }
    refreshKnowledge();
    refreshTaxonomyTrees();
  }

  function showStage(name) {
    $$("[data-stage-panel]").forEach((el) => {
      const on = el.getAttribute("data-stage-panel") === name;
      el.hidden = !on;
      el.classList.toggle("active", on);
    });
    if (name === "settings") refreshStatus();
    if (name === "workshop") {
      refreshPackages();
      refreshArtifacts();
      refreshKnowledge();
      refreshMaintainKnowledge();
    }
    if (name === "tasks") refreshJobs();
  }

  function showPanel(name) {
    $$(".rail-item").forEach((btn) => {
      btn.classList.toggle("active", btn.getAttribute("data-panel") === name);
    });
    $$("[data-panel-view]").forEach((el) => {
      const on = el.getAttribute("data-panel-view") === name;
      el.hidden = !on;
      el.classList.toggle("active", on);
    });
    if (name === "distill") refreshMaintainKnowledge();
    if (name === "express") refreshKnowledge();
    if (name === "reconstruct" || name === "retrieve") refreshTaxonomyTree(name);
  }

  async function refreshTaxonomyTrees() {
    const reconstructOpen = !$('[data-panel-view="reconstruct"]')?.hidden;
    const retrieveOpen = !$('[data-panel-view="retrieve"]')?.hidden;
    if (reconstructOpen) await refreshTaxonomyTree("reconstruct");
    if (retrieveOpen) await refreshTaxonomyTree("retrieve");
  }

  function renderTaxNode(node, surface) {
    const hasKids = (node.children || []).length > 0;
    const twist = hasKids ? "▾" : "·";
    const kids = (node.children || []).map((c) => renderTaxNode(c, surface)).join("");
    return `<div class="tax-node" data-prefix="${escapeAttr(node.prefix_key || "")}">
      <button type="button" class="tax-node-row" data-tax-select="${escapeAttr(
        surface
      )}" data-prefix="${escapeAttr(node.prefix_key || "")}" data-label="${escapeAttr(
      node.label || ""
    )}" data-count="${Number(node.count || 0)}">
        <span class="tax-twist" data-tax-twist>${twist}</span>
        <span class="tax-label">${escapeHtml(node.label || "")}</span>
        <span class="tax-count">${Number(node.count || 0)}</span>
      </button>
      ${
        hasKids
          ? `<div class="tax-children">${kids}</div>`
          : ""
      }
    </div>`;
  }

  async function refreshTaxonomyTree(surface) {
    const tree = $(`#tax-tree-${surface}`);
    if (!tree) return;
    tree.innerHTML = `<p class="muted">加载大纲…</p>`;
    try {
      const data = await api(`/api/taxonomy/tree?lane=${encodeURIComponent(accessLane)}`);
      const roots = data.roots || [];
      if (!roots.length) {
        tree.innerHTML = `<p class="muted">当前访问层暂无带 taxonomy 的卡片</p>`;
        return;
      }
      tree.innerHTML = roots.map((n) => renderTaxNode(n, surface)).join("");
      tree.querySelectorAll("[data-tax-select]").forEach((btn) => {
        btn.addEventListener("click", (e) => {
          e.preventDefault();
          const prefix = btn.getAttribute("data-prefix") || "";
          selectTaxonomyPrefix(surface, prefix, btn.getAttribute("data-label") || "");
        });
      });
      tree.querySelectorAll("[data-tax-twist]").forEach((twist) => {
        twist.addEventListener("click", (e) => {
          e.stopPropagation();
          const row = twist.closest(".tax-node");
          const kids = row?.querySelector(":scope > .tax-children");
          if (!kids) return;
          const hidden = kids.hasAttribute("hidden");
          if (hidden) kids.removeAttribute("hidden");
          else kids.setAttribute("hidden", "");
          twist.textContent = hidden ? "▾" : "▸";
        });
      });
    } catch (err) {
      tree.innerHTML = `<p class="error-text">${escapeHtml(String(err.message || err))}</p>`;
    }
  }

  async function selectTaxonomyPrefix(surface, prefix, label) {
    const selected = $(`#tax-selected-${surface}`);
    if (selected) {
      selected.textContent = prefix
        ? `已选：${prefix.replace(/\//g, " › ")}`
        : "未选分组 · 全库";
    }
    $$(`#tax-tree-${surface} .tax-node-row`).forEach((btn) => {
      btn.classList.toggle("active", (btn.getAttribute("data-prefix") || "") === prefix);
    });
    if (surface === "reconstruct") {
      const input = $("#reconstruct-taxonomy-prefix");
      const view = $("#reconstruct-view");
      if (input) input.value = prefix;
      if (view && prefix) view.value = "taxonomy";
    }
    if (surface === "retrieve") {
      const input = $("#retrieve-taxonomy-prefix");
      if (input) input.value = prefix;
      await loadTaxonomyGroupCards(prefix);
    }
  }

  async function loadTaxonomyGroupCards(prefix) {
    const box = $("#tax-group-cards-retrieve");
    const list = $("#tax-group-list-retrieve");
    if (!box || !list) return;
    if (!prefix) {
      box.hidden = true;
      list.innerHTML = "";
      return;
    }
    box.hidden = false;
    list.innerHTML = `<li class="muted">加载本组…</li>`;
    try {
      const data = await api(
        `/api/taxonomy/cards?lane=${encodeURIComponent(accessLane)}&prefix=${encodeURIComponent(
          prefix
        )}`
      );
      const cards = data.cards || [];
      if (!cards.length) {
        list.innerHTML = `<li class="muted">本组无卡片</li>`;
        return;
      }
      list.innerHTML = cards
        .slice(0, 40)
        .map(
          (c) => `<li>
          <button type="button" class="linkish tax-card-pick" data-title="${escapeAttr(
            c.title || ""
          )}" data-path="${escapeAttr(c.path || "")}">${escapeHtml(
            c.title || c.path || ""
          )}</button>
          <span class="chip access-${escapeAttr(c.classification || "")}">${escapeHtml(
            c.classification || ""
          )}</span>
        </li>`
        )
        .join("");
      list.querySelectorAll(".tax-card-pick").forEach((btn) => {
        btn.addEventListener("click", () => {
          const q = $("#form-retrieve input[name='query']");
          if (q) q.value = btn.getAttribute("data-title") || "";
          const path = btn.getAttribute("data-path");
          if (path) openPreview(path);
        });
      });
    } catch (err) {
      list.innerHTML = `<li class="error-text">${escapeHtml(String(err.message || err))}</li>`;
    }
  }

  async function api(path, opts) {
    const res = await fetch(path, {
      headers: { "Content-Type": "application/json", ...(opts?.headers || {}) },
      ...opts,
    });
    const text = await res.text();
    let data;
    try {
      data = text ? JSON.parse(text) : {};
    } catch {
      data = { detail: text };
    }
    if (!res.ok) {
      const msg = data.detail || data.message || res.statusText;
      throw new Error(typeof msg === "string" ? msg : JSON.stringify(msg));
    }
    return data;
  }

  function writeOut(el, data, isError = false) {
    el.hidden = false;
    el.classList.toggle("error", isError);
    el.textContent =
      typeof data === "string" ? data : JSON.stringify(data, null, 2);
  }

  function ensureProgress(form) {
    let bar = form.querySelector(".progress");
    if (!bar) {
      bar = document.createElement("div");
      bar.className = "progress";
      bar.innerHTML =
        '<div class="progress-track"><div class="progress-fill"></div></div><div class="progress-label"></div>';
      form.appendChild(bar);
    }
    return bar;
  }

  function setProgress(form, pct, message, visible = true) {
    const bar = ensureProgress(form);
    bar.hidden = !visible;
    const fill = bar.querySelector(".progress-fill");
    const label = bar.querySelector(".progress-label");
    fill.style.width = `${Math.max(0, Math.min(100, pct))}%`;
    label.textContent = message || `${pct}%`;
  }

  async function pollJob(jobId, form, out, onDone) {
    for (;;) {
      const snap = await api(`/api/jobs/${jobId}`);
      setProgress(form, snap.progress || 0, `${snap.message} (${snap.progress || 0}%)`);
      if (snap.status === "done") {
        writeOut(out, snap.result, false);
        setProgress(form, 100, "完成", true);
        if (onDone) await onDone(snap.result, snap);
        return snap.result;
      }
      if (snap.status === "error") {
        writeOut(out, snap.error || "job failed", true);
        setProgress(form, snap.progress || 0, "失败", true);
        throw new Error(snap.error || "job failed");
      }
      await new Promise((r) => setTimeout(r, 400));
    }
  }

  function bindForm(formId, outId, buildRequest, onSuccess) {
    const form = $(formId);
    const out = $(outId);
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const btn = form.querySelector('button[type="submit"]');
      btn.disabled = true;
      setProgress(form, 2, "提交中…", true);
      try {
        const { path, body } = buildRequest(new FormData(form));
        const data = await api(path, {
          method: "POST",
          body: JSON.stringify({ ...body, async_job: true }),
        });
        if (data.job_id) {
          await pollJob(data.job_id, form, out, onSuccess);
        } else {
          writeOut(out, data, false);
          setProgress(form, 100, "完成", true);
          if (onSuccess) await onSuccess(data, null);
        }
        if (formId === "form-compile" || formId === "form-compose") {
          refreshPackages();
          refreshArtifacts();
        }
      } catch (err) {
        writeOut(out, String(err.message || err), true);
      } finally {
        btn.disabled = false;
      }
    });
  }

  async function refreshStatus() {
    const out = $("#out-status");
    const note = $("#settings-ui-note");
    const bindEl = $("#settings-bind-url");
    try {
      const health = await api("/api/health");
      const data = await api("/api/status");
      const bind = (health.ui && health.ui.bind) || "127.0.0.1";
      const url = `http://${bind}:${location.port || 8765}`;
      if (bindEl) bindEl.textContent = url;
      if (note) {
        const surface = (health.ui && health.ui.surface) || "web";
        note.textContent = `UI ${health.ui_version || ""} · ${surface} · browser-first${
          health.ui && health.ui.note ? ` — ${health.ui.note}` : ""
        }`;
      }
      writeOut(out, { health: { ui: health.ui, features: health.features }, ...data }, false);
    } catch (err) {
      writeOut(out, String(err.message || err), true);
    }
  }

  async function refreshPackages() {
    const ul = $("#package-list");
    if (!ul) return;
    try {
      const data = await api("/api/packages");
      ul.innerHTML =
        (data.items || [])
          .map(
            (it) =>
              `<li><strong>${escapeHtml(it.name)}</strong><br /><span>${escapeHtml(
                it.path
              )}</span></li>`
          )
          .join("") || "<li>暂无 package</li>";
    } catch {
      ul.innerHTML = "<li>无法读取 packages</li>";
    }
  }

  async function refreshArtifacts() {
    const ul = $("#artifact-list");
    if (!ul) return;
    try {
      const data = await api("/api/artifacts");
      const rows = [
        ...(data.compose || []).map(
          (c) =>
            `<li><button type="button" class="preview-link" data-path="${escapeAttr(
              c.path
            )}"><strong>${escapeHtml(c.kind)}</strong> — ${escapeHtml(
              c.path
            )}</button></li>`
        ),
        ...(data.media || []).map(
          (m) =>
            `<li><button type="button" class="preview-link" data-path="${escapeAttr(
              m.path
            )}"><strong>${escapeHtml(m.suffix)}</strong> — ${escapeHtml(
              m.path
            )}</button></li>`
        ),
      ];
      ul.innerHTML = rows.join("") || "<li>暂无产物</li>";
      ul.querySelectorAll(".preview-link").forEach((btn) => {
        btn.addEventListener("click", () => openPreview(btn.getAttribute("data-path")));
      });
    } catch {
      ul.innerHTML = "<li>无法读取产物</li>";
    }
  }

  async function refreshKnowledge() {
    const ul = $("#knowledge-list");
    if (!ul) return;
    try {
      const data = await api(
        `/api/knowledge?lane=${encodeURIComponent(accessLane)}&limit=24`
      );
      const items = data.items || [];
      ul.innerHTML =
        items
          .map(
            (item) => `<li>
          <button type="button" class="preview-link" data-path="${escapeAttr(item.path)}">
            <span class="access-chip access-${escapeAttr(item.classification)}">${escapeHtml(
              item.source_project || item.classification
            )}</span>
            <strong>${escapeHtml(item.name)}</strong>
          </button>
        </li>`
          )
          .join("") ||
        `<li class='muted'>当前层暂无卡片 — ${
          accessLane === "proprietary"
            ? "可先跑 setv snapshot|evolution|family / ecosystem ingest"
            : "可先获取资料"
        }</li>`;
      ul.querySelectorAll(".preview-link").forEach((btn) => {
        btn.addEventListener("click", () =>
          openPreview(btn.getAttribute("data-path"))
        );
      });
    } catch {
      ul.innerHTML = "<li>无法读取知识库</li>";
    }
  }

  async function refreshMaintainKnowledge() {
    const ul = $("#maintain-knowledge-list");
    if (!ul) return;
    try {
      const data = await api(`/api/knowledge?lane=all&limit=40`);
      const items = [...(data.general || []), ...(data.proprietary || [])];
      ul.innerHTML =
        items
          .map(
            (item) => `<li class="maintain-row">
          <button type="button" class="preview-link" data-path="${escapeAttr(item.path)}">
            <span class="access-chip access-${escapeAttr(item.classification)}">${escapeHtml(
              item.source_project || item.classification
            )}</span>
            <strong>${escapeHtml(item.name)}</strong>
          </button>
          <button type="button" class="btn ghost btn-sm knowledge-delete" data-path="${escapeAttr(
            item.path
          )}">删除</button>
        </li>`
          )
          .join("") || "<li class='muted'>暂无卡片可维护</li>";
      ul.querySelectorAll(".preview-link").forEach((btn) => {
        btn.addEventListener("click", () =>
          openPreview(btn.getAttribute("data-path"))
        );
      });
      ul.querySelectorAll(".knowledge-delete").forEach((btn) => {
        btn.addEventListener("click", () =>
          deleteKnowledgeCard(btn.getAttribute("data-path"))
        );
      });
    } catch {
      ul.innerHTML = "<li>无法读取知识库</li>";
    }
  }

  async function deleteKnowledgeCard(path) {
    if (!path) return;
    const name = path.split(/[/\\]/).pop() || path;
    if (
      !confirm(
        `删除知识卡？\n${name}\n\n仅删除；新增/更新请重新获取。\n此操作不可撤销。`
      )
    ) {
      return;
    }
    const status = $("#maintain-status");
    try {
      const data = await api("/api/knowledge", {
        method: "DELETE",
        body: JSON.stringify({ paths: [path], dry_run: false }),
      });
      if (status) {
        status.hidden = false;
        status.textContent = `已删除 ${data.deleted_count || 1} 张 · audit ${
          data.audit_path || ""
        }`;
      }
      refreshMaintainKnowledge();
      refreshKnowledge();
    } catch (err) {
      if (status) {
        status.hidden = false;
        status.textContent = `删除失败：${err.message || err}`;
      } else {
        alert(`删除失败：${err.message || err}`);
      }
    }
  }

  async function tryExport(path) {
    if (!path) return;
    try {
      const res = await fetch(`/api/export?path=${encodeURIComponent(path)}`);
      if (!res.ok) {
        const text = await res.text();
        let msg = text;
        try {
          msg = JSON.parse(text).detail || text;
        } catch {
          /* keep */
        }
        alert(`导出被拒绝：${msg}`);
        return;
      }
      const blob = await res.blob();
      const warn = res.headers.get("X-KF-Export-Warning");
      if (warn && !confirm(`${warn}\n\n仍要下载吗？`)) return;
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = path.split(/[/\\]/).pop() || "export.bin";
      a.click();
      URL.revokeObjectURL(a.href);
    } catch (err) {
      alert(`导出失败：${err.message || err}`);
    }
  }

  const ACTION_LABELS = {
    capture: "获取",
    compile: "沉淀",
    reconstruct: "重组",
    retrieve: "检索",
    compose: "表达",
  };

  async function refreshJobs() {
    const ul = $("#job-list");
    if (!ul) return;
    try {
      const data = await api("/api/jobs?limit=40");
      const items = data.items || [];
      ul.innerHTML =
        items
          .map(
            (job) => `<li class="job-row">
        <button type="button" class="job-row-btn" data-job-id="${escapeAttr(job.id)}">
          <span class="job-status job-status-${escapeAttr(job.status)}">${escapeHtml(
              job.status
            )}</span>
          <strong>${escapeHtml(ACTION_LABELS[job.action] || job.action)}</strong>
          <span class="job-meta">${escapeHtml(job.message)} · ${job.progress || 0}%</span>
          <span class="job-time">${escapeHtml(job.updated || job.created || "")}</span>
        </button>
      </li>`
          )
          .join("") || "<li class='muted'>暂无任务 — 在车间提交长任务后会出现在这里</li>";
      ul.querySelectorAll(".job-row-btn").forEach((btn) => {
        btn.addEventListener("click", () =>
          showJobDetail(btn.getAttribute("data-job-id"))
        );
      });
    } catch {
      ul.innerHTML = "<li>无法读取任务列表</li>";
    }
  }

  async function showJobDetail(jobId) {
    const detail = $("#out-job-detail");
    const previewBox = $("#job-preview");
    const previewBody = $("#job-preview-body");
    if (!detail) return;
    try {
      const snap = await api(`/api/jobs/${jobId}`);
      writeOut(detail, snap, snap.status === "error");
      if (previewBox) previewBox.hidden = true;
      if (previewBody) previewBody.innerHTML = "";
      if (snap.status === "done" && snap.action === "compose" && snap.result?.draft) {
        await renderInlinePreview(snap.result.draft, previewBody, previewBox);
      }
    } catch (err) {
      writeOut(detail, String(err.message || err), true);
    }
  }

  async function renderInlinePreview(path, bodyEl, boxEl) {
    if (!path || !bodyEl || !boxEl) return;
    boxEl.hidden = false;
    bodyEl.innerHTML = "<p class='muted'>加载中…</p>";
    try {
      const data = await api(`/api/preview?path=${encodeURIComponent(path)}`);
      if (data.kind === "text") {
        bodyEl.innerHTML = `<pre class="preview-text compose-inline-text">${escapeHtml(
          data.text || ""
        )}</pre>`;
      } else {
        bodyEl.innerHTML = `<p class="muted">非文本产物 — 请用全屏或产物列表打开。</p>`;
      }
      lastComposeDraftPath = path;
    } catch (err) {
      bodyEl.innerHTML = `<p class="error-text">${escapeHtml(String(err.message || err))}</p>`;
    }
  }

  async function showComposeInlinePreview(path) {
    await renderInlinePreview(
      path,
      $("#compose-preview-body"),
      $("#compose-preview")
    );
  }

  function escapeHtml(s) {
    return String(s)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  function escapeAttr(s) {
    return escapeHtml(s).replaceAll("'", "&#39;");
  }

  async function openPreview(path) {
    const modal = $("#preview-modal");
    const body = $("#preview-body");
    const title = $("#preview-title");
    modal.hidden = false;
    title.textContent = path;
    body.innerHTML = "<p class='muted'>加载中…</p>";
    try {
      const data = await api(`/api/preview?path=${encodeURIComponent(path)}`);
      const chip = data.access
        ? `<span class="access-chip access-${escapeAttr(
            data.access.classification
          )}">${escapeHtml(
            data.access.source_project || data.access.classification
          )}</span>`
        : "";
      title.innerHTML = `${chip} ${escapeHtml(data.name || path)}`;
      const exportBtn = data.access?.export_external_allowed
        ? `<p><button type="button" class="btn ghost btn-sm" id="modal-export-btn">导出到本机下载</button></p>`
        : `<p class="muted">外发导出已关闭（${escapeHtml(
            data.access?.policy?.export || "local_only"
          )}）— 仅可在 KF 内预览。</p>`;
      if (data.kind === "text") {
        body.innerHTML = `${exportBtn}<pre class="preview-text">${escapeHtml(
          data.text || ""
        )}</pre>`;
      } else if (
        data.suffix === ".gif" ||
        data.suffix === ".png" ||
        data.suffix === ".jpg" ||
        data.suffix === ".jpeg" ||
        data.suffix === ".webp"
      ) {
        body.innerHTML = `${exportBtn}<img class="preview-media" src="${data.file_url}" alt="${escapeAttr(
          data.name
        )}" />`;
      } else if (data.suffix === ".wav") {
        body.innerHTML = `${exportBtn}<audio class="preview-media" controls src="${data.file_url}"></audio>`;
      } else {
        body.innerHTML = `${exportBtn}<p><a href="${data.file_url}" target="_blank" rel="noopener">打开文件</a></p>`;
      }
      $("#modal-export-btn")?.addEventListener("click", () => tryExport(path));
    } catch (err) {
      body.innerHTML = `<p class="error-text">${escapeHtml(String(err.message || err))}</p>`;
    }
  }

  function closePreview() {
    const modal = $("#preview-modal");
    modal.hidden = true;
    $("#preview-body").innerHTML = "";
  }

  $$("[data-stage]").forEach((el) => {
    el.addEventListener("click", () => showStage(el.getAttribute("data-stage")));
  });
  $$(".rail-item").forEach((btn) => {
    btn.addEventListener("click", () => showPanel(btn.getAttribute("data-panel")));
  });
  $("#preview-close")?.addEventListener("click", closePreview);
  $("#preview-modal")?.addEventListener("click", (e) => {
    if (e.target.id === "preview-modal") closePreview();
  });
  $("#compose-preview-modal")?.addEventListener("click", () => {
    if (lastComposeDraftPath) openPreview(lastComposeDraftPath);
  });
  $("#job-preview-modal")?.addEventListener("click", () => {
    if (lastComposeDraftPath) openPreview(lastComposeDraftPath);
  });

  bindForm("#form-capture", "#out-capture", (fd) => ({
    path: "/api/capture",
    body: { kind: fd.get("kind"), target: fd.get("target") },
  }));

  bindForm("#form-compile", "#out-compile", (fd) => ({
    path: "/api/compile",
    body: {
      path: fd.get("path"),
      from_card: true,
      animate: fd.get("animate") === "on",
      fast: true,
    },
  }));

  bindForm("#form-reconstruct", "#out-reconstruct", (fd) => ({
    path: "/api/reconstruct",
    body: {
      from_index: true,
      view: fd.get("view"),
      taxonomy_prefix: (fd.get("taxonomy_prefix") || "").toString().trim() || null,
    },
  }));

  bindForm("#form-retrieve", "#out-retrieve", (fd) => ({
    path: "/api/retrieve",
    body: {
      query: fd.get("query"),
      top_k: Number(fd.get("top_k") || 5),
      access_lane: fd.get("access_lane") || accessLane,
      taxonomy_prefix: (fd.get("taxonomy_prefix") || "").toString().trim() || null,
    },
  }));

  $$("[data-tax-refresh]").forEach((btn) => {
    btn.addEventListener("click", () => refreshTaxonomyTree(btn.getAttribute("data-tax-refresh")));
  });
  $("#reconstruct-tax-clear")?.addEventListener("click", () => {
    selectTaxonomyPrefix("reconstruct", "", "");
  });
  $("#retrieve-tax-clear")?.addEventListener("click", () => {
    selectTaxonomyPrefix("retrieve", "", "");
  });

  function renderMultiCardColumn(card, role) {
    const tax = (card.taxonomy_path || []).join(" › ");
    const checked = role === "member" ? "checked" : "";
    return `<article class="multi-card ${role === "family" ? "family" : ""}">
      <label class="multi-card-select">
        <input type="checkbox" class="multi-card-check" data-path="${escapeAttr(
          card.path
        )}" ${checked} />
        <span>纳入 Compose</span>
      </label>
      <div class="multi-card-head">
        <span class="chip">${escapeHtml(card.asset_class || role)}</span>
        <span class="chip access-${escapeAttr(card.classification || "")}">${escapeHtml(
          card.source_project || card.classification || ""
        )}</span>
      </div>
      <h4>${escapeHtml(card.title || card.artifact_id || "")}</h4>
      <div class="muted">${escapeHtml(card.artifact_id || "")}</div>
      <div class="muted">${escapeHtml(tax)}</div>
      <pre class="multi-card-excerpt">${escapeHtml(card.excerpt || "")}</pre>
      <button type="button" class="btn ghost btn-sm preview-link" data-path="${escapeAttr(
        card.path
      )}">全屏预览</button>
    </article>`;
  }

  function selectedMultiCardPaths() {
    return [...document.querySelectorAll(".multi-card-check:checked")]
      .map((el) => el.getAttribute("data-path"))
      .filter(Boolean);
  }

  const LAYOUT_LS_KEY = "kf.ui.multi_card_layout.v0";
  let layoutSaveTimer = null;
  let suppressLayoutAutosave = false;

  function currentLayoutPayload() {
    const idEl = $("#family-artifact-id");
    const q = $("#family-compose-query");
    const kind = $("#family-compose-kind");
    return {
      artifact_id: String(idEl?.value || "").trim(),
      selected_paths: selectedMultiCardPaths(),
      compose_query: String(q?.value || ""),
      compose_kind: String(kind?.value || "lecture"),
    };
  }

  function setLayoutStatus(text) {
    const el = $("#multi-card-layout-status");
    if (!el) return;
    if (!text) {
      el.hidden = true;
      el.textContent = "";
      return;
    }
    el.hidden = false;
    el.textContent = text;
  }

  function mirrorLayoutLocal(layout) {
    try {
      localStorage.setItem(LAYOUT_LS_KEY, JSON.stringify(layout));
    } catch {
      /* ignore quota */
    }
  }

  async function persistMultiCardLayout(opts = {}) {
    const body = currentLayoutPayload();
    if (!body.artifact_id && !(opts.force || false)) return null;
    try {
      const data = await api("/api/ui/layout/multi-card", {
        method: "PUT",
        body: JSON.stringify(body),
      });
      mirrorLayoutLocal(data.layout || body);
      if (!opts.silent) {
        setLayoutStatus(
          `H1c 已记住 · ${data.layout?.artifact_id || body.artifact_id} · ${
            (data.layout?.selected_paths || body.selected_paths || []).length
          } 卡`
        );
      }
      return data.layout;
    } catch (err) {
      setLayoutStatus(`布局保存失败：${err.message || err}`);
      return null;
    }
  }

  function scheduleLayoutPersist() {
    if (suppressLayoutAutosave) return;
    clearTimeout(layoutSaveTimer);
    layoutSaveTimer = setTimeout(() => persistMultiCardLayout({ silent: true }), 400);
  }

  function applySelectedPaths(paths) {
    const want = new Set((paths || []).map(String));
    document.querySelectorAll(".multi-card-check").forEach((el) => {
      const p = el.getAttribute("data-path");
      el.checked = want.has(p);
    });
  }

  async function loadFamilyMultiCard(artifactId, opts = {}) {
    const row = $("#multi-card-row");
    const meta = $("#multi-card-meta");
    const composeForm = $("#form-family-compose");
    if (!row || !meta || !artifactId) return;
    meta.hidden = false;
    meta.textContent = "加载中…";
    row.hidden = false;
    row.innerHTML = "";
    if (composeForm) composeForm.hidden = true;
    const lane = accessLane === "general" ? "general" : "proprietary";
    try {
      const data = await api(
        `/api/family/${encodeURIComponent(artifactId)}?lane=${encodeURIComponent(
          lane
        )}&limit=8`
      );
      const cols = [];
      if (data.family) cols.push(renderMultiCardColumn(data.family, "family"));
      for (const m of data.members || []) cols.push(renderMultiCardColumn(m, "member"));
      row.innerHTML = cols.join("") || "<p class='muted'>无成员卡</p>";
      row.querySelectorAll(".preview-link").forEach((btn) => {
        btn.addEventListener("click", () => openPreview(btn.getAttribute("data-path")));
      });
      const n = (data.members || []).length;
      meta.textContent = `${data.family?.artifact_id || artifactId} · ${n} 成员 · ${
        data.resolve?.strategy || ""
      } · lane=${data.lane}`;
      if (composeForm && n > 0) {
        composeForm.hidden = false;
        const q = $("#family-compose-query");
        if (q) {
          if (opts.compose_query != null && String(opts.compose_query).trim()) {
            q.value = opts.compose_query;
          } else if (!q.value) {
            q.value = `${data.family?.artifact_id || artifactId} 状态家族观察`;
          }
        }
        const kind = $("#family-compose-kind");
        if (kind && opts.compose_kind) kind.value = opts.compose_kind;
      }
      if (Array.isArray(opts.selected_paths)) {
        applySelectedPaths(opts.selected_paths);
      }
      if (!opts.skipPersist) scheduleLayoutPersist();
    } catch (err) {
      meta.textContent = `展开失败：${err.message || err}`;
      row.innerHTML = "";
    }
  }

  async function restoreMultiCardLayout() {
    let layout = null;
    try {
      const data = await api("/api/ui/layout/multi-card");
      layout = data.layout;
    } catch {
      try {
        layout = JSON.parse(localStorage.getItem(LAYOUT_LS_KEY) || "null");
      } catch {
        layout = null;
      }
    }
    if (!layout?.artifact_id) return;
    const idEl = $("#family-artifact-id");
    if (idEl) idEl.value = layout.artifact_id;
    if (accessLane !== "proprietary") setAccessLane("proprietary");
    suppressLayoutAutosave = true;
    try {
      await loadFamilyMultiCard(layout.artifact_id, {
        selected_paths: layout.selected_paths || [],
        compose_query: layout.compose_query || "",
        compose_kind: layout.compose_kind || "lecture",
        skipPersist: true,
      });
      setLayoutStatus(
        `H1c 已恢复 · ${layout.artifact_id}${
          layout.updated ? ` · ${layout.updated}` : ""
        }`
      );
    } finally {
      suppressLayoutAutosave = false;
    }
  }

  $("#form-family")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const id = String(fd.get("artifact_id") || "").trim();
    if (!id) return;
    if (accessLane !== "proprietary") setAccessLane("proprietary");
    await loadFamilyMultiCard(id);
  });

  $("#family-layout-save")?.addEventListener("click", () => {
    persistMultiCardLayout({ force: true });
  });
  $("#family-layout-clear")?.addEventListener("click", async () => {
    try {
      await api("/api/ui/layout/multi-card", { method: "DELETE" });
      try {
        localStorage.removeItem(LAYOUT_LS_KEY);
      } catch {
        /* ignore */
      }
      setLayoutStatus("H1c 布局已清除");
    } catch (err) {
      setLayoutStatus(`清除失败：${err.message || err}`);
    }
  });

  $("#family-select-all")?.addEventListener("click", () => {
    document.querySelectorAll(".multi-card-check").forEach((el) => {
      el.checked = true;
    });
    scheduleLayoutPersist();
  });
  $("#family-select-none")?.addEventListener("click", () => {
    document.querySelectorAll(".multi-card-check").forEach((el) => {
      el.checked = false;
    });
    scheduleLayoutPersist();
  });

  $("#multi-card-row")?.addEventListener("change", (e) => {
    if (e.target?.classList?.contains("multi-card-check")) scheduleLayoutPersist();
  });
  $("#family-compose-query")?.addEventListener("change", scheduleLayoutPersist);
  $("#family-compose-kind")?.addEventListener("change", scheduleLayoutPersist);

  bindForm(
    "#form-family-compose",
    "#out-family-compose",
    (fd) => {
      const paths = selectedMultiCardPaths();
      if (!paths.length) throw new Error("请至少勾选一张卡");
      return {
        path: "/api/compose",
        body: {
          query: fd.get("query"),
          kind: fd.get("kind") || "lecture",
          access_lane: "proprietary",
          source_paths: paths,
        },
      };
    },
    async (result) => {
      await persistMultiCardLayout({ silent: true });
      if (result?.draft) {
        await showComposeInlinePreview(result.draft);
        refreshArtifacts();
      }
    }
  );

  bindForm(
    "#form-compose",
    "#out-compose",
    (fd) => ({
      path: "/api/compose",
      body: {
        query: fd.get("query"),
        kind: fd.get("kind"),
        top_k: 5,
        access_lane: fd.get("access_lane") || accessLane,
      },
    }),
    async (result) => {
      if (result?.draft) {
        await showComposeInlinePreview(result.draft);
      }
    }
  );

  $$(".lane-btn").forEach((btn) => {
    btn.addEventListener("click", () =>
      setAccessLane(btn.getAttribute("data-lane"))
    );
  });
  $("#compose-export-btn")?.addEventListener("click", () => {
    if (lastComposeDraftPath) tryExport(lastComposeDraftPath);
  });

  setAccessLane("general");

  api("/api/health")
    .then((h) => {
      const web = h.features && h.features.web_ui ? " · Web UI" : "";
      $("#health-line").textContent = `${h.product} · ${h.engine} · UI ${h.ui_version || ""}${web}`;
    })
    .catch(() => {
      $("#health-line").textContent = "API offline";
    });

  restoreMultiCardLayout().catch(() => {});
})();
