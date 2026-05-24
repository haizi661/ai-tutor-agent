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
            panel.style.display = active ? 'block' : 'none';
        }
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

        try {
            const data = await postJson('/api/ai-path/chat', {
                thread_id: state.currentThreadId,
                message: '',
            });

            renderAiAgentTurn(data);
        } catch (error) {
            appendAgent(`AI路径规划启动失败：${error.message}`);
            app.setStatusBanner?.('AI路径规划启动失败', 'danger');
        }
    }

    async function advanceAiPathNode() {
        app.setStatusBanner?.('正在进入下一个节点', 'processing');
    
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
            } else {
                app.setStatusBanner?.('已进入下一个节点', 'success');
            }
        } catch (error) {
            appendAgent(`进入下一个节点失败：${error.message}`);
            app.setStatusBanner?.('进入下一个节点失败', 'danger');
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
                        class="ai-path-step ${node.status === 'current' ? 'is-current' : ''} ${node.status === 'goal' ? 'is-goal' : ''}"
                        data-node-id="${escapeHtml(node.node_id)}"
                    >
                        <span class="ai-path-step-index">${index + 1}</span>
                        <span class="ai-path-step-main">
                            <strong>${escapeHtml(node.name)}</strong>
                            <small>${escapeHtml(node.node_id)} · ${escapeHtml(node.reason || '')}</small>
                        </span>
                        <span class="ai-path-step-status">
                            ${node.status === 'current' ? '当前' : node.status === 'goal' ? '目标' : '待学'}
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
    async function startLearningCurrentNode() {
        app.setStatusBanner?.('正在生成当前节点讲解', 'processing');
    
        try {
            const data = await postJson('/api/ai-path/teach', {
                thread_id: state.currentThreadId,
            });
    
            appendAgent(data.message || '已进入当前节点学习。');
            renderOptions(data.options || []);
            app.setStatusBanner?.('正在学习当前节点', 'success');
        } catch (error) {
            appendAgent(`当前节点讲解失败：${error.message}`);
            app.setStatusBanner?.('当前节点讲解失败', 'danger');
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
                </div>
                <button type="button" id="ai-path-side-close">收起</button>
            </div>
            <div id="ai-path-side-body" class="ai-path-side-body">
                <div class="ai-muted">生成路径后这里会显示当前 AI 学习主线。</div>
            </div>
        `;
    
        document.body.appendChild(panel);
    
        document.getElementById('ai-path-side-close')?.addEventListener('click', () => {
            panel.classList.toggle('is-collapsed');
            const btn = document.getElementById('ai-path-side-close');
            if (btn) btn.textContent = panel.classList.contains('is-collapsed') ? '展开' : '收起';
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

        try {
            const data = await postJson('/api/ai-path/chat', {
                thread_id: state.currentThreadId || makeThreadId(),
                message,
                choice: fromChoice ? message : '',
            });

            renderAiAgentTurn(data);

            app.setStatusBanner?.(
                data.type === 'plan' ? 'AI学习路径已生成' : '等待你继续补充',
                data.type === 'plan' ? 'success' : 'awaiting'
            );
        } catch (error) {
            appendAgent(`AI路径规划失败：${error.message}`);
            app.setStatusBanner?.('AI路径规划失败', 'danger');
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