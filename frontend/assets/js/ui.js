(() => {
    const app = window.AITutorApp;
    const state = app.state;
    const PRE_TOPIC_FLOW_STATUSES = new Set(['greeting', 'topic_intake', 'meta_qa', 'smalltalk']);
    const STATUS_BANNER_TONES = ['status-ready', 'status-info', 'status-awaiting', 'status-processing', 'status-success', 'status-warning', 'status-danger', 'status-paused'];
    const SHORT_VISIBLE_FALLBACK_MS = 1600;
    const LONG_VISIBLE_FALLBACK_MS = 5200;
    const MAX_VISIBLE_FALLBACKS = 2;

    function renderMarkdown(target, text) {
        target.innerHTML = marked.parse(text);
        app.renderMath(target);
    }

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

    let mathRenderTimeout = null;

    app.throttledRender = function throttledRender() {
        if (!state.currentAgentBodyEl) return;
        state.currentAgentBodyEl.innerHTML = marked.parse(state.currentTextBuffer);
        
        // Debounce heavy KaTeX rendering to prevent flickering and CPU spikes during fast streaming
        if (mathRenderTimeout) clearTimeout(mathRenderTimeout);
        mathRenderTimeout = setTimeout(() => {
            if (state.currentAgentBodyEl) {
                app.renderMath(state.currentAgentBodyEl);
            }
        }, 150);
    };

    app.clearTypingIndicator = function clearTypingIndicator() {
        document.getElementById('typing-indicator')?.remove();
    };

    app.setStatusBanner = function setStatusBanner(message, tone = 'ready') {
        const banner = document.getElementById('status-banner');
        if (!banner) return;
        banner.textContent = message;
        banner.classList.remove(...STATUS_BANNER_TONES);
        banner.classList.add(`status-${tone}`);
    };

    app.setInlineStatus = function setInlineStatus(elementId, message, tone = 'muted') {
        const el = document.getElementById(elementId);
        if (!el) return;
        el.textContent = message;
        el.dataset.tone = tone;
    };

    app.scrollMessagesToBottom = function scrollMessagesToBottom() {
        const container = document.getElementById('messages');
        if (!container) return;
        
        // Only auto-scroll if the user is near the bottom
        // This prevents the screen from jumping down if they scrolled up to read
        const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 150;
        
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
        if (state.latestRouteDecisionSummary) return `系统流程进展：${state.latestRouteDecisionSummary}`;
        if (state.latestNodeStartMessage) return `系统流程进展：${state.latestNodeStartMessage}`;
        if (state.latestProgressSummary) return `系统流程进展：${state.latestProgressSummary}`;
        return '系统流程仍在继续，我拿到更具体结果后会立即显示。';
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
                app.appendVisibleSystemTurn('我已接上这一步，正在处理中。', 'info', {
                    kind: 'progress',
                    clearTyping: false,
                });
                state.visibilityFallbackCount = 1;
                app.scheduleVisibilityFallback();
                return;
            }

            if (state.visibilityFallbackCount === 1) {
                app.appendVisibleSystemTurn(app.getTurnProgressFallbackText(), 'info', {
                    kind: 'progress',
                    clearTyping: false,
                });
                state.visibilityFallbackCount = 2;
            }
        }, delay);
    };

    app.appendAgentTurnShell = function appendAgentTurnShell(initialText = '') {
        const wrap = document.createElement('div');
        wrap.className = 'msg-wrapper agent';
        wrap.innerHTML = `
            <div class="avatar agent" aria-hidden="true">伴</div>
            <div class="msg-content agent-turn">
                <div class="agent-body"></div>
                <div class="agent-main-flow" hidden></div>
                <div class="turn-heartbeat" hidden aria-live="polite"></div>
                <details class="meta-block meta-block-thinking">
                    <summary>
                        <span class="meta-title">思考过程（系统信号）</span>
                        <span class="meta-badge" aria-label="思考过程条数">0</span>
                    </summary>
                    <ol class="thinking-list"></ol>
                </details>
                <details class="meta-block meta-block-notes">
                    <summary>
                        <span class="meta-title">注释（辅助说明）</span>
                        <span class="meta-badge" aria-label="注释条数">0</span>
                    </summary>
                    <ul class="notes-list"></ul>
                </details>
            </div>
        `;
        const container = document.getElementById('messages');
        container.appendChild(wrap);

        state.currentAgentTurnEl = wrap;
        state.currentAgentMainFlowEl = wrap.querySelector('.agent-main-flow');
        state.currentAgentBodyEl = wrap.querySelector('.agent-body');
        state.currentAgentMsgEl = state.currentAgentBodyEl;
        state.currentTurnHeartbeatEl = wrap.querySelector('.turn-heartbeat');
        state.currentThinkingBlockEl = wrap.querySelector('.meta-block-thinking');
        state.currentThinkingListEl = wrap.querySelector('.thinking-list');
        state.currentThinkingBadgeEl = wrap.querySelector('.meta-block-thinking .meta-badge');
        state.currentNotesBlockEl = wrap.querySelector('.meta-block-notes');
        state.currentNotesListEl = wrap.querySelector('.notes-list');
        state.currentNotesBadgeEl = wrap.querySelector('.meta-block-notes .meta-badge');
        state.currentTextBuffer = initialText;
        state.thinkingCount = 0;
        state.notesCount = 0;

        app.updateMetaBadges();
        renderMarkdown(state.currentAgentBodyEl, initialText);
        app.scrollMessagesToBottom();
        return wrap;
    };

    app.ensureAgentTurn = function ensureAgentTurn() {
        if (
            state.currentAgentBodyEl &&
            state.currentAgentMainFlowEl &&
            state.currentThinkingListEl &&
            state.currentNotesListEl
        ) {
            return state.currentAgentTurnEl;
        }
        return app.appendAgentTurnShell('');
    };

    app.updateMetaBadges = function updateMetaBadges() {
        if (state.currentThinkingBadgeEl) state.currentThinkingBadgeEl.textContent = String(state.thinkingCount);
        if (state.currentNotesBadgeEl) state.currentNotesBadgeEl.textContent = String(state.notesCount);
        if (state.currentThinkingBlockEl) state.currentThinkingBlockEl.hidden = state.thinkingCount === 0;
        if (state.currentNotesBlockEl) state.currentNotesBlockEl.hidden = state.notesCount === 0;
    };

    app.addThinkingStep = function addThinkingStep(text, tone = 'info') {
        if (!text) return false;
        if (!app.ensureAgentTurn()) return false;
        const item = document.createElement('li');
        item.className = 'meta-item';
        item.dataset.tone = tone;
        renderMarkdown(item, text);
        state.currentThinkingListEl.appendChild(item);
        state.thinkingCount += 1;
        app.updateMetaBadges();
        app.scrollMessagesToBottom();
        return true;
    };

    app.addNote = function addNote(text, tone = 'info') {
        if (!text) return false;
        if (!app.ensureAgentTurn()) return false;
        const item = document.createElement('li');
        item.className = 'meta-item';
        item.dataset.tone = tone;
        renderMarkdown(item, text);
        state.currentNotesListEl.appendChild(item);
        state.notesCount += 1;
        app.updateMetaBadges();
        app.scrollMessagesToBottom();
        return true;
    };

    app.appendVisibleSystemTurn = function appendVisibleSystemTurn(text, tone = 'info', options = {}) {
        if (!text) return false;
        const {
            kind = 'status',
            clearTyping = false,
            createIfNeeded = true,
            markVisible = true,
        } = options;

        if (clearTyping) app.clearTypingIndicator();
        if (createIfNeeded && (state.currentTurnId || state.isStreaming || state.currentAgentTurnEl)) {
            app.ensureAgentTurn();
        }

        if (!state.currentAgentMainFlowEl) {
            app.appendSystemMessage(text, tone);
            if (markVisible) app.markTurnVisible();
            return true;
        }

        const item = document.createElement('div');
        item.className = 'agent-visible-item';
        item.dataset.tone = tone;
        item.dataset.kind = kind;
        renderMarkdown(item, text);
        state.currentAgentMainFlowEl.hidden = false;
        state.currentAgentMainFlowEl.appendChild(item);
        if (markVisible) app.markTurnVisible();
        app.scrollMessagesToBottom();
        return true;
    };

    app.finalizeAgentTurn = function finalizeAgentTurn() {
        app.clearTurnHeartbeat();
        state.currentAgentMsgEl = null;
        state.currentAgentTurnEl = null;
        state.currentAgentMainFlowEl = null;
        state.currentAgentBodyEl = null;
        state.currentTurnHeartbeatEl = null;
        state.currentThinkingBlockEl = null;
        state.currentThinkingListEl = null;
        state.currentThinkingBadgeEl = null;
        state.currentNotesBlockEl = null;
        state.currentNotesListEl = null;
        state.currentNotesBadgeEl = null;
        state.currentTextBuffer = '';
        state.thinkingCount = 0;
        state.notesCount = 0;
        app.resetTurnLifecycleState();
    };

    app.appendMessage = function appendMessage(role, text) {
        app.clearTypingIndicator();

        if (role === 'agent') {
            app.appendAgentTurnShell(text);
            app.finalizeAgentTurn();
            return;
        }

        const wrap = document.createElement('div');
        wrap.className = `msg-wrapper ${role}`;
        const avatarLabel = role === 'user' ? '你' : '伴';
        wrap.innerHTML = `
            <div class="avatar ${role}" aria-hidden="true">${avatarLabel.charAt(0)}</div>
            <div class="msg-content">${marked.parse(text)}</div>
        `;
        const container = document.getElementById('messages');
        container.appendChild(wrap);
        app.scrollMessagesToBottom();
    };

    app.appendSystemMessage = function appendSystemMessage(text, tone = 'info') {
        if (!text) return;
        app.clearTypingIndicator();
        const wrap = document.createElement('div');
        wrap.className = 'msg-wrapper system';
        wrap.dataset.tone = tone;
        wrap.innerHTML = `
            <div class="avatar system" aria-hidden="true">注</div>
            <div class="msg-content system">${marked.parse(text)}</div>
        `;
        const container = document.getElementById('messages');
        container.appendChild(wrap);
        app.scrollMessagesToBottom();
    };

    app.showTyping = function showTyping() {
        app.clearTypingIndicator();
        
        const dotsHtml = `<div class="typing-dots" aria-label="我正在思考..."><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>`;
        
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
            wrap.className = 'msg-wrapper agent';
            wrap.id = 'typing-indicator';
            wrap.innerHTML = `
                <div class="avatar agent" aria-hidden="true">伴</div>
                <div class="msg-content">${dotsHtml}</div>
            `;
            const messages = document.getElementById('messages');
            if (messages) messages.appendChild(wrap);
        }
        app.scrollMessagesToBottom();
    };

    app.showRadar = function showRadar(data) {
        document.getElementById('profile-panel').classList.remove('hidden');
        const ctx = document.getElementById('radarChart').getContext('2d');
        if (state.radarChartInstance) state.radarChartInstance.destroy();
        state.radarChartInstance = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: data.dimensions,
                datasets: [
                    {
                        label: '你的感受',
                        data: data.self_scores,
                        borderColor: '#8ca6c1',
                        backgroundColor: 'rgba(140,166,193,0.16)',
                        pointBackgroundColor: '#8ca6c1',
                    },
                    {
                        label: '当前表现',
                        data: data.objective_scores,
                        borderColor: '#8cb29a',
                        backgroundColor: 'rgba(140,178,154,0.16)',
                        pointBackgroundColor: '#8cb29a',
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
                        grid: { color: 'rgba(136, 150, 168, 0.18)' },
                        angleLines: { color: 'rgba(136, 150, 168, 0.18)' },
                        pointLabels: { color: '#66758a', font: { size: 10 } },
                    },
                },
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { color: '#5b6779', boxWidth: 12, font: { size: 11 } },
                    },
                },
            },
        });
    };

    app.renderAssessmentForm = function renderAssessmentForm(questions, initialAnswers = {}) {
        state.assessmentQuestions = questions;
        state.answers = { ...initialAnswers };
        document.querySelector('.assessment-container')?.remove();
        const container = document.getElementById('messages');
        const div = document.createElement('div');
        div.className = 'assessment-container';
        div.innerHTML = `
            <h3 class="assessment-title">开始前的小测</h3>
            <p class="assessment-lead">先用这 ${questions.length} 道题对齐一下你的起点。我会根据结果调节讲解速度、例子密度和追问方式，不会直接套固定模板。</p>
        `;

        questions.forEach(q => {
            const qDiv = document.createElement('div');
            qDiv.className = 'q-item';
            qDiv.innerHTML = `<div class="q-text">${q.id}. ${q.question}</div><div class="opt-grid" id="q-${q.id}"></div>`;
            const grid = qDiv.querySelector('.opt-grid');
            q.options.forEach(opt => {
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'opt-btn';
                btn.innerText = opt;
                btn.setAttribute('aria-pressed', 'false');
                btn.onclick = () => {
                    state.answers[q.id] = opt.trim().charAt(0);
                    grid.querySelectorAll('.opt-btn').forEach(button => {
                        button.classList.remove('selected');
                        button.setAttribute('aria-pressed', 'false');
                    });
                    btn.classList.add('selected');
                    btn.setAttribute('aria-pressed', 'true');
                };
                if ((state.answers[q.id] || '').toUpperCase() === opt.trim().charAt(0).toUpperCase()) {
                    btn.classList.add('selected');
                    btn.setAttribute('aria-pressed', 'true');
                }
                grid.appendChild(btn);
            });
            div.appendChild(qDiv);
        });

        const submitBtn = document.createElement('button');
        submitBtn.type = 'button';
        submitBtn.className = 'btn-submit-all';
        submitBtn.innerText = '交给我整理，继续进入讲解';
        submitBtn.onclick = async () => {
            if (Object.keys(state.answers).length < questions.length) {
                alert('先把题目答完，我们再继续。');
                return;
            }
            submitBtn.disabled = true;
            submitBtn.innerText = '正在整理你的起点…';
            app.setStatusBanner('我在整理这轮小测，马上继续', 'processing');
            await fetch('/api/submit_assessment', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ thread_id: state.currentThreadId, answers: state.answers }),
            });
            app.connectSSE();
        };
        div.appendChild(submitBtn);
        container.appendChild(div);
        app.scrollMessagesToBottom();
    };

    app.renderTopicConfirmation = function renderTopicConfirmation(topic) {
        state.pendingTopicConfirmation = topic;
        document.querySelector('.topic-confirm-card')?.remove();
        const container = document.getElementById('messages');
        const card = document.createElement('div');
        card.className = 'topic-confirm-card';
        card.innerHTML = `
            <h3>先确认这次要学什么</h3>
            <p class="topic-confirm-lead">我先把你的目标收成下面这个主题。确认后，我们就继续进入小测和正式讲解。</p>
            <div class="topic-confirm-topic"></div>
            <div class="topic-confirm-actions">
                <button type="button" class="topic-confirm-btn primary" onclick="submitTopicConfirmation(true)">对，就按这个学</button>
                <button type="button" class="topic-confirm-btn secondary" onclick="showTopicEditInput()">我想改一下表述</button>
            </div>
            <div id="topic-edit-box" class="topic-edit-box" hidden>
                <input id="topic-edit-input" class="topic-confirm-input" placeholder="请输入更明确的主题，例如：控制理论、矩阵求逆、PID 控制器">
                <div class="topic-confirm-actions">
                    <button type="button" class="topic-confirm-btn warn" onclick="submitTopicConfirmation(false)">用这个新主题继续</button>
                </div>
            </div>
        `;
        card.querySelector('.topic-confirm-topic').textContent = topic;
        container.appendChild(card);
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
        if (stateSnapshot.assessment_radar && stateSnapshot.assessment_radar.dimensions) {
            app.showRadar(stateSnapshot.assessment_radar);
        }

        if (stateSnapshot.flow_status === 'awaiting_topic_confirmation' && stateSnapshot.proposed_topic) {
            app.renderTopicConfirmation(stateSnapshot.proposed_topic);
        }

        if (stateSnapshot.flow_status === 'awaiting_assessment' && (stateSnapshot.assessment_questions || []).length) {
            app.renderAssessmentForm(stateSnapshot.assessment_questions, stateSnapshot.assessment_answers || {});
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
        items.forEach(item => {
            const role = item.role || 'agent';
            const content = item.content || '';
            if (!content.trim()) return;
            if (role === 'user') {
                app.appendMessage('user', content);
                return;
            }
            if (role === 'system') {
                app.appendSystemMessage(content, item.tone || 'info');
                return;
            }
            app.appendMessage('agent', content);
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
            app.appendMessage('agent', '这页暂时还没有可恢复的内容。');
            return;
        }

        state.pendingTopicConfirmation = stateSnapshot.proposed_topic || null;
        const hasConfirmedTopic = Boolean(
            stateSnapshot.current_topic &&
            !PRE_TOPIC_FLOW_STATUSES.has(stateSnapshot.flow_status) &&
            stateSnapshot.flow_status !== 'awaiting_topic_confirmation'
        );
        const sessionSummary = hasConfirmedTopic
            ? `已回到之前的学习页。当前主题：${stateSnapshot.current_topic}`
            : '已回到之前的学习页。这一页还没有确认最终主题。';
        app.appendSystemMessage(sessionSummary, 'info');

        if (stateSnapshot.assessment_result) app.appendMessage('agent', stateSnapshot.assessment_result);
        if (stateSnapshot.tutor_content) app.appendMessage('agent', stateSnapshot.tutor_content);
        if (stateSnapshot.coach_content) app.appendMessage('agent', stateSnapshot.coach_content);
        if (stateSnapshot.user_answer) app.appendMessage('user', stateSnapshot.user_answer);
        if (stateSnapshot.tester_question) app.appendMessage('agent', stateSnapshot.tester_question);

        if (stateSnapshot.feedback || stateSnapshot.score) {
            const lines = [
                `最近一轮整理：总分 ${stateSnapshot.score}，逻辑 ${stateSnapshot.logic_score}，概念 ${stateSnapshot.concept_score}。`,
                '',
                `我记录下来的观察：${stateSnapshot.feedback || '这次还没有补充说明。'}`,
            ];
            if (stateSnapshot.needs_hint) {
                lines.push('', '建议：先看一条思路提示，再尝试重答。');
            }
            if (Array.isArray(stateSnapshot.next_review_points) && stateSnapshot.next_review_points.length) {
                lines.push('', '建议复习：');
                lines.push(...stateSnapshot.next_review_points.map(point => `- ${point}`));
            }
            app.appendMessage('agent', lines.join('\n'));
        }

        applySessionArtifacts(stateSnapshot);

        app.finalizeAgentTurn();
    };
})();
