(() => {
    const app = window.AITutorApp;
    const state = app.state;
    const PRE_TOPIC_FLOW_STATUSES = new Set(['greeting', 'topic_intake', 'meta_qa', 'smalltalk']);
    const LAST_THREAD_STORAGE_KEY = 'ai_tutor_last_thread_id';

    function resetRuntimeView() {
        if (state.eventSource) state.eventSource.close();
        state.eventSource = null;
        state.pendingTopicConfirmation = null;
        state.pendingInterruptConfirmation = false;
        state.isAwaitingInput = false;
        state.isStreaming = false;
        app.setChatInputPlaceholder?.();
        app.clearTypingIndicator?.();
        app.finalizeAgentTurn?.();
        document.getElementById('messages').innerHTML = '';
        document.getElementById('chat-input').value = '';
        document.getElementById('profile-panel').classList.add('hidden');
    }

    app.fetchHistory = async function fetchHistory() {
        const res = await fetch('/api/history');
        const data = await res.json();
        const list = document.getElementById('history-list');
        list.innerHTML = '';
        const items = data.items || (data.threads || []).map(id => ({ thread_id: id, current_topic: '' }));

        if (!items.length) {
            const empty = document.createElement('div');
            empty.className = 'history-group';
            empty.textContent = '这里还没有学习记录';
            list.appendChild(empty);
            return;
        }

        items.forEach((entry, index) => {
            const id = entry.thread_id;
            const label = entry.display_title || entry.current_topic || id;
            const row = document.createElement('div');
            row.className = `history-item ${id === state.currentThreadId ? 'active' : ''}`;

            const textButton = document.createElement('button');
            textButton.type = 'button';
            textButton.className = 'history-text';
            textButton.textContent = label;
            textButton.setAttribute('aria-label', `恢复学习页 ${label}`);
            textButton.setAttribute('aria-posinset', String(index + 1));
            textButton.setAttribute('aria-setsize', String(items.length));
            textButton.onclick = () => app.loadSession(id);

            const deleteButton = document.createElement('button');
            deleteButton.type = 'button';
            deleteButton.className = 'history-delete';
            deleteButton.textContent = '×';
            deleteButton.setAttribute('aria-label', `删除学习页 ${label}`);
            deleteButton.onclick = event => app.deleteSession(id, event);

            row.appendChild(textButton);
            row.appendChild(deleteButton);
            list.appendChild(row);
        });
    };

    app.startNewSession = function startNewSession() {
        if (state.isVoiceListening) app.stopVoiceInput();
        resetRuntimeView();
        state.currentThreadId = app.makeThreadId();
        window.localStorage.setItem(LAST_THREAD_STORAGE_KEY, state.currentThreadId);
        app.appendMessage('agent', '新的一页已经打开。直接告诉我这次想学什么，或者在讲解里随时追问卡点。');
        app.setStatusBanner('可以从一个新主题开始；卡住时也能随时追问', 'ready');
        app.applyPrimaryActionState?.();
        app.fetchHistory();
    };

    app.deleteSession = async function deleteSession(id, event) {
        event.stopPropagation();
        if (!confirm(`确定要删掉这页学习记录吗？\n${id}`)) return;
        await fetch(`/api/history/${id}`, { method: 'DELETE' });
        if (window.localStorage.getItem(LAST_THREAD_STORAGE_KEY) === id) {
            window.localStorage.removeItem(LAST_THREAD_STORAGE_KEY);
        }
        if (id === state.currentThreadId) app.startNewSession();
        else app.fetchHistory();
    };

    app.loadSession = async function loadSession(id) {
        if (state.isVoiceListening) app.stopVoiceInput();
        resetRuntimeView();
        state.currentThreadId = id;
        window.localStorage.setItem(LAST_THREAD_STORAGE_KEY, id);

        try {
            const [res, messagesRes] = await Promise.all([
                fetch(`/api/history/${id}`),
                fetch(`/api/messages/${id}`),
            ]);
            if (!res.ok) throw new Error(`找不到这页记录：${id}`);
            const data = await res.json();

            if (messagesRes.ok) {
                const replay = await messagesRes.json();
                const items = Array.isArray(replay.items) ? replay.items : [];
                if (items.length) app.restoreMessageTimeline(items, data.state);
                else app.restoreSessionState(data.state);
            } else {
                app.restoreSessionState(data.state);
            }

            const runtime = data.runtime || {};

            if (runtime.awaiting_input) {
                state.isAwaitingInput = true;
                app.setChatInputPlaceholder?.('输入你的解答，或先追问一个临时问题…');
                app.setStatusBanner('已经回到等你补充的那一步', 'awaiting');
            } else if (runtime.is_running) {
                app.setChatInputPlaceholder?.();
                app.setStatusBanner('这页还在运行，我正在把实时进度接回来', 'processing');
                app.connectSSE?.();
            } else if (PRE_TOPIC_FLOW_STATUSES.has(data.state.flow_status)) {
                app.setChatInputPlaceholder?.();
                app.setStatusBanner('已经回到这页内容了，你可以直接继续', 'info');
            } else if (data.state.flow_status === 'awaiting_topic_confirmation') {
                app.setChatInputPlaceholder?.();
                app.setStatusBanner('这一步在等你点头确认主题', 'awaiting');
            } else if (data.state.flow_status === 'awaiting_interrupt_confirmation') {
                app.setChatInputPlaceholder?.();
                app.setStatusBanner('这个卡点已经讲清楚了，等你决定要不要回主线', 'awaiting');
            } else if (data.state.flow_status === 'awaiting_assessment') {
                app.setChatInputPlaceholder?.();
                app.setStatusBanner('这一步在等你完成开始前的小测', 'awaiting');
            } else {
                app.setChatInputPlaceholder?.();
                app.setStatusBanner('已经回到之前的位置了，顺着当前上下文继续就行', 'info');
            }
        } catch (err) {
            app.appendMessage('agent', `这页没有恢复成功：${err.message}`);
            app.setStatusBanner(`恢复失败：${err.message}`, 'danger');
        }
        app.applyPrimaryActionState?.();
        app.fetchHistory();
    };

    app.restoreLastSessionIfAny = async function restoreLastSessionIfAny() {
        const threadId = window.localStorage.getItem(LAST_THREAD_STORAGE_KEY);
        if (!threadId) return;
        await app.loadSession(threadId);
    };
})();
