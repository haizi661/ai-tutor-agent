/**
 * teaching-insights.js — 教学洞察 (Teaching Insights) 交互逻辑
 * 以模态框形式展示教学策略效果、节点访问统计、情绪信号分布。
 */

const TeachingInsights = {
    _modalEl: null,
    _bodyEl: null,
    _loadingEl: null,

    init() {
        this._modalEl = document.getElementById('teaching-insights-modal');
        this._bodyEl = document.getElementById('teaching-insights-body');
        this._loadingEl = document.getElementById('teaching-insights-loading');
        if (!this._modalEl || !this._bodyEl) return;
        this._bindEvents();
    },

    _bindEvents() {
        // Delegate clicks inside the modal body
        if (!this._bodyEl) return;
        this._bodyEl.addEventListener('click', (event) => {
            const btn = event.target && typeof event.target.closest === 'function'
                ? event.target.closest('button')
                : null;
            if (!btn) return;
            // Node detail expand/collapse handled via CSS; no custom handlers needed.
        });
    },

    _studentId() {
        // Match the pattern used by wrong-book.js and question-help.js
        const s = window.state || window.appState || {};
        return s.studentId || s.student_id || 'default_student';
    },

    async load() {
        if (!this._bodyEl || !this._loadingEl) return;
        this._bodyEl.innerHTML = '';
        this._loadingEl.hidden = false;

        const studentId = this._studentId();
        let data;
        try {
            const resp = await fetch(
                '/api/students/' + encodeURIComponent(studentId) + '/teaching-insights'
            );
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            data = await resp.json();
        } catch (err) {
            this._loadingEl.hidden = true;
            this._bodyEl.innerHTML =
                '<div class="ti-error">加载教学洞察数据失败: ' +
                this._escapeHtml(String(err.message || err)) +
                '</div>';
            return;
        }

        this._loadingEl.hidden = true;
        this._render(data);
    },

    _render(data) {
        const summary = data.summary || {};
        const nodeDetails = data.node_details || [];
        const recent = data.recent_episodes || [];

        const totalEp = summary.total_episodes || 0;
        const totalNodes = summary.total_nodes_visited || 0;
        const strategyDist = summary.strategy_distribution || {};
        const affectDist = summary.affect_distribution || {};
        const entryModeDist = summary.entry_mode_distribution || {};

        const parts = [];

        // --- Header stats row ---
        parts.push('<div class="ti-summary-grid">');
        parts.push(this._statCard('总讲解次数', totalEp, '📊'));
        parts.push(this._statCard('涉及节点', totalNodes, '📌'));
        parts.push(this._statCard(
            '策略分布',
            this._renderSmallDist(strategyDist, { 'start_test': '小测', 'temporary_question': '追问' }),
            '🎯'
        ));
        parts.push(this._statCard(
            '情绪信号',
            this._renderSmallDist(affectDist),
            '😊'
        ));
        parts.push('</div>');

        // --- Entry mode distribution ---
        if (Object.keys(entryModeDist).length > 0) {
            parts.push('<div class="ti-section">');
            parts.push('<div class="ti-section-title">进入方式分布</div>');
            parts.push(this._renderDistDetail(entryModeDist, {
                'first_entry': '首次学习',
                'return': '再次学习',
                'remediation': '纠错学习',
            }));
            parts.push('</div>');
        }

        // --- Per-node details ---
        if (nodeDetails.length > 0) {
            parts.push('<div class="ti-section">');
            parts.push('<div class="ti-section-title">节点详情 <span class="ti-subtitle">按最近活动排序</span></div>');
            parts.push('<div class="ti-node-list">');
            for (const nd of nodeDetails) {
                parts.push(this._renderNodeCard(nd));
            }
            parts.push('</div>');
            parts.push('</div>');
        }

        // --- Recent episodes ---
        if (recent.length > 0) {
            parts.push('<div class="ti-section">');
            parts.push('<div class="ti-section-title">最近教学记录 <span class="ti-subtitle">最近 10 条</span></div>');
            parts.push('<div class="ti-recent-list">');
            for (const ep of recent) {
                parts.push(this._renderRecentRow(ep));
            }
            parts.push('</div>');
            parts.push('</div>');
        }

        // Empty state
        if (totalEp === 0) {
            parts.push('<div class="ti-empty">还没有教学记录。开始学习后，教学策略和效果数据将在这里展示。</div>');
        }

        this._bodyEl.innerHTML = parts.join('\n');
    },

    _statCard(label, value, icon) {
        const valStr = typeof value === 'object' ? value : '<strong>' + String(value) + '</strong>';
        return '<div class="ti-stat-card"><div class="ti-stat-icon">' + icon + '</div><div class="ti-stat-body"><div class="ti-stat-value">' + valStr + '</div><div class="ti-stat-label">' + label + '</div></div></div>';
    },

    _renderSmallDist(dist, labelMap) {
        const keys = Object.keys(dist);
        if (keys.length === 0) return '<span class="ti-dim">暂无</span>';
        return keys.map(k => {
            const label = (labelMap && labelMap[k]) || k;
            return '<span class="ti-chip">' + this._escapeHtml(label) + ': ' + dist[k] + '</span>';
        }).join(' ');
    },

    _renderDistDetail(dist, labelMap) {
        const total = Object.values(dist).reduce((a, b) => a + b, 0);
        if (total === 0) return '<div class="ti-dim">暂无数据</div>';
        const bars = Object.entries(dist)
            .sort((a, b) => b[1] - a[1])
            .map(([k, v]) => {
                const pct = Math.round((v / total) * 100);
                const label = (labelMap && labelMap[k]) || k;
                return '<div class="ti-bar-row"><span class="ti-bar-label">' +
                    this._escapeHtml(label) + '</span><span class="ti-bar-track"><span class="ti-bar-fill" style="width:' + pct + '%"></span></span><span class="ti-bar-count">' +
                    v + ' (' + pct + '%)</span></div>';
            }).join('');
        return '<div class="ti-bars">' + bars + '</div>';
    },

    _renderNodeCard(nd) {
        const aff = nd.affect_distribution || {};
        const strats = nd.strategy_distribution || {};
        const modes = nd.entry_mode_distribution || {};

        const affectHtml = Object.keys(aff).length > 0
            ? Object.entries(aff).map(([k, v]) =>
                '<span class="ti-mini-chip">' + this._escapeHtml(k || '中性') + ' ' + v + '</span>'
              ).join('')
            : '<span class="ti-dim">无记录</span>';

        const stratsHtml = Object.keys(strats).length > 0
            ? Object.entries(strats).map(([k, v]) => {
                const label = k === 'start_test' ? '小测' : k === 'temporary_question' ? '追问' : k;
                return '<span class="ti-chip">' + label + ': ' + v + '</span>';
              }).join('')
            : '';

        return '<details class="ti-node-card" open>' +
            '<summary class="ti-node-summary">' +
                '<span class="ti-node-title">' + this._escapeHtml(nd.node_title) + '</span>' +
                '<span class="ti-node-meta">' +
                    '<span>访问 ' + nd.total_visits + ' 次</span>' +
                    '<span>·</span>' +
                    '<span>尝试 ' + nd.attempt_count + ' 轮</span>' +
                '</span>' +
            '</summary>' +
            '<div class="ti-node-detail">' +
                (stratsHtml ? '<div class="ti-node-detail-row"><span class="ti-detail-label">策略：</span>' + stratsHtml + '</div>' : '') +
                '<div class="ti-node-detail-row"><span class="ti-detail-label">情绪：</span>' + affectHtml + '</div>' +
                (Object.keys(modes).length > 0
                    ? '<div class="ti-node-detail-row"><span class="ti-detail-label">进入方式：</span>' +
                      Object.entries(modes).map(([k, v]) => {
                          const label = ({ 'first_entry': '首次', 'return': '再次', 'remediation': '纠错' })[k] || k;
                          return '<span class="ti-mini-chip">' + label + ' ' + v + '</span>';
                      }).join('') + '</div>'
                    : '') +
                (nd.first_seen ? '<div class="ti-node-detail-row ti-detail-time">首次: ' +
                    this._escapeHtml(this._fmtTime(nd.first_seen)) +
                    ' · 最近: ' + this._escapeHtml(this._fmtTime(nd.latest_seen)) + '</div>' : '') +
            '</div>' +
        '</details>';
    },

    _renderRecentRow(ep) {
        const stratLabel = ep.strategy === 'start_test' ? '小测' : ep.strategy === 'temporary_question' ? '追问' : (ep.strategy || '—');
        const aff = ep.affect ? (' · ' + ep.affect) : '';
        const mode = ep.entry_mode ? (' · [' + ep.entry_mode + ']') : '';
        return '<div class="ti-recent-row">' +
            '<span class="ti-recent-strat ti-chip">' + stratLabel + '</span>' +
            '<span class="ti-recent-node">' + this._escapeHtml(ep.node_title || ep.node_id || '') + '</span>' +
            '<span class="ti-recent-meta">第 ' + (ep.attempt_count || 1) + ' 轮' + aff + mode + '</span>' +
            '<span class="ti-recent-time">' + this._escapeHtml(this._fmtTime(ep.created_at || '')) + '</span>' +
        '</div>';
    },

    _fmtTime(isoStr) {
        if (!isoStr) return '';
        try {
            const d = new Date(isoStr);
            if (isNaN(d.getTime())) return isoStr;
            const month = String(d.getMonth() + 1).padStart(2, '0');
            const day = String(d.getDate()).padStart(2, '0');
            const hour = String(d.getHours()).padStart(2, '0');
            const min = String(d.getMinutes()).padStart(2, '0');
            return month + '-' + day + ' ' + hour + ':' + min;
        } catch {
            return isoStr;
        }
    },

    _escapeHtml(str) {
        if (typeof str !== 'string') return String(str || '');
        const div = document.createElement('div');
        div.appendChild(document.createTextNode(str));
        return div.innerHTML;
    },
};

// --- Modal open/close (global) ---

function openTeachingInsightsModal() {
    const modal = document.getElementById('teaching-insights-modal');
    if (!modal) return;
    modal.setAttribute('aria-hidden', 'false');
    document.body.classList.add('modal-open');
    TeachingInsights.init();
    TeachingInsights.load();
}

function closeTeachingInsightsModal(event) {
    const modal = document.getElementById('teaching-insights-modal');
    if (!modal) return;
    if (event && event.target !== modal) return; // only close when clicking overlay
    modal.setAttribute('aria-hidden', 'true');
    document.body.classList.remove('modal-open');
}

// Auto-init on DOMContentLoaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => TeachingInsights.init());
} else {
    TeachingInsights.init();
}
