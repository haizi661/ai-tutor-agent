(() => {
    const app = window.AITutorApp;
    const state = app.state;
    const DEFAULT_CHAT_PLACEHOLDER = '输入想学的主题，或在讲解中直接追问临时问题…';
    const ANSWER_CHAT_PLACEHOLDER = '输入你的解答，或先追问一个临时问题…';

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

    function turnRoleForSource(source, eventType = '') {
        if (eventType === 'assessment.result') return 'evaluation';
        if (eventType === 'assessment.form_ready') return 'assessment';
        if (eventType === 'topic.confirmation_needed') return 'topic_confirmation';
        if (eventType === 'interrupt.confirmation_needed') return 'interrupt_confirmation';
        if (source === 'tutor') return 'tutor';
        if (source === 'coach') return 'coach';
        if (source === 'tester') return 'tester';
        if (source === 'interruption_tutor') return 'interruption';
        if (source === 'user_profiler') return 'profile';
        if (source === 'evaluator') return 'evaluation';
        return 'teacher';
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

    function setChatInputPlaceholder(text = DEFAULT_CHAT_PLACEHOLDER) {
        const input = document.getElementById('chat-input');
        if (!input) return;
        input.placeholder = text;
    }

    app.setChatInputPlaceholder = setChatInputPlaceholder;

    async function parseResponseJson(response) {
        try {
            return await response.json();
        } catch (_error) {
            return {};
        }
    }

    async function postJson(url, payload, fallback) {
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        const data = await parseResponseJson(res);
        if (!res.ok || data.status === 'error') {
            throw new Error(pickErrorMessage(data, fallback));
        }
        return data;
    }

    function pickErrorMessage(payload, fallback) {
        if (!payload || typeof payload !== 'object') return fallback;
        return payload.detail || payload.message || fallback;
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
        setChatInputPlaceholder();
        app.setStatusBanner(statusMessage, tone);
        closeEventSource();
        app.finalizeAgentTurn?.();
        app.applyPrimaryActionState?.();
    }

    function pauseStreamingForAwaiting(statusMessage, { render } = {}) {
        state.isStreaming = false;
        app.setStatusBanner(statusMessage, 'awaiting');
        render?.();
        closeEventSource();
        app.finalizeAgentTurn?.();
        app.applyPrimaryActionState?.();
    }

    function consumeAwaitingTurn(message, statusMessage, options = {}) {
        const {
            role = 'prompt',
            render,
            awaitingInput = false,
            pendingInterruptConfirmation = false,
            showInChat = true,
            placeholder = DEFAULT_CHAT_PLACEHOLDER,
        } = options;

        if (showInChat) {
            consumeVisibleTurn(message, 'info', { kind: 'awaiting', role, clearTyping: true });
        } else {
            app.clearTypingIndicator?.();
        }
        state.isAwaitingInput = awaitingInput;
        state.pendingInterruptConfirmation = pendingInterruptConfirmation;
        setChatInputPlaceholder(placeholder);
        pauseStreamingForAwaiting(statusMessage, { render });
    }

    app.pauseCurrentSession = function pauseCurrentSession() {
        if (state.isVoiceListening) app.stopVoiceInput();
        if (!state.currentThreadId) {
            alert('现在还没有可以暂停的学习页。');
            return;
        }
        closeEventSource();
        state.isStreaming = false;
        setChatInputPlaceholder();
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
        try {
            await postJson('/api/confirm_topic', payload, '主题确认没有保存成功');
            state.pendingTopicConfirmation = null;
            document.querySelector('.topic-confirm-card')?.remove();
            startStreamingTurn('我在接上主题确认后的流程');
            app.connectSSE();
        } catch (error) {
            const message = `主题确认请求失败：${error.message}`;
            app.setStatusBanner(message, 'danger');
            alert(message);
        }
    };

    app.submitInterruptConfirmation = async function submitInterruptConfirmation(confirmed) {
        document.querySelector('.interrupt-confirm-card')?.remove();
        state.pendingInterruptConfirmation = false;

        if (!confirmed) {
            appendNote('好，我们先不急着回主线。你继续追问这个点，我会顺着给你讲。', 'info');
            app.setStatusBanner('可以继续追问这个卡点', 'awaiting');
            document.getElementById('chat-input')?.focus();
            app.applyPrimaryActionState?.();
            return;
        }

        startStreamingTurn('我在把你带回刚才那道题');
        try {
            await postJson(
                '/api/confirm_interrupt',
                { thread_id: state.currentThreadId, confirmed },
                '回到主线失败'
            );
            app.connectSSE();
        } catch (error) {
            state.pendingInterruptConfirmation = true;
            app.renderInterruptConfirmation?.();
            app.setStatusBanner(`回主线请求失败：${error.message}`, 'danger');
            finalizeStreamState('回主线请求失败，请稍后重试', 'danger');
        }
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
        if (state.pendingInterruptConfirmation) {
            document.querySelector('.interrupt-confirm-card')?.remove();
            state.pendingInterruptConfirmation = false;
        }
        app.appendMessage('user', text);

        if (state.isAwaitingInput) {
            startStreamingTurn('收到你的补充了，我继续往下整理');
            try {
                await postJson(
                    '/api/answer',
                    { thread_id: state.currentThreadId, answer: text },
                    '服务端没有接住这次补充'
                );
            } catch (error) {
                consumeVisibleTurn(
                    `这次补充提交失败：${error.message}。你可以直接重发一次。`,
                    'danger',
                    { kind: 'error', role: 'prompt', clearTyping: true }
                );
                finalizeStreamState('补充提交失败，可以重试', 'danger');
                return;
            }
            app.connectSSE();
            return;
        }

        if (!state.currentThreadId) state.currentThreadId = app.makeThreadId();
        startStreamingTurn('先帮你铺开这一页的学习流程');
        try {
            await postJson(
                '/api/start',
                { thread_id: state.currentThreadId, topic: text },
                '服务端没有成功启动会话'
            );
        } catch (error) {
            if (state.currentThreadId) {
                app.connectSSE();
            }
            consumeVisibleTurn(
                error.message.includes('previous turn')
                    ? '上一轮还在处理中，这条消息还没有真正送进工作流。等当前步骤结束后再发，或者先看页面里是不是在等你确认主题/填写小测/输入答案。'
                    : `这次发起学习失败：${error.message}。请确认服务在线后重试。`,
                error.message.includes('previous turn') ? 'warning' : 'danger',
                { kind: 'error', role: 'prompt', clearTyping: true }
            );
            finalizeStreamState(
                error.message.includes('previous turn') ? '上一轮还在处理中，请稍等' : '会话启动失败，请重试',
                error.message.includes('previous turn') ? 'warning' : 'danger'
            );
            return;
        }
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
            const message = data.message || '我在把这一小步接好。';
            app.setPendingTurnRole?.(turnRoleForSource(data.source));
            app.setStatusBanner(message, 'processing');
            appendThinking(message, 'info', 'node.start');
            
            // Re-show typing indicator to keep UI alive during long node executions (like evaluator or assessment generation)
            app.showTyping?.();
        });

        state.eventSource.addEventListener('node.complete', e => {
            const data = safelyParseEventData(e.data);
            app.setPendingTurnRole?.(turnRoleForSource(data.source));
            appendThinking(data.message || '这一步已经接好了。', 'success', 'node.complete');
            const citations = Array.isArray(data.data?.citations) ? data.data.citations : [];
            if (data.source === 'tutor' && citations.length) {
                app.renderTutorCitations?.(citations, { tone: 'info', role: 'tutor' });
            }
            app.clearTypingIndicator?.();
        });

        state.eventSource.addEventListener('intent.detected', e => {
            const data = safelyParseEventData(e.data);
            appendThinking(data.message || '我已经判断出你这一步更像哪种需求了。', 'info', 'intent.detected');
        });

        state.eventSource.addEventListener('node.stream', e => {
            const data = safelyParseEventData(e.data);
            const chunk = data.data?.text;
            if (!chunk) return;

            const role = turnRoleForSource(data.source);
            app.setPendingTurnRole?.(role);
            app.clearTypingIndicator?.();
            app.ensureAgentTurn?.(role);
            app.markTurnVisible?.();
            app.clearVisibilityFallback?.({ resetCounter: false });
            state.currentTextBuffer += chunk;
            app.throttledRender?.();
            app.scrollMessagesToBottom?.();
        });

        state.eventSource.addEventListener('session.info', e => {
            const data = safelyParseEventData(e.data);
            appendNote(data.message || '这页内容有了新的进展。', 'info');
            if (data.data?.requires_interrupt_confirmation) {
                state.isAwaitingInput = false;
                state.pendingInterruptConfirmation = true;
                pauseStreamingForAwaiting('这个卡点已经讲清楚了，等你决定要不要回主线', {
                    render: () => app.renderInterruptConfirmation?.(),
                });
            }
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
            state.pendingTopicConfirmation = null;
            consumeAwaitingTurn(message, '先完成这轮小测，我们再继续', {
                role: 'assessment',
                render: () => app.renderAssessmentForm(data.data?.questions || []),
            });
        });

        state.eventSource.addEventListener('topic.confirmation_needed', e => {
            const data = safelyParseEventData(e.data);
            const message = data.message || '先把这次主题确认一下。';
            consumeAwaitingTurn(message, '等你确认这次要学的主题', {
                role: 'topic_confirmation',
                render: () => app.renderTopicConfirmation(data.data?.proposed_topic || ''),
            });
        });

        state.eventSource.addEventListener('interrupt.confirmation_needed', e => {
            const data = safelyParseEventData(e.data);
            const message = data.message || '临时问题已经解答，等你确认是否回到主线。';
            consumeAwaitingTurn(message, '这个卡点已经讲清楚了，等你决定要不要回主线', {
                role: 'interrupt_confirmation',
                render: () => app.renderInterruptConfirmation?.(),
                pendingInterruptConfirmation: true,
            });
        });

        state.eventSource.addEventListener('assessment.result', e => {
            const payload = safelyParseEventData(e.data);
            const summary = summarizeAssessmentResult(payload.data || {});
            consumeVisibleTurn(summary, 'success', { kind: 'result', role: 'evaluation', clearTyping: true });
            app.setStatusBanner('这轮评估我已经替你整理好了', 'success');
        });

        state.eventSource.addEventListener('profile.radar_data', e => {
            const payload = safelyParseEventData(e.data);
            consumeVisibleTurn(payload.message || '学习画像已更新，右侧可以看到新的雷达图。', 'success', {
                kind: 'result',
                role: 'profile',
                clearTyping: false,
            });
            app.showRadar(payload.data);
        });

        state.eventSource.addEventListener('session.awaiting_input', e => {
            const data = safelyParseEventData(e.data);
            const message = data.message || '这里还需要你再补一句，我才能继续往下带。';
            consumeAwaitingTurn(message, message, {
                role: 'prompt',
                awaitingInput: true,
                showInChat: false,
                placeholder: ANSWER_CHAT_PLACEHOLDER,
            });
            document.getElementById('chat-input')?.focus();
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
            const rawMessage = String(data.message || '').trim();
            const isGenericEndMarker = !rawMessage || /^session ended\.?$/i.test(rawMessage);
            if (state.pendingInterruptConfirmation) {
                state.isAwaitingInput = false;
                finalizeStreamState('这个卡点已经讲清楚了，等你决定要不要回主线', 'awaiting');
                app.fetchHistory();
                return;
            }
            const message = isGenericEndMarker
                ? '这一小段先到这里。如果页面里出现主题确认卡或小测，就顺着完成；如果没有新控件，直接发下一条内容就行。'
                : rawMessage;
            if (!state.turnHasVisibleOutput && !isGenericEndMarker) {
                consumeVisibleTurn(message, 'success', { kind: 'end', role: 'prompt', clearTyping: true });
            } else {
                app.clearTypingIndicator?.();
            }
            state.isAwaitingInput = false;
            finalizeStreamState('这一段我已经整理好了', 'ready');
            app.fetchHistory();
        });

        state.eventSource.addEventListener('session.error', e => {
            const data = safelyParseEventData(e.data);
            const message = data.message || '暂时没有拿到更具体的错误信息。';
            consumeVisibleTurn(`这一步出了点问题：${message}。你可以稍后再试一次，或换一种表述继续告诉我。`, 'danger', {
                kind: 'error',
                role: 'prompt',
                clearTyping: true,
            });
            state.isAwaitingInput = false;
            finalizeStreamState(`这一步没有顺利接上：${message}`, 'danger');
        });

        state.eventSource.onerror = () => {
            if (!state.eventSource) return;
            consumeVisibleTurn('连接暂时断了一下。这一轮已先停住；你可以稍后重试，或直接继续发送下一条内容。', 'danger', {
                kind: 'error',
                role: 'prompt',
                clearTyping: true,
            });
            state.isAwaitingInput = false;
            finalizeStreamState('连接暂时断了一下，可以稍后重试', 'danger');
        };
    };
})();
