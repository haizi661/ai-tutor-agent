(() => {
    const app = window.AITutorApp;
    const state = app.state;
    const PRE_TOPIC_FLOW_STATUSES = new Set(['greeting', 'topic_intake', 'meta_qa', 'smalltalk']);

    app.fetchHistory = async function fetchHistory() {
        const res = await fetch('/api/history');
        const data = await res.json();
        const list = document.getElementById('history-list');
        list.innerHTML = '';
        const items = data.items || (data.threads || []).map(id => ({ thread_id: id, current_topic: '' }));
        items.forEach(entry => {
            const id = entry.thread_id;
            const label = entry.display_title || entry.current_topic || id;
            const row = document.createElement('div');
            row.className = `history-item ${id === state.currentThreadId ? 'active' : ''}`;
            row.innerHTML = `
                <span class="history-text" onclick="loadSession('${id}')">📝 ${id}</span>
                <span class="history-delete" onclick="deleteSession('${id}', event)">🗑️</span>
            `;
            row.querySelector('.history-text').textContent = `📝 ${label}`;
            list.appendChild(row);
        });
    };

    app.startNewSession = function startNewSession() {
        if (state.eventSource) state.eventSource.close();
        state.currentThreadId = app.makeThreadId();
        state.pendingTopicConfirmation = null;
        state.isAwaitingInput = false;
        document.getElementById('messages').innerHTML = '';
        app.appendMessage('agent', '已开启新会话。你想学习什么知识点？');
        document.getElementById('profile-panel').classList.add('hidden');
        app.fetchHistory();
    };

    app.deleteSession = async function deleteSession(id, event) {
        event.stopPropagation();
        if (!confirm(`确定要彻底删除会话 ${id} 的所有记录吗？`)) return;
        await fetch(`/api/history/${id}`, { method: 'DELETE' });
        if (id === state.currentThreadId) app.startNewSession();
        else app.fetchHistory();
    };

    app.loadSession = async function loadSession(id) {
        if (state.eventSource) state.eventSource.close();
        state.currentThreadId = id;
        state.isAwaitingInput = false;
        document.getElementById('messages').innerHTML = '';
        document.getElementById('profile-panel').classList.add('hidden');

        try {
            const res = await fetch(`/api/history/${id}`);
            if (!res.ok) throw new Error(`会话 ${id} 不存在`);
            const data = await res.json();
            app.restoreSessionState(data.state);
            const runtime = data.runtime || {};

            if (runtime.awaiting_input) {
                state.isAwaitingInput = true;
                document.getElementById('status-banner').innerText = '已恢复到等待你继续输入的状态';
            } else if (PRE_TOPIC_FLOW_STATUSES.has(data.state.flow_status)) {
                document.getElementById('status-banner').innerText = '已恢复历史会话，可直接继续发送下一条消息';
            } else if (data.state.flow_status === 'awaiting_topic_confirmation') {
                document.getElementById('status-banner').innerText = '等待确认学习主题';
            } else if (data.state.flow_status === 'awaiting_assessment') {
                document.getElementById('status-banner').innerText = '已恢复到学前测评阶段';
            } else {
                document.getElementById('status-banner').innerText = '已恢复历史会话，请根据当前上下文继续';
            }
        } catch (err) {
            app.appendMessage('agent', `恢复会话失败：${err.message}`);
        }
        app.fetchHistory();
    };
})();
