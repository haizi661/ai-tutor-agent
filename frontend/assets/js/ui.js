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

    function renderMarkdown(target, text) {
        target.innerHTML = marked.parse(text);
        app.renderMath(target);
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
        if (window.renderMathInElement) {
            renderMathInElement(el, {
                delimiters: [
                    { left: '$$', right: '$$', display: true },
                    { left: '$', right: '$', display: false },
                ],
                throwOnError: false,
            });
        }
    };

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
        state.currentAgentBodyEl.innerHTML = marked.parse(displayText);
        
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
        }

        const sameStatus = prev && typeof prev === 'object' && prev.status === status;

        // 仅对明确的教学里程碑追加 event chip（避免 in_progress 频繁插入）
        if (status === 'mastered' && !sameStatus) {
            _appendGraphEventChip(`✅  已掌握：${title}`, 'mastered');
        } else if (status === 'skipped' && !sameStatus) {
            _appendGraphEventChip(`⏭  已跳过：${title}`, 'skipped');
        }

        app.refreshUserKgMapIfOpen?.();
    };

    /** 在下游节点到来时高亮提示（不影响 UKG 状态，只做视觉）*/
    app.highlightNextNode = function highlightNextNode(title) {
        if (!title) return;
        _appendGraphEventChip(`→  即将进入：${title}`, 'next');
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

    app.scrollMessagesToBottom = function scrollMessagesToBottom() {
        const container = document.getElementById('messages');
        if (!container) return;
        const shouldForceScroll = container.hidden;
        app.refreshChatSurfaceState?.();
        if (container.hidden) return;
        
        // Only auto-scroll if the user is near the bottom
        // This prevents the screen from jumping down if they scrolled up to read
        const isNearBottom = shouldForceScroll || container.scrollHeight - container.scrollTop - container.clientHeight < 150;
        
        if (isNearBottom) {
            container.scrollTop = container.scrollHeight;
        }
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

    app.appendAgentTurnShell = function appendAgentTurnShell(initialText = '', role = state.currentTurnRole || 'teacher') {
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

        renderMarkdown(state.currentAgentBodyEl, initialText);
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

    app.addThinkingStep = function addThinkingStep(text, tone = 'info') {
        if (!text) return false;
        if (tone === 'warning' || tone === 'danger') app.setStatusBanner(text, tone);
        return true;
    };

    app.addNote = function addNote(text, tone = 'info') {
        if (!text) return false;
        if (tone === 'warning' || tone === 'danger') app.setStatusBanner(text, tone);
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
            app.appendAgentTurnShell(text, turnRole);
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
        bubble.innerHTML = marked.parse(text);
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
                    <div class="system-body">${marked.parse(text)}</div>
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

    function _answeredAssessmentCount(questions = [], answers = {}) {
        return questions.filter(q => Boolean(String(answers[q.id] || '').trim())).length;
    }

    function _assessmentProgressMetaHtml(questions = [], answers = {}) {
        const answeredCount = _answeredAssessmentCount(questions, answers);
        return `
            <span>已作答 ${answeredCount} / ${questions.length}</span>
            <span>每题一旦作答就会锁定，恢复历史时保持同样状态。</span>
        `;
    }

    function _refreshAssessmentProgressMeta() {
        const meta = document.querySelector('.assessment-progress-meta');
        if (!meta) return;
        meta.innerHTML = _assessmentProgressMetaHtml(state.assessmentQuestions, state.answers);
    }

    app.renderAssessmentForm = function renderAssessmentForm(questions, initialAnswers = {}) {
        state.assessmentQuestions = questions;
        state.answers = { ...initialAnswers };
        document.querySelector('.assessment-container')?.remove();
        const container = document.getElementById('messages');
        const row = createAssistantCardRow('assessment-container');
        const div = document.createElement('div');
        div.className = 'assessment-container prompt-flow-card';

        const selfEvalQs = questions.filter(q => q.type === 'self_eval');
        const objectiveQs = questions.filter(q => q.type === 'objective');
        const hasPairing = selfEvalQs.some(q => q.concept);
        const introCard = document.createElement('div');
        introCard.className = 'prompt-card prompt-flow-shell';
        introCard.innerHTML = `
            <div class="prompt-label">开始前的小测</div>
            <div class="prompt-title">先对齐起点</div>
            <div class="prompt-copy">
                ${hasPairing
                    ? `前 ${selfEvalQs.length} 题是<strong>自我评价</strong>，后 ${objectiveQs.length} 题是对应的<strong>实际测验</strong>。`
                    : `先用这 ${questions.length} 题确定你的起点。`}
            </div>
        `;
        div.appendChild(introCard);

        const shortcutRow = document.createElement('div');
        shortcutRow.className = 'suggestion-row prompt-flow-actions';
        const skipBtn = document.createElement('button');
        skipBtn.type = 'button';
        skipBtn.className = 'chip chip-muted assessment-skip-btn';
        skipBtn.title = '跳过测评，直接进入讲解';
        skipBtn.textContent = '先不测，直接开始';
        shortcutRow.appendChild(skipBtn);
        div.appendChild(shortcutRow);

        const progressMeta = document.createElement('div');
        progressMeta.className = 'assessment-progress-meta';
        progressMeta.innerHTML = _assessmentProgressMetaHtml(questions, state.answers);
        div.appendChild(progressMeta);

        skipBtn.onclick = () => {
            row.wrap.remove();
            fetch('/api/confirm_topic', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    thread_id: state.currentThreadId,
                    confirmed: true,
                    topic: state.pendingTopicConfirmation || '',
                    start_mode: 'direct_tutor',
                }),
            }).then(() => app.connectSSE());
        };

        app.updateLearningProgress({ step: 2, label: '学习进度 2/5' });

        if (selfEvalQs.length) {
            const sec1 = document.createElement('section');
            sec1.className = 'assessment-section';
            sec1.innerHTML = `<div class="assessment-section-title">自我评价</div>`;
            selfEvalQs.forEach(q => sec1.appendChild(_buildQuestionItem(q, state)));
            div.appendChild(sec1);
        }

        if (objectiveQs.length) {
            const sec2 = document.createElement('section');
            sec2.className = 'assessment-section';
            sec2.innerHTML = `<div class="assessment-section-title">实际测验</div>`;
            objectiveQs.forEach(q => sec2.appendChild(_buildQuestionItem(q, state)));
            div.appendChild(sec2);
        }

        if (!selfEvalQs.length && !objectiveQs.length) {
            questions.forEach(q => div.appendChild(_buildQuestionItem(q, state)));
        }

        const submitBtn = document.createElement('button');
        submitBtn.type = 'button';
        submitBtn.className = 'chip chip-primary btn-submit-all';
        submitBtn.innerText = '提交答案';
        submitBtn.onclick = async () => {
            const totalRequired = questions.length;
            const answered = Object.keys(state.answers).length;
            if (answered < totalRequired) {
                const unanswered = questions.filter(q => !state.answers[q.id]);
                const firstUnanswered = unanswered[0];
                if (firstUnanswered) {
                    div.querySelector(`#q-${firstUnanswered.id}`)?.closest('.q-item')
                        ?.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
                submitBtn.classList.add('shake');
                setTimeout(() => submitBtn.classList.remove('shake'), 600);
                return;
            }
            submitBtn.disabled = true;
            submitBtn.innerText = '整理中…';
            app.setStatusBanner('正在分析自评与实测的差距…', 'processing');
            await fetch('/api/submit_assessment', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ thread_id: state.currentThreadId, answers: state.answers }),
            });
            app.connectSSE();
        };
        div.appendChild(submitBtn);
        row.body.appendChild(div);
        container.appendChild(row.wrap);
        app.scrollMessagesToBottom();
    };

    /** 构建单题 DOM，支持 concept 标签 */
    function _buildQuestionItem(q, state) {
        const answerCode = String(state.answers[q.id] || '').trim().toUpperCase();
        const matchedOption = (q.options || []).find(opt => answerCode === opt.trim().charAt(0).toUpperCase()) || '';
        const qDiv = document.createElement('div');
        qDiv.className = `q-item${answerCode ? ' q-item--answered' : ''}`;
        const conceptTag = q.concept
            ? `<span class="q-concept-tag">${q.concept}</span>`
            : '';
        const statusChip = answerCode
            ? `<span class="q-status-chip q-status-chip--locked">已作答</span>`
            : `<span class="q-status-chip q-status-chip--pending">待作答</span>`;
        qDiv.innerHTML = `
            <div class="q-head">
                <div class="q-text">${conceptTag}${q.id}. ${q.question}</div>
                ${statusChip}
            </div>
            ${
                answerCode
                    ? `
                        <div class="q-answer-card">
                            <div class="q-answer-label">你的选择</div>
                            <div class="q-answer-text">${matchedOption || answerCode}</div>
                        </div>
                        <div class="q-answer-note">答案已锁定并随会话保存，恢复后保持不可重复作答。</div>
                    `
                    : `<div class="opt-grid suggestion-row" id="q-${q.id}"></div>`
            }
        `;
        if (answerCode) {
            return qDiv;
        }
        const grid = qDiv.querySelector('.opt-grid');
        (q.options || []).forEach(opt => {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'chip opt-btn';
            btn.innerText = opt;
            btn.setAttribute('aria-pressed', 'false');
            btn.onclick = async () => {
                state.answers[q.id] = opt.trim().charAt(0).toUpperCase();
                qDiv.replaceWith(_buildQuestionItem(q, state));
                _refreshAssessmentProgressMeta();
                if (!state.currentThreadId) return;
                try {
                    await fetch('/api/assessment_draft', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ thread_id: state.currentThreadId, answers: state.answers }),
                    });
                } catch (_error) {
                    app.setStatusBanner?.('答案已锁定，但暂时没有写回草稿。', 'warning');
                }
            };
            grid.appendChild(btn);
        });
        return qDiv;
    }

    // ================================================================
    // 对话式逐题测评 UI  — 三种题型 × 三种状态
    // ================================================================
    //
    // 题型：self_eval（自评 1-5 点选）、objective（客观四选一）
    // 状态：unanswered → selected → locked（含对错反馈）
    //
    // 后端 payload:
    //   assessment.question → { pair_index, total_pairs, phase, concept, question_id, question, options }
    //   assessment.feedback → { pair_index, concept, is_correct, correct_answer, chosen, gap }

    const SELF_EVAL_LABELS = ['', '完全没把握', '有点模糊', '有点把握', '比较确定', '非常确定'];

    function _parseOptionKey(optText) {
        return (optText || '').trim().charAt(0).toUpperCase();
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
        const phaseLabel = phase === 'self_eval' ? '自评' : '客观题';
        const phaseCls = phase === 'self_eval' ? 'q-tag--self' : 'q-tag--obj';
        const headerHtml = `
            <div class="q-header">
                <span class="q-tag ${phaseCls}">${phaseLabel}</span>
                <span class="q-tag q-tag--concept">${concept}</span>
            </div>`;

        // ── 题面 ──
        const questionHtml = `<div class="q-text">${qText}</div>`;

        if (phase === 'self_eval') {
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
        document.querySelector('.topic-confirm-card')?.remove();
        const container = document.getElementById('messages');
        const row = createAssistantCardRow('topic-confirm-card');
        const card = document.createElement('div');
        card.className = 'topic-confirm-card prompt-flow-card';
        const detailSummary = (details.detail_summary || '').trim();
        const focus = (details.topic_focus || '').trim();
        const background = (details.topic_background || '').trim();
        const starterOptions = Array.isArray(details.topic_starter_options) ? details.topic_starter_options.filter(Boolean) : [];
        const detailItems = [];
        if (focus) detailItems.push(`这次先抓：${focus}`);
        if (background) detailItems.push(`当前状态：${background}`);
        if (!detailItems.length && detailSummary) detailItems.push(detailSummary);
        const prompt = document.createElement('div');
        prompt.className = 'prompt-card prompt-flow-shell';
        prompt.innerHTML = `
            <div class="prompt-label">确认主题</div>
            <div class="prompt-title">${topic}</div>
            <div class="prompt-copy">确认后直接开始。</div>
        `;
        card.appendChild(prompt);

        if (detailItems.length) {
            const detailBox = document.createElement('div');
            detailBox.className = 'topic-confirm-details prompt-flow-section';
            detailBox.innerHTML = `
                <div class="topic-confirm-detail-title">重点</div>
                <ul class="topic-confirm-detail-list"></ul>
            `;
            const detailList = detailBox.querySelector('.topic-confirm-detail-list');
            detailItems.forEach(item => {
                const li = document.createElement('li');
                li.textContent = item;
                detailList.appendChild(li);
            });
            card.appendChild(detailBox);
        }

        if (starterOptions.length) {
            const starterBox = document.createElement('div');
            starterBox.className = 'topic-confirm-starters prompt-flow-section';
            starterBox.innerHTML = `<div class="topic-confirm-detail-title">切入点</div>`;
            const starterList = document.createElement('div');
            starterList.className = 'suggestion-row topic-confirm-chip-list';
            starterOptions.forEach(option => {
                const chip = document.createElement('button');
                chip.type = 'button';
                chip.className = 'chip topic-confirm-chip';
                chip.textContent = option;
                chip.onclick = () => {
                    app.showTopicEditInput?.();
                    const input = document.getElementById('topic-edit-input');
                    if (input) {
                        input.value = option;
                        input.focus();
                    }
                };
                starterList.appendChild(chip);
            });
            starterBox.appendChild(starterList);
            card.appendChild(starterBox);
        }

        const actions = document.createElement('div');
        actions.className = 'suggestion-row prompt-flow-actions';
        const actionButtons = [
            { label: '直接开始', className: 'chip chip-primary', run: () => app.submitTopicConfirmation(true, 'direct_tutor') },
            { label: '先看例子', className: 'chip', run: () => app.submitTopicConfirmation(true, 'analogy_tutor') },
            { label: '先做小测', className: 'chip', run: () => app.submitTopicConfirmation(true, 'assessment') },
            { label: '修改主题', className: 'chip chip-muted', run: () => app.showTopicEditInput?.() },
        ];
        actionButtons.forEach(({ label, className, run }) => {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = className;
            button.textContent = label;
            button.onclick = run;
            actions.appendChild(button);
        });
        card.appendChild(actions);

        const editBox = document.createElement('div');
        editBox.id = 'topic-edit-box';
        editBox.className = 'prompt-inline-editor';
        editBox.hidden = true;
        editBox.innerHTML = `
            <input id="topic-edit-input" class="topic-confirm-input" placeholder="输入更明确的主题">
            <div class="suggestion-row prompt-flow-actions">
                <button type="button" class="chip chip-warn">用这个继续</button>
            </div>
        `;
        editBox.querySelector('button').onclick = () => app.submitTopicConfirmation(false, 'assessment');
        card.appendChild(editBox);

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

    app.renderNextStepSelector = function renderNextStepSelector(options = []) {
        document.querySelector('.next-step-card')?.remove();
        document.querySelector('.post-eval-card')?.remove();
        const container = document.getElementById('messages');
        const row = createAssistantCardRow('topic-confirm-card next-step-card');
        const card = document.createElement('div');
        card.className = 'topic-confirm-card next-step-card prompt-flow-card';
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
            button.onclick = () => app.submitAwaitingChoice?.(option.value, option.label);
            actions.appendChild(button);
        });
        row.body.appendChild(card);
        container.appendChild(row.wrap);
        app.updateLearningProgress({ step: 4, label: '学习进度 4/5' });
        app.scrollMessagesToBottom();
    };

    app.renderPostEvalSelector = function renderPostEvalSelector(options = []) {
        document.querySelector('.post-eval-card')?.remove();
        document.querySelector('.next-step-card')?.remove();
        const container = document.getElementById('messages');
        const row = createAssistantCardRow('topic-confirm-card post-eval-card');
        const card = document.createElement('div');
        card.className = 'topic-confirm-card post-eval-card prompt-flow-card';
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
            button.onclick = () => app.submitAwaitingChoice?.(option.value, option.label);
            actions.appendChild(button);
        });
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

    function applySessionArtifacts(stateSnapshot) {
        state.currentTopic = stateSnapshot.current_topic || '';
        state.currentTopicFocus = stateSnapshot.topic_focus || '';
        state.graphTopicHint = stateSnapshot.current_topic || stateSnapshot.proposed_topic || state.graphTopicHint || '';
        state.currentGraphNode = stateSnapshot.graph_anchor_title || state.currentGraphNode || '';
        if (stateSnapshot.user_knowledge_graph && typeof stateSnapshot.user_knowledge_graph === 'object') {
            state.userKnowledgeGraph = { ...stateSnapshot.user_knowledge_graph };
        } else if (stateSnapshot.userKnowledgeGraph && typeof stateSnapshot.userKnowledgeGraph === 'object') {
            state.userKnowledgeGraph = { ...stateSnapshot.userKnowledgeGraph };
        }
        app.updateLearningProgress(stateSnapshot || {});
        if (stateSnapshot.assessment_radar && stateSnapshot.assessment_radar.dimensions) {
            app.showRadar(stateSnapshot.assessment_radar);
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
            app.renderAssessmentForm(stateSnapshot.assessment_questions, stateSnapshot.assessment_answers || {});
        }

        if (stateSnapshot.flow_status === 'awaiting_next_step_selector') {
            app.renderNextStepSelector(stateSnapshot.pending_interaction_options || []);
        }

        if (stateSnapshot.flow_status === 'awaiting_post_eval_selector') {
            app.renderPostEvalSelector(stateSnapshot.pending_interaction_options || []);
        }
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
            if (
                item.kind === 'topic_confirmation_card'
                && (data.proposed_topic || content.trim())
            ) {
                app.renderTopicConfirmation(data.proposed_topic || content, data);
                return;
            }
            if (item.kind === 'assessment_form' && Array.isArray(data.questions) && data.questions.length) {
                app.renderAssessmentForm(data.questions, data.answers || {});
                return;
            }
            if (item.kind === 'interrupt_confirmation_card') {
                app.renderInterruptConfirmation?.();
                return;
            }
            if (item.kind === 'next_step_selector') {
                app.renderNextStepSelector?.(data.options || []);
                return;
            }
            if (item.kind === 'post_eval_selector') {
                app.renderPostEvalSelector?.(data.options || []);
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

            for (let i = 0; i < total; i++) {
                const pair = pairs[i];
                if (!pair) continue;

                // 自评题
                const selfId = String(pair.self_eval?.id);
                if (answers[selfId] != null) {
                    // 将 A/B/C/D 映射为 1-5
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
})();
