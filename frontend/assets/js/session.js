(() => {
    const app = window.AITutorApp;
    const state = app.state;

    app.pauseCurrentSession = function pauseCurrentSession() {
        if (!state.currentThreadId) {
            alert('当前没有可暂停的会话。');
            return;
        }
        if (state.eventSource) {
            state.eventSource.close();
            state.eventSource = null;
        }
        document.getElementById('status-banner').innerText = '当前会话已暂停，可稍后继续';
        app.appendSystemMessage('你已暂停当前会话。系统不会自动继续；你可以稍后回到该会话，再根据上次上下文继续输入。');
    };

    app.submitTopicConfirmation = async function submitTopicConfirmation(confirmed) {
        const payload = {
            thread_id: state.currentThreadId,
            confirmed,
            topic: confirmed ? state.pendingTopicConfirmation : (document.getElementById('topic-edit-input')?.value || '').trim(),
        };
        if (!confirmed && !payload.topic) {
            alert('请输入新的学习主题。');
            return;
        }
        const res = await fetch('/api/confirm_topic', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        const data = await res.json();
        if (!res.ok || data.status === 'error') {
            alert(data.detail || data.message || '主题确认失败');
            return;
        }
        document.querySelector('.topic-confirm-card')?.remove();
        app.connectSSE();
    };

    app.handleSend = async function handleSend() {
        const input = document.getElementById('chat-input');
        const text = input.value.trim();
        if (!text) return;
        input.value = '';
        app.appendMessage('user', text);

        if (state.isAwaitingInput) {
            state.isAwaitingInput = false;
            state.currentAgentMsgEl = null;
            state.currentTextBuffer = '';
            app.showTyping();
            await fetch('/api/answer', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ thread_id: state.currentThreadId, answer: text }),
            });
            return;
        }

        if (!state.currentThreadId) state.currentThreadId = app.makeThreadId();
        app.showTyping();
        await fetch('/api/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ thread_id: state.currentThreadId, topic: text }),
        });
        app.connectSSE();
    };

    app.connectSSE = function connectSSE() {
        if (state.eventSource) state.eventSource.close();
        state.currentAgentMsgEl = null;
        state.currentTextBuffer = '';
        state.eventSource = new EventSource(`/api/stream?thread_id=${state.currentThreadId}`);

        state.eventSource.addEventListener('node.start', e => {
            const data = JSON.parse(e.data);
            document.getElementById('status-banner').innerText = data.message || `正在运行: ${data.source}...`;
            app.clearTypingIndicator();
            app.appendSystemMessage(`进行中：${data.message || data.source}`);
        });

        state.eventSource.addEventListener('node.complete', e => {
            const data = JSON.parse(e.data);
            if (data.message) app.appendSystemMessage(`完成：${data.message}`);
        });

        state.eventSource.addEventListener('intent.detected', e => {
            const data = JSON.parse(e.data);
            if (data.message) app.appendSystemMessage(data.message);
        });

        state.eventSource.addEventListener('node.stream', e => {
            const data = JSON.parse(e.data);
            if (data.data?.text) {
                if (!state.currentAgentMsgEl) app.appendMessage('agent', '');
                state.currentTextBuffer += data.data.text;
                state.currentAgentMsgEl.innerHTML = marked.parse(state.currentTextBuffer);
                app.renderMath(state.currentAgentMsgEl);
                document.getElementById('messages').scrollTop = document.getElementById('messages').scrollHeight;
            }
        });

        state.eventSource.addEventListener('session.info', e => {
            const data = JSON.parse(e.data);
            app.appendSystemMessage(data.message || '会话状态已更新');
        });

        state.eventSource.addEventListener('session.warning', e => {
            const data = JSON.parse(e.data);
            app.appendSystemMessage(`警告：${data.message || '系统遇到异常'}`);
        });

        state.eventSource.addEventListener('route.decision', e => {
            const data = JSON.parse(e.data);
            const decision = data.data?.decision || 'unknown';
            const score = data.data?.score;
            app.appendSystemMessage(`路由决策：${decision}${score !== undefined ? `（当前得分 ${score}）` : ''}`);
        });

        state.eventSource.addEventListener('assessment.form_ready', e => {
            const data = JSON.parse(e.data);
            app.appendSystemMessage(data.message || '学前测评已生成，请完成作答。');
            app.renderAssessmentForm(data.data.questions);
        });

        state.eventSource.addEventListener('topic.confirmation_needed', e => {
            const data = JSON.parse(e.data);
            app.appendSystemMessage(data.message || '请确认学习主题。');
            app.renderTopicConfirmation(data.data.proposed_topic);
            document.getElementById('status-banner').innerText = '等待确认学习主题';
        });

        state.eventSource.addEventListener('profile.radar_data', e => {
            const data = JSON.parse(e.data).data;
            app.appendSystemMessage('能力画像已生成，右侧面板已更新。');
            app.showRadar(data);
        });

        state.eventSource.addEventListener('session.awaiting_input', e => {
            state.isAwaitingInput = true;
            const data = JSON.parse(e.data);
            app.clearTypingIndicator();
            state.currentAgentMsgEl = null;
            state.currentTextBuffer = '';
            app.appendSystemMessage(data.message);
            document.getElementById('status-banner').innerText = '等待你继续输入';
        });

        state.eventSource.addEventListener('session.end', () => {
            app.clearTypingIndicator();
            document.getElementById('status-banner').innerText = '系统就绪';
            app.appendSystemMessage('本轮处理已结束。若页面出现主题确认卡片或测评表单，请继续完成该步骤；如果没有出现新的交互控件，直接发送下一条消息即可。');
            state.eventSource.close();
            state.eventSource = null;
            app.fetchHistory();
        });

        state.eventSource.addEventListener('session.error', e => {
            const data = JSON.parse(e.data);
            app.clearTypingIndicator();
            document.getElementById('status-banner').innerText = `❌ 错误: ${data.message}`;
            app.appendMessage('agent', `⚠️ 系统遇到错误: ${data.message}`);
            state.eventSource.close();
            state.eventSource = null;
        });
    };
})();
