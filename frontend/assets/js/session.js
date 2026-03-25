(() => {
    const app = window.AITutorApp;
    const state = app.state;

    function closeEventSource() {
        if (!state.eventSource) return;
        state.eventSource.close();
        state.eventSource = null;
    }

    function safelyParseEventData(raw) {
        try {
            return JSON.parse(raw);
        } catch (_error) {
            return {};
        }
    }

    function appendMeta(kind, text, tone = 'info', { createIfStreaming = true, fallbackToSystem = true } = {}) {
        if (!text) return false;

        const hasActiveTurn = Boolean(state.currentAgentTurnEl);
        if (!hasActiveTurn && createIfStreaming && state.isStreaming) {
            app.ensureAgentTurn?.();
        }

        const didAppend = kind === 'thinking'
            ? app.addThinkingStep?.(text, tone)
            : app.addNote?.(text, tone);

        if (didAppend) return true;
        if (!fallbackToSystem) return false;

        app.finalizeAgentTurn?.();
        app.appendSystemMessage(text, tone);
        return true;
    }

    function appendThinking(text, tone = 'info', source = 'progress') {
        if (text) app.recordTurnProgress?.(text, source);
        return appendMeta('thinking', text, tone);
    }

    function appendNote(text, tone = 'info', options) {
        return appendMeta('note', text, tone, options);
    }

    function startStreamingTurn(statusMessage) {
        state.isStreaming = true;
        state.isAwaitingInput = false;
        app.finalizeAgentTurn?.();
        app.startAgentTurnLifecycle?.();
        app.showTyping?.();
        app.setStatusBanner(statusMessage, 'processing');
        app.applyPrimaryActionState?.();
    }

    function consumeVisibleTurn(text, tone = 'info', options = {}) {
        if (!text) return false;
        app.appendVisibleSystemTurn?.(text, tone, options);
        app.clearTypingIndicator?.();
        return true;
    }

    function summarizeAssessmentResult(data) {
        const total = data.total_score ?? '—';
        const logic = data.logic_score ?? '—';
        const concept = data.concept_score ?? '—';
        const feedback = data.feedback || '这轮评估已完成，我会据此调整后续讲解。';
        const rubric = Array.isArray(data.rubric_feedback) ? data.rubric_feedback : [];
        const hintLine = data.needs_hint ? '建议先看一条思路提示，再尝试重答。' : '';
        return [
            '### 这轮评估结果',
            '',
            `- 总分：**${total}**`,
            `- 逻辑：**${logic}**`,
            `- 概念：**${concept}**`,
            '',
            `简要诊断：${feedback}`,
            ...(rubric.length ? ['', '量表依据：', ...rubric.map(item => `- ${item}`)] : []),
            ...(hintLine ? ['', `提示：${hintLine}`] : []),
        ].join('\n');
    }

    function finalizeStreamState(statusMessage, tone = 'ready') {
        state.isStreaming = false;
        app.setStatusBanner(statusMessage, tone);
        closeEventSource();
        app.finalizeAgentTurn?.();
        app.applyPrimaryActionState?.();
    }

    app.pauseCurrentSession = function pauseCurrentSession() {
        if (state.isVoiceListening) app.stopVoiceInput();
        if (!state.currentThreadId) {
            alert('现在还没有可以暂停的学习页。');
            return;
        }
        closeEventSource();
        state.isStreaming = false;
        app.finalizeAgentTurn?.();
        app.setStatusBanner('这一页先停在这里，稍后可以继续', 'paused');
        app.appendSystemMessage('我先替你把这一页停住了。之后回到这个会话时，可以顺着刚才的位置继续。', 'warning');
        app.applyPrimaryActionState?.();
    };

    app.submitTopicConfirmation = async function submitTopicConfirmation(confirmed) {
        const payload = {
            thread_id: state.currentThreadId,
            confirmed,
            topic: confirmed ? state.pendingTopicConfirmation : (document.getElementById('topic-edit-input')?.value || '').trim(),
        };
        if (!confirmed && !payload.topic) {
            alert('先写下你想改成的主题。');
            return;
        }
        app.setStatusBanner('我在记录这次主题确认', 'processing');
        const res = await fetch('/api/confirm_topic', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        const data = await res.json();
        if (!res.ok || data.status === 'error') {
            app.setStatusBanner(data.detail || data.message || '主题确认没有保存成功', 'danger');
            alert(data.detail || data.message || '主题确认没有保存成功');
            return;
        }
        document.querySelector('.topic-confirm-card')?.remove();
        startStreamingTurn('我在接上主题确认后的流程');
        app.connectSSE();
    };

    app.handleSend = async function handleSend() {
        if (state.isVoiceListening) app.stopVoiceInput();
        const input = document.getElementById('chat-input');
        const text = input.value.trim();
        if (!text) return;
        input.value = '';
        state.voiceInputBase = '';
        state.voiceFinalTranscript = '';
        state.voiceInterimTranscript = '';
        app.appendMessage('user', text);

        if (state.isAwaitingInput) {
            startStreamingTurn('收到你的补充了，我继续往下整理');
            await fetch('/api/answer', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ thread_id: state.currentThreadId, answer: text }),
            });
            app.connectSSE();
            return;
        }

        if (!state.currentThreadId) state.currentThreadId = app.makeThreadId();
        startStreamingTurn('先帮你铺开这一页的学习流程');
        await fetch('/api/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ thread_id: state.currentThreadId, topic: text }),
        });
        app.connectSSE();
    };

    app.connectSSE = function connectSSE() {
        closeEventSource();
        if (!state.currentThreadId) return;
        if (!state.isStreaming) {
            startStreamingTurn('我在接上这页内容，请稍等一下');
        } else if (!state.currentTurnId) {
            app.startAgentTurnLifecycle?.();
            app.showTyping?.();
        }
        app.setStatusBanner('我在接上这页内容，请稍等一下', 'processing');
        state.eventSource = new EventSource(`/api/stream?thread_id=${state.currentThreadId}`);
        app.applyPrimaryActionState?.();

        state.eventSource.addEventListener('node.start', e => {
            const data = safelyParseEventData(e.data);
            const message = data.message || '正在把这一小步接好。';
            app.setStatusBanner(message, 'processing');
            appendThinking(message, 'info', 'node.start');
            
            // Re-show typing indicator to keep UI alive during long node executions (like evaluator or assessment generation)
            app.showTyping?.();
        });

        state.eventSource.addEventListener('node.complete', e => {
            const data = safelyParseEventData(e.data);
            appendThinking(data.message || '这一小步已经接好。', 'success', 'node.complete');
            app.clearTypingIndicator?.();
        });

        state.eventSource.addEventListener('intent.detected', e => {
            const data = safelyParseEventData(e.data);
            appendThinking(data.message || '我已经识别到你当前这一步的意图。', 'info', 'intent.detected');
        });

        state.eventSource.addEventListener('node.stream', e => {
            const data = safelyParseEventData(e.data);
            const chunk = data.data?.text;
            if (!chunk) return;

            app.clearTypingIndicator?.();
            app.ensureAgentTurn?.();
            app.markTurnVisible?.();
            app.clearVisibilityFallback?.({ resetCounter: false });
            state.currentTextBuffer += chunk;
            app.throttledRender?.();
            app.scrollMessagesToBottom?.();
        });

        state.eventSource.addEventListener('session.info', e => {
            const data = safelyParseEventData(e.data);
            appendNote(data.message || '这页状态有了新的进展。', 'info');
        });

        state.eventSource.addEventListener('session.warning', e => {
            const data = safelyParseEventData(e.data);
            const message = data.message || '这里出现了一点需要你留意的情况。';
            appendNote(message, 'warning');
            app.setStatusBanner(message, 'warning');
        });

        state.eventSource.addEventListener('route.decision', e => {
            const data = safelyParseEventData(e.data);
            const decision = data.data?.decision || 'unknown';
            const score = data.data?.score;
            const summary = `已根据当前情况切换后续路径：${decision}${score !== undefined ? `（参考分数 ${score}）` : ''}`;
            appendThinking(summary, 'info', 'route.decision');
        });

        state.eventSource.addEventListener('assessment.form_ready', e => {
            const data = safelyParseEventData(e.data);
            const message = data.message || '小测已经准备好了，先一起对齐起点。';
            consumeVisibleTurn(message, 'info', { kind: 'awaiting', clearTyping: true });
            state.isStreaming = false;
            app.setStatusBanner('先完成这轮小测，我们再继续', 'awaiting');
            app.renderAssessmentForm(data.data?.questions || []);
            closeEventSource();
            app.finalizeAgentTurn?.();
            app.applyPrimaryActionState?.();
        });

        state.eventSource.addEventListener('topic.confirmation_needed', e => {
            const data = safelyParseEventData(e.data);
            const message = data.message || '先把这次主题确认一下。';
            consumeVisibleTurn(message, 'info', { kind: 'awaiting', clearTyping: true });
            state.isStreaming = false;
            app.setStatusBanner('等你确认这次要学的主题', 'awaiting');
            app.renderTopicConfirmation(data.data?.proposed_topic || '');
            closeEventSource();
            app.finalizeAgentTurn?.();
            app.applyPrimaryActionState?.();
        });

        state.eventSource.addEventListener('assessment.result', e => {
            const payload = safelyParseEventData(e.data);
            const summary = summarizeAssessmentResult(payload.data || {});
            consumeVisibleTurn(summary, 'success', { kind: 'result', clearTyping: true });
            app.setStatusBanner('这轮评估结果已经整理好了', 'success');
        });

        state.eventSource.addEventListener('profile.radar_data', e => {
            const payload = safelyParseEventData(e.data);
            consumeVisibleTurn(payload.message || '学习画像已更新，右侧可以看到新的雷达图。', 'success', {
                kind: 'result',
                clearTyping: false,
            });
            app.showRadar(payload.data);
        });

        state.eventSource.addEventListener('session.awaiting_input', e => {
            const data = safelyParseEventData(e.data);
            const message = data.message || '这一步需要你再补充一点。';
            consumeVisibleTurn(message, 'info', { kind: 'awaiting', clearTyping: true });
            state.isAwaitingInput = true;
            state.isStreaming = false;
            app.setStatusBanner(message, 'awaiting');
            closeEventSource();
            app.finalizeAgentTurn?.();
            app.applyPrimaryActionState?.();
        });

        state.eventSource.addEventListener('session.ping', e => {
            const data = safelyParseEventData(e.data);
            state.lastHeartbeatAt = Date.now();
            app.setTurnHeartbeat?.(data.message || '我还在处理中');
            if (!state.turnHasVisibleOutput) {
                app.scheduleVisibilityFallback?.();
            }
        });

        state.eventSource.addEventListener('session.end', e => {
            const data = safelyParseEventData(e.data);
            const message = data.message || '这一步先告一段落。若页面里出现主题确认卡或小测，请继续完成；如果没有新的控件，直接发送下一条内容就可以。';
            if (!state.turnHasVisibleOutput) {
                consumeVisibleTurn(message, 'success', { kind: 'end', clearTyping: true });
            } else {
                app.clearTypingIndicator?.();
            }
            state.isAwaitingInput = false;
            finalizeStreamState('这一段已经整理好了', 'ready');
            app.fetchHistory();
        });

        state.eventSource.addEventListener('session.error', e => {
            const data = safelyParseEventData(e.data);
            const message = data.message || '暂时没有拿到更具体的错误信息。';
            consumeVisibleTurn(`这一步出了点问题：${message}。你可以稍后再试一次，或换一种表述继续告诉我。`, 'danger', {
                kind: 'error',
                clearTyping: true,
            });
            state.isAwaitingInput = false;
            finalizeStreamState(`这一步没有顺利接上：${message}`, 'danger');
        });

        state.eventSource.onerror = () => {
            if (!state.eventSource) return;
            consumeVisibleTurn('连接暂时断了一下。这一轮已先停住；你可以稍后重试，或直接继续发送下一条内容。', 'danger', {
                kind: 'error',
                clearTyping: true,
            });
            state.isAwaitingInput = false;
            finalizeStreamState('连接暂时断了一下，可以稍后重试', 'danger');
        };
    };
})();
