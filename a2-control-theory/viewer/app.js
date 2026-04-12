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

  if (!data || !window.ForceGraph) {
    detailElement.innerHTML = "<p>无法加载图谱数据或渲染库。</p>";
    return;
  }

  const nodes = data.graph.nodes.map((node) => ({ ...node }));
  const links = data.graph.links.map((link) => ({ ...link }));
  const noteMap = data.notes || {};
  const nodeById = new Map(nodes.map((node) => [node.id, node]));
  const categories = [...new Set(nodes.map((node) => node.category))];
  const colorPalette = [
    "#5ec8ff",
    "#7de2a9",
    "#ffbe5c",
    "#f08080",
    "#c18cff",
    "#ffd166",
    "#64dfdf",
    "#ff8fab",
  ];
  const categoryColors = Object.fromEntries(
    categories.map((category, index) => [category, colorPalette[index % colorPalette.length]])
  );

  let selectedCategories = new Set(categories);
  let selectedNodeId = null;
  let hoverNodeId = null;
  let hoverLinkKey = null;

  const graph = window
    .ForceGraph()(graphElement)
    .nodeId("id")
    .nodeLabel((node) => {
      const note = noteMap[node.id];
      return `
        <div style="padding:8px 10px;max-width:260px;">
          <strong>${node.name}</strong><br>
          <span>${node.category} / ${node.subcategory}</span><br>
          <span style="color:#b9d7e8;">${(note && note.summary) || ""}</span>
        </div>
      `;
    })
    .nodeVal((node) => node.size)
    .nodeColor((node) => getNodeColor(node))
    .linkWidth((link) => getLinkWidth(link))
    .linkColor((link) => getLinkColor(link))
    .linkCanvasObjectMode(() => "after")
    .linkCanvasObject((link, ctx, globalScale) => {
      drawLinkLabel(link, ctx, globalScale);
    })
    .backgroundColor("#08131a")
    .cooldownTicks(120)
    .onNodeHover((node) => {
      hoverNodeId = node ? node.id : null;
      graph.linkWidth((link) => getLinkWidth(link));
      graph.linkColor((link) => getLinkColor(link));
    })
    .onLinkHover((link) => {
      hoverLinkKey = link ? getLinkKey(link) : null;
    })
    .onNodeClick((node) => {
      selectNode(node.id, true);
    });

  function getLinkKey(link) {
    const source = typeof link.source === "object" ? link.source.id : link.source;
    const target = typeof link.target === "object" ? link.target.id : link.target;
    return `${source}=>${target}`;
  }

  function getNodeColor(node) {
    if (selectedNodeId === node.id) {
      return "#ffffff";
    }
    if (hoverNodeId === node.id) {
      return "#ffd166";
    }
    return categoryColors[node.category] || "#5ec8ff";
  }

  function getLinkColor(link) {
    const source = typeof link.source === "object" ? link.source.id : link.source;
    const target = typeof link.target === "object" ? link.target.id : link.target;
    if (selectedNodeId && (source === selectedNodeId || target === selectedNodeId)) {
      return "#ffd166";
    }
    if (hoverNodeId && (source === hoverNodeId || target === hoverNodeId)) {
      return "#a7ddff";
    }
    return "rgba(110, 151, 178, 0.28)";
  }

  function getLinkWidth(link) {
    const source = typeof link.source === "object" ? link.source.id : link.source;
    const target = typeof link.target === "object" ? link.target.id : link.target;
    if (selectedNodeId && (source === selectedNodeId || target === selectedNodeId)) {
      return 2.8;
    }
    if (hoverNodeId && (source === hoverNodeId || target === hoverNodeId)) {
      return 2.2;
    }
    return 0.8 + (link.weight || 1) * 0.15;
  }

  function drawLinkLabel(link, ctx, globalScale) {
    const label = (link.relation_label || "").trim();
    if (!label) {
      return;
    }

    const source = link.source;
    const target = link.target;
    if (
      !source ||
      !target ||
      typeof source !== "object" ||
      typeof target !== "object" ||
      !Number.isFinite(source.x) ||
      !Number.isFinite(source.y) ||
      !Number.isFinite(target.x) ||
      !Number.isFinite(target.y)
    ) {
      return;
    }

    const midX = (source.x + target.x) / 2;
    const midY = (source.y + target.y) / 2;
    const dx = target.x - source.x;
    const dy = target.y - source.y;
    const angle = Math.atan2(dy, dx);
    const normalizedAngle = Math.abs(angle) > Math.PI / 2 ? angle + Math.PI : angle;
    const active =
      hoverLinkKey === getLinkKey(link) ||
      (selectedNodeId &&
        (source.id === selectedNodeId || target.id === selectedNodeId));

    const fontSize = active ? 3.6 : 2.9;
    const paddingX = active ? 2.1 : 1.8;
    const paddingY = active ? 1.15 : 0.95;

    ctx.save();
    ctx.translate(midX, midY);
    ctx.rotate(normalizedAngle);
    ctx.font = `${active ? 700 : 500} ${fontSize}px "PingFang SC", "Noto Sans SC", sans-serif`;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";

    const metrics = ctx.measureText(label);
    const textWidth = metrics.width;
    const boxWidth = textWidth + paddingX * 2;
    const boxHeight = fontSize + paddingY * 2;

    ctx.fillStyle = active ? "rgba(8, 19, 26, 0.92)" : "rgba(8, 19, 26, 0.72)";
    ctx.strokeStyle = active ? "rgba(255, 209, 102, 0.72)" : "rgba(94, 200, 255, 0.16)";
    ctx.lineWidth = 0.18;
    ctx.beginPath();
    ctx.roundRect(-boxWidth / 2, -boxHeight / 2, boxWidth, boxHeight, 1.4);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = active ? "#fff7e2" : "rgba(232, 240, 245, 0.88)";
    ctx.fillText(label, 0, 0.1);
    ctx.restore();
  }

  function currentGraphData() {
    const visibleIds = new Set(
      nodes.filter((node) => selectedCategories.has(node.category)).map((node) => node.id)
    );
    return {
      nodes: nodes.filter((node) => visibleIds.has(node.id)),
      links: links.filter((link) => visibleIds.has(link.source) && visibleIds.has(link.target)),
    };
  }

  function renderGraph() {
    const graphData = currentGraphData();
    graph.graphData(graphData);
    statusElement.textContent = `当前显示 ${graphData.nodes.length} 个节点，${graphData.links.length} 条边`;

    if (selectedNodeId && !graphData.nodes.some((node) => node.id === selectedNodeId)) {
      selectedNodeId = null;
      renderDetail(null);
    }

    window.setTimeout(() => {
      if (graphData.nodes.length > 0) {
        graph.zoomToFit(300, 48);
      }
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
      .map(
        ([label, value]) => `
          <div class="stat-card">
            <span class="stat-label">${label}</span>
            <span class="stat-value">${value}</span>
          </div>
        `
      )
      .join("");
  }

  function renderLegend() {
    legendElement.innerHTML = categories
      .map((category) => {
        const active = selectedCategories.has(category);
        const style = `border-color:${categoryColors[category]};box-shadow:inset 0 0 0 1px ${categoryColors[category]}33;`;
        return `
          <button
            type="button"
            class="legend-chip ${active ? "" : "is-off"}"
            data-category="${category}"
            style="${style}"
          >
            <span style="display:inline-block;width:10px;height:10px;border-radius:999px;background:${categoryColors[category]};margin-right:8px;"></span>
            ${category}
          </button>
        `;
      })
      .join("");

    legendElement.querySelectorAll("[data-category]").forEach((button) => {
      button.addEventListener("click", () => {
        const category = button.getAttribute("data-category");
        if (selectedCategories.has(category)) {
          selectedCategories.delete(category);
        } else {
          selectedCategories.add(category);
        }
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
        if (!node) {
          return "";
        }
        return `<button type="button" class="root-chip" data-root-id="${id}">${node.name}</button>`;
      })
      .join("");

    rootNotesElement.querySelectorAll("[data-root-id]").forEach((button) => {
      button.addEventListener("click", () => {
        selectNode(button.getAttribute("data-root-id"), true);
      });
    });
  }

  function createChipList(values, className, emptyText) {
    if (!values || values.length === 0) {
      return `<p class="empty-state">${emptyText}</p>`;
    }
    return `
      <div class="chip-list">
        ${values.map((value) => `<span class="${className}">${value}</span>`).join("")}
      </div>
    `;
  }

  function escapeHtml(value) {
    return String(value || "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function preserveLineBreaks(value) {
    return escapeHtml(value).replace(/\n/g, "<br>");
  }

  function typesetMath(target) {
    if (!target || !window.MathJax || typeof window.MathJax.typesetPromise !== "function") {
      return;
    }

    window.MathJax.typesetClear?.([target]);
    window.MathJax.typesetPromise([target]).catch((error) => {
      console.warn("MathJax render failed.", error);
    });
  }

  function createInternalLinks(note) {
    if (!note.internal_links || note.internal_links.length === 0) {
      return `<p class="empty-state">没有 A2 子图内部链接。</p>`;
    }
    return `
      <div class="internal-link-list">
        ${note.internal_links
          .map((id) => `<button type="button" class="link-chip" data-node-jump="${id}">${id}</button>`)
          .join("")}
      </div>
    `;
  }

  function createExternalLinks(note) {
    const groups = [];
    if (note.out_of_scope_links && note.out_of_scope_links.length > 0) {
      groups.push(`
        <div class="detail-section">
          <h3>跨域先修知识</h3>
          <div class="chip-list">
            ${note.out_of_scope_links
              .map((item) => `<span class="external-chip">${item}</span>`)
              .join("")}
          </div>
        </div>
      `);
    }
    if (note.missing_links && note.missing_links.length > 0) {
      groups.push(`
        <div class="detail-section">
          <h3>当前仓库缺失概念</h3>
          <div class="chip-list">
            ${note.missing_links
              .map((item) => `<span class="external-chip is-missing">${item}</span>`)
              .join("")}
          </div>
        </div>
      `);
    }
    return groups.join("") || `<p class="empty-state">没有外部引用。</p>`;
  }

  function renderDetail(noteId) {
    if (!noteId || !noteMap[noteId]) {
      detailElement.innerHTML = `
        <p class="eyebrow">Node Detail</p>
        <h2>选择一个知识点</h2>
        <p class="muted">点击图中的节点，或在左侧搜索。</p>
      `;
      typesetMath(detailElement);
      return;
    }

    const note = noteMap[noteId];
    detailElement.innerHTML = `
      <div class="note-block">
        <p class="eyebrow">${note.category}</p>
        <div class="note-title-row">
          <div>
            <h2 class="note-title">${note.title}</h2>
            <p class="muted">${note.subcategory}${note.terminology ? ` / ${note.terminology}` : ""}</p>
          </div>
          ${note.pinned ? `<span class="meta-chip">Pinned</span>` : ""}
        </div>

        <div class="detail-section">
          <h3>摘要</h3>
          <p class="detail-copy">${preserveLineBreaks(note.summary || "暂无摘要。")}</p>
        </div>

        <div class="detail-section">
          <h3>章节结构</h3>
          ${createChipList(note.headings, "tag-chip", "没有提取到章节标题。")}
        </div>

        <div class="detail-section">
          <h3>标签与别名</h3>
          ${createChipList(
            [...(note.tags || []), ...(note.aliases || [])],
            "meta-chip",
            "没有标签或别名。"
          )}
        </div>

        <div class="detail-section">
          <h3>内部关联</h3>
          ${createInternalLinks(note)}
        </div>

        ${createExternalLinks(note)}

        <div class="detail-section">
          <h3>内容摘录</h3>
          <p class="detail-copy">${preserveLineBreaks(note.content_excerpt || "暂无内容。")}</p>
        </div>

        <div class="detail-section">
          <h3>文件信息</h3>
          <div class="meta-list">
            <span class="meta-chip">${note.dg_path}</span>
            ${note.level !== null && note.level !== undefined ? `<span class="meta-chip">Level ${note.level}</span>` : ""}
          </div>
          <p class="muted">原始笔记：<a class="file-link" href="${note.viewer_markdown_path}" target="_blank" rel="noreferrer">${note.viewer_markdown_path}</a></p>
          <p class="muted">项目源路径：${note.source_path}</p>
        </div>
      </div>
    `;

    detailElement.querySelectorAll("[data-node-jump]").forEach((button) => {
      button.addEventListener("click", () => {
        selectNode(button.getAttribute("data-node-jump"), true);
      });
    });

    typesetMath(detailElement);
  }

  function selectNode(nodeId, focusNode) {
    if (!nodeById.has(nodeId)) {
      return;
    }

    const node = nodeById.get(nodeId);
    selectedNodeId = nodeId;

    if (!selectedCategories.has(node.category)) {
      selectedCategories.add(node.category);
      renderLegend();
      renderGraph();
    } else {
      graph.nodeColor((item) => getNodeColor(item));
      graph.linkWidth((link) => getLinkWidth(link));
      graph.linkColor((link) => getLinkColor(link));
    }

    renderDetail(nodeId);

    if (focusNode) {
      graph.centerAt(node.x || 0, node.y || 0, 450);
      graph.zoom(5.2, 450);
    }
  }

  function searchNotes(query) {
    const keyword = query.trim().toLowerCase();
    if (!keyword) {
      return [];
    }

    return nodes
      .map((node) => {
        const note = noteMap[node.id] || {};
        const haystack = [
          node.name,
          note.summary || "",
          ...(note.aliases || []),
          ...(note.tags || []),
        ]
          .join(" ")
          .toLowerCase();
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

  function renderSearchResults(query) {
    const results = searchNotes(query);
    if (!query.trim()) {
      resultsElement.innerHTML = "";
      return;
    }
    if (results.length === 0) {
      resultsElement.innerHTML = `<div class="empty-state">没有找到匹配的知识点。</div>`;
      return;
    }

    resultsElement.innerHTML = results
      .map((node) => {
        const note = noteMap[node.id] || {};
        return `
          <div class="search-result" data-search-id="${node.id}">
            <div class="search-result-title">${node.name}</div>
            <div class="search-result-meta">${node.category} / ${node.subcategory}</div>
            <div class="search-result-meta">${note.summary || ""}</div>
          </div>
        `;
      })
      .join("");

    resultsElement.querySelectorAll("[data-search-id]").forEach((item) => {
      item.addEventListener("click", () => {
        const nodeId = item.getAttribute("data-search-id");
        searchInput.value = nodeId;
        selectNode(nodeId, true);
      });
    });
  }

  searchInput.addEventListener("input", () => {
    renderSearchResults(searchInput.value);
  });

  fitGraphButton.addEventListener("click", () => {
    graph.zoomToFit(300, 48);
  });

  resetFiltersButton.addEventListener("click", () => {
    selectedCategories = new Set(categories);
    renderLegend();
    renderGraph();
  });

  renderStats();
  renderLegend();
  renderRootNotes();
  renderGraph();

  if (data.meta.root_notes && data.meta.root_notes.length > 0) {
    window.setTimeout(() => {
      selectNode(data.meta.root_notes[0], true);
    }, 400);
  }
})();
