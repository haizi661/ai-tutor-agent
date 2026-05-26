(() => {
    const app = window.AITutorApp || {};
    const state = app.state || {};

    const originalStartNewSession = app.startNewSession?.bind(app);
    const originalHandleSend = app.handleSend?.bind(app);

    function escapeHtml(text) {
        return String(text || '')
            .replaceAll('&', '&amp;')
            .replaceAll('<', '&lt;')
            .replaceAll('>', '&gt;')
            .replaceAll('"', '&quot;')
            .replaceAll("'", '&#39;');
    }

    async function postJson(url, payload) {
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload || {}),
        });

        const data = await res.json().catch(() => ({}));

        if (!res.ok || data.status === 'error') {
            throw new Error(data.message || data.detail || '请求失败');
        }

        return data;
    }

    function clearMessages() {
        const messages = document.getElementById('messages');
        if (messages) messages.innerHTML = '';
    }

    function appendAgent(text) {
        if (app.appendMessage) {
            app.appendMessage('agent', text);
        } else {
            appendFallbackMessage('agent', text);
        }
    }

    function appendUser(text) {
        if (app.appendMessage) {
            app.appendMessage('user', text);
        } else {
            appendFallbackMessage('user', text);
        }
    }

    function appendFallbackMessage(role, text) {
        const messages = document.getElementById('messages');
        if (!messages) return;

        const row = document.createElement('div');
        row.className = `msg-wrapper ${role === 'user' ? 'user' : 'agent'}`;
        row.innerHTML = `<div class="msg-content">${escapeHtml(text)}</div>`;

        messages.appendChild(row);
        messages.scrollTop = messages.scrollHeight;
    }

    function makeThreadId() {
        return app.makeThreadId ? app.makeThreadId() : `ai_path_${Date.now()}`;
    }

    function setAiMode(active) {
        state.aiPathMode = Boolean(active);
        document.body.classList.toggle('ai-path-chat-mode', Boolean(active));
        app.patchState?.({ aiPathMode: Boolean(active) }, 'ai-path-mode');

        const panel = document.getElementById('ai-path-side-panel');
        if (panel) {
            panel.style.display = active ? 'flex' : 'none';
        }
    }

    let aiPathProgressTimer = null;
    let aiPathProgressRow = null;
    let aiPathProgressSteps = [];
    let aiPathProgressIndex = 0;

    function createAiPathProgressRow(text) {
        const messages = document.getElementById('messages');
        if (!messages) return null;

        const row = document.createElement('div');
        row.className = 'ai-path-progress-row';
        row.innerHTML = `
            <span class="ai-path-progress-dot" aria-hidden="true"></span>
            <span class="ai-path-progress-text">${escapeHtml(text || '')}</span>
        `;

        messages.appendChild(row);
        messages.scrollTop = messages.scrollHeight;
        return row;
    }

    function updateAiPathProgressText(text) {
        const el = document.getElementById('ai-path-progress');
        if (el) {
            el.textContent = text || '';
        }

        if (!aiPathProgressRow) return;
        const label = aiPathProgressRow.querySelector('.ai-path-progress-text');
        if (label) {
            label.textContent = text || '';
        }
    }

    function startAiPathProgress(steps) {
        if (aiPathProgressTimer) {
            clearInterval(aiPathProgressTimer);
        }

        aiPathProgressSteps = Array.isArray(steps) ? steps.filter(Boolean) : [];
        aiPathProgressIndex = 0;
        aiPathProgressRow = createAiPathProgressRow(aiPathProgressSteps[0] || '正在思考');
        updateAiPathProgressText(aiPathProgressSteps[0] || '正在思考');

        if (aiPathProgressSteps.length <= 1) return;

        aiPathProgressTimer = setInterval(() => {
            if (aiPathProgressIndex + 1 >= aiPathProgressSteps.length) return;
            aiPathProgressIndex += 1;
            updateAiPathProgressText(aiPathProgressSteps[aiPathProgressIndex]);
        }, 1800);
    }

    function finishAiPathProgress(text, status = 'done') {
        if (aiPathProgressTimer) {
            clearInterval(aiPathProgressTimer);
            aiPathProgressTimer = null;
        }

        updateAiPathProgressText(text || '已完成');

        if (!aiPathProgressRow) return;
        aiPathProgressRow.classList.remove('is-done', 'is-error');
        aiPathProgressRow.classList.add(status === 'error' ? 'is-error' : 'is-done');
    }

    async function submitAiPathReplan(goalText) {
        const text = String(goalText || '').trim();
        if (!text) return;

        appendUser(text);
        app.setStatusBanner?.('正在理解新的学习方向', 'processing');
        startAiPathProgress([
            '正在解析新目标',
            '正在搜索知识图谱',
            '知识图谱搜索完成',
            '正在组织输出',
        ]);

        try {
            const data = await postJson('/api/ai-path/chat', {
                thread_id: state.currentThreadId || makeThreadId(),
                message: text,
                choice: 'restart_keep_progress',
            });

            renderAiAgentTurn(data);
            app.setStatusBanner?.('已收到新的学习方向', 'awaiting');
            finishAiPathProgress('组织输出完成');
        } catch (error) {
            appendAgent(`更改学习路径失败：${error.message}`);
            app.setStatusBanner?.('更改学习路径失败', 'danger');
            finishAiPathProgress('更改路径失败', 'error');
        }

        app.applyPrimaryActionState?.();
    }

    function renderCourseChoice() {
        setAiMode(false);
        clearMessages();

        const messages = document.getElementById('messages');
        if (!messages) return;

        const card = document.createElement('section');
        card.className = 'course-choice-card';
        card.innerHTML = `
            <div class="course-choice-kicker">NEW LEARNING SESSION</div>
            <h2>请选择本次学习方向</h2>
            <p>自动控制原理会进入原来的伴学流程；人工智能会进入新的“对话式学习路径规划”流程。</p>
            <div class="course-choice-actions">
                <button type="button" id="course-choice-auto">
                    <strong>自动控制原理</strong>
                    <span>沿用原来的知识图谱伴学流程</span>
                </button>
                <button type="button" id="course-choice-ai">
                    <strong>人工智能</strong>
                    <span>通过多轮问答生成定制化学习路径</span>
                </button>
            </div>
        `;

        messages.appendChild(card);

        document.getElementById('course-choice-auto')?.addEventListener('click', () => {
            setAiMode(false);
            if (originalStartNewSession) originalStartNewSession();
            app.setStatusBanner?.('已选择自动控制原理', 'success');
        });

        document.getElementById('course-choice-ai')?.addEventListener('click', () => {
            startAiPathDialogue();
        });

        app.setStatusBanner?.('请选择学习方向', 'awaiting');
    }

    async function startAiPathDialogue() {
        setAiMode(true);
        clearMessages();
        ensureAiPathSidePanel();

        state.currentThreadId = makeThreadId();
        state.currentTopic = '人工智能学习路径';
        state.graphTopicHint = '人工智能学习路径';
        state.currentGraphNode = '';
        state.currentGraphNodeId = '';
        state.userKnowledgeGraph = {};

        app.updateSidebarState?.();
        app.setChatInputPlaceholder?.('例如：我想学习自动驾驶目标检测 / 机器人强化学习 / 大语言模型RAG');
        app.setStatusBanner?.('AI路径规划模式：请描述你想学习的方向', 'awaiting');
        updateAiPathProgressText('等待输入学习方向');

        try {
            startAiPathProgress([
                '正在初始化 AI 路径',
                '正在准备对话',
            ]);
            const data = await postJson('/api/ai-path/chat', {
                thread_id: state.currentThreadId,
                message: '',
            });

            renderAiAgentTurn(data);
            finishAiPathProgress('对话已就绪');
        } catch (error) {
            appendAgent(`AI路径规划启动失败：${error.message}`);
            app.setStatusBanner?.('AI路径规划启动失败', 'danger');
            finishAiPathProgress('启动失败', 'error');
        }
    }

    async function advanceAiPathNode() {
        app.setStatusBanner?.('正在进入下一个节点', 'processing');
        startAiPathProgress([
            '正在更新学习进度',
            '学习进度更新完成',
            '正在定位下一个节点',
            '下一个节点已定位',
            '正在组织输出',
        ]);

        try {
            const data = await postJson('/api/ai-path/next', {
                thread_id: state.currentThreadId,
            });

            appendAgent(data.message || '已进入下一个节点。');
            renderOptions(data.options || []);

            if (data.path?.length) {
                updateAiPathSidePanel(data.path);
            }

            if (data.current_node) {
                app.patchState?.({
                    currentGraphNodeId: data.current_node,
                }, 'ai-path-next');
            }

            if (data.type === 'complete') {
                app.setStatusBanner?.('AI学习路径已完成', 'success');
                finishAiPathProgress('路径已完成');
            } else {
                app.setStatusBanner?.('已进入下一个节点', 'success');
                finishAiPathProgress('组织输出完成');
            }
        } catch (error) {
            appendAgent(`进入下一个节点失败：${error.message}`);
            app.setStatusBanner?.('进入下一个节点失败', 'danger');
            finishAiPathProgress('进入下一节点失败', 'error');
        }
    }

    function renderOptions(options = []) {
        if (!Array.isArray(options) || !options.length) return;

        const messages = document.getElementById('messages');
        if (!messages) return;

        const row = document.createElement('div');
        row.className = 'ai-path-option-row';

        row.innerHTML = options.map(opt => `
            <button type="button" data-ai-choice="${escapeHtml(opt)}">${escapeHtml(opt)}</button>
        `).join('');

        messages.appendChild(row);
        messages.scrollTop = messages.scrollHeight;

        row.querySelectorAll('[data-ai-choice]').forEach(btn => {
            btn.addEventListener('click', () => {
                const choice = btn.dataset.aiChoice || '';
                if (choice === '我懂了，进入下一个节点') {
                    advanceAiPathNode();
                } else {
                    submitAiPathMessage(choice, true);
                }
            });
        });
    }

    function renderAiAgentTurn(data) {
        appendAgent(data.message || '我已经收到。');

        if (data.candidates?.length) {
            renderCandidateMiniList(data.candidates);
        }

        if (data.type === 'plan') {
            renderAiPathPlan(data);
            applyPlanToGraph(data);
        }

        renderOptions(data.options || []);
    }

    function renderCandidateMiniList(candidates) {
        const messages = document.getElementById('messages');
        if (!messages) return;

        const card = document.createElement('section');
        card.className = 'ai-candidate-mini-card';

        card.innerHTML = `
            <div class="ai-card-title">当前候选目标节点</div>
            <div class="ai-mini-list">
                ${candidates.slice(0, 8).map(item => `
                    <button type="button" class="ai-mini-item ai-mini-item--clickable" data-ai-choice="${escapeHtml(item.name)}">
                        <strong>${escapeHtml(item.name)}</strong>
                        <span>${escapeHtml(item.node_id)} · ${escapeHtml(item.importance_level || '')}</span>
                    </button>
                `).join('')}
            </div>
        `;

        messages.appendChild(card);
        messages.scrollTop = messages.scrollHeight;

        card.querySelectorAll('[data-ai-choice]').forEach(btn => {
            btn.addEventListener('click', () => {
                submitAiPathMessage(btn.dataset.aiChoice || '', true);
            });
        });
    }

    function renderAiPathPlan(data) {
        const path = data.path || [];
        updateAiPathSidePanel(path);
        const messages = document.getElementById('messages');
        if (!messages) return;

        const card = document.createElement('section');
        card.className = 'ai-path-plan-card';

        if (!path.length) {
            card.innerHTML = `
                <div class="ai-card-title">学习路径</div>
                <p>暂时没有生成可用路径。</p>
            `;
            messages.appendChild(card);
            return;
        }

        card.innerHTML = `
            <div class="ai-card-title">定制化学习路径</div>
            <p class="ai-path-plan-summary">
                共 ${path.length} 个待学习节点。系统已根据 AI 学生状态跳过已掌握节点，并保留目标相关前置知识。
            </p>
            <div class="ai-path-roadmap-chat">
                ${path.map((node, index) => `
                    <button
                        type="button"
                        class="ai-path-step ${node.status === 'current' ? 'is-current' : ''} ${node.status === 'goal' ? 'is-goal' : ''} ${node.status === 'mastered' ? 'is-mastered' : ''}"
                        data-node-id="${escapeHtml(node.node_id)}"
                    >
                        <span class="ai-path-step-index">${index + 1}</span>
                        <span class="ai-path-step-main">
                            <strong>${escapeHtml(node.name)}</strong>
                            <small>${escapeHtml(node.node_id)} · ${escapeHtml(node.reason || '')}</small>
                        </span>
                        <span class="ai-path-step-status">
                            ${node.status === 'current' ? '当前' : node.status === 'goal' ? '目标' : node.status === 'mastered' ? '已学' : '待学'}
                        </span>
                    </button>
                `).join('')}
            </div>
            <div id="ai-path-node-detail" class="ai-path-node-detail"></div>

            <div class="ai-path-learn-actions">
                <button type="button" class="ai-path-start-btn" id="ai-path-start-learning">
                    开始学习当前节点
                </button>
</div>
        `;

        messages.appendChild(card);
        messages.scrollTop = messages.scrollHeight;

        card.querySelectorAll('[data-node-id]').forEach(btn => {
            btn.addEventListener('click', () => {
                loadNodeDetail(btn.dataset.nodeId);
            });
        });

        if (path[0]) renderNodeDetail(path[0]);
        document.getElementById('ai-path-start-learning')?.addEventListener('click', () => {
            startLearningCurrentNode();
        });
    }

    function renderAiPathReplanCard() {
        const messages = document.getElementById('messages');
        if (!messages) return;

        const card = document.createElement('section');
        card.className = 'ai-path-replan-card';
        card.innerHTML = `
            <div class="ai-path-replan-title">更改学习方向</div>
            <div class="ai-path-replan-copy">填写你想调整到的新方向，我会只更新未学部分的路径。</div>
            <div class="ai-path-replan-form">
                <input type="text" class="ai-path-replan-input" placeholder="例如：机器人强化学习 / 大模型RAG" />
                <button type="button" class="ai-path-replan-submit">确认更改</button>
            </div>
            <div class="ai-path-replan-history"></div>
        `;

        messages.appendChild(card);
        messages.scrollTop = messages.scrollHeight;

        const input = card.querySelector('.ai-path-replan-input');
        const submit = card.querySelector('.ai-path-replan-submit');
        const history = card.querySelector('.ai-path-replan-history');

        const submitValue = () => {
            const value = String(input?.value || '').trim();
            if (!value) return;
            const row = document.createElement('div');
            row.className = 'ai-path-replan-history-item';
            row.textContent = `已提交：${value}`;
            history?.appendChild(row);
            submitAiPathReplan(value);
            if (input) input.value = '';
        };

        submit?.addEventListener('click', submitValue);
        input?.addEventListener('keydown', (event) => {
            if (event.key !== 'Enter') return;
            event.preventDefault();
            submitValue();
        });
    }
    async function startLearningCurrentNode() {
        app.setStatusBanner?.('正在生成当前节点讲解', 'processing');
        startAiPathProgress([
            '正在检索当前节点重点知识',
            '当前节点重点知识检索完成',
            '正在组织输出',
        ]);

        try {
            const data = await postJson('/api/ai-path/teach', {
                thread_id: state.currentThreadId,
            });

            appendAgent(data.message || '已进入当前节点学习。');
            renderOptions(data.options || []);
            app.setStatusBanner?.('正在学习当前节点', 'success');
            finishAiPathProgress('组织输出完成');
        } catch (error) {
            appendAgent(`当前节点讲解失败：${error.message}`);
            app.setStatusBanner?.('当前节点讲解失败', 'danger');
            finishAiPathProgress('讲解失败', 'error');
        }
    }
    function applyPlanToGraph(data) {
        const path = data.path || [];
        const first = path[0];
        const targetNames = data.summary?.target_names || [];

        app.patchState?.({
            currentTopic: targetNames.length ? targetNames.join('、') : '人工智能学习路径',
            graphTopicHint: targetNames.length ? targetNames.join('、') : '人工智能学习路径',
            currentGraphNode: first?.name || '',
            currentGraphNodeId: first?.node_id || '',
            userKnowledgeGraph: data.userKnowledgeGraph || {},
        }, 'ai-path-plan');

        app.updateSidebarState?.();

        // 注意：
        // 这里不要调用 app.renderKnowledgeGraphVisualCard()
        // 也不要调用 app.syncKnowledgeGraphVisualState()
        // 那套 iframe 仍然保留给自动控制原理使用。
        // AI 路径的可视化由 renderAiPathPlan(data) 根据 data.path 自己渲染。
    }
    function ensureAiPathSidePanel() {
        let panel = document.getElementById('ai-path-side-panel');
        if (panel) return panel;

        panel = document.createElement('aside');
        panel.id = 'ai-path-side-panel';
        panel.className = 'ai-path-side-panel';
        panel.innerHTML = `
            <div class="ai-path-side-head">
                <div>
                    <div class="ai-path-side-kicker">AI PATH</div>
                    <strong>路径总览</strong>
                    <div class="ai-path-progress" id="ai-path-progress">等待输入学习方向</div>
                </div>
                <div class="ai-path-side-actions">
                    <button type="button" id="ai-path-replan-btn">更改学习路径</button>
                    <button type="button" id="ai-path-side-close">收起</button>
                </div>
            </div>
            <div id="ai-path-side-body" class="ai-path-side-body">
                <div class="ai-muted">生成路径后这里会显示当前 AI 学习主线。</div>
            </div>
        `;

        const container = document.querySelector('.container');
        if (container) {
            container.appendChild(panel);
        } else {
            document.body.appendChild(panel);
        }

        document.getElementById('ai-path-side-close')?.addEventListener('click', () => {
            panel.classList.toggle('is-collapsed');
            const btn = document.getElementById('ai-path-side-close');
            if (btn) btn.textContent = panel.classList.contains('is-collapsed') ? '展开' : '收起';
        });

        const replanBtn = document.getElementById('ai-path-replan-btn');
        replanBtn?.addEventListener('click', () => {
            renderAiPathReplanCard();
        });

        return panel;
    }

    function updateAiPathSidePanel(path = []) {
        const panel = ensureAiPathSidePanel();
        const body = document.getElementById('ai-path-side-body');
        if (!body) return;

        if (!path.length) {
            body.innerHTML = `<div class="ai-muted">生成路径后这里会显示当前 AI 学习主线。</div>`;
            return;
        }

        body.innerHTML = `
            <div class="ai-path-side-list">
                ${path.map((node, index) => `
                    <button
                        type="button"
                        class="ai-path-side-node ${node.status === 'current' ? 'is-current' : ''} ${node.status === 'goal' ? 'is-goal' : ''} ${node.status === 'mastered' ? 'is-mastered' : ''}"
                        data-node-id="${escapeHtml(node.node_id)}"
                    >
                        <span>${index + 1}</span>
                        <div>
                            <strong>${escapeHtml(node.name)}</strong>
                            <small>${escapeHtml(node.node_id)} · ${
                                node.status === 'current' ? '当前'
                                : node.status === 'goal' ? '目标'
                                : node.status === 'mastered' ? '已学'
                                : '待学'
                            }</small>
                        </div>
                    </button>
                `).join('')}
            </div>
        `;

        body.querySelectorAll('[data-node-id]').forEach(btn => {
            btn.addEventListener('click', () => {
                loadNodeDetail(btn.dataset.nodeId);
            });
        });

        panel.classList.add('is-visible');
    }

    async function loadNodeDetail(nodeId) {
        if (!nodeId) return;

        try {
            const data = await fetch(`/api/ai-path/node/${encodeURIComponent(nodeId)}`)
                .then(r => r.json());

            if (data.status !== 'success') {
                throw new Error(data.message || '节点不存在');
            }

            renderNodeDetail(data.node);
        } catch (error) {
            const box = document.getElementById('ai-path-node-detail');
            if (box) {
                box.innerHTML = `<p>节点详情加载失败：${escapeHtml(error.message)}</p>`;
            }
        }
    }

    function renderNodeDetail(node) {
        const box = document.getElementById('ai-path-node-detail');
        if (!box || !node) return;

        const list = arr => Array.isArray(arr) && arr.length
            ? `<ul>${arr.slice(0, 6).map(x => `<li>${escapeHtml(x)}</li>`).join('')}</ul>`
            : `<p class="ai-muted">暂无</p>`;

        box.innerHTML = `
            <div class="ai-detail-title">${escapeHtml(node.name)}</div>
            <div class="ai-detail-meta">
                <span>${escapeHtml(node.node_id)}</span>
                <span>${escapeHtml(node.importance_level || '')}</span>
                <span>掌握阈值 ${escapeHtml(node.mastery_threshold)}</span>
            </div>
            <p>${escapeHtml(node.summary || '')}</p>
            <h4>老师风格讲解</h4>
            <p>${escapeHtml(node.explanation_teacher_style || '')}</p>
            <h4>学习要点</h4>
            ${list(node.key_points)}
            <h4>典型例子</h4>
            ${list(node.examples)}
        `;
    }

    async function submitAiPathMessage(text, fromChoice = false) {
        const input = document.getElementById('chat-input');
        const message = String(text || input?.value || '').trim();

        if (!message) return;

        if (input && !fromChoice) {
            input.value = '';
        }

        appendUser(message);
        app.setStatusBanner?.('正在理解你的学习目标', 'processing');
        startAiPathProgress([
            '正在解析学习目标',
            '正在搜索知识图谱',
            '知识图谱搜索完成',
            '正在组织输出',
        ]);

        try {
            const data = await postJson('/api/ai-path/chat', {
                thread_id: state.currentThreadId || makeThreadId(),
                message,
                choice: fromChoice ? message : '',
            });

            renderAiAgentTurn(data);

            if (data.type === 'plan') {
                finishAiPathProgress('组织输出完成');
            } else {
                finishAiPathProgress('等待你确认方向');
            }

            app.setStatusBanner?.(
                data.type === 'plan' ? 'AI学习路径已生成' : '等待你继续补充',
                data.type === 'plan' ? 'success' : 'awaiting'
            );
        } catch (error) {
            appendAgent(`AI路径规划失败：${error.message}`);
            app.setStatusBanner?.('AI路径规划失败', 'danger');
            finishAiPathProgress('路径规划失败', 'error');
        }

        app.applyPrimaryActionState?.();
    }

    app.startNewSession = function patchedStartNewSession() {
        renderCourseChoice();
    };

    app.handleSend = async function patchedHandleSend() {
        if (state.aiPathMode) {
            await submitAiPathMessage();
            return;
        }

        if (originalHandleSend) {
            return originalHandleSend();
        }
    };

    app.openAiPathMode = startAiPathDialogue;
    app.renderCourseChoice = renderCourseChoice;

    window.startNewSession = () => app.startNewSession();
    window.handleSend = () => app.handleSend();

    document.addEventListener('DOMContentLoaded', () => {
        const url = new URL(window.location.href);

        if (url.searchParams.get('mode') === 'ai_path' || url.hash === '#ai-path') {
            startAiPathDialogue();
        }
    });
})();
