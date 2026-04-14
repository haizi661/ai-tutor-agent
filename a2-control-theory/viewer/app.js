(function () {
  const data = window.A2_GRAPH_VIEWER_DATA;
  const graphElement = document.getElementById("graph");
  const detailElement = document.getElementById("detail-content");
  const statsElement = document.getElementById("stats-grid");
  const legendElement = document.getElementById("legend");
  const rootNotesElement = document.getElementById("root-notes");
  const resultsElement = document.getElementById("search-results");
  const searchInput = document.getElementById("search-input");
  const statusElement = document.getElementById("graph-status");
  const fitGraphButton = document.getElementById("fit-graph");
  const resetFiltersButton = document.getElementById("reset-filters");
  const toggleSubgraphButton = document.getElementById("toggle-subgraph");
  const query = new URLSearchParams(window.location.search);
  const embeddedMode = query.get("embedded") === "1";
  const topicHint = String(query.get("topic") || "").trim();
  const focusHint = String(query.get("focus") || "").trim();

  if (!data || !window.ForceGraph) {
    detailElement.innerHTML = "<p>无法加载图谱数据或渲染库。</p>";
    return;
  }

  /* ─── 色彩系统适配方案C ─── */
  const isDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  const canvasBg = isDark ? "#14161c" : "#fafbfc";

  const nodes = data.graph.nodes.map((node) => ({ ...node }));
  const links = data.graph.links.map((link) => ({ ...link }));
  const noteMap = data.notes || {};
  const nodeById = new Map(nodes.map((node) => [node.id, node]));
  const categories = [...new Set(nodes.map((node) => node.category))];

  /* 品类颜色：浅填充 + 深描边 */
  const categoryPalette = [
    { fill: isDark ? "#1e2e46" : "#e8f0fa", stroke: isDark ? "#6aa0e0" : "#3a72b5", base: "#4a90d9" },
    { fill: isDark ? "#1a3028" : "#e6f5ee", stroke: isDark ? "#5ec498" : "#2e8a5f", base: "#45b07c" },
    { fill: isDark ? "#302418" : "#fdf2e4", stroke: isDark ? "#eaa44e" : "#c07520", base: "#e8943a" },
    { fill: isDark ? "#301c1c" : "#fce8e8", stroke: isDark ? "#e07070" : "#b53a3a", base: "#d95b5b" },
    { fill: isDark ? "#261e38" : "#f0ebf8", stroke: isDark ? "#a884dd" : "#6f4eaa", base: "#8e6ec5" },
    { fill: isDark ? "#302a16" : "#fbf4df", stroke: isDark ? "#e4c04a" : "#b08a14", base: "#d4a82a" },
    { fill: isDark ? "#1a2e2d" : "#e3f4f3", stroke: isDark ? "#4ec4bc" : "#288580", base: "#36a8a0" },
    { fill: isDark ? "#301c24" : "#fbe9ef", stroke: isDark ? "#e08aa4" : "#b04a6c", base: "#d46b8a" },
  ];
  const categoryColors = Object.fromEntries(
    categories.map((cat, i) => [cat, categoryPalette[i % categoryPalette.length]])
  );

  let selectedCategories = new Set(categories);
  let selectedNodeId = null;
  let hoverNodeId = null;
  let hoverLinkKey = null;
  let subgraphMode = embeddedMode;
  let searchFilter = "";

  if (embeddedMode) document.body.classList.add("embedded");

  /* ─── Tooltip ─── */
  const tooltip = document.createElement("div");
  tooltip.className = "graph-tooltip";
  tooltip.innerHTML = '<div class="graph-tooltip-title"></div><div class="graph-tooltip-meta"></div>';
  document.body.appendChild(tooltip);

  /* ─── 力导图 ─── */
  const graph = window
    .ForceGraph()(graphElement)
    .nodeId("id")
    .nodeLabel("")
    .nodeVal((node) => node.size)
    .nodeCanvasObject((node, ctx, globalScale) => {
      drawNode(node, ctx, globalScale);
    })
    .nodePointerAreaPaint((node, color, ctx) => {
      const r = Math.sqrt(node.size || 4) * 2.5 + 2;
      ctx.beginPath();
      ctx.arc(node.x, node.y, r, 0, 2 * Math.PI);
      ctx.fillStyle = color;
      ctx.fill();
    })
    .linkWidth((link) => getLinkWidth(link))
    .linkColor((link) => getLinkColor(link))
    .linkCanvasObjectMode(() => "after")
    .linkCanvasObject((link, ctx, globalScale) => {
      drawLinkLabel(link, ctx, globalScale);
    })
    .backgroundColor(canvasBg)
    .cooldownTicks(120)
    .onNodeHover((node, prevNode) => {
      hoverNodeId = node ? node.id : null;
      graphElement.style.cursor = node ? "pointer" : "default";

      if (node) {
        const pal = categoryColors[node.category] || categoryPalette[0];
        tooltip.querySelector(".graph-tooltip-title").textContent = node.name;
        tooltip.querySelector(".graph-tooltip-meta").textContent = node.category;
        tooltip.classList.add("is-visible");
      } else {
        tooltip.classList.remove("is-visible");
      }

      graph.nodeCanvasObject((n, ctx, gs) => drawNode(n, ctx, gs));
      graph.linkWidth((link) => getLinkWidth(link));
      graph.linkColor((link) => getLinkColor(link));
    })
    .onLinkHover((link) => {
      hoverLinkKey = link ? getLinkKey(link) : null;
    })
    .onNodeClick((node) => {
      selectNode(node.id, true);
    });

  /* tooltip跟随鼠标 */
  graphElement.addEventListener("mousemove", (e) => {
    tooltip.style.left = e.clientX + 12 + "px";
    tooltip.style.top = e.clientY + 12 + "px";
  });

  /* ─── ResizeObserver ─── */
  const resizeObserver = new ResizeObserver(() => {
    if (graphElement.offsetWidth > 0 && graphElement.offsetHeight > 0) {
      graph.width(graphElement.offsetWidth);
      graph.height(graphElement.offsetHeight);
    }
  });
  resizeObserver.observe(graphElement);

  /* ─── 节点渲染：浅填充 + 深描边 ─── */
  function drawNode(node, ctx, globalScale) {
    const pal = categoryColors[node.category] || categoryPalette[0];
    const isSelected = selectedNodeId === node.id;
    const isHovered = hoverNodeId === node.id;
    const isSearchDimmed = searchFilter && !nodeMatchesSearch(node, searchFilter);

    const baseR = Math.sqrt(node.size || 4) * 2.5;
    const r = isSelected ? baseR + 1.5 : isHovered ? baseR + 0.8 : baseR;

    ctx.save();
    if (isSearchDimmed) ctx.globalAlpha = 0.15;

    ctx.beginPath();
    ctx.arc(node.x, node.y, r, 0, 2 * Math.PI);

    if (isSelected || isHovered) {
      ctx.fillStyle = pal.stroke;
      ctx.strokeStyle = isSelected ? (isDark ? "#fff" : "#1a1d24") : pal.stroke;
      ctx.lineWidth = isSelected ? 1.5 : 0.8;
    } else {
      ctx.fillStyle = pal.fill;
      ctx.strokeStyle = pal.stroke;
      ctx.lineWidth = 0.8;
    }
    ctx.fill();
    ctx.stroke();

    /* 标签 */
    const showLabel = globalScale > 1.8 || isSelected || isHovered;
    if (showLabel) {
      const fontSize = Math.max(3, 11 / globalScale);
      ctx.font = `${isSelected || isHovered ? 600 : 400} ${fontSize}px "PingFang SC", "Noto Sans SC", sans-serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "top";
      ctx.fillStyle = isSelected || isHovered
        ? (isDark ? "#e4e6ec" : "#1a1d24")
        : (isDark ? "#a0a4b0" : "#5a5e6a");
      ctx.fillText(node.name, node.x, node.y + r + 1.5);
    }

    ctx.restore();
  }

  function nodeMatchesSearch(node, keyword) {
    if (!keyword) return true;
    const note = noteMap[node.id] || {};
    const haystack = [node.name, node.id, ...(note.aliases || []), ...(note.tags || [])]
      .join(" ").toLowerCase();
    return haystack.includes(keyword.toLowerCase());
  }

  function normalizeText(value) {
    return String(value || "").toLowerCase().replace(/\s+/g, "").replace(/[（）()\-_.·、，,]/g, "");
  }

  function scoreNodeAgainstHint(node, hint) {
    const note = noteMap[node.id] || {};
    const keyword = normalizeText(hint);
    if (!keyword) return 0;
    const aliases = Array.isArray(note.aliases) ? note.aliases : [];
    const haystacks = [
      node.id, node.name, note.title, note.summary,
      ...(note.tags || []),
      ...aliases,
      ...(note.prerequisites || []),
      ...(note.neighbors || []),
    ].map(normalizeText);

    if (haystacks.some((item) => item === keyword)) return 12;
    if (haystacks.some((item) => item.startsWith(keyword) || keyword.startsWith(item))) return 8;
    if (haystacks.some((item) => item.includes(keyword) || keyword.includes(item))) return 5;
    return 0;
  }

  function resolveInitialNodeId() {
    const candidates = [focusHint, topicHint].filter(Boolean);
    let bestNode = null;
    let bestScore = 0;
    candidates.forEach((hint, index) => {
      nodes.forEach((node) => {
        const score = scoreNodeAgainstHint(node, hint) - index * 0.25;
        if (score > bestScore) { bestNode = node; bestScore = score; }
      });
    });
    if (bestNode) return bestNode.id;
    if (data.meta.root_notes && data.meta.root_notes.length > 0) return data.meta.root_notes[0];
    return nodes[0]?.id || "";
  }

  function getLinkKey(link) {
    const source = typeof link.source === "object" ? link.source.id : link.source;
    const target = typeof link.target === "object" ? link.target.id : link.target;
    return `${source}=>${target}`;
  }

  function getLinkColor(link) {
    const source = typeof link.source === "object" ? link.source.id : link.source;
    const target = typeof link.target === "object" ? link.target.id : link.target;
    if (selectedNodeId && (source === selectedNodeId || target === selectedNodeId)) {
      return isDark ? "rgba(110, 160, 245, 0.7)" : "rgba(59, 110, 232, 0.5)";
    }
    if (hoverNodeId && (source === hoverNodeId || target === hoverNodeId)) {
      return isDark ? "rgba(110, 160, 245, 0.45)" : "rgba(59, 110, 232, 0.3)";
    }
    return isDark ? "rgba(100, 110, 130, 0.18)" : "rgba(140, 150, 170, 0.22)";
  }

  function getLinkWidth(link) {
    const source = typeof link.source === "object" ? link.source.id : link.source;
    const target = typeof link.target === "object" ? link.target.id : link.target;
    if (selectedNodeId && (source === selectedNodeId || target === selectedNodeId)) return 2.4;
    if (hoverNodeId && (source === hoverNodeId || target === hoverNodeId)) return 1.8;
    return 0.6 + (link.weight || 1) * 0.12;
  }

  function drawLinkLabel(link, ctx) {
    const label = (link.relation_label || "").trim();
    if (!label) return;
    const source = link.source;
    const target = link.target;
    if (!source || !target || typeof source !== "object" || typeof target !== "object" ||
      !Number.isFinite(source.x) || !Number.isFinite(source.y) ||
      !Number.isFinite(target.x) || !Number.isFinite(target.y)) return;

    const midX = (source.x + target.x) / 2;
    const midY = (source.y + target.y) / 2;
    const dx = target.x - source.x;
    const dy = target.y - source.y;
    const angle = Math.atan2(dy, dx);
    const normalizedAngle = Math.abs(angle) > Math.PI / 2 ? angle + Math.PI : angle;
    const active =
      hoverLinkKey === getLinkKey(link) ||
      (selectedNodeId && (source.id === selectedNodeId || target.id === selectedNodeId));

    const fontSize = active ? 3.6 : 2.9;
    const paddingX = active ? 2.1 : 1.8;
    const paddingY = active ? 1.15 : 0.95;

    ctx.save();
    ctx.translate(midX, midY);
    ctx.rotate(normalizedAngle);
    ctx.font = `${active ? 700 : 400} ${fontSize}px "PingFang SC", "Noto Sans SC", sans-serif`;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";

    const metrics = ctx.measureText(label);
    const boxWidth = metrics.width + paddingX * 2;
    const boxHeight = fontSize + paddingY * 2;

    ctx.fillStyle = isDark
      ? (active ? "rgba(26, 29, 36, 0.92)" : "rgba(26, 29, 36, 0.72)")
      : (active ? "rgba(255, 255, 255, 0.95)" : "rgba(255, 255, 255, 0.82)");
    ctx.strokeStyle = active
      ? (isDark ? "rgba(110, 160, 245, 0.6)" : "rgba(59, 110, 232, 0.4)")
      : (isDark ? "rgba(100, 110, 130, 0.15)" : "rgba(140, 150, 170, 0.2)");
    ctx.lineWidth = 0.18;
    ctx.beginPath();
    ctx.roundRect(-boxWidth / 2, -boxHeight / 2, boxWidth, boxHeight, 1.4);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = active
      ? (isDark ? "#e4e6ec" : "#1a1d24")
      : (isDark ? "rgba(160, 164, 176, 0.8)" : "rgba(90, 94, 106, 0.85)");
    ctx.fillText(label, 0, 0.1);
    ctx.restore();
  }

  function currentGraphData() {
    const visibleIds = new Set(
      nodes.filter((node) => selectedCategories.has(node.category)).map((node) => node.id)
    );
    if (subgraphMode && selectedNodeId) {
      const relatedIds = new Set([selectedNodeId]);
      links.forEach((link) => {
        const source = typeof link.source === "object" ? link.source.id : link.source;
        const target = typeof link.target === "object" ? link.target.id : link.target;
        if (source === selectedNodeId || target === selectedNodeId) {
          relatedIds.add(source);
          relatedIds.add(target);
        }
      });
      return {
        nodes: nodes.filter((node) => visibleIds.has(node.id) && relatedIds.has(node.id)),
        links: links.filter((link) => {
          const source = typeof link.source === "object" ? link.source.id : link.source;
          const target = typeof link.target === "object" ? link.target.id : link.target;
          return visibleIds.has(source) && visibleIds.has(target) && relatedIds.has(source) && relatedIds.has(target);
        }),
      };
    }
    return {
      nodes: nodes.filter((node) => visibleIds.has(node.id)),
      links: links.filter((link) => visibleIds.has(link.source) && visibleIds.has(link.target)),
    };
  }

  function postStatus(message) {
    if (!embeddedMode || !window.parent) return;
    window.parent.postMessage({ type: "a2-graph-viewer:status", message }, "*");
  }

  function renderGraph() {
    const graphData = currentGraphData();
    graph.graphData(graphData);
    statusElement.textContent = `${graphData.nodes.length} 节点 · ${graphData.links.length} 关系`;
    if (toggleSubgraphButton) {
      toggleSubgraphButton.textContent = subgraphMode ? "查看全图" : "当前节点";
    }
    if (selectedNodeId && !graphData.nodes.some((node) => node.id === selectedNodeId)) {
      selectedNodeId = null;
      renderDetail(null);
    }
    window.setTimeout(() => {
      if (graphData.nodes.length > 0) graph.zoomToFit(300, 48);
    }, 80);
  }

  function renderStats() {
    const summary = [
      ["知识点", data.meta.note_count],
      ["内部边", data.meta.internal_edge_count],
      ["跨域引用", data.meta.out_of_scope_reference_count],
      ["缺失概念", data.meta.missing_reference_count],
    ];
    statsElement.innerHTML = summary
      .map(([label, value]) => `
        <div class="stat-card">
          <span class="stat-label">${label}</span>
          <span class="stat-value">${value}</span>
        </div>`)
      .join("");
  }

  function renderLegend() {
    legendElement.innerHTML = categories
      .map((category) => {
        const active = selectedCategories.has(category);
        const pal = categoryColors[category] || categoryPalette[0];
        return `
          <button type="button" class="legend-chip ${active ? "" : "is-off"}"
            data-category="${category}"
            style="border-color:${pal.stroke};background:${active ? pal.fill : ''};">
            <span style="display:inline-block;width:8px;height:8px;border-radius:999px;background:${pal.stroke};margin-right:6px;"></span>${category}
          </button>`;
      })
      .join("");
    legendElement.querySelectorAll("[data-category]").forEach((button) => {
      button.addEventListener("click", () => {
        const category = button.getAttribute("data-category");
        if (selectedCategories.has(category)) selectedCategories.delete(category);
        else selectedCategories.add(category);
        renderLegend();
        renderGraph();
      });
    });
  }

  function renderRootNotes() {
    const rootNotes = data.meta.root_notes || [];
    rootNotesElement.innerHTML = rootNotes
      .map((id) => {
        const node = nodeById.get(id);
        if (!node) return "";
        return `<button type="button" class="root-chip" data-root-id="${id}">${node.name}</button>`;
      })
      .join("");
    rootNotesElement.querySelectorAll("[data-root-id]").forEach((button) => {
      button.addEventListener("click", () => {
        selectNode(button.getAttribute("data-root-id"), true);
      });
    });
  }

  function createChipList(values, className, emptyText, attributeName) {
    if (!values || values.length === 0) return `<p class="empty-state">${emptyText}</p>`;
    return `<div class="chip-list">${values.map((value) => {
      const escaped = escapeHtml(value);
      if (!attributeName) return `<span class="${className}">${escaped}</span>`;
      return `<button type="button" class="${className}" data-${attributeName}="${escaped}">${escaped}</button>`;
    }).join("")}</div>`;
  }

  function escapeHtml(value) {
    return String(value || "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#39;");
  }

  function preserveLineBreaks(value) {
    return escapeHtml(value).replace(/\n/g, "<br>");
  }

  function typesetMath(target) {
    if (!target || !window.MathJax || typeof window.MathJax.typesetPromise !== "function") return;
    window.MathJax.typesetClear?.([target]);
    window.MathJax.typesetPromise([target]).catch(() => {});
  }

  function createInternalLinks(note) {
    if (!note.internal_links || note.internal_links.length === 0)
      return `<p class="empty-state">暂无关联。</p>`;
    return `<div class="internal-link-list">${note.internal_links
      .map((id) => `<button type="button" class="link-chip" data-node-jump="${escapeHtml(id)}">${escapeHtml(id)}</button>`)
      .join("")}</div>`;
  }

  function createExternalLinks(note) {
    const groups = [];
    if (note.out_of_scope_links && note.out_of_scope_links.length > 0) {
      groups.push(`<div class="detail-section"><h3>跨域</h3><div class="chip-list">${note.out_of_scope_links.map((item) => `<span class="external-chip">${escapeHtml(item)}</span>`).join("")}</div></div>`);
    }
    if (note.missing_links && note.missing_links.length > 0) {
      groups.push(`<div class="detail-section"><h3>待补概念</h3><div class="chip-list">${note.missing_links.map((item) => `<span class="external-chip is-missing">${escapeHtml(item)}</span>`).join("")}</div></div>`);
    }
    return groups.join("") || `<p class="empty-state">暂无外部引用。</p>`;
  }

  function createCommonErrors(note) {
    const rows = Array.isArray(note.common_errors) ? note.common_errors : [];
    if (!rows.length) return `<p class="empty-state">暂无误区。</p>`;
    return rows.slice(0, 3).map((row) => `
      <div class="detail-error">
        <strong>${escapeHtml(row.error || "常见误区")}</strong>
        ${row.cause ? `<p class="muted">原因：${escapeHtml(row.cause)}</p>` : ""}
        ${row.correction ? `<p class="muted">纠偏：${escapeHtml(row.correction)}</p>` : ""}
      </div>`).join("");
  }

  function createSmartPath(note) {
    const prerequisites = Array.isArray(note.prerequisites) ? note.prerequisites.slice(0, 4) : [];
    const neighbors = Array.isArray(note.neighbors) ? note.neighbors.slice(0, 4) : [];
    const actions = [];
    if (prerequisites.length) {
      actions.push(`<div class="detail-section"><h3>先看</h3>${createChipList(prerequisites, "link-chip", "暂无前置。", "suggest-node")}</div>`);
    }
    if (neighbors.length) {
      actions.push(`<div class="detail-section"><h3>延伸</h3>${createChipList(neighbors, "link-chip", "暂无延伸。", "suggest-node")}</div>`);
    }
    return actions.join("");
  }

  function renderDetail(noteId) {
    if (!noteId || !noteMap[noteId]) {
      detailElement.innerHTML = `<p class="eyebrow">Detail</p><h2>选择知识点</h2><p class="muted">点击节点或搜索。</p>`;
      typesetMath(detailElement);
      return;
    }
    const note = noteMap[noteId];
    const objectives = Array.isArray(note.learning_objectives) ? note.learning_objectives.slice(0, 3) : [];
    const mustKnow = Array.isArray(note.must_know) ? note.must_know.slice(0, 3) : [];
    const descriptor = [note.target_mastery_level, note.difficulty].filter(Boolean).join(" / ");

    detailElement.innerHTML = `
      <div class="note-block">
        <p class="eyebrow">${escapeHtml(note.category || "")}</p>
        <div class="note-title-row">
          <div>
            <h2 class="note-title">${escapeHtml(note.title || noteId)}</h2>
            <p class="muted">${escapeHtml(note.subcategory || "")}${note.terminology ? ` / ${escapeHtml(note.terminology)}` : ""}</p>
          </div>
          ${note.pinned ? `<span class="meta-chip">Pinned</span>` : ""}
        </div>
        <div class="detail-action-row">
          <button type="button" class="primary-button" data-learn-node="${escapeHtml(note.title || noteId)}">带回聊天框</button>
          ${descriptor ? `<span class="meta-chip">${escapeHtml(descriptor)}</span>` : ""}
        </div>
        <div class="detail-section"><h3>摘要</h3><p class="detail-copy">${preserveLineBreaks(note.summary || "暂无。")}</p></div>
        <div class="detail-section"><h3>重点</h3>${mustKnow.length ? createChipList(mustKnow, "tag-chip", "暂无重点。") : `<p class="empty-state">暂无重点。</p>`}</div>
        <div class="detail-section"><h3>目标</h3>${objectives.length ? createChipList(objectives, "meta-chip", "暂无目标。") : `<p class="empty-state">暂无目标。</p>`}</div>
        ${createSmartPath(note)}
        <div class="detail-section"><h3>误区</h3>${createCommonErrors(note)}</div>
        <div class="detail-section"><h3>结构</h3>${createChipList(note.headings, "tag-chip", "暂无结构。")}</div>
        <div class="detail-section"><h3>标签</h3>${createChipList([...(note.tags || []), ...(note.aliases || [])], "meta-chip", "暂无标签。")}</div>
        <div class="detail-section"><h3>关联</h3>${createInternalLinks(note)}</div>
        ${createExternalLinks(note)}
        <div class="detail-section"><h3>摘录</h3><p class="detail-copy">${preserveLineBreaks(note.content_excerpt || "暂无。")}</p></div>
        <div class="detail-section"><h3>路径</h3>
          <div class="meta-list">
            <span class="meta-chip">${escapeHtml(note.dg_path || "")}</span>
            ${note.level !== null && note.level !== undefined ? `<span class="meta-chip">Level ${escapeHtml(note.level)}</span>` : ""}
          </div>
          <p class="muted">笔记：<a class="file-link" href="${escapeHtml(note.viewer_markdown_path || "#")}" target="_blank" rel="noreferrer">${escapeHtml(note.viewer_markdown_path || "")}</a></p>
          <p class="muted">源：${escapeHtml(note.source_path || "")}</p>
        </div>
      </div>`;

    detailElement.querySelectorAll("[data-node-jump]").forEach((button) => {
      button.addEventListener("click", () => selectNode(button.getAttribute("data-node-jump"), true));
    });
    detailElement.querySelectorAll("[data-suggest-node]").forEach((button) => {
      button.addEventListener("click", () => {
        const target = button.getAttribute("data-suggest-node");
        if (nodeById.has(target)) { selectNode(target, true); return; }
        const fallback = nodes.find((node) => scoreNodeAgainstHint(node, target) > 0);
        if (fallback) selectNode(fallback.id, true);
      });
    });
    detailElement.querySelectorAll("[data-learn-node]").forEach((button) => {
      button.addEventListener("click", () => {
        const nodeTitle = button.getAttribute("data-learn-node");
        if (embeddedMode && window.parent) {
          window.parent.postMessage({ type: "a2-graph-viewer:learn-node", nodeId: nodeTitle }, "*");
        }
      });
    });
    typesetMath(detailElement);
    postStatus(`当前定位：${note.title || noteId}`);
  }

  function selectNode(nodeId, focusNode) {
    if (!nodeById.has(nodeId)) return;
    const node = nodeById.get(nodeId);
    selectedNodeId = nodeId;
    if (!selectedCategories.has(node.category)) {
      selectedCategories.add(node.category);
      renderLegend();
      renderGraph();
    } else {
      graph.nodeCanvasObject((n, ctx, gs) => drawNode(n, ctx, gs));
      graph.linkWidth((link) => getLinkWidth(link));
      graph.linkColor((link) => getLinkColor(link));
    }
    renderDetail(nodeId);
    if (focusNode) {
      graph.centerAt(node.x || 0, node.y || 0, 450);
      graph.zoom(5.2, 450);
    }
  }

  function searchNotes(queryText) {
    const keyword = queryText.trim().toLowerCase();
    if (!keyword) return [];
    return nodes
      .map((node) => {
        const note = noteMap[node.id] || {};
        const haystack = [node.name, note.summary || "", ...(note.aliases || []), ...(note.tags || [])]
          .join(" ").toLowerCase();
        const titleScore = node.name.toLowerCase().includes(keyword) ? 3 : 0;
        const aliasScore = (note.aliases || []).some((item) => item.toLowerCase().includes(keyword)) ? 2 : 0;
        const bodyScore = haystack.includes(keyword) ? 1 : 0;
        return { node, score: titleScore + aliasScore + bodyScore };
      })
      .filter((item) => item.score > 0)
      .sort((a, b) => b.score - a.score || a.node.name.localeCompare(b.node.name, "zh-CN"))
      .slice(0, 10)
      .map((item) => item.node);
  }

  function renderSearchResults(queryText) {
    const results = searchNotes(queryText);
    searchFilter = queryText.trim().toLowerCase();
    /* 搜索时非匹配节点淡出 */
    graph.nodeCanvasObject((n, ctx, gs) => drawNode(n, ctx, gs));

    if (!queryText.trim()) { resultsElement.innerHTML = ""; return; }
    if (results.length === 0) {
      resultsElement.innerHTML = `<div class="empty-state">没有找到匹配的知识点。</div>`;
      return;
    }
    resultsElement.innerHTML = results.map((node) => {
      const note = noteMap[node.id] || {};
      return `
        <div class="search-result" data-search-id="${escapeHtml(node.id)}">
          <div class="search-result-title">${escapeHtml(node.name)}</div>
          <div class="search-result-meta">${escapeHtml(node.category)} / ${escapeHtml(node.subcategory)}</div>
          <div class="search-result-meta">${escapeHtml(note.summary || "")}</div>
        </div>`;
    }).join("");
    resultsElement.querySelectorAll("[data-search-id]").forEach((item) => {
      item.addEventListener("click", () => {
        const nodeId = item.getAttribute("data-search-id");
        searchInput.value = nodeId;
        selectNode(nodeId, true);
      });
    });
  }

  searchInput.addEventListener("input", () => renderSearchResults(searchInput.value));

  fitGraphButton.addEventListener("click", () => graph.zoomToFit(300, 48));

  if (toggleSubgraphButton) {
    toggleSubgraphButton.addEventListener("click", () => {
      subgraphMode = !subgraphMode;
      renderGraph();
      if (selectedNodeId) {
        window.setTimeout(() => selectNode(selectedNodeId, true), 20);
      }
    });
  }

  resetFiltersButton.addEventListener("click", () => {
    selectedCategories = new Set(categories);
    searchFilter = "";
    searchInput.value = "";
    resultsElement.innerHTML = "";
    renderLegend();
    renderGraph();
  });

  renderStats();
  renderLegend();
  renderRootNotes();
  renderGraph();

  const initialNodeId = resolveInitialNodeId();
  if (initialNodeId) {
    window.setTimeout(() => selectNode(initialNodeId, true), 400);
  }
})();
