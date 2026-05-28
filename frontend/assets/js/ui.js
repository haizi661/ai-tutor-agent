(() => {
    const app = window.AITutorApp;
    const state = app.state;
    const PRE_TOPIC_FLOW_STATUSES = new Set(['greeting', 'topic_intake', 'meta_qa', 'smalltalk']);
    const TOPIC_CONFIRM_FLOW_STATUSES = new Set(['topic_confirmation_pending', 'awaiting_topic_confirmation']);
    const STATUS_BANNER_TONES = ['status-ready', 'status-info', 'status-awaiting', 'status-processing', 'status-success', 'status-warning', 'status-danger', 'status-paused'];
    const TURN_ROLE_COPY = {
        teacher: { label: '', avatar: '伴' },
        tutor: { label: '', avatar: '伴' },
        coach: { label: '', avatar: '伴' },
        tester: { label: '', avatar: '伴' },
        interruption: { label: '', avatar: '伴' },
        interruption_tutor: { label: '', avatar: '伴' },
        graph_rag_debug_report: { label: '', avatar: '伴' },
        graph_rag_answer: { label: '', avatar: '伴' },
        evaluation: { label: '', avatar: '伴' },
        profile: { label: '', avatar: '伴' },
        assessment: { label: '', avatar: '伴' },
        topic_confirmation: { label: '', avatar: '伴' },
        interrupt_confirmation: { label: '', avatar: '伴' },
        prompt: { label: '', avatar: '伴' },
        system: { label: '', avatar: '伴' },
    };
    const PROGRESS_LABELS = ['准备中', '摸底中', '讲解中', '巩固中', '收束中'];
    const SHORT_VISIBLE_FALLBACK_MS = 1600;
    const LONG_VISIBLE_FALLBACK_MS = 5200;
    const MAX_VISIBLE_FALLBACKS = 2;

    function escapeHtml(value) {
        return String(value || '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function normalizeCasesBody(body) {
        return String(body || '')
            .split(/(\\\\(?:\s*\[[^\]]+\])?)/)
            .map((part) => {
                if (part.startsWith('\\\\') || part.includes('&')) return part;
                return part.replace(
                    /,\s*((?:(?:\\?[a-zA-Z]|[^\s,])[\s\S]*?(?:\\leq?|\\geq?|[<>≤≥=])[\s\S]*))$/,
                    ', & $1'
                );
            })
            .join('');
    }

    function normalizeLatexSource(latex) {
        return String(latex || '').replace(
            /\\left\\\{\s*\\begin\{array\}\{[^}]*\}([\s\S]*?)\\end\{array\}\s*\\right\.?/g,
            (_match, body) => `\\begin{cases}${normalizeCasesBody(body)}\\end{cases}`
        ).replace(
            /\\begin\{cases\}([\s\S]*?)\\end\{cases\}/g,
            (_match, body) => `\\begin{cases}${normalizeCasesBody(body)}\\end{cases}`
        );
    }

    function normalizeMathBlock(block) {
        const value = String(block || '');
        const wrappers = [
            ['$$', '$$'],
            ['\\[', '\\]'],
            ['\\(', '\\)'],
            ['$', '$'],
        ];
        const wrapper = wrappers.find(([left, right]) => value.startsWith(left) && value.endsWith(right));
        if (!wrapper) return normalizeLatexSource(value);
        const [left, right] = wrapper;
        const inner = value.slice(left.length, value.length - right.length);
        return `${left}${normalizeLatexSource(inner)}${right}`;
    }

    function parseMarkdown(text) {
        if (typeof marked === 'undefined') return text;
        const mathBlocks = [];
        let processed = String(text || '').replace(/(\$\$[\s\S]*?\$\$|\$[\s\S]*?\$|\\\[[\s\S]*?\\\]|\\\([\s\S]*?\\\))/g, (match) => {
            mathBlocks.push(normalizeMathBlock(match));
            return `@@MATH_BLOCK_${mathBlocks.length - 1}@@`;
        });

        let html = marked.parse(processed);

        html = html.replace(/@@MATH_BLOCK_(\d+)@@/g, (match, i) => {
            return mathBlocks[i];
        });
        return html;
    }

    function renderMarkdown(target, text, options = {}) {
        const rawText = String(text || '');
        const allowGraphRagHtml = options.allowGraphRagHtml === true;
        const allowLearningHtml = options.allowLearningHtml === true;
        if (allowGraphRagHtml) {
            target.innerHTML = sanitizeLearningHtml(extractGraphRagReportBody(rawText), { allowDebugClasses: true });
        } else if (allowLearningHtml) {
            target.innerHTML = sanitizeLearningHtml(renderLearningHtmlOrMarkdown(rawText));
        } else {
            target.innerHTML = sanitizeRenderedHtml(parseMarkdown(rawText));
        }
        normalizeLearningRelatedOverview(target);
        stripRedundantTextAfterTables(target);
        app.renderMath(target);
    }

    app.renderMarkdownContent = function renderMarkdownContent(target, text, options = {}) {
        renderMarkdown(target, text, options);
    };

    function renderLearningHtmlOrMarkdown(rawText = '') {
        const text = String(rawText || '');
        if (/<(?:div|section)\b[^>]*class=["'][^"']*(?:learning-answer-content|homework-answer-content|learning-reference-block|learning-evidence-card|learning-formula-card|learning-figure-card|learning-table-card)/i.test(text)) {
            return text;
        }
        return parseMarkdown(text);
    }

    /**
     * When an answer contains <table> elements, the LLM often also writes
     * text paragraphs that restate the same content.  Hide those paragraphs
     * so the user only sees the table itself.
     */
    function stripRedundantTextAfterTables(root) {
        if (!root?.querySelectorAll) return;
        const tables = root.querySelectorAll('table');
        if (!tables.length) return;
        tables.forEach((table) => {
            // Walk siblings after the table; hide text-only elements until we
            // hit another structured block (table, figure, formula card, etc.).
            let sibling = table.nextElementSibling;
            while (sibling) {
                const tag = (sibling.tagName || '').toLowerCase();
                // Stop at another structured element
                if (['table', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'section'].includes(tag)) break;
                if (sibling.classList?.contains('learning-table-card') ||
                    sibling.classList?.contains('learning-formula-card') ||
                    sibling.classList?.contains('learning-figure-card') ||
                    sibling.classList?.contains('learning-evidence-card') ||
                    sibling.classList?.contains('learning-related-overview')) break;
                // Hide text-only elements (p, div, span wrappers around text)
                if (['p', 'div', 'span', 'ul', 'ol'].includes(tag)) {
                    sibling.style.display = 'none';
                }
                sibling = sibling.nextElementSibling;
            }
        });
    }

    function sanitizeRenderedHtml(rawHtml = '') {
        return sanitizeLearningHtml(rawHtml, { allowDebugClasses: false });
    }

    function sanitizeLearningHtml(rawText = '', options = {}) {
        const text = String(rawText || '');
        const source = /<html[\s>]/i.test(text) ? extractGraphRagReportBody(text) : text;
        const template = document.createElement('template');
        template.innerHTML = source;
        const allowedTags = [
            'a', 'b', 'blockquote', 'br', 'button', 'caption', 'code', 'details', 'div', 'em',
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'img', 'li', 'main', 'ol', 'p', 'pre',
            'section', 'span', 'strong', 'sub', 'summary', 'sup', 'table', 'tbody', 'td', 'th',
            'thead', 'tr', 'ul',
        ];
        const allowedAttributes = [
            'alt', 'aria-hidden', 'aria-label', 'aria-modal', 'class', 'colspan', 'data-latex', 'data-learning-action',
            'href', 'id', 'loading', 'role', 'rowspan', 'src', 'target', 'title', 'type',
        ];
        const allowedClasses = [
            'learning-answer-content',
            'learning-block-header',
            'learning-block-title',
            'learning-block-actions',
            'learning-block-caption',
            'learning-evidence-card',
            'learning-evidence-card--formula',
            'learning-evidence-card--figure',
            'learning-evidence-card--table',
            'learning-evidence-card--source',
            'learning-evidence-header',
            'learning-evidence-type',
            'learning-evidence-title',
            'learning-evidence-summary',
            'learning-citation',
            'learning-citation-index',
            'learning-source-line',
            'learning-source-item',
            'learning-source-body',
            'learning-debug-details',
            'learning-latex-details',
            'learning-figure-unavailable',
            'learning-media-ref',
            'learning-reference-block',
            'learning-reference-text',
            'learning-reference-media',
            'learning-reference-media-title',
            'learning-reference-media-grid',
            'learning-related-overview',
            'learning-formula-card',
            'learning-inline-formula-card',
            'learning-formula-viewport',
            'learning-figure-card',
            'learning-figure-viewport',
            'learning-table-card',
            'learning-table-viewport',
            'learning-table-empty',
            'learning-derivation-card',
            'learning-derivation-steps',
            'learning-code-viewport',
            'learning-media-group',
            'formula-render',
            'formula-math',
            'homework-answer-content',
            'homework-assignment-card',
            'homework-feedback-card',
            'homework-item-list',
            'homework-item-card',
            'homework-result-card',
            'homework-item-meta',
            'homework-item-index',
            'homework-item-id',
            'homework-question-text',
            'homework-answer-viewport',
            'homework-reference',
            'homework-rubric-list',
            'homework-score-badge',
            'homework-score-badge--good',
            'homework-score-badge--warn',
            'homework-score-badge--danger',
            'homework-answer-line',
            'homework-feedback-text',
        ];
        if (options.allowDebugClasses) {
            allowedClasses.push(
                'graph-rag-answer-panel', 'graph-rag-evidence-panel', 'answer-media-block', 'media-grid',
                'media-card', 'formula-card', 'figure-card', 'table-card', 'media-ref', 'raw-ref',
                'media-node', 'media-caption', 'media-hint', 'modal', 'modal-content', 'modal-content--wide',
                'close-btn', 'figure-viewport', 'figure-gallery', 'formula-scroll', 'formula-viewport',
                'formula-full', 'formula-raw', 'table-preview', 'table-viewport', 'table-full',
                'answer-formula', 'section-title', 'media-unavailable-card', 'media-unavailable-copy'
            );
        }
        template.content.querySelectorAll('*').forEach((node) => {
            const tag = node.tagName.toLowerCase();
            if (!allowedTags.includes(tag)) {
                node.replaceWith(document.createTextNode(node.textContent || ''));
                return;
            }
            [...node.attributes].forEach((attr) => {
                const name = attr.name.toLowerCase();
                const value = attr.value || '';
                if (name.startsWith('on') || !allowedAttributes.includes(name)) {
                    node.removeAttribute(attr.name);
                    return;
                }
                if ((name === 'href' || name === 'src') && !isSafeUrl(value, name)) {
                    node.removeAttribute(attr.name);
                    return;
                }
                if (name === 'target' && value !== '_blank') {
                    node.removeAttribute(attr.name);
                }
            });
            if (node.classList?.length) {
                [...node.classList].forEach((className) => {
                    if (!allowedClasses.includes(className) && !className.startsWith('katex')) {
                        node.classList.remove(className);
                    }
                });
            }
            if (node.tagName.toLowerCase() === 'a' && node.getAttribute('target') === '_blank') {
                node.setAttribute('rel', 'noopener noreferrer');
            }
        });
        return template.innerHTML;
    }

    function isSafeUrl(value = '', attrName = '') {
        const raw = String(value || '').trim();
        if (!raw) return false;
        if (raw.startsWith('#') || raw.startsWith('/') || raw.startsWith('./') || raw.startsWith('../')) return true;
        const lower = raw.toLowerCase();
        if (attrName === 'src' && lower.startsWith('data:image/')) return true;
        return lower.startsWith('http://') || lower.startsWith('https://');
    }

    function extractGraphRagReportBody(rawText = '') {
        const text = String(rawText || '');
        if (!/<html[\s>]/i.test(text)) return text;
        try {
            const doc = new DOMParser().parseFromString(text, 'text/html');
            const main = doc.querySelector('main');
            return main ? main.innerHTML : (doc.body?.innerHTML || text);
        } catch (_err) {
            return text;
        }
    }

    function normalizeLearningRelatedOverview(root) {
        root.querySelectorAll?.('.learning-related-overview').forEach((overview) => {
            const cards = Array.from(overview.querySelectorAll([
                ':scope > .learning-formula-card',
                ':scope > .learning-figure-card',
                ':scope > .learning-table-card',
                ':scope > .learning-derivation-card',
                ':scope > .learning-evidence-card',
            ].join(', ')));
            const seen = new Set();
            let kept = 0;
            cards.forEach((card) => {
                const key = (
                    card.querySelector('[data-latex]')?.getAttribute('data-latex')
                    || card.querySelector('img')?.getAttribute('src')
                    || card.querySelector('.learning-block-title, .learning-evidence-title')?.textContent
                    || card.textContent
                    || ''
                ).replace(/\s+/g, ' ').trim();
                if (!key || seen.has(key) || kept >= 3) {
                    card.remove();
                    return;
                }
                seen.add(key);
                kept += 1;
            });
            if (!overview.querySelector('.learning-formula-card, .learning-figure-card, .learning-table-card, .learning-derivation-card, .learning-evidence-card')) {
                overview.remove();
            }
        });
    }

    function deriveLearningProgressStep(snapshot = {}) {
        const flowStatus = String(snapshot.flow_status || '').trim();
        if (flowStatus === 'awaiting_post_eval_selector') return 5;
        if (flowStatus === 'awaiting_next_step_selector') return 4;
        if (
            flowStatus === 'normal'
            || flowStatus === 'direct_tutor'
            || flowStatus === 'awaiting_interrupt_confirmation'
        ) {
            return 3;
        }
        if (
            flowStatus === 'awaiting_assessment'
            || flowStatus === 'assessment_pending'
            || flowStatus === 'profiling'
        ) {
            return 2;
        }
        if (PRE_TOPIC_FLOW_STATUSES.has(flowStatus) || TOPIC_CONFIRM_FLOW_STATUSES.has(flowStatus)) {
            return 1;
        }
        if (snapshot.tester_question || snapshot.tutor_content || snapshot.coach_content) return 3;
        if (snapshot.score || snapshot.feedback) return 4;
        return 1;
    }

    app.updateLearningProgress = function updateLearningProgress(input = {}) {
        const nextStep = Math.max(1, Math.min(5, Number(input.step || deriveLearningProgressStep(input) || 1)));
        const stageName = input.stage || PROGRESS_LABELS[nextStep - 1] || '准备中';
        const dots = document.querySelectorAll('.learning-progress-dot');
        dots.forEach((dot, index) => {
            dot.classList.toggle('active', index < nextStep);
        });
        const labelEl = document.getElementById('learning-progress-label');
        if (labelEl) {
            labelEl.textContent = stageName;
        }
        app.patchState?.({
            learningProgressStep: nextStep,
            learningProgressLabel: stageName,
        }, 'learning-progress');
    };

    app.renderMath = function renderMath(el) {
        if (window.katex) {
            el.querySelectorAll?.('.formula-render[data-latex]').forEach((node) => {
                const latex = normalizeLatexSource(node.getAttribute('data-latex') || node.textContent || '');
                if (!latex.trim()) return;
                try {
                    katex.render(latex, node, { displayMode: true, throwOnError: false, strict: 'ignore' });
                    updateFormulaViewportOverflow(node.closest('.formula-scroll, .learning-formula-viewport') || node);
                } catch (err) {
                    console.warn('KaTeX formula-render failed', err);
                }
            });
        }
        if (window.renderMathInElement) {
            renderMathInElement(el, {
                delimiters: [
                    { left: '$$', right: '$$', display: true },
                    { left: '$', right: '$', display: false },
                    { left: '\\[', right: '\\]', display: true },
                    { left: '\\(', right: '\\)', display: false },
                ],
                throwOnError: false,
            });
        }
        markTaggedMathDisplays(el);
        updateFormulaViewportOverflow(el);
    };

    function markTaggedMathDisplays(root) {
        const scope = root || document;
        scope.querySelectorAll?.('.katex-display .tag').forEach((tag) => {
            const display = tag.closest('.katex-display');
            if (!display) return;
            const tagWidth = Math.ceil(tag.getBoundingClientRect().width || tag.offsetWidth || 0);
            display.classList.add('katex-display--tagged');
            display.style.setProperty('--katex-tag-space', `${Math.max(tagWidth + 16, 56)}px`);
        });
    }

    function updateFormulaViewportOverflow(root) {
        const scope = root || document;
        const viewports = scope.matches?.('.formula-scroll, .learning-formula-viewport')
            ? [scope]
            : [...(scope.querySelectorAll?.('.formula-scroll, .learning-formula-viewport') || [])];
        viewports.forEach((viewport) => {
            const content = viewport.querySelector?.('.katex, .formula-render, .formula-math') || viewport.firstElementChild;
            const isOverflowing = Boolean(content && content.scrollWidth > viewport.clientWidth + 2);
            viewport.classList.toggle('is-overflowing', isOverflowing);
        });
    }

    let formulaOverflowResizeTimer = null;
    window.addEventListener('resize', () => {
        window.clearTimeout(formulaOverflowResizeTimer);
        formulaOverflowResizeTimer = window.setTimeout(() => updateFormulaViewportOverflow(document), 120);
    });

    window.openModal = function openModal(id) {
        const modal = document.getElementById(id);
        if (!modal) return;
        modal.style.display = 'block';
        modal.setAttribute('aria-hidden', 'false');
        app.renderMath(modal);
    };

    window.closeModal = function closeModal(id) {
        const modal = document.getElementById(id);
        if (!modal) return;
        modal.style.display = 'none';
        modal.setAttribute('aria-hidden', 'true');
    };

    function ensureLearningViewer() {
        let overlay = document.getElementById('learning-viewer-overlay');
        if (overlay) return overlay;
        overlay = document.createElement('div');
        overlay.id = 'learning-viewer-overlay';
        overlay.className = 'learning-viewer-overlay';
        overlay.setAttribute('aria-hidden', 'true');
        overlay.innerHTML = `
            <div class="learning-viewer-panel" role="dialog" aria-modal="true" aria-label="学习内容放大查看" onclick="event.stopPropagation()">
                <div class="learning-viewer-header">
                    <div class="learning-viewer-title">放大查看</div>
                    <button type="button" class="learning-viewer-close" onclick="closeLearningViewer()">关闭</button>
                </div>
                <div class="learning-viewer-body"></div>
            </div>
        `;
        overlay.addEventListener('click', () => window.closeLearningViewer());
        document.body.appendChild(overlay);
        return overlay;
    }

    window.openLearningViewer = function openLearningViewer(source) {
        const sourceEl = typeof source === 'string' ? document.querySelector(source) : source;
        if (!sourceEl) return;
        const overlay = ensureLearningViewer();
        const body = overlay.querySelector('.learning-viewer-body');
        body.innerHTML = '';
        body.appendChild(sourceEl.cloneNode(true));
        overlay.classList.add('is-open');
        overlay.setAttribute('aria-hidden', 'false');
        app.renderMath(body);
    };

    window.closeLearningViewer = function closeLearningViewer() {
        const overlay = document.getElementById('learning-viewer-overlay');
        if (!overlay) return;
        overlay.classList.remove('is-open');
        overlay.setAttribute('aria-hidden', 'true');
    };

    window.copyLearningBlock = async function copyLearningBlock(source) {
        const sourceEl = typeof source === 'string' ? document.querySelector(source) : source;
        if (!sourceEl) return false;
        const text = sourceEl.innerText || sourceEl.textContent || '';
        if (!text.trim()) return false;
        try {
            await navigator.clipboard.writeText(text.trim());
            return true;
        } catch (_error) {
            app.setStatusBanner?.('复制失败，请手动选择内容复制。', 'warning');
            return false;
        }
    };

    document.addEventListener('click', (event) => {
        const actionButton = event.target?.closest?.('[data-learning-action]');
        if (!actionButton) return;
        const block = actionButton.closest('.learning-formula-card, .learning-figure-card, .learning-table-card, .learning-derivation-card');
        if (!block) return;
        const action = actionButton.dataset.learningAction;
        if (action === 'open') {
            window.openLearningViewer?.(block);
        } else if (action === 'copy') {
            window.copyLearningBlock?.(block);
        }
    });

    /* ── Sidebar state sync ── */
    app.updateSidebarState = function updateSidebarState(snapshot) {
        if (!snapshot) snapshot = state;
        const ukg = snapshot.userKnowledgeGraph || snapshot.user_knowledge_graph || state.userKnowledgeGraph || {};
        const entries = Object.entries(ukg);
        let mastered = 0, progress = 0, pending = 0;
        let nextNode = '';
        entries.forEach(([title, info]) => {
            const s = (typeof info === 'object' ? info.status : info) || 'not_started';
            if (s === 'mastered') mastered++;
            else if (s === 'in_progress') progress++;
            else pending++;
        });
        // Find next node (first not_started after current)
        const currentNode = snapshot.currentGraphNode || snapshot.graph_anchor_title || state.currentGraphNode || '';
        const currentTopic = snapshot.currentTopic || snapshot.current_topic || state.currentTopic || '';
        const topicHint = snapshot.graphTopicHint || snapshot.current_topic || snapshot.proposed_topic || state.graphTopicHint || '';
        let foundCurrent = false;
        for (const [title, info] of entries) {
            const s = (typeof info === 'object' ? info.status : info) || 'not_started';
            if (title === currentNode) { foundCurrent = true; continue; }
            if (foundCurrent && s === 'not_started') { nextNode = title; break; }
        }
        if (!nextNode) {
            for (const [title, info] of entries) {
                const s = (typeof info === 'object' ? info.status : info) || 'not_started';
                if (s === 'not_started') { nextNode = title; break; }
            }
        }

        const empty = entries.length === 0;
        const el = id => document.getElementById(id);
        const setText = (id, val) => { const e = el(id); if (e) e.textContent = val; };
        const currentIndex = currentNode ? entries.findIndex(([title]) => title === currentNode) : -1;

        // Session card
        setText('ssc-profile', currentTopic || '—');
        setText('ssc-node', currentIndex >= 0 ? `节点 ${currentIndex + 1}/${entries.length}` : '—');
        setText('ssc-progress', empty ? '—' : String(progress));
        setText('ssc-mastered', empty ? '—' : String(mastered));
        setText('ssc-pending', empty ? '—' : String(pending));
        setText('ssc-current-node', currentNode || '完成测评后自动填充');
        setText('ssc-next-node', nextNode || '—');

        // Header title and hidden compatibility fields
        setText('header-thread-title', currentTopic || '新对话');
        setText('cl-profile', currentTopic || 'AI Tutor');
        setText('cl-node-text', currentNode || topicHint || '等待开始');
        setText('cl-progress', empty ? '—' : String(progress));
        setText('cl-mastered', empty ? '—' : String(mastered));
        setText('cl-pending', empty ? '—' : String(pending));
        setText('cl-next-node', nextNode || '等待开始');

        document.title = currentTopic ? `${currentTopic} - AI Tutor` : 'AI Tutor';

        const nodeChip = el('cl-node-chip');
        if (nodeChip) {
            const chipText = currentNode || topicHint || '等待开始';
            nodeChip.title = currentNode ? `当前节点：${chipText}` : '打开知识图谱';
            nodeChip.setAttribute('aria-label', currentNode ? `当前节点 ${chipText}，点击打开知识图谱` : '打开知识图谱');
        }

        app.refreshChatSurfaceState?.();
    };

    /* Debounced sidebar update */
    let _sidebarUpdateTimer = null;
    app.scheduleSidebarUpdate = function scheduleSidebarUpdate() {
        if (_sidebarUpdateTimer) return;
        _sidebarUpdateTimer = window.requestAnimationFrame(() => {
            _sidebarUpdateTimer = null;
            app.updateSidebarState();
        });
    };

    function normalizeEvidenceItems(evidence) {
        if (!Array.isArray(evidence) || !evidence.length) return [];

        const normalized = [];
        const seen = new Set();
        const clip = (value, limit = 74) => {
            const text = String(value || '').replace(/\s+/g, ' ').trim();
            if (!text) return '';
            return text.length > limit ? `${text.slice(0, limit).trim()}…` : text;
        };

        evidence.forEach(raw => {
            const sourceType = String(raw?.source_type || 'local_kb').trim();
            const label = String(raw?.display_label || raw?.filename || raw?.title || '').trim();
            if (!label) return;

            const rank = Number.isInteger(raw?.rank) ? raw.rank : null;
            const snippet = clip(raw?.snippet || '');
            const url = String(raw?.url || '').trim();
            const sourceScope = String(raw?.source_scope || '').trim();
            const groupLabel = sourceType === 'web_search'
                ? '外部'
                : (sourceScope === 'course_primary' ? '主课程' : '补充资料');
            const sourceBadge = sourceType === 'web_search'
                ? '外部网页'
                : (sourceScope === 'course_primary' ? '课程图谱' : '上传资料');
            const dedupKey = `${sourceType}|${label}|${url}|${snippet.slice(0, 80)}`;
            if (seen.has(dedupKey)) return;
            seen.add(dedupKey);

            normalized.push({ sourceType, label, rank, snippet, url, sourceScope, groupLabel, sourceBadge });
        });

        return normalized.slice(0, 4);
    }

    app.formatEvidencePanel = function formatEvidencePanel(evidence) {
        const normalized = normalizeEvidenceItems(evidence);
        if (!normalized.length) return '';

        const lines = ['### 依据'];
        let currentGroup = '';
        normalized.forEach((item, index) => {
            if (item.groupLabel !== currentGroup) {
                currentGroup = item.groupLabel;
                lines.push('');
                lines.push(`**${currentGroup}**`);
            }
            lines.push('');
            lines.push(`${item.rank || index + 1}. ${item.label}`);
            lines.push(`来源：${item.sourceBadge}`);
            if (item.url) {
                lines.push(`<${item.url}>`);
            }
            if (item.snippet) {
                lines.push(`> ${item.snippet}`);
            }
        });

        return lines.join('\n');
    };

    function buildCompactPromptCardContent(text = '', fallbackTitle = '') {
        const lines = String(text || '')
            .split('\n')
            .map(line => line.trim())
            .filter(Boolean);

        const chips = [];
        const paragraphs = [];
        let activeSection = '';
        const pushUniqueChip = (value, className = '') => {
            const normalized = String(value || '').trim();
            if (!normalized) return;
            if (chips.some(item => item.text === normalized)) return;
            chips.push({ text: normalized, className });
        };
        const pushParagraph = value => {
            const normalized = String(value || '').trim();
            if (!normalized) return;
            if (!paragraphs.includes(normalized)) paragraphs.push(normalized);
        };
        const classifyBullet = value => {
            if (/(误区|混淆|风险|盲点|卡点|薄弱|遗漏)/.test(value)) return 'chip-risk';
            if (/(建议|下一步|复习|再试|提示|先看|先补)/.test(value)) return 'chip-next';
            return '';
        };

        lines.forEach(line => {
            if (/^###\s+/.test(line)) return;
            const cleaned = line.replace(/\*\*/g, '').trim();
            const normalized = cleaned
                .replace(/^\d+\.\s+/, '')
                .replace(/^[-*]\s+/, '')
                .trim();
            const scoreMatch = normalized.match(/^(总分|逻辑|概念)[：:]\s*(.+)$/);
            if (scoreMatch) {
                pushUniqueChip(`${scoreMatch[1]} ${scoreMatch[2]}`, 'chip-score');
                return;
            }
            const riskMatch = normalized.match(/^(风险点|风险|误区|盲点|卡点|量表依据)[：:]\s*(.+)$/);
            if (riskMatch) {
                activeSection = 'risk';
                pushUniqueChip(riskMatch[2], 'chip-risk');
                return;
            }
            const nextMatch = normalized.match(/^(下一步|建议|建议复习|行动建议|提示)[：:]\s*(.+)$/);
            if (nextMatch) {
                activeSection = 'next';
                pushUniqueChip(nextMatch[2], 'chip-next');
                return;
            }
            if (/^(量表依据|风险点|误区|盲点)[：:]?$/.test(normalized)) {
                activeSection = 'risk';
                return;
            }
            if (/^(建议复习|下一步|建议|提示)[：:]?$/.test(normalized)) {
                activeSection = 'next';
                return;
            }
            if (/^(结论|观察|简要诊断|依据)[：:]\s*/.test(normalized)) {
                pushParagraph(normalized);
                return;
            }
            if (/^[-*]\s+/.test(cleaned)) {
                const className = activeSection === 'risk'
                    ? 'chip-risk'
                    : activeSection === 'next'
                        ? 'chip-next'
                        : classifyBullet(normalized);
                if (className) {
                    pushUniqueChip(normalized, className);
                }
                return;
            }
            pushParagraph(normalized);
        });

        const bodyLines = paragraphs.slice(0, 3).map(line => `<p>${line}</p>`);

        return {
            title: fallbackTitle,
            html: bodyLines.join('') || `<p>${fallbackTitle}</p>`,
            chips: chips.slice(0, 6),
        };
    }

    app.renderEvidencePanel = function renderEvidencePanel(evidence, options = {}) {
        const items = normalizeEvidenceItems(evidence);
        if (!items.length) return false;

        const role = options.role || 'tutor';
        if (options.clearTyping) app.clearTypingIndicator();

        if (state.currentTurnId || state.isStreaming || state.currentAgentTurnEl) {
            app.setPendingTurnRole?.(role);
            app.ensureAgentTurn?.(role);
        }

        if (!state.currentAgentMainFlowEl) {
            app.appendSystemMessage(app.formatEvidencePanel(evidence), options.tone || 'info');
            app.markTurnVisible?.();
            return true;
        }

        const panel = document.createElement('section');
        panel.className = 'agent-visible-item evidence-panel';
        panel.dataset.tone = options.tone || 'info';
        panel.dataset.kind = 'evidence';
        panel.dataset.role = role;

        const header = document.createElement('div');
        header.className = 'agent-visible-kicker';
        header.textContent = '依据';
        panel.appendChild(header);

        const list = document.createElement('div');
        list.className = 'evidence-panel-list';
        let currentGroup = '';
        items.forEach((item, index) => {
            if (item.groupLabel !== currentGroup) {
                currentGroup = item.groupLabel;
            const group = document.createElement('div');
            group.className = 'evidence-panel-group';
            group.textContent = currentGroup;
            list.appendChild(group);
        }

            const row = document.createElement('article');
            row.className = 'evidence-panel-item';

            const heading = document.createElement('div');
            heading.className = 'evidence-panel-heading';

            const badge = document.createElement('span');
            badge.className = 'evidence-panel-index';
            badge.textContent = String(item.rank || index + 1);
            heading.appendChild(badge);

            const title = document.createElement(item.url ? 'a' : 'div');
            title.className = 'evidence-panel-title';
            title.textContent = item.label;
            if (item.url) {
                title.href = item.url;
                title.target = '_blank';
                title.rel = 'noreferrer noopener';
            }
            heading.appendChild(title);

            const source = document.createElement('span');
            source.className = 'evidence-panel-source';
            source.textContent = item.sourceBadge;
            heading.appendChild(source);
            row.appendChild(heading);

            if (item.snippet) {
                const snippet = document.createElement('p');
                snippet.className = 'evidence-panel-snippet';
                snippet.textContent = item.snippet;
                row.appendChild(snippet);
            }

            list.appendChild(row);
        });

        panel.appendChild(list);
        state.currentAgentMainFlowEl.hidden = false;
        state.currentAgentMainFlowEl.appendChild(panel);
        app.markTurnVisible?.();
        app.scrollMessagesToBottom();
        return true;
    };

    app.formatTutorCitations = app.formatEvidencePanel;
    app.renderTutorCitations = app.renderEvidencePanel;

    let mathRenderTimeout = null;

    app.syncProfilePanelState = function syncProfilePanelState() {};

    function resolveGraphNodeTitle(reference = '') {
        const ref = String(reference || '').trim();
        if (!ref) return '';
        if (state.userKnowledgeGraph?.[ref]) return ref;

        const entries = Object.entries(state.userKnowledgeGraph || {});
        const matched = entries.find(([, value]) => String(value?.id || '').trim() === ref);
        if (matched) return matched[0];
        return ref;
    }

    function collectTeachingMarkers(text = '') {
        return {
            mastered: [...String(text || '').matchAll(/\[MASTERY_ACHIEVED:\s*([^\]]+)\]/g)].map(match => match[1].trim()),
            skipped: [...String(text || '').matchAll(/\[SKIPPED:\s*([^\]]+)\]/g)].map(match => match[1].trim()),
            next: [...String(text || '').matchAll(/\[→ 下一概念[:：]\s*([^\]|]+?)(?:\s*\|\s*([^\]]+))?\]/g)].map(match => ({
                title: match[1].trim(),
                id: String(match[2] || '').trim(),
            })),
        };
    }

    app.throttledRender = function throttledRender() {
        if (!state.currentAgentBodyEl) return;
        // Strip teaching markers from displayed text (pure transform, side effects applied on session.end)
        const displayText = app.filterTeachingMarkersFromBuffer(state.currentTextBuffer);
        renderMarkdown(state.currentAgentBodyEl, displayText, {
            allowLearningHtml: state.currentTurnRole === 'graph_rag_answer' || state.currentTurnRole === 'graph_rag_debug_report',
            allowGraphRagHtml: state.currentTurnRole === 'graph_rag_debug_report',
        });
        
        // Debounce heavy KaTeX rendering to prevent flickering and CPU spikes during fast streaming
        if (mathRenderTimeout) clearTimeout(mathRenderTimeout);
        mathRenderTimeout = setTimeout(() => {
            if (state.currentAgentBodyEl) {
                app.renderMath(state.currentAgentBodyEl);
            }
        }, 150);
    };

    /** 纯函数：从文本中过滤教学标记（供渲染时调用，不产生副作用）*/
    app.filterTeachingMarkersFromBuffer = function filterTeachingMarkersFromBuffer(text) {
        return String(text || '')
            .replace(/\[MASTERY_ACHIEVED:\s*[^\]]+\]/g, '')
            .replace(/\[SKIPPED:\s*[^\]]+\]/g, '')
            .replace(/\[→ 下一概念[:：]\s*([^\]|]+?)(?:\s*\|\s*[^\]]+)?\]/g, (_m, title) =>
                `<span class="graph-event-chip graph-event-chip--next">→ 即将进入：${title.trim()}</span>`
            )
            // 处理流式传输中不完整的标记（防止暴露 "[MASTERY_ACHIEVED:" 半截文字）
            .replace(/\[(MASTERY_ACHIEVED|SKIPPED|→ 下一概念)[^\]]*$/, '');
    };

    /** 应用教学标记的副作用（在 session.end 时调用一次）*/
    app.applyTeachingMarkerSideEffects = function applyTeachingMarkerSideEffects(text) {
        const markers = collectTeachingMarkers(text);
        markers.mastered.forEach(reference => app.updateGraphNode(resolveGraphNodeTitle(reference), 'mastered'));
        markers.skipped.forEach(reference => app.updateGraphNode(resolveGraphNodeTitle(reference), 'skipped'));
        markers.next.forEach(item => app.highlightNextNode(item.title || resolveGraphNodeTitle(item.id)));
    };

    /**
     * 更新用户知识图谱节点状态，并在消息流中插入事件 chip。
     * status: 'in_progress' | 'mastered' | 'skipped' | 'upcoming'
     */
    app.updateGraphNode = function updateGraphNode(title, status, type, nodeId) {
        if (!title) return;
        const prev = (state.userKnowledgeGraph || {})[title] || {};
        state.userKnowledgeGraph = state.userKnowledgeGraph || {};
        state.userKnowledgeGraph[title] = {
            ...(typeof prev === 'object' ? prev : {}),
            ...(nodeId ? { id: nodeId } : {}),
            status,
            updatedAt: Date.now(),
        };
        if (status === 'in_progress' || type === 'current') {
            state.currentGraphNode = title;
            state.currentGraphNodeId = nodeId || state.currentGraphNodeId || '';
        }

        const sameStatus = prev && typeof prev === 'object' && prev.status === status;

        // 仅对明确的教学里程碑追加 event chip（避免 in_progress 频繁插入）
        if (status === 'mastered' && !sameStatus) {
            _appendGraphEventChip(`✅  已掌握：${title}`, 'mastered');
        } else if (status === 'skipped' && !sameStatus) {
            _appendGraphEventChip(`⏭  已跳过：${title}`, 'skipped');
        }

        app.refreshUserKgMapIfOpen?.();
        app.syncKnowledgeGraphVisualState?.();
    };

    /** 在下游节点到来时高亮提示（不影响 UKG 状态，只做视觉）*/
    app.highlightNextNode = function highlightNextNode(title) {
        if (!title) return;
        _appendGraphEventChip(`→  即将进入：${title}`, 'next');
    };

    function _buildGraphViewerUrl({ nodeTitle = '', nodeId = '' } = {}) {
        if (typeof app.buildKnowledgeGraphUrl === 'function') {
            return app.buildKnowledgeGraphUrl({ embedded: true, focus: nodeTitle || nodeId });
        }
        const params = new URLSearchParams();
        const topic = (state.currentTopic || state.graphTopicHint || '').trim();
        const focus = (nodeTitle || nodeId || state.currentGraphNode || state.currentGraphNodeId || '').trim();
        if (topic) params.set('topic', topic);
        if (focus) params.set('focus', focus);
        params.set('embedded', '1');
        return `/knowledge-graph/b/viewer/index.html?${params.toString()}`;
    }

    app.renderKnowledgeGraphVisualCard = function renderKnowledgeGraphVisualCard(payload = {}) {
        const nodeTitle = String(payload.title || payload.node_name || state.currentGraphNode || state.graph_anchor_title || '').trim();
        const nodeId = String(payload.id || payload.node_id || state.currentGraphNodeId || state.graph_anchor_id || '').trim();
        if (!nodeTitle && !nodeId) return;

        state.currentGraphNode = nodeTitle || state.currentGraphNode;
        state.currentGraphNodeId = nodeId || state.currentGraphNodeId;

        document.querySelector('.assistant-card-row.graph-visual-card-row')?.remove();
        const container = document.getElementById('messages');
        if (!container) return;
        const row = createAssistantCardRow('graph-visual-card-row');
        const card = document.createElement('section');
        card.className = 'graph-visual-card prompt-flow-card';
        const graphSrc = _buildGraphViewerUrl({ nodeTitle, nodeId });
        card.innerHTML = `
            <div class="graph-visual-head">
                <div>
                    <div class="prompt-label">当前主讲节点</div>
                    <div class="graph-visual-title">${nodeTitle || nodeId}</div>
                    <div class="graph-visual-copy">这不是重新开始，而是在标记当前讲到图谱的哪个节点。临时问题会单独回答，不改变这里的主线进度。</div>
                </div>
                <button type="button" class="graph-visual-open">打开完整图谱</button>
            </div>
            <div class="graph-visual-frame-wrap">
                <iframe
                    class="graph-visual-frame"
                    data-graph-mini-frame
                    title="当前学习节点知识图谱"
                    loading="lazy"
                    src="${graphSrc}"
                ></iframe>
            </div>
        `;
        const frame = card.querySelector('[data-graph-mini-frame]');
        if (frame) {
            frame.dataset.src = graphSrc;
            frame.onload = () => app.syncKnowledgeGraphVisualState?.();
        }
        card.querySelector('.graph-visual-open')?.addEventListener('click', () => app.openKnowledgeGraphModal?.());
        row.body.appendChild(card);
        container.appendChild(row.wrap);
        app.syncKnowledgeGraphVisualState?.();
        app.scrollMessagesToBottom?.();
    };

    /** 若"掌握图"面板已打开则刷新 */
    app.refreshUserKgMapIfOpen = function refreshUserKgMapIfOpen() {
        if (state.userKgMapOpen) app.renderUserKnowledgeMap();
    };

    /** 在消息流中插入一条图谱事件 chip */
    function _appendGraphEventChip(text, kind) {
        const container = document.getElementById('messages');
        if (!container) return;
        const chip = document.createElement('div');
        chip.className = `graph-event-chip-row graph-event-chip-row--${kind}`;
        chip.innerHTML = `<span class="graph-event-chip graph-event-chip--${kind}">${text}</span>`;
        container.appendChild(chip);
        app.scrollMessagesToBottom?.();
    }

    app.clearTypingIndicator = function clearTypingIndicator() {
        document.getElementById('typing-indicator')?.remove();
        app.refreshChatSurfaceState?.();
    };

    app.refreshChatSurfaceState = function refreshChatSurfaceState() {
        const chatMain = document.querySelector('.chat-main');
        const landingStage = document.getElementById('landing-stage');
        const messages = document.getElementById('messages');
        const locator = document.getElementById('chat-locator');
        const sessionStrip = document.getElementById('cl-session-strip');
        if (!chatMain || !landingStage || !messages || !locator) return;

        const hasConversationContent = messages.childElementCount > 0;
        const hasContext = Boolean(
            state.currentTopic
            || state.currentGraphNode
            || state.graphTopicHint
            || Object.keys(state.userKnowledgeGraph || {}).length
        );
        const isLanding = !hasConversationContent && !state.isStreaming && !state.isAwaitingInput;

        chatMain.classList.toggle('chat-main--landing', isLanding);
        chatMain.classList.toggle('chat-main--conversation', !isLanding);
        chatMain.classList.toggle('chat-main--has-context', !isLanding && hasContext);
        chatMain.classList.toggle('chat-main--no-context', !isLanding && !hasContext);

        landingStage.hidden = !isLanding;
        messages.hidden = isLanding;
        locator.hidden = false;
        locator.classList.toggle('chat-header--landing', isLanding);
        locator.classList.toggle('chat-header--conversation', !isLanding);
        if (sessionStrip) sessionStrip.hidden = true;
    };

    app.setStatusBanner = function setStatusBanner(message, tone = 'ready') {
        const banner = document.getElementById('status-banner');
        if (!banner) return;
        const text = String(message || '').trim();
        banner.textContent = text;
        banner.hidden = !text;
        banner.classList.remove(...STATUS_BANNER_TONES);
        banner.classList.add(`status-${tone}`);
    };

    app.setInlineStatus = function setInlineStatus(elementId, message, tone = 'muted') {
        const el = document.getElementById(elementId);
        if (!el) return;
        const text = String(message || '').trim();
        el.textContent = text;
        el.hidden = !text;
        el.dataset.tone = tone;
    };

    app.scrollMessagesToBottom = function scrollMessagesToBottom(options = {}) {
        const container = document.getElementById('messages');
        if (!container) return;
        const shouldForceScroll = Boolean(options.force) || container.hidden;
        app.refreshChatSurfaceState?.();
        if (container.hidden) return;
        
        // Only auto-scroll if the user is near the bottom
        // This prevents the screen from jumping down if they scrolled up to read
        const isNearBottom = shouldForceScroll || container.scrollHeight - container.scrollTop - container.clientHeight < 150;
        
        if (isNearBottom) {
            container.scrollTop = container.scrollHeight;
        }
    };

    function restoredInteractionSelector(snapshot = {}) {
        const flowStatus = String(snapshot.flow_status || '').trim();
        const pendingKind = String(snapshot.pending_interaction_kind || '').trim();
        const kind = pendingKind || ({
            awaiting_post_lesson_choice: 'post_lesson_choice',
            awaiting_next_step_selector: 'next_step_selector',
            awaiting_post_eval_selector: 'post_eval_selector',
            awaiting_continue_or_homework_choice: 'continue_or_homework_choice',
            awaiting_homework_review_choice: 'homework_review_choice',
            awaiting_homework_answers: 'homework_answers',
            homework_assigned: 'homework_review_choice',
            awaiting_consolidation_choice: 'consolidation_choice',
            awaiting_objective_answers: 'objective_test_answers',
            awaiting_variant_answers: 'variant_test_answers',
            awaiting_assessment: 'assessment',
            assessment_dialog: 'assessment',
            awaiting_topic_confirmation: 'topic_confirmation',
            awaiting_interrupt_confirmation: 'interrupt_confirmation',
        }[flowStatus] || '');
        return {
            post_lesson_choice: '.post-lesson-card',
            next_step_selector: '.next-step-card',
            post_eval_selector: '.post-eval-card',
            continue_or_homework_choice: '.continue-homework-card',
            homework_review_choice: '.homework-review-card, .homework-assignment-card',
            homework_answers: '.homework-answer-card',
            consolidation_choice: '.consolidation-card',
            objective_test_answers: '.obj-test-card',
            variant_test_answers: '.obj-test-card',
            assessment: '.assessment-container, .q-card',
            topic_confirmation: '.topic-confirm-card:not(.tc-locked)',
            interrupt_confirmation: '.interrupt-confirm-card',
        }[kind] || '.msg-wrapper:last-child';
    }

    app.focusRestoredSessionPosition = function focusRestoredSessionPosition(snapshot = {}) {
        const container = document.getElementById('messages');
        if (!container) return;
        app.refreshChatSurfaceState?.();
        if (container.hidden) return;

        const selector = restoredInteractionSelector(snapshot);
        const candidates = Array.from(container.querySelectorAll(selector));
        const rawTarget = candidates.pop() || container.querySelector('.msg-wrapper:last-child');
        const target = rawTarget?.closest?.('.msg-wrapper') || rawTarget;
        if (!target) return;

        const scrollToTarget = () => {
            const containerRect = container.getBoundingClientRect();
            const targetRect = target.getBoundingClientRect();
            const top = container.scrollTop + targetRect.top - containerRect.top - 16;
            container.scrollTop = Math.max(0, top);
        };

        window.requestAnimationFrame(scrollToTarget);
        window.setTimeout(scrollToTarget, 150);
        window.setTimeout(scrollToTarget, 500);
        window.setTimeout(scrollToTarget, 1200);
        window.setTimeout(scrollToTarget, 1800);
    };

    app.clearTurnHeartbeat = function clearTurnHeartbeat() {
        if (!state.currentTurnHeartbeatEl) return;
        state.currentTurnHeartbeatEl.hidden = true;
        state.currentTurnHeartbeatEl.textContent = '';
    };

    app.setTurnHeartbeat = function setTurnHeartbeat(message = '我还在处理中') {
        if (!state.currentTurnId || state.turnHasVisibleOutput) return false;
        app.ensureAgentTurn();
        if (!state.currentTurnHeartbeatEl) return false;
        state.currentTurnHeartbeatEl.hidden = false;
        state.currentTurnHeartbeatEl.textContent = message;
        app.scrollMessagesToBottom();
        return true;
    };

    app.clearVisibilityFallback = function clearVisibilityFallback({ resetCounter = true } = {}) {
        if (state.visibilityFallbackTimer) {
            window.clearTimeout(state.visibilityFallbackTimer);
            state.visibilityFallbackTimer = null;
        }
        if (resetCounter) state.visibilityFallbackCount = 0;
    };

    app.resetTurnLifecycleState = function resetTurnLifecycleState() {
        app.clearVisibilityFallback({ resetCounter: true });
        state.currentTurnId = '';
        state.currentTurnRole = 'teacher';
        state.turnHasVisibleOutput = false;
        state.turnStartedAt = 0;
        state.lastVisibleAt = 0;
        state.lastHeartbeatAt = 0;
        state.latestProgressSummary = '';
        state.latestNodeStartMessage = '';
        state.latestRouteDecisionSummary = '';
    };

    app.startAgentTurnLifecycle = function startAgentTurnLifecycle() {
        app.clearVisibilityFallback({ resetCounter: true });
        const now = Date.now();
        state.currentTurnId = `turn_${now}_${Math.random().toString(36).slice(2, 8)}`;
        state.turnHasVisibleOutput = false;
        state.turnStartedAt = now;
        state.lastVisibleAt = 0;
        state.lastHeartbeatAt = 0;
        state.latestProgressSummary = '';
        state.latestNodeStartMessage = '';
        state.latestRouteDecisionSummary = '';
        app.clearTurnHeartbeat();
        app.scheduleVisibilityFallback();
    };

    app.markTurnVisible = function markTurnVisible() {
        state.turnHasVisibleOutput = true;
        state.lastVisibleAt = Date.now();
        app.clearTurnHeartbeat();
    };

    app.recordTurnProgress = function recordTurnProgress(text, source = 'progress') {
        if (!text) return;
        state.latestProgressSummary = text;
        if (source === 'node.start') state.latestNodeStartMessage = text;
        if (source === 'route.decision') state.latestRouteDecisionSummary = text;
    };

    app.getTurnProgressFallbackText = function getTurnProgressFallbackText() {
        if (state.latestRouteDecisionSummary) return `我这边的推进情况：${state.latestRouteDecisionSummary}`;
        if (state.latestNodeStartMessage) return `我这边正在做这一步：${state.latestNodeStartMessage}`;
        if (state.latestProgressSummary) return `我这边已经推进到这里：${state.latestProgressSummary}`;
        return '我还在整理这一步，拿到更具体结果后会立刻告诉你。';
    };

    app.getTurnRoleMeta = function getTurnRoleMeta(role = 'teacher') {
        return TURN_ROLE_COPY[role] || TURN_ROLE_COPY.teacher;
    };

    app.applyCurrentTurnRole = function applyCurrentTurnRole(role = state.currentTurnRole || 'teacher') {
        state.currentTurnRole = role || 'teacher';
        if (!state.currentAgentTurnEl) return;
        const meta = app.getTurnRoleMeta(state.currentTurnRole);
        state.currentAgentTurnEl.dataset.role = state.currentTurnRole;
        state.currentAgentTurnKickerEl && (state.currentAgentTurnKickerEl.textContent = meta.label || '');
        const avatar = state.currentAgentTurnEl.querySelector('.avatar.agent');
        if (avatar) avatar.textContent = meta.avatar;
    };

    app.currentTurnHasRenderableContent = function currentTurnHasRenderableContent() {
        return Boolean(state.currentTextBuffer.trim())
            || Boolean(state.currentAgentMainFlowEl?.childElementCount)
            || state.turnHasVisibleOutput;
    };

    app.setPendingTurnRole = function setPendingTurnRole(role, { forceSplit = false } = {}) {
        const nextRole = role || 'teacher';
        if (!state.currentAgentTurnEl) {
            state.currentTurnRole = nextRole;
            return;
        }
        if (state.currentTurnRole === nextRole) {
            app.applyCurrentTurnRole(nextRole);
            return;
        }
        if (forceSplit || app.currentTurnHasRenderableContent()) {
            const wasStreaming = state.isStreaming;
            app.finalizeAgentTurn?.();
            if (wasStreaming) app.startAgentTurnLifecycle?.();
            state.currentTurnRole = nextRole;
            return;
        }
        app.applyCurrentTurnRole(nextRole);
    };

    app.scheduleVisibilityFallback = function scheduleVisibilityFallback() {
        if (!state.currentTurnId || state.visibilityFallbackCount >= MAX_VISIBLE_FALLBACKS) return;
        app.clearVisibilityFallback({ resetCounter: false });
        const turnId = state.currentTurnId;
        const delay = state.visibilityFallbackCount === 0 ? SHORT_VISIBLE_FALLBACK_MS : LONG_VISIBLE_FALLBACK_MS;
        state.visibilityFallbackTimer = window.setTimeout(() => {
            state.visibilityFallbackTimer = null;
            if (state.currentTurnId !== turnId || !state.isStreaming) return;

            if (state.visibilityFallbackCount === 0) {
                app.setTurnHeartbeat?.('我已经接上这一步了，正在替你往下理。');
                state.visibilityFallbackCount = 1;
                app.scheduleVisibilityFallback();
                return;
            }

            if (state.visibilityFallbackCount === 1) {
                app.setTurnHeartbeat?.(app.getTurnProgressFallbackText());
                state.visibilityFallbackCount = 2;
            }
        }, delay);
    };

    app.appendAgentTurnShell = function appendAgentTurnShell(initialText = '', role = state.currentTurnRole || 'teacher', renderOptions = {}) {
        const meta = app.getTurnRoleMeta(role);
        const wrap = document.createElement('div');
        wrap.className = 'msg-wrapper msg-row agent';
        wrap.dataset.role = role;
        wrap.innerHTML = `
            <div class="avatar agent ai" aria-hidden="true">${meta.avatar}</div>
            <div class="bubble-wrap">
                <div class="agent-turn bubble ai">
                    <div class="agent-body"></div>
                    <div class="agent-main-flow" hidden></div>
                    <div class="turn-heartbeat" hidden aria-live="polite"></div>
                </div>
            </div>
        `;
        const container = document.getElementById('messages');
        container.appendChild(wrap);

        state.currentAgentTurnEl = wrap;
        state.currentAgentMainFlowEl = wrap.querySelector('.agent-main-flow');
        state.currentAgentBodyEl = wrap.querySelector('.agent-body');
        state.currentAgentTurnKickerEl = null;
        state.currentAgentMsgEl = state.currentAgentBodyEl;
        state.currentTurnHeartbeatEl = wrap.querySelector('.turn-heartbeat');
        state.currentTraceBlockEl = null;
        state.currentTraceListEl = null;
        state.currentTraceBadgeEl = null;
        state.currentTextBuffer = initialText;
        state.traceCount = 0;

        renderMarkdown(state.currentAgentBodyEl, initialText, renderOptions);
        wrap.querySelector('.bubble-wrap')?.appendChild(buildAssistantMessageTools(wrap));
        app.setAssistantActionBarState?.(wrap, Boolean(state.isStreaming));
        app.scrollMessagesToBottom();
        return wrap;
    };

    app.ensureAgentTurn = function ensureAgentTurn(role = state.currentTurnRole || 'teacher') {
        if (
            state.currentAgentBodyEl &&
            state.currentAgentMainFlowEl
        ) {
            app.applyCurrentTurnRole(role);
            return state.currentAgentTurnEl;
        }
        return app.appendAgentTurnShell('', role);
    };

    app.updateMetaBadges = function updateMetaBadges() {
        return;
    };

    function normalizeMetaKey(text) {
        return String(text || '').replace(/\s+/g, ' ').trim();
    }

    function appendMetaItem(listEl, text, tone = 'info', kind = 'thinking') {
        const normalized = normalizeMetaKey(text);
        if (!normalized) return false;

        const last = listEl?.lastElementChild;
        if (last && last.dataset.raw === normalized && last.dataset.kind === kind) {
            last.dataset.tone = tone;
            return false;
        }

        const item = document.createElement('li');
        item.className = 'trace-item';
        item.dataset.tone = tone;
        item.dataset.raw = normalized;
        item.dataset.kind = kind;

        const tag = document.createElement('span');
        tag.className = 'trace-tag';
        tag.textContent = kind === 'note' ? '注' : '步';
        item.appendChild(tag);

        const body = document.createElement('div');
        body.className = 'trace-body';
        renderMarkdown(body, text);
        item.appendChild(body);
        listEl.appendChild(item);
        return true;
    }

    function _ensureThinkDrawer() {
        if (!state.currentAgentTurnEl) return null;
        const existing = state.currentAgentTurnEl.querySelector('.trace-drawer');
        if (existing) return existing;

        const bubble = state.currentAgentTurnEl.querySelector('.bubble.ai') || state.currentAgentTurnEl.querySelector('.agent-turn');
        if (!bubble) return null;

        const drawer = document.createElement('details');
        drawer.className = 'trace-drawer';
        drawer.dataset.thinkDrawer = '1';
        if (!state.thinkingMode) drawer.setAttribute('hidden', '');

        const summary = document.createElement('summary');
        summary.innerHTML = '<span class="meta-title">教学推理</span><span class="meta-badge">0</span>';
        drawer.appendChild(summary);

        const list = document.createElement('ol');
        list.className = 'trace-list';
        drawer.appendChild(list);

        bubble.insertBefore(drawer, bubble.firstChild);
        return drawer;
    }

    function _updateThinkDrawerVisibility() {
        if (!state.currentAgentTurnEl) return;
        const drawer = state.currentAgentTurnEl.querySelector('.trace-drawer');
        if (!drawer) return;
        if (state.thinkingMode) {
            drawer.removeAttribute('hidden');
        } else {
            drawer.setAttribute('hidden', '');
        }
    }

    app.syncThinkDrawerVisibility = _updateThinkDrawerVisibility;

    app.addThinkingStep = function addThinkingStep(text, tone = 'info') {
        if (!text) return false;
        if (tone === 'warning' || tone === 'danger') app.setStatusBanner(text, tone);
        // 推理模式关闭时静默吞掉推理事件，避免 appendMeta() fallback 成聊天区系统消息。
        if (!state.thinkingMode) return true;
        const drawer = _ensureThinkDrawer();
        if (!drawer) return false;
        const list = drawer.querySelector('.trace-list');
        if (!list) return false;
        const appended = appendMetaItem(list, text, tone, 'thinking');
        if (appended) {
            const badge = drawer.querySelector('.meta-badge');
            if (badge) badge.textContent = String(list.children.length);
        }
        return true;
    };

    app.addNote = function addNote(text, tone = 'info') {
        if (!text) return false;
        if (tone === 'warning' || tone === 'danger') app.setStatusBanner(text, tone);
        // 推理模式关闭时静默吞掉注记事件，避免 appendMeta() fallback 成聊天区系统消息。
        if (!state.thinkingMode) return true;
        const drawer = _ensureThinkDrawer();
        if (!drawer) return false;
        const list = drawer.querySelector('.trace-list');
        if (!list) return false;
        const appended = appendMetaItem(list, text, tone, 'note');
        if (appended) {
            const badge = drawer.querySelector('.meta-badge');
            if (badge) badge.textContent = String(list.children.length);
        }
        return true;
    };

    function visibleLabelFor(role, kind) {
        if (kind === 'evidence') return '证据';
        return '';
    }

    app.appendVisibleSystemTurn = function appendVisibleSystemTurn(text, tone = 'info', options = {}) {
        if (!text) return false;
        const {
            kind = 'status',
            clearTyping = false,
            createIfNeeded = true,
            markVisible = true,
            role = state.currentTurnRole || 'teacher',
        } = options;

        if (clearTyping) app.clearTypingIndicator();
        if (createIfNeeded && (state.currentTurnId || state.isStreaming || state.currentAgentTurnEl)) {
            app.setPendingTurnRole?.(role);
            app.ensureAgentTurn(role);
        }

        if (!state.currentAgentMainFlowEl) {
            app.appendSystemMessage(text, tone);
            if (markVisible) app.markTurnVisible();
            return true;
        }

        const item = document.createElement('section');
        item.className = 'agent-visible-item';
        item.dataset.tone = tone;
        item.dataset.kind = kind;
        item.dataset.role = role;
        const label = visibleLabelFor(role, kind);
        if (label) {
            const kicker = document.createElement('div');
            kicker.className = 'agent-visible-kicker';
            kicker.textContent = label;
            item.appendChild(kicker);
        }
        const body = document.createElement('div');
        body.className = 'agent-visible-body';
        renderMarkdown(body, text);
        item.appendChild(body);
        state.currentAgentMainFlowEl.hidden = false;
        state.currentAgentMainFlowEl.appendChild(item);
        if (markVisible) app.markTurnVisible();
        app.scrollMessagesToBottom();
        return true;
    };

    app.finalizeAgentTurn = function finalizeAgentTurn() {
        app.clearTurnHeartbeat();
        app.setAssistantActionBarState?.(state.currentAgentTurnEl, false);
        const finalizedTurn = state.currentAgentTurnEl;
        if (finalizedTurn?.dataset?.containsObjectiveReview === 'true') {
            finalizedTurn.classList.add('agent-turn-finalized-review');
        }
        state.currentAgentMsgEl = null;
        state.currentAgentTurnEl = null;
        state.currentAgentMainFlowEl = null;
        state.currentAgentBodyEl = null;
        state.currentAgentTurnKickerEl = null;
        state.currentTurnHeartbeatEl = null;
        state.currentTraceBlockEl = null;
        state.currentTraceListEl = null;
        state.currentTraceBadgeEl = null;
        state.currentTextBuffer = '';
        state.traceCount = 0;
        app.resetTurnLifecycleState();
    };

    app.roleFromMessageKind = function roleFromMessageKind(kind) {
        if (kind === 'tutor') return 'tutor';
        if (kind === 'tutor_citations' || kind === 'tutor_evidence') return 'tutor';
        if (kind === 'coach') return 'coach';
        if (kind === 'tester_question') return 'tester';
        if (kind === 'graph_rag_answer') return 'graph_rag_answer';
        if (kind === 'graph_rag_debug_report') return 'graph_rag_debug_report';
        if (kind === 'evaluator_card') return 'evaluation';
        if (kind === 'assessment_result') return 'profile';
        return 'teacher';
    };

    function createPromptCardRow({
        label = '提示',
        title = '',
        html = '',
        chips = [],
        rowClass = '',
        tone = 'info',
    } = {}) {
        const wrap = document.createElement('div');
        wrap.className = `msg-wrapper msg-row system ${rowClass}`.trim();
        wrap.dataset.tone = tone;

        const avatar = document.createElement('div');
        avatar.className = 'avatar system ai';
        avatar.setAttribute('aria-hidden', 'true');
        avatar.textContent = '伴';
        wrap.appendChild(avatar);

        const bubbleWrap = document.createElement('div');
        bubbleWrap.className = 'bubble-wrap';

        const card = document.createElement('div');
        card.className = 'prompt-card prompt-flow-shell';

        if (label) {
            const labelEl = document.createElement('div');
            labelEl.className = 'prompt-label';
            labelEl.textContent = label;
            card.appendChild(labelEl);
        }

        if (title) {
            const titleEl = document.createElement('div');
            titleEl.className = 'prompt-title';
            titleEl.textContent = title;
            card.appendChild(titleEl);
        }

        if (html) {
            const body = document.createElement('div');
            body.className = 'prompt-copy';
            body.innerHTML = html;
            card.appendChild(body);
        }

        bubbleWrap.appendChild(card);

        if (chips.length) {
            const row = document.createElement('div');
            row.className = 'suggestion-row prompt-card-chips';
            chips.forEach(({ text, className = '' }) => {
                const chip = document.createElement('span');
                chip.className = `chip ${className}`.trim();
                chip.textContent = text;
                row.appendChild(chip);
            });
            bubbleWrap.appendChild(row);
        }

        wrap.appendChild(bubbleWrap);
        app.renderMath?.(card);
        return wrap;
    }

    function createAssistantCardRow(rowClass = '') {
        const wrap = document.createElement('section');
        wrap.className = `msg-wrapper msg-row agent assistant-card-row ${rowClass}`.trim();
        wrap.innerHTML = `
            <div class="avatar agent ai" aria-hidden="true">伴</div>
            <div class="bubble-wrap bubble-wrap--card"></div>
        `;
        return {
            wrap,
            body: wrap.querySelector('.bubble-wrap'),
        };
    }

    const messageTimeFormatter = new Intl.DateTimeFormat('zh-CN', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: false,
    });

    function formatMessageTime(timestamp) {
        if (!timestamp) return messageTimeFormatter.format(new Date());
        const parsed = new Date(timestamp);
        if (Number.isNaN(parsed.getTime())) return messageTimeFormatter.format(new Date());
        return messageTimeFormatter.format(parsed);
    }

    function seedChatInput(nextValue, { submit = false } = {}) {
        const input = document.getElementById('chat-input');
        if (!input) return;
        input.value = nextValue;
        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.focus();
        if (submit) app.handlePrimaryAction?.();
    }

    function buildUserMessageTools(text, timestamp) {
        const row = document.createElement('div');
        row.className = 'message-tools message-tools--user';
        row.innerHTML = `
            <span class="message-time">${formatMessageTime(timestamp)}</span>
            <button type="button" class="message-tool-btn" aria-label="重新发送这条消息" title="重新发送">
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                    <path d="M11.7 7A4.7 4.7 0 1 1 10.32 3.68L8.9 3.82M10.48 1.95L10.32 3.68L8.59 3.52" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </button>
            <button type="button" class="message-tool-btn" aria-label="编辑这条消息" title="编辑">
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                    <path d="M9.85 2.1L11.9 4.15M2.25 11.75L4.9 11.15L11.25 4.8C11.58 4.47 11.58 3.93 11.25 3.6L10.4 2.75C10.07 2.42 9.53 2.42 9.2 2.75L2.85 9.1L2.25 11.75Z" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </button>
            <button type="button" class="message-tool-btn" aria-label="复制这条消息" title="复制">
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                    <rect x="4.2" y="3.2" width="6.3" height="7.1" rx="1.3" stroke="currentColor" stroke-width="1.1"/>
                    <path d="M3.4 9.1H2.9C2.18 9.1 1.6 8.52 1.6 7.8V2.9C1.6 2.18 2.18 1.6 2.9 1.6H7.8C8.52 1.6 9.1 2.18 9.1 2.9V3.4" stroke="currentColor" stroke-width="1.1" stroke-linecap="round"/>
                </svg>
            </button>
        `;
        const [retryBtn, editBtn, copyBtn] = row.querySelectorAll('.message-tool-btn');
        retryBtn.addEventListener('click', () => {
            if (state.isStreaming) {
                app.setStatusBanner?.('当前这一轮还在生成，先等它结束。', 'warning');
                return;
            }
            seedChatInput(text, { submit: true });
        });
        editBtn.addEventListener('click', () => {
            seedChatInput(text, { submit: false });
        });
        copyBtn.addEventListener('click', async () => {
            try {
                await navigator.clipboard.writeText(text);
                app.setStatusBanner?.('已复制到剪贴板', 'success');
            } catch (_error) {
                app.setStatusBanner?.('复制失败，请稍后重试', 'warning');
            }
        });
        return row;
    }

    function extractAssistantTurnText(turnEl) {
        const bubbleWrap = turnEl?.querySelector('.bubble-wrap');
        if (!bubbleWrap) return '';
        const clone = bubbleWrap.cloneNode(true);
        clone.querySelectorAll('.assistant-actions, .turn-heartbeat').forEach(node => node.remove());
        return String(clone.innerText || '').replace(/\n{3,}/g, '\n\n').trim();
    }

    function findPreviousUserMessageText(turnEl) {
        let node = turnEl?.previousElementSibling || null;
        while (node) {
            const userBubble = node.querySelector('.bubble.user');
            if (userBubble) return String(userBubble.innerText || '').trim();
            node = node.previousElementSibling;
        }
        return '';
    }

    const ASSISTANT_ACTION_ICONS = {
        copy: `
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                <rect x="5" y="4.5" width="7" height="8.5" rx="1.5" stroke="currentColor" stroke-width="1.2"/>
                <path d="M4.2 10.7H3.8C3.03 10.7 2.4 10.07 2.4 9.3V3.8C2.4 3.03 3.03 2.4 3.8 2.4H9.3C10.07 2.4 10.7 3.03 10.7 3.8V4.2" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
            </svg>
        `,
        copied: `
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                <path d="M3.6 8.3L6.4 11.1L12.2 5.3" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        `,
        up: `
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                <path d="M6.7 6.1L8.05 2.9C8.26 2.39 8.75 2.06 9.31 2.06C9.87 2.06 10.32 2.51 10.32 3.07V5.16H12.25C13.13 5.16 13.76 6 13.49 6.84L12.48 10.05C12.28 10.69 11.68 11.13 11.01 11.13H6.7M6.7 6.1V11.13M6.7 6.1H4.59C4.2 6.1 3.89 6.42 3.89 6.8V10.43C3.89 10.82 4.2 11.13 4.59 11.13H6.7" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        `,
        upFilled: `
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                <path d="M6.3 6.1L7.8 2.72C8 2.25 8.47 1.94 9 1.94C9.76 1.94 10.37 2.55 10.37 3.31V5.1H12.2C12.86 5.1 13.34 5.73 13.14 6.36L12.12 9.78C11.94 10.39 11.38 10.81 10.75 10.81H6.3V6.1Z" fill="currentColor"/>
                <path d="M3.55 6.28H5.55V10.81H3.55C3.24 10.81 2.99 10.56 2.99 10.25V6.84C2.99 6.53 3.24 6.28 3.55 6.28Z" fill="currentColor"/>
            </svg>
        `,
        down: `
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                <path d="M9.3 9.9L7.95 13.1C7.74 13.61 7.25 13.94 6.69 13.94C6.13 13.94 5.68 13.49 5.68 12.93V10.84H3.75C2.87 10.84 2.24 10 2.51 9.16L3.52 5.95C3.72 5.31 4.32 4.87 4.99 4.87H9.3M9.3 9.9V4.87M9.3 9.9H11.41C11.8 9.9 12.11 9.58 12.11 9.2V5.57C12.11 5.18 11.8 4.87 11.41 4.87H9.3" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        `,
        downFilled: `
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                <path d="M9.7 9.9L8.2 13.28C8 13.75 7.53 14.06 7 14.06C6.24 14.06 5.63 13.45 5.63 12.69V10.9H3.8C3.14 10.9 2.66 10.27 2.86 9.64L3.88 6.22C4.06 5.61 4.62 5.19 5.25 5.19H9.7V9.9Z" fill="currentColor"/>
                <path d="M12.45 9.72H10.45V5.19H12.45C12.76 5.19 13.01 5.44 13.01 5.75V9.16C13.01 9.47 12.76 9.72 12.45 9.72Z" fill="currentColor"/>
            </svg>
        `,
        refresh: `
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                <path d="M12.92 8A4.92 4.92 0 1 1 11.48 4.52L10 4.68M11.64 2.68L11.48 4.52L9.64 4.36" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        `,
    };

    function setAssistantActionIcon(button, iconName) {
        if (!button) return;
        button.innerHTML = ASSISTANT_ACTION_ICONS[iconName] || '';
    }

    app.setAssistantActionBarState = function setAssistantActionBarState(turnEl, isStreaming) {
        if (!turnEl) return;
        const actionBar = turnEl.querySelector('.assistant-actions');
        if (!actionBar) return;
        const nextStreaming = Boolean(isStreaming);
        const hasText = Boolean(extractAssistantTurnText(turnEl));
        turnEl.classList.toggle('msg-row--streaming', nextStreaming);
        actionBar.hidden = nextStreaming || !hasText;
        actionBar.setAttribute('aria-hidden', actionBar.hidden ? 'true' : 'false');
    };

    function buildAssistantMessageTools(turnEl) {
        const row = document.createElement('div');
        row.className = 'assistant-actions';
        row.setAttribute('aria-label', '回答操作');
        row.innerHTML = `
            <button type="button" class="assistant-action-btn" data-action="copy" aria-label="复制这条回答" title="复制"></button>
            <button type="button" class="assistant-action-btn" data-feedback="up" aria-label="标记这条回答有帮助" aria-pressed="false" title="有帮助">
            </button>
            <button type="button" class="assistant-action-btn" data-feedback="down" aria-label="标记这条回答还不够好" aria-pressed="false" title="还不够好">
            </button>
            <button type="button" class="assistant-action-btn" data-action="refresh" aria-label="基于上一条消息重新生成" title="重新生成">
            </button>
        `;

        const copyButton = row.querySelector('[data-action="copy"]');
        const feedbackButtons = row.querySelectorAll('[data-feedback]');
        const upButton = row.querySelector('[data-feedback="up"]');
        const downButton = row.querySelector('[data-feedback="down"]');
        const refreshButton = row.querySelector('[data-action="refresh"]');
        let copyResetTimer = null;
        let feedbackState = null;

        const updateCopyState = copied => {
            copyButton?.classList.toggle('is-confirmed', copied);
            copyButton?.setAttribute('aria-label', copied ? '已复制这条回答' : '复制这条回答');
            copyButton?.setAttribute('title', copied ? '已复制' : '复制');
            setAssistantActionIcon(copyButton, copied ? 'copied' : 'copy');
        };

        const updateFeedbackState = nextFeedback => {
            feedbackState = feedbackState === nextFeedback ? null : nextFeedback;
            upButton?.classList.toggle('is-active', feedbackState === 'up');
            downButton?.classList.toggle('is-active', feedbackState === 'down');
            upButton?.setAttribute('aria-pressed', feedbackState === 'up' ? 'true' : 'false');
            downButton?.setAttribute('aria-pressed', feedbackState === 'down' ? 'true' : 'false');
            setAssistantActionIcon(upButton, feedbackState === 'up' ? 'upFilled' : 'up');
            setAssistantActionIcon(downButton, feedbackState === 'down' ? 'downFilled' : 'down');
        };

        updateCopyState(false);
        updateFeedbackState(null);
        setAssistantActionIcon(refreshButton, 'refresh');

        feedbackButtons.forEach(button => {
            button.addEventListener('click', () => {
                const feedback = button.dataset.feedback || '';
                const willClear = feedbackState === feedback;
                updateFeedbackState(feedback);
                app.setStatusBanner(
                    willClear ? '已取消反馈' : (feedback === 'up' ? '已记录正向反馈' : '已记录负向反馈'),
                    'success'
                );
            });
        });

        copyButton?.addEventListener('click', async () => {
            const text = extractAssistantTurnText(turnEl);
            if (!text) {
                app.setStatusBanner('这条回答还没有可复制内容', 'warning');
                return;
            }
            try {
                await navigator.clipboard.writeText(text);
                window.clearTimeout(copyResetTimer);
                updateCopyState(true);
                copyResetTimer = window.setTimeout(() => updateCopyState(false), 1500);
                app.setStatusBanner('已复制回答内容', 'success');
            } catch (_error) {
                updateCopyState(false);
                app.setStatusBanner('复制失败，请稍后重试', 'warning');
            }
        });

        refreshButton?.addEventListener('click', () => {
            if (state.isStreaming) {
                app.setStatusBanner('当前还在生成中，请稍等这一轮结束', 'warning');
                return;
            }
            const previousUserText = findPreviousUserMessageText(turnEl);
            if (!previousUserText) {
                app.setStatusBanner('没有找到上一条用户消息，暂时无法重新生成', 'warning');
                return;
            }
            seedChatInput(previousUserText, { submit: true });
        });

        return row;
    }

    app.appendMessage = function appendMessage(role, text, options = {}) {
        app.clearTypingIndicator();

        if (role === 'agent') {
            if (options.kind === 'assessment_result') {
                const compact = buildCompactPromptCardContent(String(text || ''), '起点已对齐');
                const container = document.getElementById('messages');
                container.appendChild(createPromptCardRow({
                    label: '评估结果',
                    title: compact.title,
                    html: compact.html,
                    chips: compact.chips,
                    rowClass: 'assessment-result-row',
                    tone: 'success',
                }));
                app.finalizeAgentTurn();
                app.scrollMessagesToBottom();
                return;
            }
            if (options.kind === 'evaluator_card') {
                const compact = buildCompactPromptCardContent(String(text || ''), '这一轮的结论');
                const container = document.getElementById('messages');
                container.appendChild(createPromptCardRow({
                    label: '评估反馈',
                    title: compact.title,
                    html: compact.html,
                    chips: compact.chips,
                    rowClass: 'evaluator-card-row',
                    tone: 'info',
                }));
                app.finalizeAgentTurn();
                app.scrollMessagesToBottom();
                return;
            }
            const turnRole = options.turnRole || app.roleFromMessageKind(options.kind);
            app.appendAgentTurnShell(text, turnRole, {
                allowLearningHtml: options.allowLearningHtml === true || options.kind === 'graph_rag_answer' || options.kind === 'homework_answer_prompt',
                allowGraphRagHtml: options.allowGraphRagHtml === true || options.kind === 'graph_rag_debug_report',
            });
            app.finalizeAgentTurn();
            return;
        }

        const wrap = document.createElement('div');
        wrap.className = `msg-wrapper msg-row ${role}`;

        if (role !== 'user') {
            const avatar = document.createElement('div');
            avatar.className = `avatar ${role} ${role === 'user' ? 'user' : 'ai'}`;
            avatar.setAttribute('aria-hidden', 'true');
            avatar.textContent = role === 'user' ? '我' : '伴';
            wrap.appendChild(avatar);
        }

        const bubbleWrap = document.createElement('div');
        bubbleWrap.className = 'bubble-wrap';
        const bubble = document.createElement('div');
        bubble.className = role === 'user' ? 'bubble user' : 'bubble ai';
        bubble.innerHTML = sanitizeRenderedHtml(parseMarkdown(text));
        bubbleWrap.appendChild(bubble);

        if (role === 'user') {
            bubbleWrap.appendChild(buildUserMessageTools(text, options.timestamp));
        }

        wrap.appendChild(bubbleWrap);
        const container = document.getElementById('messages');
        container.appendChild(wrap);
        app.scrollMessagesToBottom();
    };

    app.appendSystemMessage = function appendSystemMessage(text, tone = 'info') {
        if (!text) return;
        app.clearTypingIndicator();
        const wrap = document.createElement('div');
        wrap.className = 'msg-wrapper msg-row system';
        wrap.dataset.tone = tone;
        wrap.innerHTML = `
            <div class="avatar system ai" aria-hidden="true">伴</div>
            <div class="bubble-wrap">
                <div class="msg-content system prompt-card">
                    <div class="system-kicker prompt-label">提示</div>
                    <div class="system-body">${sanitizeRenderedHtml(parseMarkdown(text))}</div>
                </div>
            </div>
        `;
        const container = document.getElementById('messages');
        container.appendChild(wrap);
        app.scrollMessagesToBottom();
    };

    app.showTyping = function showTyping() {
        app.clearTypingIndicator();
        
        const dotsHtml = `<div class="typing-dots" aria-label="我在整理思路..."><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>`;
        
        // If an agent turn is already active, put the typing indicator inside its body
        if (state.currentAgentBodyEl) {
            const tempDiv = document.createElement('div');
            tempDiv.id = 'typing-indicator';
            tempDiv.innerHTML = dotsHtml;
            // Append it right after the current text
            state.currentAgentBodyEl.appendChild(tempDiv);
        } else {
            // Create a standalone bubble
            const wrap = document.createElement('div');
            wrap.className = 'msg-wrapper msg-row agent';
            wrap.id = 'typing-indicator';
            wrap.innerHTML = `
                <div class="avatar agent ai" aria-hidden="true">伴</div>
                <div class="bubble-wrap">
                    <div class="bubble ai">${dotsHtml}</div>
                </div>
            `;
            const messages = document.getElementById('messages');
            if (messages) messages.appendChild(wrap);
        }
        app.scrollMessagesToBottom();
    };

    app.showRadar = function showRadar(data) {
        if (!data || !Array.isArray(data.dimensions) || !data.dimensions.length) return;
        state.latestRadarData = data;
        const ctx = document.getElementById('radarChart').getContext('2d');
        if (state.radarChartInstance) state.radarChartInstance.destroy();
        state.radarChartInstance = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: data.dimensions,
                datasets: [
                    {
                        label: '自评',
                        data: data.self_scores,
                        borderColor: '#7b71df',
                        backgroundColor: 'rgba(123,113,223,0.16)',
                        pointBackgroundColor: '#7b71df',
                    },
                    {
                        label: '表现',
                        data: data.objective_scores,
                        borderColor: '#9a98ad',
                        backgroundColor: 'rgba(154,152,173,0.12)',
                        pointBackgroundColor: '#9a98ad',
                    },
                ],
            },
            options: {
                maintainAspectRatio: false,
                scales: {
                    r: {
                        min: 0,
                        max: 100,
                        ticks: { display: false },
                        grid: { color: 'rgba(123, 113, 223, 0.14)' },
                        angleLines: { color: 'rgba(123, 113, 223, 0.14)' },
                        pointLabels: { color: '#6e6996', font: { size: 10 } },
                    },
                },
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { color: '#5f5a7a', boxWidth: 12, font: { size: 11 } },
                    },
                },
            },
        });
        const breakdown = document.getElementById('radar-breakdown');
        if (!breakdown) return;
        const rows = Array.isArray(data.breakdown) ? data.breakdown : [];
        breakdown.innerHTML = rows.length
            ? rows
                .map(item => {
                    const gap = Number(item.gap || 0);
                    const tone = gap >= 20 ? ' is-risk' : gap <= -20 ? ' is-overconfident' : '';
                    return `
                        <article class="radar-breakdown-item${tone}">
                            <div class="radar-breakdown-head">
                                <strong>${item.dimension}</strong>
                                <span>${gap > 0 ? '+' : ''}${gap}</span>
                            </div>
                            <div class="radar-breakdown-meta">
                                <span>自评 ${item.self_score}</span>
                                <span>客观 ${item.objective_score}</span>
                            </div>
                        </article>
                    `;
                })
                .join('')
            : '<p class="muted">还没有画像数据。</p>';
    };

    function _assessmentQuestionKey(question = {}, index = 0) {
        const rawKey = question.id ?? question.question_id ?? question.key ?? question.concept_id ?? (index + 1);
        return String(rawKey ?? (index + 1));
    }

    function _assessmentBackendQuestionKey(question = {}, index = 0) {
        return String(question.id ?? (index + 1));
    }

    function _assessmentCandidateKeys(question = {}, index = 0) {
        return [
            _assessmentQuestionKey(question, index),
            _assessmentBackendQuestionKey(question, index),
            question.id,
            question.question_id,
            question.key,
            question.concept_id,
            index + 1,
            String(index + 1),
        ]
            .filter(value => value !== undefined && value !== null && String(value).trim() !== '')
            .map(value => String(value));
    }

    function _assessmentAnswerFor(question = {}, answers = {}, index = 0) {
        const keys = _assessmentCandidateKeys(question, index);
        for (const key of keys) {
            const answer = answers[key];
            if (answer !== undefined && answer !== null && String(answer).trim() !== '') {
                return String(answer).trim().toUpperCase();
            }
        }
        return '';
    }

    function _normalizeAssessmentAnswers(questions = [], answers = {}) {
        const normalized = {};
        questions.forEach((question, index) => {
            const answer = _assessmentAnswerFor(question, answers, index);
            if (!answer) return;
            const uiKey = _assessmentQuestionKey(question, index);
            const backendKey = _assessmentBackendQuestionKey(question, index);
            normalized[uiKey] = answer;
            normalized[backendKey] = answer;
        });
        return normalized;
    }

    function _answeredAssessmentCount(questions = [], answers = {}) {
        return questions.filter((q, index) => Boolean(_assessmentAnswerFor(q, answers, index))).length;
    }

    function _assessmentProgressMetaHtml(questions = [], answers = {}) {
        const answeredCount = _answeredAssessmentCount(questions, answers);
        return `
            <span>已作答 ${answeredCount} / ${questions.length}</span>
            <span>提交后答案会固定展示，恢复历史时保持同样状态。</span>
        `;
    }

    function _refreshAssessmentProgressMeta() {
        const meta = document.querySelector('.assessment-progress-meta');
        if (!meta) return;
        meta.innerHTML = _assessmentProgressMetaHtml(state.assessmentQuestions, state.answers);
    }

    function _allAssessmentAnswered(questions = [], answers = {}) {
        return Array.isArray(questions)
            && questions.length > 0
            && questions.every((q, index) => Boolean(_assessmentAnswerFor(q, answers, index)));
    }

    function _assessmentOptionLabel(question = {}, answer = '') {
        const normalized = String(answer || '').trim().toUpperCase();
        const matched = (question.options || []).find(opt => (opt || '').trim().charAt(0).toUpperCase() === normalized);
        if (!matched) return normalized || '未作答';
        return matched.replace(/^[A-D]\.\s*/, '').trim() || matched;
    }

    function _renderLockedAssessmentSummary(target, questions = [], answers = {}, statusText = '已提交，答案已固定') {
        const rows = questions.map((q, index) => {
            const answer = _assessmentAnswerFor(q, answers, index);
            const concept = q.concept || q.concept_title || '';
            return `
                <article class="assessment-locked-row">
                    <div class="assessment-locked-index">${index + 1}</div>
                    <div class="assessment-locked-main">
                        <div class="q-header">
                            <span class="q-tag q-tag--subj">自评题</span>
                            ${concept ? `<span class="q-tag q-tag--concept">${concept}</span>` : ''}
                            <span class="q-status-chip q-status-chip--locked">已固定</span>
                        </div>
                        <div class="q-text">${q.question || ''}</div>
                        <div class="assessment-locked-answer">
                            <span class="q-opt-letter">${answer || '-'}</span>
                            <span class="q-opt-label">${_assessmentOptionLabel(q, answer)}</span>
                        </div>
                    </div>
                </article>
            `;
        }).join('');

        target.classList.add('assessment-locked-summary');
        target.innerHTML = `
            <div class="prompt-card prompt-flow-shell">
                <div class="prompt-label">快速摸底</div>
                <div class="prompt-title">${statusText}</div>
                <div class="prompt-copy">这份测评记录将作为学习画像和初始图谱节点选择的依据，不能在当前流程中继续修改。</div>
            </div>
            <div class="assessment-progress-meta">${_assessmentProgressMetaHtml(questions, answers)}</div>
            <div class="assessment-locked-list">${rows}</div>
        `;
        app.renderMath?.(target);
    }

    app.renderAssessmentForm = function renderAssessmentForm(questions, initialAnswers = {}, options = {}) {
        state.assessmentQuestions = questions;
        state.answers = _normalizeAssessmentAnswers(questions, initialAnswers || {});
        document.querySelector('.assessment-container')?.remove();

        const container = document.getElementById('messages');
        const row = createAssistantCardRow('assessment-container');
        const div = document.createElement('div');
        div.className = 'assessment-container prompt-flow-card';

        const total = Array.isArray(questions) ? questions.length : 0;
        if (!total) {
            div.innerHTML = `
                <div class="prompt-card prompt-flow-shell">
                    <div class="prompt-label">快速摸底</div>
                    <div class="prompt-title">暂时没有拿到测评题</div>
                    <div class="prompt-copy">可以先跳过摸底，直接开始正式讲解。</div>
                </div>
                <div class="q-stepper-nav">
                    <button type="button" class="q-stepper-btn q-stepper-skip">先不测，直接开始</button>
                </div>
            `;
            div.querySelector('.q-stepper-skip').onclick = async () => {
                _renderLockedAssessmentSummary(div, questions, state.answers, '已跳过学前测评，答案已固定');
                app.setStatusBanner('已跳过摸底，正在进入正式讲解', 'processing');
                try {
                    await app.submitTopicConfirmation?.(true, 'direct_tutor');
                } catch (err) {
                    console.error(err);
                    app.setStatusBanner('跳过摸底失败，请稍后重试。', 'danger');
                }
            };
            row.body.appendChild(div);
            container.appendChild(row.wrap);
            app.scrollMessagesToBottom();
            return;
        }
        if (options.locked === true && options.allowEdit !== true) {
            _renderLockedAssessmentSummary(div, questions, state.answers, options.statusText || '测评已完成，答案已固定');
            row.body.appendChild(div);
            container.appendChild(row.wrap);
            app.scrollMessagesToBottom();
            return;
        }
        let currentIdx = 0;

        // ── 步进器骨架 ──
        div.innerHTML = `
            <div class="q-stepper-progress">
                <span class="q-stepper-label">第 <span data-cur>1</span> 题 / 共 ${total} 题</span>
                <div class="q-progress-bar"><div class="q-progress-fill" data-fill style="width:${(1 / total) * 100}%"></div></div>
            </div>
            <div class="q-stepper-body"></div>
            <div class="q-stepper-nav">
                <button type="button" class="q-stepper-btn q-stepper-prev" disabled>上一题</button>
                <button type="button" class="q-stepper-btn q-stepper-skip">先不测，直接开始</button>
                <button type="button" class="q-stepper-btn q-stepper-next" disabled>下一题</button>
                <button type="button" class="q-stepper-btn q-stepper-submit" style="display:none" disabled>确认提交</button>
            </div>
        `;

        const body = div.querySelector('.q-stepper-body');
        const prevBtn = div.querySelector('.q-stepper-prev');
        const nextBtn = div.querySelector('.q-stepper-next');
        const submitBtn = div.querySelector('.q-stepper-submit');
        const skipBtn = div.querySelector('.q-stepper-skip');
        const curLabel = div.querySelector('[data-cur]');
        const fillBar = div.querySelector('[data-fill]');
        let draftTimer = null;

        function scheduleDraftSave() {
            if (!state.currentThreadId) return;
            window.clearTimeout(draftTimer);
            draftTimer = window.setTimeout(() => {
                fetch('/api/assessment_draft', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        thread_id: state.currentThreadId,
                        answers: _normalizeAssessmentAnswers(questions, state.answers),
                    }),
                }).catch(err => console.warn('assessment draft save failed', err));
            }, 250);
        }

        function renderQuestion(idx) {
            currentIdx = idx;
            const q = questions[idx];
            const answerKey = _assessmentQuestionKey(q, idx);
            const backendAnswerKey = _assessmentBackendQuestionKey(q, idx);
            const savedAnswer = _assessmentAnswerFor(q, state.answers, idx);
            const concept = q.concept || q.concept_title || '';
            const phaseLabel = '自评题';

            body.innerHTML = `
                <div class="q-header">
                    <span class="q-tag q-tag--subj">${phaseLabel}</span>
                    ${concept ? `<span class="q-tag q-tag--concept">${concept}</span>` : ''}
                </div>
                <div class="q-text">${q.question}</div>
                <div class="q-options">${(q.options || []).map(opt => {
                    const key = (opt || '').trim().charAt(0).toUpperCase();
                    const label = opt.replace(/^[A-D]\.\s*/, '');
                    const isSelected = key === savedAnswer;
                    return `<div class="q-opt${isSelected ? ' selected' : ''}" data-v="${key}">
                        <span class="q-opt-letter">${key}</span>
                        <span class="q-opt-indicator"></span>
                        <span class="q-opt-label">${label}</span>
                    </div>`;
                }).join('')}</div>
            `;

            // Option click
            body.querySelectorAll('.q-opt').forEach(opt => {
                opt.addEventListener('click', () => {
                    body.querySelectorAll('.q-opt').forEach(o => o.classList.remove('selected'));
                    opt.classList.add('selected');
                    state.answers[answerKey] = opt.dataset.v;
                    state.answers[backendAnswerKey] = opt.dataset.v;
                    state.answers = _normalizeAssessmentAnswers(questions, state.answers);
                    updateNav();
                    _refreshAssessmentProgressMeta();
                    scheduleDraftSave();
                });
            });

            updateNav();
        }

        function updateNav() {
            const q = questions[currentIdx];
            const hasAnswer = Boolean(_assessmentAnswerFor(q, state.answers, currentIdx));
            const isFirst = currentIdx === 0;
            const isLast = currentIdx === total - 1;

            curLabel.textContent = currentIdx + 1;
            fillBar.style.width = `${((currentIdx + 1) / total) * 100}%`;

            prevBtn.disabled = isFirst;
            prevBtn.style.visibility = isFirst ? 'hidden' : 'visible';

            if (isLast) {
                nextBtn.style.display = 'none';
                submitBtn.style.display = '';
                const allAnswered = _allAssessmentAnswered(questions, state.answers);
                submitBtn.disabled = !allAnswered;
            } else {
                nextBtn.style.display = '';
                submitBtn.style.display = 'none';
                nextBtn.disabled = !hasAnswer;
            }
        }

        prevBtn.onclick = () => { if (currentIdx > 0) renderQuestion(currentIdx - 1); };
        nextBtn.onclick = () => { if (currentIdx < total - 1 && _assessmentAnswerFor(questions[currentIdx], state.answers, currentIdx)) renderQuestion(currentIdx + 1); };

        submitBtn.onclick = async () => {
            const allAnswered = _allAssessmentAnswered(questions, state.answers);
            if (!allAnswered) return;
            const normalizedAnswers = _normalizeAssessmentAnswers(questions, state.answers);
            state.answers = normalizedAnswers;
            submitBtn.disabled = true;
            submitBtn.textContent = '正在分析…';
            app.setStatusBanner('正在分析你的起点…', 'processing');
            try {
                const response = await fetch('/api/submit_assessment', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ thread_id: state.currentThreadId, answers: normalizedAnswers }),
                });
                if (!response.ok) throw new Error(`submit_assessment failed: ${response.status}`);
                _renderLockedAssessmentSummary(div, questions, normalizedAnswers);
                app.startStreamingTurn?.('正在生成学习画像');
                app.connectSSE();
            } catch (err) {
                console.error(err);
                submitBtn.disabled = false;
                submitBtn.textContent = '确认提交';
                app.setStatusBanner('测评提交失败，请稍后重试。', 'danger');
            }
        };

        skipBtn.onclick = async () => {
            _renderLockedAssessmentSummary(div, questions, state.answers, '已跳过学前测评，答案已固定');
            app.setStatusBanner('已跳过摸底，正在进入正式讲解', 'processing');
            try {
                await app.submitTopicConfirmation?.(true, 'direct_tutor');
            } catch (err) {
                console.error(err);
                app.setStatusBanner('跳过摸底失败，请稍后重试。', 'danger');
            }
        };

        app.updateLearningProgress({ step: 2, label: '学习进度 2/5' });
        renderQuestion(0);
        row.body.appendChild(div);
        container.appendChild(row.wrap);
        app.scrollMessagesToBottom();
    };

    // ================================================================
    // 对话式逐题测评 UI  — 三种题型 × 三种状态
    // ================================================================
    //
    // 题型：self_eval（自评 1-5 点选）、objective（客观四选一）、subjective_choice（主观四选一）
    // 状态：unanswered → selected → locked（含对错反馈）
    //
    // 后端 payload:
    //   assessment.question → { pair_index, total_pairs, phase, concept, question_id, question, options }
    //   assessment.feedback → { pair_index, concept, is_correct, correct_answer, chosen, gap }

    const SELF_EVAL_LABELS = ['', '完全没把握', '有点模糊', '有点把握', '比较确定', '非常确定'];

    function _parseOptionKey(optText) {
        return (optText || '').trim().charAt(0).toUpperCase();
    }

    function _stripObjectiveOptionLabel(optText, key = '') {
        const text = String(optText || '').trim();
        const normalizedKey = String(key || '').trim().toUpperCase();
        if (normalizedKey && text.toUpperCase().startsWith(normalizedKey)) {
            return text.slice(normalizedKey.length).replace(/^[\s.．、:：-]+/, '').trim() || text;
        }
        return text.replace(/^[A-Da-d][\s.．、:：-]+/, '').trim() || text;
    }

    /**
     * 渲染"对话式测评"的单题卡片。
     * @param {object} data - 后端 payload
     * @param {object} [restore] - 历史恢复时传入 { answer, is_correct, correct_answer }
     */
    app.renderAssessmentDialogQuestion = function renderAssessmentDialogQuestion(data, restore) {
        // 不移除旧卡，保留已锁定的历史题目
        const container = document.getElementById('messages');
        const row = createAssistantCardRow('assessment-dialog-row');
        const card = document.createElement('section');
        card.className = 'q-card';
        card.dataset.questionId = data.question_id;

        const pairIdx = data.pair_index ?? 0;
        const total = data.total_pairs ?? 10;
        const phase = data.phase || 'self_eval';
        const concept = data.concept || '';
        const qId = data.question_id;
        const qText = data.question || '';
        const options = data.options || [];
        const isRestored = restore != null;

        // ── 进度条（卡片内部顶端 3px 细条 + 文字）──
        const progressPct = ((pairIdx + 1) / total) * 100;
        const progressHtml = `
            <div class="q-progress">
                <span class="q-progress-label">第 ${pairIdx + 1} 题 / 共 ${total} 题</span>
                <div class="q-progress-bar"><div class="q-progress-fill" style="width:${progressPct}%"></div></div>
            </div>`;

        // ── 标题行 ──
        const phaseLabel = phase === 'self_eval' ? '自评' : phase === 'subjective_choice' ? '摩底题' : '客观题';
        const phaseCls = phase === 'self_eval' ? 'q-tag--self' : phase === 'subjective_choice' ? 'q-tag--subj' : 'q-tag--obj';
        const headerHtml = `
            <div class="q-header">
                <span class="q-tag ${phaseCls}">${phaseLabel}</span>
                <span class="q-tag q-tag--concept">${concept}</span>
            </div>`;

        // ── 题面 ──
        const questionHtml = `<div class="q-text">${qText}</div>`;

        if (phase === 'subjective_choice') {
            // ── 主观选择题：四选一，选完即锁定，不等 feedback ──
            const chosenKey = isRestored ? (restore.chosen || '').toUpperCase() : '';

            const optsHtml = options.map(opt => {
                const key = _parseOptionKey(opt);
                let cls = 'q-opt';
                if (isRestored) {
                    cls += ' locked';
                    if (key === chosenKey) cls += ' correct-chosen';
                    else cls += ' dimmed';
                }
                const label = opt.replace(/^[A-D]\.\s*/, '');
                return `<div class="${cls}" data-v="${key}">
                    <span class="q-opt-letter">${key}</span>
                    <span class="q-opt-indicator"></span>
                    <span class="q-opt-label">${label}</span>
                </div>`;
            }).join('');

            card.innerHTML = `
                ${isRestored ? '<div class="q-restored-banner">历史记录，不可修改</div>' : ''}
                ${progressHtml}
                ${headerHtml}
                ${questionHtml}
                <div class="q-options">${optsHtml}</div>
                ${!isRestored ? '<button class="q-submit" disabled>确认</button>' : ''}
            `;

            if (!isRestored) {
                let sel = null;
                const opts = card.querySelectorAll('.q-opt');
                const submitBtn = card.querySelector('.q-submit');

                opts.forEach(opt => {
                    opt.addEventListener('click', () => {
                        if (opt.classList.contains('locked')) return;
                        opts.forEach(o => o.classList.remove('selected'));
                        opt.classList.add('selected');
                        sel = opt.dataset.v;
                        submitBtn.disabled = false;
                    });
                });

                submitBtn.addEventListener('click', () => {
                    if (!sel) return;
                    submitBtn.disabled = true;
                    submitBtn.textContent = '已记录';
                    opts.forEach(o => {
                        o.classList.add('locked');
                        if (o.dataset.v === sel) o.classList.add('correct-chosen');
                        else o.classList.add('dimmed');
                        o.style.pointerEvents = 'none';
                    });
                    _submitDialogAnswer(qId, sel, card);
                });
            }
        } else if (phase === 'self_eval') {
            // ── 自评题：1-5 圆点 ──
            const savedVal = isRestored ? parseInt(restore.answer) || 0 : 0;
            const dotsHtml = [1, 2, 3, 4, 5].map(v => {
                const active = savedVal === v ? ' active' : '';
                const locked = isRestored ? ' locked' : '';
                return `<div class="self-dot${active}${locked}" data-v="${v}">${v}</div>`;
            }).join('');

            const descText = isRestored && savedVal
                ? `你选了：${SELF_EVAL_LABELS[savedVal]}`
                : '点击选择把握程度';

            card.innerHTML = `
                ${isRestored ? '<div class="q-restored-banner">历史记录，不可修改</div>' : ''}
                ${progressHtml}
                ${headerHtml}
                ${questionHtml}
                <div class="self-slider-wrap">
                    <div class="self-label-row"><span>完全不确定</span><span>非常确定</span></div>
                    <div class="self-dots">${dotsHtml}</div>
                    <div class="self-desc">${descText}</div>
                </div>
                ${!isRestored ? '<button class="q-submit" disabled>确认</button>' : ''}
            `;

            if (!isRestored) {
                let val = 0;
                const dots = card.querySelectorAll('.self-dot');
                const desc = card.querySelector('.self-desc');
                const submitBtn = card.querySelector('.q-submit');

                dots.forEach(dot => {
                    dot.addEventListener('click', () => {
                        val = parseInt(dot.dataset.v);
                        dots.forEach(d => d.classList.toggle('active', parseInt(d.dataset.v) === val));
                        desc.textContent = SELF_EVAL_LABELS[val];
                        submitBtn.disabled = false;
                    });
                });

                submitBtn.addEventListener('click', () => {
                    dots.forEach(d => d.classList.add('locked'));
                    submitBtn.remove();
                    desc.textContent = '你选了：' + SELF_EVAL_LABELS[val];
                    _submitDialogAnswer(qId, String.fromCharCode(64 + val), card);
                });
            }
        } else {
            // ── 客观题：标准选项 ──
            const chosenKey = isRestored ? (restore.chosen || '').toUpperCase() : '';
            const correctKey = isRestored ? (restore.correct_answer || '').toUpperCase() : '';

            const optsHtml = options.map(opt => {
                const key = _parseOptionKey(opt);
                let cls = 'q-opt';
                let indicator = '';
                if (isRestored) {
                    cls += ' locked';
                    cls += ' ' + _lockedClass(key, chosenKey, correctKey);
                    indicator = _indicatorHtml(key, chosenKey, correctKey);
                }
                const label = opt.replace(/^[A-D]\.\s*/, '');
                return `<div class="${cls}" data-v="${key}">
                    <span class="q-opt-letter">${key}</span>
                    <span class="q-opt-indicator">${indicator}</span>
                    <span class="q-opt-label">${label}</span>
                </div>`;
            }).join('');

            card.innerHTML = `
                ${isRestored ? '<div class="q-restored-banner">历史记录，不可修改</div>' : ''}
                ${progressHtml}
                ${headerHtml}
                ${questionHtml}
                <div class="q-options">${optsHtml}</div>
                ${!isRestored ? '<button class="q-submit" disabled>提交答案</button>' : ''}
            `;

            if (!isRestored) {
                let sel = null;
                const opts = card.querySelectorAll('.q-opt');
                const submitBtn = card.querySelector('.q-submit');

                opts.forEach(opt => {
                    opt.addEventListener('click', () => {
                        if (opt.classList.contains('locked')) return;
                        opts.forEach(o => o.classList.remove('selected'));
                        opt.classList.add('selected');
                        sel = opt.dataset.v;
                        submitBtn.disabled = false;
                    });
                });

                submitBtn.addEventListener('click', () => {
                    if (!sel) return;
                    submitBtn.disabled = true;
                    submitBtn.textContent = '已提交';
                    // 暂时只锁定选中态，等 feedback 来后才加颜色
                    opts.forEach(o => {
                        o.classList.add('pending-lock');
                        o.style.pointerEvents = 'none';
                    });
                    _submitDialogAnswer(qId, sel, card);
                });
            }
        }

        row.body.appendChild(card);
        container.appendChild(row.wrap);
        app.scrollMessagesToBottom();
    };

    // 锁定状态类名
    function _lockedClass(key, chosen, correct) {
        if (!chosen) return '';
        if (key === correct && key === chosen) return 'correct-chosen';
        if (key === correct && key !== chosen) return 'correct-unchosen';
        if (key === chosen && key !== correct) return 'wrong-chosen';
        return 'dimmed';
    }

    // 锁定后图标
    function _indicatorHtml(key, chosen, correct) {
        const check = '<svg viewBox="0 0 10 10" fill="none"><path d="M2 5l2.5 2.5L8 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>';
        const cross = '<svg viewBox="0 0 10 10" fill="none"><path d="M3 3l4 4M7 3l-4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>';
        if (!chosen) return '';
        if (key === correct && key === chosen) return check;
        if (key === correct) return check;
        if (key === chosen) return cross;
        return '';
    }

    // 动态锁定选项（feedback 到达时调用）
    function _lockCardOptions(card, chosen, correct) {
        card.querySelectorAll('.q-opt').forEach(opt => {
            const k = opt.dataset.v;
            opt.classList.remove('selected', 'pending-lock');
            opt.classList.add('locked', _lockedClass(k, chosen, correct));
            opt.querySelector('.q-opt-indicator').innerHTML = _indicatorHtml(k, chosen, correct);
            opt.style.pointerEvents = 'none';
        });
        // 移除提交按钮
        card.querySelector('.q-submit')?.remove();
    }

    /**
     * 渲染对话式测评反馈卡片。
     * data: { pair_index, concept, is_correct, correct_answer, chosen, gap }
     */
    app.renderAssessmentFeedback = function renderAssessmentFeedback(message, data) {
        const container = document.getElementById('messages');
        const isCorrect = data.is_correct;
        const chosen = (data.chosen || '').toUpperCase();
        const correct = (data.correct_answer || '').toUpperCase();

        // 找到对应的题卡并锁定选项
        const cards = container.querySelectorAll('.q-card');
        const latestCard = cards[cards.length - 1];
        if (latestCard && latestCard.querySelector('.q-opt')) {
            _lockCardOptions(latestCard, chosen, correct);
        }

        // 渲染反馈块（紧跟在选项下方）
        const fb = document.createElement('div');
        fb.className = `q-feedback ${isCorrect ? 'q-feedback--correct' : 'q-feedback--wrong'}`;

        const iconSvg = isCorrect
            ? '<svg class="q-fb-icon" viewBox="0 0 14 14" fill="none"><circle cx="7" cy="7" r="6" fill="#1D9E75"/><path d="M4 7l2 2 4-4" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>'
            : '<svg class="q-fb-icon" viewBox="0 0 14 14" fill="none"><circle cx="7" cy="7" r="6" fill="#E24B4A"/><path d="M4.5 4.5l5 5M9.5 4.5l-5 5" stroke="white" stroke-width="1.5" stroke-linecap="round"/></svg>';

        fb.innerHTML = `
            <div class="q-fb-row">
                ${iconSvg}
                <span class="q-fb-text">${message}</span>
            </div>
            ${!isCorrect ? `<div class="q-fb-correct">正确答案：${correct}</div>` : ''}
        `;

        // 插入到题卡底部
        if (latestCard) {
            latestCard.appendChild(fb);
        } else {
            container.appendChild(fb);
        }
        app.scrollMessagesToBottom();
    };

    function _submitDialogAnswer(questionId, answer, cardEl) {
        if (!state.currentThreadId) return;
        app.startStreamingTurn?.('已收到');
        fetch('/api/assessment_answer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                thread_id: state.currentThreadId,
                answer: answer,
            }),
        }).then(() => {
            app.connectSSE();
        }).catch(err => {
            app.setStatusBanner?.('答案提交失败，请重试。', 'error');
            console.error('Assessment answer submit error:', err);
        });
    }

    app.renderTopicConfirmation = function renderTopicConfirmation(topic, details = {}) {
        state.pendingTopicConfirmation = topic;
        state.pendingTopicConfirmationDetails = details || {};
        document.querySelector('.assistant-card-row.topic-confirm-card')?.remove();
        const container = document.getElementById('messages');
        const row = createAssistantCardRow('topic-confirm-card');
        const card = document.createElement('div');
        card.className = 'topic-confirm-card prompt-flow-card tc-card-v2';

        card.innerHTML = `
            <div class="tc-header">
                <span class="tc-icon">📖</span>
                <span class="tc-label">确认学习主题</span>
            </div>
            <div class="tc-body">
                <div class="tc-topic">${topic}</div>
                <div class="tc-desc">确认后先做一组快速摸底，了解你的起点再正式开始讲解。</div>
                <div class="tc-actions">
                    <button type="button" class="tc-btn tc-btn-primary" data-action="assess">
                        <span class="tc-btn-icon">✅</span> 确认，开始摸底
                    </button>
                    <button type="button" class="tc-btn tc-btn-secondary" data-action="skip">
                        <span class="tc-btn-icon">⚡</span> 跳过摸底直接学
                    </button>
                </div>
                <div class="tc-edit-trigger">
                    <a href="#" class="tc-edit-link">不是这个主题？点击修改</a>
                </div>
                <div class="tc-edit-box" id="topic-edit-box">
                    <div class="tc-edit-inner">
                        <input id="topic-edit-input" class="tc-edit-input" placeholder="输入你想学的主题" />
                        <button type="button" class="tc-btn tc-btn-change" data-action="change">换这个主题</button>
                    </div>
                </div>
            </div>
        `;

        card.querySelector('[data-action="assess"]').onclick = () => app.submitTopicConfirmation(true, 'assessment');
        card.querySelector('[data-action="skip"]').onclick = () => app.submitTopicConfirmation(true, 'direct_tutor');
        card.querySelector('.tc-edit-link').onclick = (e) => {
            e.preventDefault();
            const box = document.getElementById('topic-edit-box');
            if (box) {
                const isOpen = box.classList.toggle('tc-edit-open');
                if (isOpen) document.getElementById('topic-edit-input')?.focus();
            }
        };
        card.querySelector('[data-action="change"]').onclick = () => app.submitTopicConfirmation(false, 'assessment');

        row.body.appendChild(card);
        container.appendChild(row.wrap);
        app.updateLearningProgress({ step: 1, label: '学习进度 1/5' });
        app.scrollMessagesToBottom();
    };

    app.renderInterruptConfirmation = function renderInterruptConfirmation() {
        state.pendingInterruptConfirmation = true;
        document.querySelector('.interrupt-confirm-card')?.remove();
        const container = document.getElementById('messages');
        const row = createAssistantCardRow('topic-confirm-card interrupt-confirm-card');
        const card = document.createElement('div');
        card.className = 'topic-confirm-card interrupt-confirm-card prompt-flow-card';
        card.innerHTML = `
            <div class="prompt-card prompt-flow-shell">
                <div class="prompt-label">回主线</div>
                <div class="prompt-title">这个点先收住？</div>
                <div class="prompt-copy">先回当前主线，还是继续追问。</div>
            </div>
            <div class="suggestion-row prompt-flow-actions">
                <button type="button" class="chip chip-primary">回到主线</button>
                <button type="button" class="chip">继续追问</button>
            </div>
        `;
        const [confirmBtn, stayBtn] = card.querySelectorAll('button');
        confirmBtn.onclick = () => app.submitInterruptConfirmation(true);
        stayBtn.onclick = () => app.submitInterruptConfirmation(false);
        row.body.appendChild(card);
        container.appendChild(row.wrap);
        app.scrollMessagesToBottom();
    };

    app.lockChoiceCard = function lockChoiceCard(card, value = '', label = '') {
        if (!card) return;
        const normalized = String(value || '').trim();
        const visible = String(label || value || '').trim();
        card.classList.add('choice-card--locked');
        card.dataset.lockedChoice = normalized;
        card.querySelectorAll('button').forEach(button => {
            const isChosen = String(button.dataset.choiceValue || '').trim() === normalized
                || String(button.dataset.choiceLabel || '').trim() === visible;
            button.disabled = true;
            button.classList.add('choice-chip--locked');
            button.classList.toggle('choice-chip--chosen', isChosen);
            button.setAttribute('aria-disabled', 'true');
        });
        const actions = card.querySelector('.selector-chip-list, .suggestion-row');
        if (actions && !card.querySelector('.choice-locked-summary')) {
            const summary = document.createElement('div');
            summary.className = 'choice-locked-summary';
            summary.textContent = visible ? `已选择：${visible}` : '已选择，等待继续。';
            actions.insertAdjacentElement('afterend', summary);
        }
    };

    app.lockActiveChoiceCard = function lockActiveChoiceCard(value = '', label = '') {
        const activeCards = document.querySelectorAll([
            '.next-step-card',
            '.post-eval-card',
            '.post-lesson-card',
            '.continue-homework-card',
            '.homework-review-card',
            '.consolidation-card',
        ].join(','));
        activeCards.forEach(card => app.lockChoiceCard(card, value, label));
    };

    app.renderNextStepSelector = function renderNextStepSelector(options = [], renderOptions = {}) {
        document.querySelector('.next-step-card')?.remove();
        document.querySelector('.post-eval-card')?.remove();
        const container = document.getElementById('messages');
        const row = createAssistantCardRow('topic-confirm-card next-step-card');
        const card = document.createElement('div');
        card.className = 'topic-confirm-card next-step-card prompt-flow-card';
        card.dataset.cardKind = 'next_step_selector';
        card.innerHTML = `
            <div class="prompt-card prompt-flow-shell">
                <div class="prompt-label">下一步</div>
                <div class="prompt-title">接下来怎么学</div>
                <div class="prompt-copy">选一个继续。</div>
            </div>
            <div class="suggestion-row topic-confirm-chip-list selector-chip-list next-step-actions"></div>
        `;
        const actions = card.querySelector('.next-step-actions');
        const normalized = Array.isArray(options) && options.length
            ? options
            : [
                { value: 'continue_deeper', label: '继续深入' },
                { value: 'example_first', label: '换个例子' },
                { value: 'practice_now', label: '来一道题' },
                { value: 'summarize_now', label: '先总结一下' },
            ];
        normalized.forEach(option => {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'chip topic-confirm-chip selector-chip';
            button.textContent = option.label;
            button.dataset.choiceValue = option.value;
            button.dataset.choiceLabel = option.label;
            button.onclick = () => app.submitAwaitingChoice?.(option.value, option.label);
            actions.appendChild(button);
        });
        if (renderOptions.locked) {
            app.lockChoiceCard(card, renderOptions.selectedValue || '', renderOptions.selectedLabel || renderOptions.statusText || '');
        }
        row.body.appendChild(card);
        container.appendChild(row.wrap);
        app.updateLearningProgress({ step: 4, label: '学习进度 4/5' });
        app.scrollMessagesToBottom();
    };

    app.renderPostEvalSelector = function renderPostEvalSelector(options = [], renderOptions = {}) {
        document.querySelector('.post-eval-card')?.remove();
        document.querySelector('.next-step-card')?.remove();
        const container = document.getElementById('messages');
        const row = createAssistantCardRow('topic-confirm-card post-eval-card');
        const card = document.createElement('div');
        card.className = 'topic-confirm-card post-eval-card prompt-flow-card';
        card.dataset.cardKind = 'post_eval_selector';
        card.innerHTML = `
            <div class="prompt-card prompt-flow-shell">
                <div class="prompt-label">这轮完成</div>
                <div class="prompt-title">接下来做什么</div>
                <div class="prompt-copy">继续或收住。</div>
            </div>
            <div class="suggestion-row topic-confirm-chip-list selector-chip-list post-eval-actions"></div>
        `;
        const actions = card.querySelector('.post-eval-actions');
        const normalized = Array.isArray(options) && options.length
            ? options
            : [
                { value: 'continue_advance', label: '继续拔高' },
                { value: 'same_type_practice', label: '换一道同类型' },
                { value: 'summarize_wrapup', label: '总结本轮收获' },
            ];
        normalized.forEach(option => {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'chip topic-confirm-chip selector-chip';
            button.textContent = option.label;
            button.dataset.choiceValue = option.value;
            button.dataset.choiceLabel = option.label;
            button.onclick = () => app.submitAwaitingChoice?.(option.value, option.label);
            actions.appendChild(button);
        });
        if (renderOptions.locked) {
            app.lockChoiceCard(card, renderOptions.selectedValue || '', renderOptions.selectedLabel || renderOptions.statusText || '');
        }
        row.body.appendChild(card);
        container.appendChild(row.wrap);
        app.updateLearningProgress({ step: 5, label: '学习进度 5/5' });
        app.scrollMessagesToBottom();
    };

    app.showTopicEditInput = function showTopicEditInput() {
        const box = document.getElementById('topic-edit-box');
        if (box) {
            box.hidden = false;
            document.getElementById('topic-edit-input')?.focus();
        }
    };

    // ================================================================
    // 课后 / 作业 / 客观题 选择卡片
    // ================================================================

    app.renderPostLessonChoice = function renderPostLessonChoice(options = [], renderOptions = {}) {
        document.querySelector('.post-lesson-card')?.remove();
        const container = document.getElementById('messages');
        const row = createAssistantCardRow('topic-confirm-card post-lesson-card');
        const card = document.createElement('div');
        card.className = 'topic-confirm-card post-lesson-card prompt-flow-card';
        card.dataset.cardKind = 'post_lesson_choice';
        card.innerHTML = `
            <div class="prompt-card prompt-flow-shell">
                <div class="prompt-label">课后停顿</div>
                <div class="prompt-title">还有哪里卡住？</div>
                <div class="prompt-copy">可以直接打一整句问题，也可以先说“这里没懂”；顺了再进入小测。</div>
            </div>
            <div class="suggestion-row topic-confirm-chip-list selector-chip-list post-lesson-actions"></div>
        `;
        const actions = card.querySelector('.post-lesson-actions');
        const normalized = Array.isArray(options) && options.length
            ? options
            : [
                { value: 'temporary_question', label: '继续追问' },
                { value: 'start_test', label: '我懂了，进入小测' },
            ];
        normalized.forEach(option => {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'chip topic-confirm-chip selector-chip';
            button.textContent = option.label || option.value;
            button.dataset.choiceValue = option.value;
            button.dataset.choiceLabel = option.label || option.value;
            button.onclick = () => app.submitAwaitingChoice?.(option.value, option.label || option.value);
            actions.appendChild(button);
        });
        if (renderOptions.locked) {
            app.lockChoiceCard(card, renderOptions.selectedValue || '', renderOptions.selectedLabel || renderOptions.statusText || '');
        }
        row.body.appendChild(card);
        container.appendChild(row.wrap);
        app.scrollMessagesToBottom();
    };

    app.renderContinueOrHomeworkChoice = function renderContinueOrHomeworkChoice(options = [], renderOptions = {}) {
        document.querySelector('.continue-homework-card')?.remove();
        const container = document.getElementById('messages');
        const row = createAssistantCardRow('topic-confirm-card continue-homework-card');
        const card = document.createElement('div');
        card.className = 'topic-confirm-card continue-homework-card prompt-flow-card';
        card.dataset.cardKind = 'continue_or_homework_choice';
        card.innerHTML = `
            <div class="prompt-card prompt-flow-shell">
                <div class="prompt-label">继续 / 收作业</div>
                <div class="prompt-title">还学吗</div>
                <div class="prompt-copy">继续下一个节点还是今天先到这里。</div>
            </div>
            <div class="suggestion-row topic-confirm-chip-list selector-chip-list continue-homework-actions"></div>
        `;
        const actions = card.querySelector('.continue-homework-actions');
        const normalized = Array.isArray(options) && options.length
            ? options
            : [
                { value: 'continue_next_node', label: '继续下一个' },
                { value: 'stop_today', label: '今天先到这里' },
            ];
        normalized.forEach(option => {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'chip topic-confirm-chip selector-chip';
            button.textContent = option.label || option.value;
            button.dataset.choiceValue = option.value;
            button.dataset.choiceLabel = option.label || option.value;
            button.onclick = () => app.submitAwaitingChoice?.(option.value, option.label || option.value);
            actions.appendChild(button);
        });
        if (renderOptions.locked) {
            app.lockChoiceCard(card, renderOptions.selectedValue || '', renderOptions.selectedLabel || renderOptions.statusText || '');
        }
        row.body.appendChild(card);
        container.appendChild(row.wrap);
        app.scrollMessagesToBottom();
    };

    app.renderHomeworkReviewChoice = function renderHomeworkReviewChoice(options = [], renderOptions = {}) {
        document.querySelector('.homework-review-card')?.remove();
        const container = document.getElementById('messages');
        const row = createAssistantCardRow('topic-confirm-card homework-review-card');
        const card = document.createElement('div');
        card.className = 'topic-confirm-card homework-review-card prompt-flow-card';
        card.dataset.cardKind = 'homework_review_choice';
        card.innerHTML = `
            <div class="prompt-card prompt-flow-shell">
                <div class="prompt-label">作业</div>
                <div class="prompt-title">作业安排</div>
                <div class="prompt-copy">现在做，保存到下次，或保留作业继续学习。</div>
            </div>
            <div class="suggestion-row topic-confirm-chip-list selector-chip-list homework-review-actions"></div>
        `;
        const actions = card.querySelector('.homework-review-actions');
        const normalized = Array.isArray(options) && options.length
            ? options
            : [
                { value: 'answer_homework', label: '现在做作业' },
                { value: 'save_for_later', label: '保存，下次再做' },
                { value: 'continue_learning', label: '保留作业，继续学习' },
            ];
        normalized.forEach(option => {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'chip topic-confirm-chip selector-chip';
            button.textContent = option.label || option.value;
            button.dataset.choiceValue = option.value;
            button.dataset.choiceLabel = option.label || option.value;
            button.onclick = () => app.submitAwaitingChoice?.(option.value, option.label || option.value);
            actions.appendChild(button);
        });
        if (renderOptions.locked) {
            app.lockChoiceCard(card, renderOptions.selectedValue || '', renderOptions.selectedLabel || renderOptions.statusText || '');
        }
        row.body.appendChild(card);
        container.appendChild(row.wrap);
        app.scrollMessagesToBottom();
    };

    app.renderConsolidationChoice = function renderConsolidationChoice(options = [], renderOptions = {}) {
        document.querySelector('.consolidation-card')?.remove();
        const container = document.getElementById('messages');
        const row = createAssistantCardRow('topic-confirm-card consolidation-card');
        const card = document.createElement('div');
        card.className = 'topic-confirm-card consolidation-card prompt-flow-card';
        card.dataset.cardKind = 'consolidation_choice';
        card.innerHTML = `
            <div class="prompt-card prompt-flow-shell">
                <div class="prompt-label">继续学习</div>
                <div class="prompt-title">上次没有留作业</div>
                <div class="prompt-copy">你想先巩固复习已学内容，还是直接开始下一节点？</div>
            </div>
            <div class="suggestion-row topic-confirm-chip-list selector-chip-list consolidation-actions"></div>
        `;
        const actions = card.querySelector('.consolidation-actions');
        const normalized = Array.isArray(options) && options.length
            ? options
            : [
                { value: 'consolidate', label: '巩固复习（生成复习题）' },
                { value: 'continue_learning', label: '直接开始下一节点' },
            ];
        normalized.forEach(option => {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'chip topic-confirm-chip selector-chip';
            button.textContent = option.label || option.value;
            button.dataset.choiceValue = option.value;
            button.dataset.choiceLabel = option.label || option.value;
            button.onclick = () => app.submitAwaitingChoice?.(option.value, option.label || option.value);
            actions.appendChild(button);
        });
        if (renderOptions.locked) {
            app.lockChoiceCard(card, renderOptions.selectedValue || '', renderOptions.selectedLabel || renderOptions.statusText || '');
        }
        row.body.appendChild(card);
        container.appendChild(row.wrap);
        app.scrollMessagesToBottom();
    };

    app.renderHomeworkAnswerCard = function renderHomeworkAnswerCard(items = [], renderOptions = {}) {
        document.querySelectorAll('.homework-answer-card:not(.locked)').forEach(card => card.remove());
        const container = document.getElementById('messages');
        const row = createAssistantCardRow('topic-confirm-card homework-answer-card');
        const card = document.createElement('div');
        card.className = 'topic-confirm-card homework-answer-card prompt-flow-card';
        card.dataset.cardKind = 'homework_answers';
        const normalized = Array.isArray(items) ? items : [];
        card.innerHTML = `
            <div class="prompt-card prompt-flow-shell">
                <div class="prompt-label">作业提交</div>
                <div class="prompt-title">按题号填写答案</div>
                <div class="prompt-copy">支持逐题填写，也可以直接在输入框提交 JSON。</div>
            </div>
            <div class="homework-answer-fields"></div>
            <button type="button" class="chip chip-primary homework-submit-btn">提交作业答案</button>
        `;
        const fields = card.querySelector('.homework-answer-fields');
        normalized.forEach((item, idx) => {
            const qid = String(item.question_id || item.id || `HW-${idx + 1}`);
            const promptText = String(item.prompt || qid);
            const field = document.createElement('label');
            field.className = 'homework-answer-field';
            const label = document.createElement('span');
            label.className = 'homework-answer-field-label';
            label.textContent = `${idx + 1}. ${promptText}`;
            const textarea = document.createElement('textarea');
            textarea.rows = 3;
            textarea.dataset.qid = qid;
            textarea.placeholder = `填写 ${qid} 的答案`;
            field.appendChild(label);
            field.appendChild(textarea);
            fields.appendChild(field);
        });
        const submitBtn = card.querySelector('.homework-submit-btn');
        submitBtn.onclick = () => {
            const answers = {};
            card.querySelectorAll('textarea[data-qid]').forEach(input => {
                const value = String(input.value || '').trim();
                if (value) answers[input.dataset.qid] = value;
                input.disabled = true;
            });
            submitBtn.disabled = true;
            submitBtn.textContent = '已提交，等待批改…';
            card.classList.add('locked');
            app.submitAwaitingChoice?.(JSON.stringify(answers), '作业答案已提交');
        };
        if (renderOptions.locked) {
            card.classList.add('locked');
            card.querySelectorAll('textarea').forEach(input => input.disabled = true);
            submitBtn.disabled = true;
        }
        row.body.appendChild(card);
        container.appendChild(row.wrap);
        app.scrollMessagesToBottom();
    };

    app.renderObjectiveTestCard = function renderObjectiveTestCard(questions = [], kind = 'objective_test_answers') {
        document.querySelectorAll('.obj-test-card:not(.submitted-collapsed)').forEach(card => card.remove());
        const container = document.getElementById('messages');
        const row = createAssistantCardRow('topic-confirm-card obj-test-card');
        const card = document.createElement('div');
        card.className = 'topic-confirm-card obj-test-card prompt-flow-card';
        card.dataset.quizKind = kind;
        const label = kind === 'variant_test_answers' ? '变式练习' : '客观测验';
        card.innerHTML = `
            <div class="prompt-card prompt-flow-shell">
                <div class="prompt-label">${label}</div>
                <div class="prompt-title">请逐题作答</div>
                <div class="prompt-copy">选好后点提交。</div>
            </div>
            <button type="button" class="chip selector-chip obj-test-review-toggle" hidden aria-expanded="true">默认收起，点击展开查看作答情况</button>
            <div class="obj-test-review-body">
                <div class="obj-test-questions"></div>
                <button class="chip chip-primary obj-test-submit" disabled>提交全部答案</button>
            </div>
        `;
        const qContainer = card.querySelector('.obj-test-questions');
        const submitBtn = card.querySelector('.obj-test-submit');
        const reviewToggle = card.querySelector('.obj-test-review-toggle');
        const reviewBody = card.querySelector('.obj-test-review-body');
        const answerMap = {};
        const normalizedQs = Array.isArray(questions) ? questions : [];
        const setReviewCollapsed = (collapsed) => {
            card.classList.toggle('submitted-collapsed', collapsed);
            if (reviewBody) reviewBody.hidden = collapsed;
            if (reviewToggle) {
                reviewToggle.hidden = false;
                reviewToggle.setAttribute('aria-expanded', collapsed ? 'false' : 'true');
                reviewToggle.textContent = collapsed ? '已提交客观题，点击展开查看作答情况' : '收起作答情况';
            }
        };
        if (reviewToggle) {
            reviewToggle.onclick = () => setReviewCollapsed(reviewToggle.getAttribute('aria-expanded') === 'true');
        }

        normalizedQs.forEach((q, idx) => {
            const qEl = document.createElement('div');
            qEl.className = 'obj-test-q';
            const qid = q.question_id || q.id || `Q${idx + 1}`;
            const qText = q.question || q.stem || `第 ${idx + 1} 题`;
            const rawOpts = q.options || [];
            const optEntries = Array.isArray(rawOpts)
                ? rawOpts.map((o, optIdx) => {
                    const parsedKey = _parseOptionKey(o);
                    const key = ['A', 'B', 'C', 'D'].includes(parsedKey) ? parsedKey : String.fromCharCode(65 + optIdx);
                    return { key, text: _stripObjectiveOptionLabel(o, key) };
                })
                : Object.entries(rawOpts).map(([k, v]) => {
                    const key = String(k || '').trim().toUpperCase();
                    return { key, text: _stripObjectiveOptionLabel(v, key) };
                });
            const qTextEl = document.createElement('div');
            qTextEl.className = 'obj-test-q-text';
            qTextEl.textContent = `${idx + 1}. ${qText}`;
            const optContainer = document.createElement('div');
            optContainer.className = 'obj-test-q-opts';
            qEl.appendChild(qTextEl);
            qEl.appendChild(optContainer);
            optEntries.forEach(({ key, text }) => {
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'chip selector-chip obj-test-opt';
                btn.dataset.qIdx = String(idx);
                btn.dataset.qid = qid;
                btn.dataset.v = key;
                const keyEl = document.createElement('span');
                keyEl.className = 'obj-test-opt-key';
                keyEl.textContent = key;
                const textEl = document.createElement('span');
                textEl.className = 'obj-test-opt-text';
                textEl.textContent = text;
                btn.appendChild(keyEl);
                btn.appendChild(textEl);
                btn.onclick = () => {
                    optContainer.querySelectorAll('.obj-test-opt').forEach(o => o.classList.remove('selected'));
                    btn.classList.add('selected');
                    answerMap[qid] = key;
                    submitBtn.disabled = Object.keys(answerMap).length < normalizedQs.length;
                };
                optContainer.appendChild(btn);
            });
            qContainer.appendChild(qEl);
        });

        submitBtn.onclick = () => {
            const answerPayload = JSON.stringify(answerMap);
            submitBtn.disabled = true;
            submitBtn.textContent = '已提交，等待批改…';
            card.querySelectorAll('.obj-test-opt').forEach(o => {
                o.style.pointerEvents = 'none';
                o.classList.add('locked');
            });
            card.querySelectorAll('.obj-test-answer-summary').forEach(el => el.remove());
            normalizedQs.forEach((q, idx) => {
                const qid = q.question_id || q.id || `Q${idx + 1}`;
                const userKey = answerMap[qid] || '';
                const correctKey = (q.answer_key || q.correct_answer || '').toUpperCase();
                const qEl = qContainer.children[idx];
                if (qEl) {
                    if (correctKey) {
                        qEl.querySelectorAll('.obj-test-opt').forEach(o => {
                            const v = (o.dataset.v || '').toUpperCase();
                            if (v === correctKey) o.classList.add('correct-answer');
                            if (v === userKey && userKey !== correctKey) o.classList.add('wrong-answer');
                        });
                    }
                    const summary = document.createElement('div');
                    summary.className = 'obj-test-answer-summary';
                    summary.textContent = `你的答案：${userKey || '未作答'}；正确答案：${correctKey || '未提供'}`;
                    qEl.appendChild(summary);
                }
            });
            setReviewCollapsed(true);
            app.submitAwaitingChoice?.(answerPayload, '答案已提交');
        };

        app.collapseSubmittedObjectiveTestCard = function collapseSubmittedObjectiveTestCard() {
            const activeCard = document.querySelector('.obj-test-card');
            if (!activeCard) return;
            const activeToggle = activeCard.querySelector('.obj-test-review-toggle');
            const activeBody = activeCard.querySelector('.obj-test-review-body');
            if (!activeToggle || activeToggle.hidden) return;
            activeCard.classList.add('submitted-collapsed');
            if (activeBody) activeBody.hidden = true;
            activeToggle.setAttribute('aria-expanded', 'false');
            activeToggle.textContent = '已提交客观题，点击展开查看作答情况';
        };

        row.body.appendChild(card);
        container.appendChild(row.wrap);
        app.scrollMessagesToBottom();
    };

    app.renderObjectiveQuizReviewCard = function renderObjectiveQuizReviewCard(data = {}, content = '') {
        app.finalizeAgentTurn?.();
        const questions = Array.isArray(data.questions) ? data.questions : [];
        const answers = data.answers || {};
        const kind = data.kind || data.quiz_kind || 'objective_test_answers';
        const title = data.title || (kind === 'variant_test_answers' ? '变式练习' : '客观测评');
        const score = Number.isFinite(Number(data.score)) ? Number(data.score) : 0;
        const passScore = Number.isFinite(Number(data.pass_score)) ? Number(data.pass_score) : 80;
        const passed = Boolean(data.passed);
        const questionCount = Number(data.question_count || questions.length || 0);
        const correctCount = Number(data.correct_count || questions.filter(q => q.is_correct).length || 0);
        const wrongCount = Number(data.wrong_count ?? Math.max(0, questionCount - correctCount));
        const nodeName = data.node_name || '';
        const existingCards = Array.from(document.querySelectorAll('.obj-test-card'));
        const card = existingCards.find(candidate => candidate.dataset.quizKind === kind && !candidate.dataset.reviewRendered)
            || existingCards.find(candidate => !candidate.dataset.reviewRendered)
            || null;
        if (!card) {
            app.renderObjectiveTestCard(questions, kind);
        }
        const reviewCard = card || Array.from(document.querySelectorAll('.obj-test-card')).pop();
        if (!reviewCard) {
            if (content) app.appendMessage('agent', content, { kind: 'objective_quiz_review' });
            return;
        }
        reviewCard.dataset.reviewRendered = 'true';
        reviewCard.dataset.reviewState = data.review_state || 'graded';
        reviewCard.closest('.msg-wrapper')?.setAttribute('data-contains-objective-review', 'true');
        const qContainer = reviewCard.querySelector('.obj-test-questions');
        const submitBtn = reviewCard.querySelector('.obj-test-submit');
        const toggle = reviewCard.querySelector('.obj-test-review-toggle');
        const body = reviewCard.querySelector('.obj-test-review-body');
        const heading = reviewCard.querySelector('.prompt-label');
        const titleEl = reviewCard.querySelector('.prompt-title');
        const copyEl = reviewCard.querySelector('.prompt-copy');
        if (heading) heading.textContent = `${title} · 已批改`;
        if (titleEl) titleEl.textContent = passed ? '本轮已通过，可以继续推进' : `本轮未通过，需要订正 ${wrongCount} 道错题`;
        if (copyEl) copyEl.textContent = nodeName ? `节点：${nodeName}` : '提交后答案已锁定，下面是本轮复盘。';
        if (submitBtn) submitBtn.remove();
        reviewCard.querySelectorAll('.obj-test-opt').forEach(o => {
            o.style.pointerEvents = 'none';
            o.classList.add('locked');
        });

        reviewCard.querySelectorAll('.obj-quiz-review-summary').forEach(el => el.remove());
        reviewCard.querySelectorAll('.obj-test-answer-summary, .obj-test-explanation').forEach(el => el.remove());
        const summary = document.createElement('section');
        summary.className = `obj-quiz-review-summary ${passed ? 'is-passed' : 'is-failed'}`;
        summary.innerHTML = `
            <div class="obj-review-kicker">${passed ? '已通过' : '需要订正'} · 已锁定</div>
            <div class="obj-review-score-row">
                <div class="obj-review-score"><strong>${score}</strong><span>/100</span></div>
                <div class="obj-review-result">通过线 ${passScore} · ${correctCount}/${questionCount} 正确</div>
            </div>
            <div class="obj-review-stats">
                <span>错题 ${wrongCount} 道</span>
                <span>${passed ? '下一步：进入后续节点决策' : '下一步：先看错题讲解，再做变式练习'}</span>
            </div>
        `;
        reviewCard.querySelector('.prompt-card')?.after(summary);

        questions.forEach((q, idx) => {
            const qid = q.question_id || q.id || `Q${idx + 1}`;
            const userKey = String(q.chosen_answer || answers[qid] || answers[String(idx + 1)] || answers[`Q${idx + 1}`] || '').toUpperCase();
            const correctKey = String(q.correct_answer || q.answer_key || q.correct || '').toUpperCase();
            const isCorrect = typeof q.is_correct === 'boolean' ? q.is_correct : Boolean(correctKey && userKey === correctKey);
            const qEl = qContainer?.children?.[idx];
            if (!qEl) return;
            qEl.classList.toggle('is-correct', isCorrect);
            qEl.classList.toggle('is-wrong', !isCorrect);
            qEl.querySelectorAll('.obj-test-opt').forEach(o => {
                const v = String(o.dataset.v || '').toUpperCase();
                if (correctKey && v === correctKey) o.classList.add('correct-answer');
                if (userKey && correctKey && v === userKey && userKey !== correctKey) o.classList.add('wrong-answer');
                if (userKey && v === userKey) o.classList.add('selected');
            });
            const itemSummary = document.createElement('div');
            itemSummary.className = 'obj-test-answer-summary';
            itemSummary.innerHTML = `
                <span class="obj-result-pill ${isCorrect ? 'ok' : 'bad'}">${isCorrect ? '正确' : '错误'}</span>
                <span>你的答案：${escapeHtml(userKey || '未作答')}</span>
                <span>正确答案：${escapeHtml(correctKey || '未提供')}</span>
                ${q.wrong_reason ? `<span>错因：${escapeHtml(q.wrong_reason)}</span>` : ''}
            `;
            qEl.appendChild(itemSummary);

            const targetObjective = String(q.target_objective || q.objective || '').trim();
            const explanationText = String(q.explanation || q.analysis || '').trim();
            const wrong_option_analysis = q.wrong_option_analysis || {};
            const chosenWrongAnalysis = !isCorrect ? String(wrong_option_analysis[userKey] || '').trim() : '';
            const misconception = String(q.misconception || '').trim();
            if (targetObjective || explanationText || chosenWrongAnalysis || misconception) {
                const explanation = document.createElement('div');
                explanation.className = 'obj-test-explanation';
                const head = document.createElement('div');
                head.className = 'obj-test-explanation-head';
                const title = document.createElement('span');
                title.className = 'obj-test-explanation-title';
                title.textContent = '本题解析';
                const state = document.createElement('span');
                state.className = `obj-test-explanation-state ${isCorrect ? 'ok' : 'bad'}`;
                state.textContent = isCorrect ? '已掌握' : '需订正';
                head.appendChild(title);
                head.appendChild(state);
                explanation.appendChild(head);
                const addLine = (label, value) => {
                    const cleanValue = String(value || '').trim();
                    if (!cleanValue) return;
                    const line = document.createElement('div');
                    line.className = 'obj-test-explanation-row';
                    const labelEl = document.createElement('span');
                    labelEl.className = 'obj-test-explanation-label';
                    labelEl.textContent = label;
                    const valueEl = document.createElement('span');
                    valueEl.className = 'obj-test-explanation-value';
                    valueEl.textContent = cleanValue;
                    line.appendChild(labelEl);
                    line.appendChild(valueEl);
                    explanation.appendChild(line);
                };
                addLine('考察目标', targetObjective);
                addLine('判断依据', explanationText);
                addLine('所选项问题', chosenWrongAnalysis);
                addLine('常见误区', misconception);
                addLine('下一步', isCorrect ? '保留这条判断依据，后续遇到同类题先按这个条件定位。' : '先回看考察目标和所选项问题，再重做同类题验证是否真正掌握。');
                qEl.appendChild(explanation);
                app.renderMath?.(explanation);
            }
        });
        reviewCard.classList.add('submitted-collapsed', 'review-locked');
        if (body) body.hidden = true;
        if (toggle) {
            toggle.hidden = false;
            toggle.setAttribute('aria-expanded', 'false');
            toggle.textContent = `已批改${title}，点击展开逐题结果`;
        }
    };

    app.renderWrongQuestionExplanationCard = function renderWrongQuestionExplanationCard(explanations = [], options = {}) {
        app.finalizeAgentTurn?.();
        const items = Array.isArray(explanations) ? explanations : [];
        const container = document.getElementById('messages');
        if (!container) return;
        const row = createAssistantCardRow('wrong-explanation-card');
        const card = document.createElement('section');
        card.className = 'topic-confirm-card prompt-flow-card wrong-explain-card';
        card.dataset.reviewState = options.review_state || 'explained';
        const count = items.length;
        card.innerHTML = `
            <div class="prompt-card prompt-flow-shell wrong-explain-head">
                <div class="prompt-label">错题讲解 · 已生成</div>
                <div class="prompt-title">${count ? `已整理 ${count} 道错题的订正思路` : '暂无需要订正的错题'}</div>
                <div class="prompt-copy">默认收起详细讲解，展开后查看错因、判断依据和复习动作。</div>
            </div>
            <div class="wrong-explain-list"></div>
        `;
        const list = card.querySelector('.wrong-explain-list');
        items.forEach((item, idx) => {
            const qid = String(item.question_id || `Q${idx + 1}`);
            const stem = String(item.stem || '未提供题干');
            const userAnswer = String(item.user_answer || '').toUpperCase() || '未作答';
            const answerKey = String(item.answer_key || item.correct_answer || '').toUpperCase() || '未提供';
            const wrongReason = String(item.wrong_reason || '未分类');
            const target = String(item.target_objective || '');
            const block = document.createElement('article');
            block.className = 'wrong-explain-item';
            block.innerHTML = `
                <button type="button" class="wrong-explain-summary" aria-expanded="false">
                    <span class="wrong-explain-index">${idx + 1}</span>
                    <span class="wrong-explain-main">
                        <strong>${escapeHtml(stem)}</strong>
                        <span>你的答案 ${escapeHtml(userAnswer)} · 正确答案 ${escapeHtml(answerKey)}${target ? ` · 考察：${escapeHtml(target)}` : ''}</span>
                    </span>
                    <span class="wrong-explain-reason">${escapeHtml(wrongReason)}</span>
                </button>
                <div class="wrong-explain-detail" hidden>
                    ${item.why_user_wrong ? `<section><b>你错在</b><p>${escapeHtml(item.why_user_wrong)}</p></section>` : ''}
                    ${item.why_correct ? `<section><b>正确理解</b><p>${escapeHtml(item.why_correct)}</p></section>` : ''}
                    ${item.key_rule ? `<section><b>下次判断依据</b><p>${escapeHtml(item.key_rule)}</p></section>` : ''}
                    <section><b>完整讲解</b><p>${escapeHtml(item.explanation || '这题需要回到题干条件和节点核心概念重新判断。')}</p></section>
                    ${item.review_action ? `<section><b>下一步</b><p>${escapeHtml(item.review_action)}</p></section>` : ''}
                </div>
            `;
            const btn = block.querySelector('.wrong-explain-summary');
            const detail = block.querySelector('.wrong-explain-detail');
            btn.onclick = () => {
                const expanded = btn.getAttribute('aria-expanded') === 'true';
                btn.setAttribute('aria-expanded', expanded ? 'false' : 'true');
                detail.hidden = expanded;
            };
            list.appendChild(block);
        });
        row.body.appendChild(card);
        container.appendChild(row.wrap);
        app.scrollMessagesToBottom();
    };

    function applySessionArtifacts(stateSnapshot) {
        state.currentTopic = stateSnapshot.current_topic || stateSnapshot.currentTopic || stateSnapshot.current_user_goal || stateSnapshot.session_goal || '';
        state.currentTopicFocus = stateSnapshot.topic_focus || stateSnapshot.currentTopicFocus || '';
        state.graphTopicHint = state.currentTopic || stateSnapshot.proposed_topic || state.graphTopicHint || '';
        state.learningTrack = stateSnapshot.learning_track || stateSnapshot.learningTrack || '';
        state.learningTrackLabel = stateSnapshot.learning_track_label || stateSnapshot.learningTrackLabel || '';
        state.learningTrackLocked = Boolean(stateSnapshot.learning_track_locked || stateSnapshot.learningTrackLocked);
        state.currentGraphNode = stateSnapshot.graph_anchor_title || stateSnapshot.current_node_name || stateSnapshot.currentGraphNode || '';
        if (stateSnapshot.user_knowledge_graph && typeof stateSnapshot.user_knowledge_graph === 'object') {
            state.userKnowledgeGraph = { ...stateSnapshot.user_knowledge_graph };
        } else if (stateSnapshot.userKnowledgeGraph && typeof stateSnapshot.userKnowledgeGraph === 'object') {
            state.userKnowledgeGraph = { ...stateSnapshot.userKnowledgeGraph };
        }
        app.updateLearningProgress(stateSnapshot || {});
        state.currentGraphNodeId = stateSnapshot.graph_anchor_id || stateSnapshot.current_node_id || '';
        if (stateSnapshot.assessment_radar && stateSnapshot.assessment_radar.dimensions) {
            app.showRadar(stateSnapshot.assessment_radar);
        }
        if (state.currentGraphNode || state.currentGraphNodeId) {
            app.renderKnowledgeGraphVisualCard?.({
                title: state.currentGraphNode,
                id: state.currentGraphNodeId,
                status: stateSnapshot.current_node_status || 'in_progress',
                type: 'current',
            });
        }

        if (stateSnapshot.flow_status === 'awaiting_topic_confirmation' && stateSnapshot.proposed_topic) {
            app.renderTopicConfirmation(stateSnapshot.proposed_topic, {
                detail_summary: stateSnapshot.topic_detail_summary || '',
                topic_focus: stateSnapshot.topic_focus || '',
                topic_background: stateSnapshot.topic_background || '',
                topic_starter_options: stateSnapshot.topic_starter_options || [],
                clarify_rounds: stateSnapshot.topic_clarify_rounds || 0,
            });
        }

        if (stateSnapshot.flow_status === 'awaiting_interrupt_confirmation') {
            app.renderInterruptConfirmation();
        }

        if (stateSnapshot.flow_status === 'awaiting_assessment' && (stateSnapshot.assessment_questions || []).length) {
            const assessmentQuestions = stateSnapshot.assessment_questions || [];
            const assessmentAnswers = stateSnapshot.assessment_answers || {};
            const isCompletedAssessment = Boolean(stateSnapshot.is_assessed)
                && _allAssessmentAnswered(assessmentQuestions, assessmentAnswers);
            app.renderAssessmentForm(assessmentQuestions, assessmentAnswers, {
                locked: isCompletedAssessment,
                statusText: isCompletedAssessment ? '测评已完成，答案已固定' : undefined,
            });
        }

        if (stateSnapshot.flow_status === 'awaiting_next_step_selector') {
            app.renderNextStepSelector(stateSnapshot.pending_interaction_options || []);
        }

        if (stateSnapshot.flow_status === 'awaiting_post_eval_selector') {
            app.renderPostEvalSelector(stateSnapshot.pending_interaction_options || []);
        }

        if (stateSnapshot.flow_status === 'assessment_dialog') {
            const asState = stateSnapshot.assessment_state || {};
            const asPairs = asState.pairs || [];
            const asIdx = asState.current_pair_index || 0;
            const asPhase = asState.phase || 'subjective_choice';
            if (asIdx < asPairs.length) {
                const pair = asPairs[asIdx];
                const src = asPhase === 'subjective_choice' ? pair?.subjective : asPhase === 'self_eval' ? pair?.self_eval : pair?.objective;
                if (src) {
                    app.renderAssessmentDialogQuestion({
                        pair_index: asIdx,
                        total_pairs: asPairs.length,
                        phase: asPhase,
                        concept: pair.concept,
                        question_id: src.id,
                        question: src.question,
                        options: src.options,
                    });
                }
            }
        }

        const pik = stateSnapshot.pending_interaction_kind || '';
        const pio = stateSnapshot.pending_interaction_options || [];
        if (pik === 'post_lesson_choice') {
            app.renderPostLessonChoice?.(pio);
        }
        if (pik === 'continue_or_homework_choice') {
            app.renderContinueOrHomeworkChoice?.(pio);
        }
        if (pik === 'homework_review_choice') {
            app.renderHomeworkReviewChoice?.(pio);
        }
        if (pik === 'consolidation_choice') {
            app.renderConsolidationChoice?.(pio);
        }
        if (pik === 'homework_answers') {
            state.isAwaitingInput = true;
            app.renderHomeworkAnswerCard?.(stateSnapshot.homework_items || [], stateSnapshot);
            app.setChatInputPlaceholder?.('请输入你的作业答案');
        }
        if (pik === 'objective_test_answers' || pik === 'variant_test_answers') {
            const selector = `.obj-test-card[data-quiz-kind="${pik}"]:not(.submitted-collapsed)`;
            if (!document.querySelector(selector)) {
                app.renderObjectiveTestCard?.(pio, pik);
            }
        }
        app.updateSidebarState?.(stateSnapshot);
        app.refreshChatSurfaceState?.();
    }

    app.restoreMessageTimeline = function restoreMessageTimeline(items, stateSnapshot) {
        const messages = document.getElementById('messages');
        messages.innerHTML = '';
        app.finalizeAgentTurn();

        if (!Array.isArray(items) || !items.length) {
            app.restoreSessionState(stateSnapshot);
            return;
        }

        state.pendingTopicConfirmation = stateSnapshot?.proposed_topic || null;
        state.pendingTopicConfirmationDetails = {
            detail_summary: stateSnapshot?.topic_detail_summary || '',
            topic_focus: stateSnapshot?.topic_focus || '',
            topic_background: stateSnapshot?.topic_background || '',
            topic_starter_options: stateSnapshot?.topic_starter_options || [],
            clarify_rounds: stateSnapshot?.topic_clarify_rounds || 0,
        };
        const renderTimelineItem = item => {
            const role = item.role || 'agent';
            const content = item.content || '';
            const data = item.data || {};
            if (item.kind === 'topic_confirmation_locked') {
                const topic = data.topic || stateSnapshot?.current_topic || stateSnapshot?.current_user_goal || content;
                const label = data.label || '已确认';
                if (topic) {
                    const row = createAssistantCardRow('topic-confirm-card');
                    const card = document.createElement('div');
                    card.className = 'topic-confirm-card prompt-flow-card tc-card-v2 tc-locked';
                    card.innerHTML = `
                        <div class="tc-locked-content">
                            <span class="tc-locked-icon">✅</span>
                            <span class="tc-locked-topic">${topic}</span>
                            <span class="tc-confirmed-badge">${label}</span>
                        </div>
                    `;
                    row.body.appendChild(card);
                    messages.appendChild(row.wrap);
                }
                return;
            }
            if (item.kind === 'course_choice_card') {
                if (app.renderCourseChoiceCard) {
                    app.renderCourseChoiceCard({
                        locked: data.locked !== false,
                        selectedTrack: data.selected_track || stateSnapshot?.learning_track || '',
                        selectedLabel: data.selected_label || stateSnapshot?.learning_track_label || '',
                        statusText: data.statusText || '',
                        append: true,
                    });
                } else {
                    app.appendSystemMessage(data.statusText || content || '学习方向已固定', 'info');
                }
                return;
            }
            if (item.kind === 'course_choice_selection') {
                return;
            }
            if (
                item.kind === 'topic_confirmation_card'
                && (data.proposed_topic || content.trim())
            ) {
                if (stateSnapshot?.flow_status !== 'awaiting_topic_confirmation') {
                    return;
                }
                app.renderTopicConfirmation(data.proposed_topic || content, data);
                return;
            }
            if (item.kind === 'assessment_form' && Array.isArray(data.questions) && data.questions.length) {
                const snapshotAnswers = stateSnapshot?.assessment_answers || {};
                const timelineAnswers = data.answers || {};
                const isCompletedAssessment = Boolean(stateSnapshot?.is_assessed)
                    && _allAssessmentAnswered(data.questions, snapshotAnswers);
                app.renderAssessmentForm(
                    data.questions,
                    isCompletedAssessment ? snapshotAnswers : timelineAnswers,
                    {
                        locked: isCompletedAssessment || data.locked === true,
                        statusText: isCompletedAssessment ? '测评已完成，答案已固定' : data.statusText,
                    }
                );
                return;
            }
            if (item.kind === 'interrupt_confirmation_card') {
                app.renderInterruptConfirmation?.();
                return;
            }
            if (item.kind === 'objective_test_card') {
                app.renderObjectiveTestCard?.(data.questions || data.options || [], data.interaction_kind || 'objective_test_answers');
                return;
            }
            if (item.kind === 'objective_quiz_review') {
                app.renderObjectiveQuizReviewCard?.(data, content);
                return;
            }
            if (item.kind === 'homework_answer_prompt') {
                app.renderHomeworkAnswerCard?.(data.homework_items || data.items || stateSnapshot?.homework_items || [], data);
                return;
            }
            if (item.kind === 'graph_rag_answer' || item.kind === 'graph_rag_debug_report') {
                const fallbackHtml = item.kind === 'graph_rag_answer'
                    ? '<section class="learning-answer-content"><p></p></section>'
                    : '<section class="graph-rag-answer-panel"><div class="answer"></div></section>';
                app.appendMessage('agent', content || fallbackHtml, { kind: item.kind });
                return;
            }
            if (item.kind === 'wrong_question_explanations') {
                const explanations = Array.isArray(data.explanations) ? data.explanations : [];
                if (explanations.length) {
                    app.renderWrongQuestionExplanationCard?.(explanations, data);
                } else {
                    app.appendMessage('agent', content || '错题订正讲解', { kind: 'wrong_question_explanations' });
                }
                return;
            }
            if (item.kind === 'next_step_selector') {
                app.renderNextStepSelector?.(data.options || [], data);
                return;
            }
            if (item.kind === 'post_eval_selector') {
                app.renderPostEvalSelector?.(data.options || [], data);
                return;
            }
            if (item.kind === 'post_lesson_choice_card') {
                app.renderPostLessonChoice?.(data.options || [], data);
                return;
            }
            if (item.kind === 'continue_or_homework_choice_card') {
                app.renderContinueOrHomeworkChoice?.(data.options || [], data);
                return;
            }
            if (item.kind === 'homework_review_choice_card') {
                app.renderHomeworkReviewChoice?.(data.options || [], data);
                return;
            }
            if (item.kind === 'consolidation_choice_card') {
                app.renderConsolidationChoice?.(data.options || [], data);
                return;
            }
            if (!content.trim()) return;
            if (role === 'user') {
                app.appendMessage('user', content, { timestamp: item.updated_at });
                return;
            }
            if (item.kind === 'tutor_evidence') {
                if (Array.isArray(item.data?.evidence)) {
                    app.renderEvidencePanel(item.data.evidence, { role: 'tutor', tone: item.tone || 'info' });
                } else {
                    app.appendSystemMessage(content, item.tone || 'info');
                }
                return;
            }
            if (role === 'system') {
                app.appendSystemMessage(content, item.tone || 'info');
                return;
            }
            app.appendMessage('agent', content, { kind: item.kind || '' });
        };
        items.forEach(item => {
            renderTimelineItem(item);
        });

        if (stateSnapshot) {
            applySessionArtifacts(stateSnapshot);
        }

        app.finalizeAgentTurn();
    };

    app.restoreSessionState = function restoreSessionState(stateSnapshot) {
        const messages = document.getElementById('messages');
        messages.innerHTML = '';
        app.finalizeAgentTurn();

        if (!stateSnapshot) {
            app.updateLearningProgress({ step: 1, label: '学习进度 1/5' });
            app.updateSidebarState?.();
            app.refreshChatSurfaceState?.();
            return;
        }

        state.pendingTopicConfirmation = stateSnapshot.proposed_topic || null;
        state.pendingTopicConfirmationDetails = {
            detail_summary: stateSnapshot?.topic_detail_summary || '',
            topic_focus: stateSnapshot?.topic_focus || '',
            topic_background: stateSnapshot?.topic_background || '',
            topic_starter_options: stateSnapshot?.topic_starter_options || [],
            clarify_rounds: stateSnapshot?.topic_clarify_rounds || 0,
        };
        const hasConfirmedTopic = Boolean(
            stateSnapshot.current_topic &&
            !PRE_TOPIC_FLOW_STATUSES.has(stateSnapshot.flow_status) &&
            stateSnapshot.flow_status !== 'awaiting_topic_confirmation'
        );
        const sessionSummary = hasConfirmedTopic
            ? `已回到这页 · ${stateSnapshot.current_topic}`
            : '已回到这页';
        app.appendSystemMessage(sessionSummary, 'info');

        if (stateSnapshot.assessment_result) app.appendMessage('agent', stateSnapshot.assessment_result, { kind: 'assessment_result' });

        // ── 恢复测评对话卡片（锁定态）──
        const as = stateSnapshot.assessment_state;
        if (as && as.pairs && as.answers) {
            const answers = as.answers || {};
            const pairs = as.pairs || [];
            const total = pairs.length;
            const isSubjective = as.phase === 'subjective_choice' || as.phase === 'done' && pairs[0]?.subjective;

            for (let i = 0; i < total; i++) {
                const pair = pairs[i];
                if (!pair) continue;

                if (isSubjective || pair.subjective) {
                    // 主观选择题恢复
                    const sq = pair.subjective;
                    if (!sq) continue;
                    const sqId = String(sq.id);
                    if (answers[sqId] != null) {
                        app.renderAssessmentDialogQuestion({
                            pair_index: i,
                            total_pairs: total,
                            phase: 'subjective_choice',
                            concept: pair.concept,
                            question_id: sq.id,
                            question: sq.question,
                            options: sq.options,
                        }, { chosen: answers[sqId] });
                    }
                    continue;
                }

                // 自评题
                const selfId = String(pair.self_eval?.id);
                if (answers[selfId] != null) {
                    const selfAnswer = 'ABCD'.indexOf(answers[selfId]) + 1;
                    app.renderAssessmentDialogQuestion({
                        pair_index: i,
                        total_pairs: total,
                        phase: 'self_eval',
                        concept: pair.concept,
                        question_id: pair.self_eval.id,
                        question: pair.self_eval.question,
                        options: pair.self_eval.options,
                    }, { answer: selfAnswer || 1 });
                }

                // 客观题
                const objId = String(pair.objective?.id);
                if (answers[objId] != null) {
                    const chosen = answers[objId];
                    const correct = pair.objective.correct || '';
                    app.renderAssessmentDialogQuestion({
                        pair_index: i,
                        total_pairs: total,
                        phase: 'objective',
                        concept: pair.concept,
                        question_id: pair.objective.id,
                        question: pair.objective.question,
                        options: pair.objective.options,
                    }, {
                        chosen: chosen,
                        correct_answer: correct,
                        is_correct: chosen === correct,
                    });
                }
            }
        }

        if (stateSnapshot.tutor_content) app.appendMessage('agent', stateSnapshot.tutor_content, { kind: 'tutor' });
        if ((stateSnapshot.tutor_evidence || []).length) {
            app.renderEvidencePanel(stateSnapshot.tutor_evidence, { role: 'tutor', tone: 'info' });
        }
        if (stateSnapshot.coach_content) app.appendMessage('agent', stateSnapshot.coach_content, { kind: 'coach' });
        if (stateSnapshot.user_answer) app.appendMessage('user', stateSnapshot.user_answer);
        if (stateSnapshot.tester_question) app.appendMessage('agent', stateSnapshot.tester_question, { kind: 'tester_question' });

        if (stateSnapshot.feedback || stateSnapshot.score) {
            const lines = [
                `总分：${stateSnapshot.score}`,
                `逻辑：${stateSnapshot.logic_score}`,
                `概念：${stateSnapshot.concept_score}`,
                '',
                `观察：${stateSnapshot.feedback || '暂无补充。'}`,
            ];
            if (stateSnapshot.needs_hint) {
                lines.push('', '下一步：先看提示。');
            }
            if (Array.isArray(stateSnapshot.next_review_points) && stateSnapshot.next_review_points.length) {
                lines.push('', '建议复习：');
                lines.push(...stateSnapshot.next_review_points.map(point => `- ${point}`));
            }
            app.appendMessage('agent', lines.join('\n'), { kind: 'evaluator_card' });
        }

        applySessionArtifacts(stateSnapshot);

        app.finalizeAgentTurn();
        app.scheduleSidebarUpdate?.();
    };

    // ── 用户知识图谱面板 ──────────────────────────────────────────────────────

    /**
     * 旧的侧边栏掌握图面板已移除，保留轻量同步入口给现有调用链复用。
     */
    app.renderUserKnowledgeMap = function renderUserKnowledgeMap() {
        app.updateSidebarState?.();
    };

    app.focusUserKgMap = function focusUserKgMap() {
        const sidebar = document.getElementById('sidebar');
        if (sidebar?.classList.contains('sidebar--collapsed')) {
            app.toggleSidebar?.(false);
        }
        app.updateSidebarState?.();
        app.openKnowledgeGraphModal?.();
    };

    app.toggleUserKgMap = function toggleUserKgMap() {
        app.focusUserKgMap();
    };

    // ── 补救决策卡 ────────────────────────────────────────────────────────────
    app.renderRemediationDecisionCard = function renderRemediationDecisionCard(data = {}, renderOptions = {}) {
        document.querySelector('.remediation-decision-card')?.remove();
        const container = document.getElementById('messages');
        const row = createAssistantCardRow('remediation-decision-card');
        const card = document.createElement('div');
        card.className = 'remediation-decision-card prompt-flow-card';
        card.dataset.cardKind = 'remediation_decision';

        const score = data.score ?? 0;
        const passScore = data.pass_score ?? 80;
        const tier = data.tier || (score >= passScore ? 'pass' : score >= 60 ? 'partial' : 'low');
        const paused = data.paused || false;
        const wrongCount = data.wrong_count ?? 0;
        const variantRounds = data.variant_rounds ?? 0;
        const maxVariantRounds = data.max_variant_rounds ?? 2;
        const extraCount = data.extra_remediation_question_count ?? 0;
        const maxExtra = data.max_extra_questions ?? 10;
        const failures = data.same_objective_failures || {};
        const pausedReasons = Array.isArray(data.paused_reasons) ? data.paused_reasons : [];
        const options = Array.isArray(renderOptions.options) ? renderOptions.options : [];

        let title, summary, recommendation;
        if (paused) {
            title = '补救已暂停';
            summary = `本轮得分 ${score} / ${passScore}`;
            recommendation = '这类错因已经连续出现，继续刷题效果不高。建议先回到节点讲解重点复习。';
        } else if (tier === 'pass') {
            title = '测验通过';
            summary = `得分 ${score} / ${passScore}，已通过`;
            recommendation = '可以进入下一节点。';
        } else if (tier === 'partial') {
            title = '需要补救';
            summary = `得分 ${score} / ${passScore}，未通过 · 共 ${wrongCount} 个错因`;
            recommendation = '已为你整理错因。建议先做变式训练巩固，如果感觉基础不稳也可以先复习本节点。';
        } else {
            title = '基础不牢';
            summary = `得分 ${score} / ${passScore}，说明当前节点基础理解还不稳`;
            recommendation = '建议先回到节点讲解重新学习，再做变式题。';
        }

        let html = `
            <div class="prompt-card prompt-flow-shell remediation-decision-shell">
                <div class="prompt-label">${title}</div>
                <div class="prompt-title">节点补救决策</div>
                <div class="prompt-copy">${summary}</div>
        `;

        if (paused && pausedReasons.length) {
            html += '<div class="remediation-paused-reasons">';
            pausedReasons.forEach(r => {
                html += `<div class="remediation-paused-reason">⚠️ ${escapeHtml(r)}</div>`;
            });
            html += '</div>';
        }

        html += `
                <div class="remediation-recommendation">${escapeHtml(recommendation)}</div>
                <div class="remediation-stats">
                    <span>错因 ${wrongCount} 个</span>
                    <span>变式轮次 ${variantRounds}/${maxVariantRounds}</span>
                    <span>补救题 ${extraCount}/${maxExtra}</span>
                </div>
        `;

        if (Object.keys(failures).length > 0) {
            html += '<div class="remediation-failures">';
            for (const [obj, count] of Object.entries(failures)) {
                html += `<div class="remediation-failure-item">「${escapeHtml(obj)}」错 ${count} 次</div>`;
            }
            html += '</div>';
        }

        html += '</div>';

        if (options.length) {
            html += '<div class="suggestion-row topic-confirm-chip-list selector-chip-list remediation-actions"></div>';
        }

        card.innerHTML = html;

        const actions = card.querySelector('.remediation-actions');
        if (actions) {
            options.forEach(option => {
                const button = document.createElement('button');
                button.type = 'button';
                button.className = 'chip topic-confirm-chip selector-chip';
                button.textContent = option.label || option.value;
                button.dataset.choiceValue = option.value;
                button.dataset.choiceLabel = option.label || option.value;
                button.onclick = () => app.submitAwaitingChoice?.(option.value, option.label || option.value);
                actions.appendChild(button);
            });
        }

        if (renderOptions.locked) {
            app.lockChoiceCard(card, renderOptions.selectedValue || '', renderOptions.selectedLabel || renderOptions.statusText || '');
        }

        row.body.appendChild(card);
        container.appendChild(row.wrap);
        app.scrollMessagesToBottom();
    };
})();
