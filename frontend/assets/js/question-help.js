/**
 * question-help.js — 侧边栏"题目答疑"临时解题框。
 * 与错题本分离：这里保存临时题目解答记录，不自动写入错题本。
 */

const QuestionHelp = {
    init() {
        this._modalEl = document.getElementById('question-help-modal');
        this._openButtonEl = document.getElementById('open-question-help-btn');
        this._textEl = document.getElementById('question-help-text');
        this._imagesEl = document.getElementById('question-help-images');
        this._fileSummaryEl = document.getElementById('question-help-file-summary');
        this._answerModeEl = document.getElementById('question-help-answer-mode');
        this._submitEl = document.getElementById('question-help-submit');
        this._statusEl = document.getElementById('question-help-status');
        this._recordsEl = document.getElementById('question-help-records');
        this._currentEl = document.getElementById('question-help-current');
        this._currentBodyEl = document.getElementById('question-help-current-body');
        this._currentModeEl = document.getElementById('question-help-current-mode');
    },

    open() {
        this.init();
        this._setOpen(true);
        this._setStatus('');
        this._fetchAndRenderRecords();
        if (this._textEl) this._textEl.focus();
    },

    close(event) {
        if (!this._modalEl) this.init();
        if (event && this._modalEl && event.target !== this._modalEl) return;
        this._setOpen(false);
    },

    chooseImages() {
        if (!this._imagesEl) this.init();
        if (this._imagesEl) this._imagesEl.click();
    },

    onImagesChanged() {
        if (!this._imagesEl) this.init();
        const files = Array.from((this._imagesEl && this._imagesEl.files) || []);
        if (!this._fileSummaryEl) return;
        if (!files.length) {
            this._fileSummaryEl.textContent = '未选择图片';
            return;
        }
        this._fileSummaryEl.textContent = files.map(file => file.name).join('、');
    },

    async submit() {
        if (!this._textEl) this.init();
        const text = String((this._textEl && this._textEl.value) || '').trim();
        const files = Array.from((this._imagesEl && this._imagesEl.files) || []);
        if (!text && !files.length) {
            this._setStatus('请先输入题目文字，或上传题目图片。', true);
            return;
        }

        const form = new FormData();
        form.append('question_text', text);
        files.forEach(file => form.append('images', file));
        const answerMode = this._answerMode(files);
        form.append('answer_mode', answerMode);

        // 传递当前学习节点上下文
        const appState = (window.AITutorApp && window.AITutorApp.state) || {};
        const nodeId = appState.currentGraphNodeId || appState.current_node_id || '';
        const nodeName = appState.currentGraphNode || appState.current_node_name || '';
        if (nodeId) form.append('current_node_id', nodeId);
        if (nodeName) form.append('current_node_name', nodeName);

        this._setBusy(true);
        this._setStatus('正在解答…');
        this._renderCurrentPending({ question_text: text, image_count: files.length, answer_mode: answerMode });
        try {
            const studentId = this._studentId();
            const resp = await fetch('/api/students/' + encodeURIComponent(studentId) + '/question-help', {
                method: 'POST',
                body: form,
            });
            if (!resp.ok) throw new Error(await this._readErrorDetail(resp));
            const data = await resp.json();
            if (this._textEl) this._textEl.value = '';
            if (this._imagesEl) this._imagesEl.value = '';
            this.onImagesChanged();
            this._renderCurrentRecord(data.record || {});
            this._renderRecords(data.records || []);
            this._setStatus('已生成解答，并保留到解答记录。');
        } catch (err) {
            this._setStatus('题目答疑失败，请稍后重试。' + (err && err.message ? ' ' + err.message : ''), true);
        } finally {
            this._setBusy(false);
        }
    },

    async _fetchAndRenderRecords() {
        if (!this._recordsEl) this.init();
        if (!this._recordsEl) return;
        this._recordsEl.textContent = '正在加载解答记录…';
        try {
            const studentId = this._studentId();
            const resp = await fetch('/api/students/' + encodeURIComponent(studentId) + '/question-help');
            if (!resp.ok) throw new Error(await this._readErrorDetail(resp));
            const data = await resp.json();
            this._renderRecords(data.items || []);
        } catch (err) {
            this._recordsEl.textContent = '解答记录加载失败。';
            this._setStatus(err && err.message ? err.message : '', true);
        }
    },

    _renderRecords(records) {
        if (!this._recordsEl) return;
        this._recordsEl.textContent = '';
        if (!records.length) {
            const empty = document.createElement('div');
            empty.className = 'qh-empty';
            empty.textContent = '暂无解答记录';
            this._recordsEl.appendChild(empty);
            return;
        }
        records.forEach(record => {
            this._recordsEl.appendChild(this._renderRecord(record || {}));
        });
    },

    _renderRecord(record, options = {}) {
        const card = document.createElement('article');
        card.className = options.current ? 'qh-record qh-record--current' : 'qh-record';

        // ── 头部元信息 ──
        const header = document.createElement('div');
        header.className = 'qh-record-header';

        const date = document.createElement('span');
        date.className = 'qh-record-date';
        date.textContent = this._formatDate(record.created_at || '') || '刚刚';
        header.appendChild(date);

        if (record.node_name) {
            const nodeTag = document.createElement('span');
            nodeTag.className = 'qh-record-node-tag';
            nodeTag.textContent = record.node_name;
            header.appendChild(nodeTag);
        }
        if (record.answer_mode_label) {
            const modeTag = document.createElement('span');
            modeTag.className = 'qh-record-node-tag';
            modeTag.textContent = record.answer_mode_label;
            header.appendChild(modeTag);
        }

        card.appendChild(header);

        // ── 题干 ──
        const questionPanel = document.createElement('section');
        questionPanel.className = 'qh-question-panel';
        const questionLabel = document.createElement('div');
        questionLabel.className = 'qh-question-label';
        questionLabel.textContent = '题目';
        questionPanel.appendChild(questionLabel);
        const question = document.createElement('div');
        question.className = 'qh-question';
        const hasText = Boolean(record.question_text && record.question_text.trim());
        question.textContent = hasText
            ? (record.question_text.length > 200 ? record.question_text.slice(0, 200) + '…' : record.question_text)
            : (Number(record.image_count || 0) ? '图片题目' : '未提供题干');
        questionPanel.appendChild(question);

        // ── 图片文件列表 ──
        const images = Array.isArray(record.images) ? record.images : [];
        if (images.length) {
            const imageList = document.createElement('div');
            imageList.className = 'qh-image-list';
            images.forEach(image => {
                const item = document.createElement('span');
                item.textContent = '图片：' + (image.filename || '未命名图片');
                imageList.appendChild(item);
            });
            questionPanel.appendChild(imageList);
        }
        card.appendChild(questionPanel);

        // ── 解答内容（复用 ui.js 中的 marked + sanitizer + KaTeX 渲染） ──
        const answerShell = document.createElement('section');
        answerShell.className = 'qh-answer-shell';
        const answerHead = document.createElement('div');
        answerHead.className = 'qh-answer-head';
        const answerKicker = document.createElement('span');
        answerKicker.className = 'qh-answer-kicker';
        answerKicker.textContent = '解答';
        const answerCopy = document.createElement('span');
        answerCopy.className = 'qh-answer-copy';
        answerCopy.textContent = '考点 · 步骤 · 答案 · 易错提醒';
        answerHead.appendChild(answerKicker);
        answerHead.appendChild(answerCopy);
        answerShell.appendChild(answerHead);
        const answer = document.createElement('div');
        answer.className = 'qh-answer';
        const answerText = record.answer || '暂无解答';
        const app = window.AITutorApp || {};
        try {
            app.renderMarkdownContent?.(answer, answerText, { allowLearningHtml: true });
        } catch (_e) {
            answer.textContent = answerText;
        }
        if (!answer.childNodes.length) {
            answer.textContent = answerText;
        }
        app.renderMath?.(answer);
        this._emphasizeAnswerSections(answer);
        answerShell.appendChild(answer);
        card.appendChild(answerShell);

        // ── 展开/收起（长解答） ──
        if (!options.current && answerText.length > 600) {
            card.classList.add('qh-record--collapsible');
            const toggleBtn = document.createElement('button');
            toggleBtn.type = 'button';
            toggleBtn.className = 'qh-toggle-btn';
            toggleBtn.textContent = '收起解答';
            toggleBtn.onclick = () => {
                card.classList.toggle('qh-record--collapsed');
                toggleBtn.textContent = card.classList.contains('qh-record--collapsed') ? '展开解答' : '收起解答';
            };
            card.appendChild(toggleBtn);
            // 默认折叠
            card.classList.add('qh-record--collapsed');
        }

        return card;
    },

    _renderCurrentPending(record = {}) {
        if (!this._currentBodyEl) this.init();
        if (!this._currentBodyEl) return;
        this._currentBodyEl.textContent = '';
        if (this._currentModeEl) this._currentModeEl.textContent = this._answerModeLabel(record.answer_mode);
        const pending = document.createElement('div');
        pending.className = 'qh-current-pending';
        const question = document.createElement('div');
        question.className = 'qh-question-panel';
        const label = document.createElement('div');
        label.className = 'qh-question-label';
        label.textContent = '正在解答';
        const summary = document.createElement('div');
        summary.className = 'qh-question';
        summary.textContent = String(record.question_text || '').trim()
            || (Number(record.image_count || 0) ? '图片题目' : '当前题目');
        question.appendChild(label);
        question.appendChild(summary);
        pending.appendChild(question);
        ['正在分析题目…', '正在识别考点…', '正在组织解题步骤…', '正在检查公式格式…'].forEach((text, index) => {
            const step = document.createElement('div');
            step.className = `qh-stream-step ${index === 0 ? 'is-active' : ''}`;
            step.textContent = text;
            pending.appendChild(step);
        });
        this._currentBodyEl.appendChild(pending);
    },

    _renderCurrentRecord(record = {}) {
        if (!this._currentBodyEl) this.init();
        if (!this._currentBodyEl) return;
        this._currentBodyEl.textContent = '';
        if (this._currentModeEl) {
            this._currentModeEl.textContent = record.answer_mode_label || this._answerModeLabel(record.answer_mode);
        }
        this._currentBodyEl.appendChild(this._renderRecord(record, { current: true }));
    },

    _answerMode(files = []) {
        const value = String((this._answerModeEl && this._answerModeEl.value) || '').trim();
        if (['quick', 'deep', 'vision'].includes(value)) return value;
        return files.length ? 'vision' : 'quick';
    },

    _answerModeLabel(mode) {
        return {
            quick: '快速解答',
            deep: '深度解析',
            vision: '图片题专用',
        }[String(mode || '').trim()] || '快速解答';
    },

    _emphasizeAnswerSections(root) {
        if (!root?.querySelectorAll) return;
        root.querySelectorAll('h2, h3').forEach(heading => {
            const text = String(heading.textContent || '').replace(/\s+/g, '');
            if (!text.includes('最终答案')) return;
            heading.classList.add('qh-answer-heading--final');
            let sibling = heading.nextElementSibling;
            while (sibling && !/^H[23]$/i.test(sibling.tagName || '')) {
                if (['P', 'UL', 'OL', 'TABLE', 'DIV'].includes((sibling.tagName || '').toUpperCase())) {
                    sibling.classList.add('qh-answer-final-block');
                }
                sibling = sibling.nextElementSibling;
            }
        });
    },

    _studentId() {
        const state = (window.AITutorApp && window.AITutorApp.state) || {};
        return state.studentId || state.student_id || 'default_student';
    },

    _setOpen(open) {
        if (!this._modalEl) return;
        this._modalEl.classList.toggle('open', Boolean(open));
        this._modalEl.setAttribute('aria-hidden', open ? 'false' : 'true');
        if (this._openButtonEl) this._openButtonEl.setAttribute('aria-expanded', open ? 'true' : 'false');
    },

    _setBusy(busy) {
        if (this._submitEl) this._submitEl.disabled = Boolean(busy);
    },

    _setStatus(message, isError) {
        if (!this._statusEl) return;
        this._statusEl.textContent = String(message || '');
        this._statusEl.classList.toggle('qh-status--error', Boolean(isError));
    },

    async _readErrorDetail(resp) {
        try {
            const data = await resp.json();
            const detail = data && data.detail;
            if (typeof detail === 'string' && detail.trim()) return detail;
            if (detail) return JSON.stringify(detail);
        } catch (_error) {
            // Fall back to HTTP status when the server did not return JSON.
        }
        return 'HTTP ' + resp.status;
    },

    _formatDate(value) {
        const text = String(value || '').trim();
        if (!text) return '';
        return text.replace('T', ' ').slice(0, 16);
    },
};

window.QuestionHelp = QuestionHelp;
window.openQuestionHelpModal = function() { QuestionHelp.open(); };
window.closeQuestionHelpModal = function(event) { QuestionHelp.close(event); };

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() { QuestionHelp.init(); });
} else {
    QuestionHelp.init();
}
