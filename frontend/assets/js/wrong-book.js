/**
 * wrong-book.js — 错题本交互逻辑
 * 独立实现 modal 打开/关闭，避免依赖 app.js 内部局部函数。
 */

const WrongBook = {
    page: 1,
    pageSize: 50,
    lastTotal: 0,
    filter: 'unmastered',

    init() {
        this._modalEl = document.getElementById('wrong-book-modal');
        this._bodyEl = document.getElementById('wrong-book-body');
        this._footerEl = document.getElementById('wrong-book-footer');
        this._summaryEl = document.getElementById('wrong-book-summary');
        this._pageInfoEl = document.getElementById('wb-page-info');
        this._openButtonEl = document.getElementById('open-wrong-book-btn');
        this._bindEvents();
    },

    _bindEvents() {
        if (!this._bodyEl || this._eventsBound) return;
        this._eventsBound = true;
        this._bodyEl.addEventListener('click', event => {
            const btn = event.target && typeof event.target.closest === 'function'
                ? event.target.closest('button')
                : null;
            if (!btn || !this._bodyEl.contains(btn)) return;

            if (btn.classList.contains('wb-filter-tab')) {
                event.preventDefault();
                this._setFilter(btn.dataset.filter || 'unmastered');
                return;
            }

            const isMasterToggle = btn.classList.contains('wb-master-toggle')
                || (
                    btn.closest('.wb-item-actions')
                    && ['标记已掌握', '取消掌握', '保存中...', '取消中...'].includes(String(btn.textContent || '').trim())
                );
            if (!isMasterToggle) return;

            event.preventDefault();
            event.stopPropagation();
            if (btn.disabled) return;

            const mastered = btn.dataset.mastered
                ? btn.dataset.mastered === 'true'
                : String(btn.textContent || '').includes('标记已掌握');
            this._markMasteredFromButton(btn, mastered);
        });
    },

    open() {
        this.init();
        this.page = 1;
        this.filter = this.filter || 'unmastered';
        this._setOpen(true);
        this._showLoading();
        this._fetchAndRender();
    },

    close(event) {
        if (!this._modalEl) this.init();
        if (event && this._modalEl && event.target !== this._modalEl) return;
        this._setOpen(false);
    },

    _setOpen(open) {
        if (!this._modalEl) return;
        this._modalEl.classList.toggle('open', Boolean(open));
        this._modalEl.setAttribute('aria-hidden', open ? 'false' : 'true');
        if (this._openButtonEl) this._openButtonEl.setAttribute('aria-expanded', open ? 'true' : 'false');
    },

    _showLoading() {
        if (!this._bodyEl) return;
        this._bodyEl.innerHTML = '<div class="wrong-book-loading">正在整理你的节点错题…</div>';
        if (this._footerEl) this._footerEl.hidden = true;
    },

    async _fetchAndRender() {
        if (!this._bodyEl) this.init();

        try {
            const studentId = this._studentId();
            const params = new URLSearchParams();
            params.set('page', String(this.page));
            params.set('page_size', String(this.pageSize));
            if (this.filter === 'unmastered') {
                params.set('mastered', 'false');
            } else if (this.filter === 'mastered') {
                params.set('mastered', 'true');
            }
            const url = '/api/students/' + encodeURIComponent(studentId) + '/wrong-questions?' + params.toString();
            const resp = await fetch(url);
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            const data = await resp.json();

            this.lastTotal = Number(data.total || 0);
            this._renderItems(data.items || [], data);
            this._renderFooter(data);
        } catch (err) {
            this._renderError(err);
        }
    },

    _studentId() {
        const state = (window.AITutorApp && window.AITutorApp.state) || {};
        return state.studentId || state.student_id || 'default_student';
    },

    _renderError(err) {
        if (!this._bodyEl) return;
        this._bodyEl.innerHTML = ''
            + '<div class="wrong-book-empty wrong-book-empty--error">'
            + '<strong>错题本加载失败</strong>'
            + '<span>请稍后重试，或检查服务是否仍在运行。</span>'
            + '<code>' + this._esc(err && err.message ? err.message : String(err || 'unknown')) + '</code>'
            + '</div>';
        if (this._footerEl) this._footerEl.hidden = true;
    },

    _renderItems(items, data) {
        const total = Number(data.total || 0);
        const totalAll = Number(data.total_all != null ? data.total_all : total);
        const totalUnmastered = Number(data.total_unmastered || 0);
        const totalMastered = Number(data.total_mastered != null ? data.total_mastered : Math.max(0, totalAll - totalUnmastered));
        const groups = this._groupByNode(items);
        let html = this._renderToolbar();
        html += this._renderOverview(total, totalUnmastered, groups, totalAll, totalMastered);

        if (!items.length) {
            this._bodyEl.innerHTML = html
                + '<div class="wrong-book-empty">'
                + '<strong>' + this._esc(this._emptyTitle()) + '</strong>'
                + '<span>' + this._esc(this._emptyHint()) + '</span>'
                + '</div>';
            return;
        }

        for (let i = 0; i < groups.length; i += 1) {
            html += this._renderGroup(groups[i]);
        }
        this._bodyEl.innerHTML = html;
    },

    _renderToolbar() {
        return ''
            + '<div class="wb-toolbar" role="group" aria-label="错题筛选">'
            + '<button type="button" class="wb-filter-tab' + (this.filter === 'all' ? ' active' : '') + '" data-filter="all" aria-pressed="' + (this.filter === 'all' ? 'true' : 'false') + '">全部</button>'
            + '<button type="button" class="wb-filter-tab' + (this.filter === 'unmastered' ? ' active' : '') + '" data-filter="unmastered" aria-pressed="' + (this.filter === 'unmastered' ? 'true' : 'false') + '">待复习</button>'
            + '<button type="button" class="wb-filter-tab' + (this.filter === 'mastered' ? ' active' : '') + '" data-filter="mastered" aria-pressed="' + (this.filter === 'mastered' ? 'true' : 'false') + '">已掌握</button>'
            + '</div>';
    },

    _setFilter(filter) {
        const next = ['all', 'unmastered', 'mastered'].includes(filter) ? filter : 'unmastered';
        if (this.filter === next) return;
        this.filter = next;
        this.page = 1;
        this._showLoading();
        this._fetchAndRender();
    },

    _groupByNode(items) {
        const map = {};
        for (let i = 0; i < items.length; i += 1) {
            const item = items[i] || {};
            const nodeId = item.node_id || 'unknown';
            if (!map[nodeId]) {
                map[nodeId] = {
                    node_id: nodeId,
                    node_name: item.node_name || nodeId || '未知节点',
                    items: [],
                };
            }
            map[nodeId].items.push(item);
        }
        return Object.keys(map).map(key => map[key]);
    },

    _renderOverview(total, totalUnmastered, groups, totalAll, totalMastered) {
        return ''
            + '<div class="wb-overview">'
            + '<div class="wb-stat"><strong>' + totalAll + '</strong><span>全部错题</span></div>'
            + '<div class="wb-stat wb-stat--warn"><strong>' + totalUnmastered + '</strong><span>待复习</span></div>'
            + '<div class="wb-stat wb-stat--ok"><strong>' + totalMastered + '</strong><span>已掌握</span></div>'
            + '<div class="wb-stat"><strong>' + total + '</strong><span>当前显示</span></div>'
            + '</div>';
    },

    _emptyTitle() {
        if (this.filter === 'mastered') return '暂无已掌握错题';
        if (this.filter === 'unmastered') return '暂无待复习错题';
        return '暂无错题';
    },

    _emptyHint() {
        if (this.filter === 'mastered') return '把待复习错题标记为已掌握后，会在这里查看。';
        if (this.filter === 'unmastered') return '完成节点小测或取消掌握后，待复习错题会显示在这里。';
        return '完成节点小测后，做错的题会自动按知识节点收录到这里。';
    },

    _renderGroup(group) {
        const unmastered = group.items.filter(item => !item.mastered).length;
        const mastered = group.items.length - unmastered;
        let html = '';
        html += '<section class="wb-group">';
        html += '<button type="button" class="wb-group-header" onclick="WrongBook._toggleGroup(this)">';
        html += '<span class="wb-group-arrow">&#9660;</span>';
        html += '<span class="wb-group-title">' + this._esc(group.node_name) + '</span>';
        html += '<span class="wb-group-count">' + group.items.length + ' 题</span>';
        html += '<span class="wb-group-progress">' + mastered + '/' + group.items.length + ' 已掌握</span>';
        html += '</button>';
        html += '<div class="wb-group-body">';
        for (let i = 0; i < group.items.length; i += 1) {
            html += this._renderItem(group.items[i]);
        }
        html += '</div></section>';
        return html;
    },

    _renderItem(item) {
        const qidRaw = String(item.question_id || '');
        const qid = this._esc(qidRaw);
        const stemRaw = String(item.stem || '未提供题干');
        const stem = this._esc(stemRaw).substring(0, 150);
        const userAns = String(item.user_answer || '?').toUpperCase();
        const correctAns = String(item.correct_answer || '?').toUpperCase();
        const wrongReason = this._wrongReasonLabel(item.wrong_reason || '');
        const target = item.target_objective || '';
        const latest = this._formatDate(item.time_latest || item.time_wrong || '');
        const mastered = Boolean(item.mastered);
        const wrongCount = Number(item.wrong_count || 1);
        const hasMore = stemRaw.length > 150;

        let html = '';
        html += '<article class="wb-item" data-qid="' + qid + '">';
        html += '<div class="wb-item-main">';
        html += '<div class="wb-item-topline">';
        html += '<span class="wb-pill ' + (mastered ? 'wb-pill--ok' : 'wb-pill--warn') + '">' + (mastered ? '已掌握' : '待复习') + '</span>';
        html += '<span class="wb-pill">' + this._esc(wrongReason) + '</span>';
        if (latest) html += '<span class="wb-item-time">最近做错：' + this._esc(latest) + '</span>';
        html += '</div>';
        html += '<div class="wb-item-stem">' + stem + (hasMore ? '…' : '') + '</div>';
        if (target) html += '<div class="wb-item-target">考察点：' + this._esc(target) + '</div>';
        html += '<div class="wb-item-answers">';
        html += '<span>你的答案 <strong class="wb-answer wb-answer--wrong">' + this._esc(userAns) + '</strong></span>';
        html += '<span>正确答案 <strong class="wb-answer wb-answer--correct">' + this._esc(correctAns) + '</strong></span>';
        html += '<span>累计做错 <strong>' + wrongCount + '</strong> 次</span>';
        html += '</div>';
        html += '<div class="wb-item-actions">';
        html += '<button type="button" class="chip" onclick="WrongBook._toggleDetail(this)">展开讲解</button>';
        html += mastered
            ? '<button type="button" class="chip chip-muted wb-master-toggle" data-mastered="false">取消掌握</button>'
            : '<button type="button" class="chip chip-primary wb-master-toggle" data-mastered="true">标记已掌握</button>';
        html += '</div>';
        html += '<div class="wb-item-detail" hidden>' + this._renderDetail(item, stemRaw, userAns, correctAns) + '</div>';
        html += '</div></article>';
        return html;
    },

    _renderDetail(item, stemRaw, userAns, correctAns) {
        const options = item.options && typeof item.options === 'object' ? item.options : {};
        const rec = item.recommended_review && typeof item.recommended_review === 'object' ? item.recommended_review : {};
        const analysis = item.wrong_option_analysis && typeof item.wrong_option_analysis === 'object' ? item.wrong_option_analysis : {};
        let html = '';
        html += '<div class="wb-detail-section"><strong>完整题干</strong><p>' + this._esc(stemRaw) + '</p></div>';
        html += '<div class="wb-detail-options"><strong>选项</strong>';
        Object.keys(options).sort().forEach(key => {
            const klass = key === correctAns ? ' wb-option--correct' : (key === userAns ? ' wb-option--wrong' : '');
            html += '<div class="wb-option' + klass + '"><span>' + this._esc(key) + '</span><p>' + this._esc(String(options[key] || '')) + '</p></div>';
        });
        html += '</div>';
        html += '<div class="wb-detail-section"><strong>讲解</strong><p>' + this._esc(item.explanation || '暂无讲解，完成错题订正后会补充。') + '</p></div>';
        if (item.why_user_wrong) {
            html += '<div class="wb-detail-section"><strong>为什么错</strong><p>' + this._esc(item.why_user_wrong) + '</p></div>';
        }
        if (item.why_correct) {
            html += '<div class="wb-detail-section"><strong>正确理解</strong><p>' + this._esc(item.why_correct) + '</p></div>';
        }
        if (item.key_rule) {
            html += '<div class="wb-detail-section"><strong>判断依据</strong><p>' + this._esc(item.key_rule) + '</p></div>';
        }
        if (item.review_action) {
            html += '<div class="wb-detail-section"><strong>下一步</strong><p>' + this._esc(item.review_action) + '</p></div>';
        }
        if (item.misconception) {
            html += '<div class="wb-detail-section"><strong>典型误区</strong><p>' + this._esc(item.misconception) + '</p></div>';
        }
        if (rec.suggestion || rec.prerequisite_hint) {
            html += '<div class="wb-detail-section wb-detail-review"><strong>复习建议</strong>';
            if (rec.suggestion) html += '<p>' + this._esc(rec.suggestion) + '</p>';
            if (rec.prerequisite_hint) html += '<p class="wb-detail-hint">前置提醒：' + this._esc(rec.prerequisite_hint) + '</p>';
            html += '</div>';
        }
        if (Object.keys(analysis).length) {
            html += '<div class="wb-detail-section"><strong>错误选项分析</strong>';
            Object.keys(analysis).sort().forEach(key => {
                html += '<p><b>' + this._esc(key) + '</b>：' + this._esc(String(analysis[key] || '')) + '</p>';
            });
            html += '</div>';
        }
        return html;
    },

    _wrongReasonLabel(reason) {
        const labels = {
            concept_confusion: '概念混淆',
            formula_misuse: '公式误用',
            condition_missing: '条件遗漏',
            calculation_error: '计算错误',
            graph_relation_gap: '图示关系不清',
            reading_misread: '审题偏差',
        };
        return labels[reason] || reason || '未分类';
    },

    _renderFooter(data) {
        const total = Number(data.total || 0);
        const page = Number(data.page || 1);
        const totalPages = Math.max(1, Math.ceil(total / this.pageSize));
        if (this._summaryEl) this._summaryEl.textContent = '共 ' + total + ' 道错题，' + Number(data.total_unmastered || 0) + ' 道待复习';
        if (this._pageInfoEl) this._pageInfoEl.textContent = page + ' / ' + totalPages;
        const prevBtn = document.getElementById('wb-prev-page');
        const nextBtn = document.getElementById('wb-next-page');
        if (prevBtn) prevBtn.disabled = page <= 1;
        if (nextBtn) nextBtn.disabled = page >= totalPages;
        if (this._footerEl) this._footerEl.hidden = false;
    },

    _toggleGroup(header) {
        const body = header.nextElementSibling;
        const arrow = header.querySelector('.wb-group-arrow');
        if (body && arrow) {
            body.hidden = !body.hidden;
            arrow.innerHTML = body.hidden ? '&#9654;' : '&#9660;';
        }
    },

    _toggleDetail(btn) {
        const main = btn.closest('.wb-item-main');
        if (!main) return;
        const detail = main.querySelector('.wb-item-detail');
        if (!detail) return;
        detail.hidden = !detail.hidden;
        btn.textContent = detail.hidden ? '展开讲解' : '收起讲解';
    },

    _markMasteredFromButton(btn, mastered) {
        const item = btn && typeof btn.closest === 'function' ? btn.closest('.wb-item') : null;
        const qid = item && item.dataset ? String(item.dataset.qid || '') : '';
        if (!qid) {
            this._renderError(new Error('缺少错题编号，无法更新掌握状态。'));
            return;
        }

        const originalText = btn.textContent;
        btn.disabled = true;
        btn.textContent = mastered ? '保存中...' : '取消中...';
        this._markMastered(qid, mastered)
            .catch(err => {
                console.error('标记失败', err);
                this._renderError(err);
            })
            .finally(() => {
                if (btn.isConnected) {
                    btn.disabled = false;
                    btn.textContent = originalText;
                }
            });
    },

    async _markMastered(qid, mastered) {
        const studentId = this._studentId();
        const resp = await fetch('/api/students/' + encodeURIComponent(studentId) + '/wrong-questions/' + encodeURIComponent(qid) + '/master', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mastered: Boolean(mastered) }),
        });
        if (!resp.ok) throw new Error('HTTP ' + resp.status);
        return this._fetchAndRender();
    },

    changePage(delta) {
        const totalPages = Math.max(1, Math.ceil(this.lastTotal / this.pageSize));
        this.page = Math.max(1, Math.min(totalPages, this.page + delta));
        this._showLoading();
        this._fetchAndRender();
    },

    _formatDate(value) {
        const text = String(value || '').trim();
        if (!text) return '';
        return text.replace('T', ' ').slice(0, 16);
    },

    _esc(value) {
        const div = document.createElement('div');
        div.textContent = String(value || '');
        return div.innerHTML;
    },
};

window.WrongBook = WrongBook;
window.openWrongBookModal = function() { WrongBook.open(); };
window.closeWrongBookModal = function(event) { WrongBook.close(event); };
window.wbChangePage = function(delta) { WrongBook.changePage(delta); };

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() { WrongBook.init(); });
} else {
    WrongBook.init();
}
