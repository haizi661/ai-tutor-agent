(() => {
    const app = window.AITutorApp;
    const state = app.state;
    const DEFAULT_CHAT_PLACEHOLDER = '输入问题…';
    const ANSWER_CHAT_PLACEHOLDER = '输入回答…';

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

    function stringifyMessageValue(value) {
        if (typeof value === 'string') return value;
        if (value == null) return '';
        try {
            return JSON.stringify(value);
        } catch (_error) {
            return String(value);
        }
    }

    function pickErrorMessage(payload, fallback) {
        if (!payload || typeof payload !== 'object') return fallback;
        const detail = stringifyMessageValue(payload.detail).trim();
        const message = stringifyMessageValue(payload.message).trim();
        return detail || message || fallback;
    }

    function formatErrorMessage(error, fallback = '请求失败') {
        return stringifyMessageValue(error?.message || error || fallback).trim() || fallback;
    }

    function summarizeAssessmentResult(data) {
        const total = data.total_score ?? '—';
        const logic = data.logic_score ?? '—';
        const concept = data.concept_score ?? '—';
        const feedback = data.feedback || '这轮评估已完成。';
        const rubric = Array.isArray(data.rubric_feedback) ? data.rubric_feedback : [];
        const nextReviewPoints = Array.isArray(data.next_review_points) ? data.next_review_points : [];
        const hintLine = data.needs_hint ? '先看一条提示，再试一次。' : '';
        return [
            '### 评估结果',
            '',
            `总分：${total}`,
            `逻辑：${logic}`,
            `概念：${concept}`,
            '',
            `观察：${feedback}`,
            ...(rubric.length ? ['', '风险点：', ...rubric.map(item => `- ${item}`)] : []),
            ...(nextReviewPoints.length ? ['', '建议复习：', ...nextReviewPoints.map(item => `- ${item}`)] : []),
            ...(hintLine ? ['', `下一步：${hintLine}`] : []),
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

    app.submitAwaitingChoice = async function submitAwaitingChoice(answer, visibleText = '') {
        const text = String(answer || '').trim();
        if (!text || !state.currentThreadId) return;
        app.lockActiveChoiceCard?.(text, visibleText);
        document.querySelector('.interrupt-confirm-card')?.remove();
        app.collapseSubmittedObjectiveTestCard?.();
        if (visibleText) app.appendMessage('user', visibleText);
        startStreamingTurn('已收到');
        try {
            await postJson(
                '/api/answer',
                { thread_id: state.currentThreadId, answer: text },
                '服务端没有接住这次选择'
            );
        } catch (error) {
            consumeVisibleTurn(
                `选择提交失败：${error.message}。再试一次。`,
                'danger',
                { kind: 'error', role: 'prompt', clearTyping: true }
            );
            finalizeStreamState('选择提交失败，可以重试', 'danger');
            return;
        }
        app.connectSSE();
    };

    app.pauseCurrentSession = function pauseCurrentSession() {
        if (state.isVoiceListening) app.stopVoiceInput();
        if (!state.currentThreadId) {
            alert('现在还没有可暂停的页面。');
            return;
        }
        closeEventSource();
        state.isStreaming = false;
        setChatInputPlaceholder();
        app.finalizeAgentTurn?.();
        app.setStatusBanner('已暂停', 'paused');
        app.appendSystemMessage('这页已暂停。', 'warning');
        app.applyPrimaryActionState?.();
    };

    app.submitTopicConfirmation = async function submitTopicConfirmation(confirmed, startMode = 'assessment') {
        const payload = {
            thread_id: state.currentThreadId,
            confirmed,
            topic: confirmed ? state.pendingTopicConfirmation : (document.getElementById('topic-edit-input')?.value || '').trim(),
            start_mode: startMode,
        };
        if (!confirmed && !payload.topic) {
            alert('先写下新主题。');
            return;
        }
        app.setStatusBanner('正在确认主题', 'processing');
        try {
            await postJson('/api/confirm_topic', payload, '主题确认没有保存成功');
            if (confirmed) {
                state.currentTopic = state.pendingTopicConfirmation || payload.topic || state.currentTopic;
            } else if (payload.topic) {
                state.currentTopic = payload.topic;
                state.graphTopicHint = payload.topic;
            }
            state.pendingTopicConfirmation = null;
            state.pendingTopicConfirmationDetails = null;
            const tcCard = document.querySelector('.topic-confirm-card.prompt-flow-card');
            if (tcCard) {
                const choiceLabel = confirmed
                    ? (startMode === 'direct_tutor' ? '跳过摸底，直接开始' : '已确认，开始摸底')
                    : `已换主题：${payload.topic}`;
                tcCard.innerHTML = `
                    <div class="tc-locked-content">
                        <span class="tc-locked-icon">✅</span>
                        <span class="tc-locked-topic">${state.currentTopic || payload.topic}</span>
                        <span class="tc-confirmed-badge">${choiceLabel}</span>
                    </div>
                `;
                tcCard.classList.add('tc-locked');
            }
            startStreamingTurn('正在继续');
            app.connectSSE();
        } catch (error) {
            const message = `主题确认请求失败：${formatErrorMessage(error)}`;
            app.setStatusBanner(message, 'danger');
            alert(message);
        }
    };

    app.submitInterruptConfirmation = async function submitInterruptConfirmation(confirmed) {
        document.querySelector('.interrupt-confirm-card')?.remove();
        state.pendingInterruptConfirmation = false;

        if (!confirmed) {
            appendNote('继续当前问题。', 'info');
            app.setStatusBanner('继续当前问题', 'awaiting');
            document.getElementById('chat-input')?.focus();
            app.applyPrimaryActionState?.();
            return;
        }

        startStreamingTurn('正在回主线');
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
        app.lockActiveChoiceCard?.(text, text);
        app.appendMessage('user', text);

        if (state.isAwaitingInput) {
            startStreamingTurn('已收到');
            try {
                await postJson(
                    '/api/answer',
                    { thread_id: state.currentThreadId, answer: text },
                    '服务端没有接住这次补充'
                );
            } catch (error) {
                consumeVisibleTurn(
                    `补充提交失败：${error.message}。请重发。`,
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
        state.graphTopicHint = text;
        startStreamingTurn('正在开始');
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
                    ? '上一轮还在处理中。等当前步骤结束后再发。'
                    : `启动失败：${error.message}。请稍后重试。`,
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
            startStreamingTurn('正在接回');
        } else if (!state.currentTurnId) {
            app.startAgentTurnLifecycle?.();
            app.showTyping?.();
        }
        app.setStatusBanner('正在接回', 'processing');
        state.eventSource = new EventSource(`/api/stream?thread_id=${state.currentThreadId}`);
        app.applyPrimaryActionState?.();

        state.eventSource.addEventListener('node.start', e => {
            const data = safelyParseEventData(e.data);
            const message = data.message || '处理中';
            if (['tutor', 'coach', 'tester', 'interruption_tutor'].includes(data.source)) {
                app.updateLearningProgress?.({ step: 3, label: '学习进度 3/5' });
            }
            app.setPendingTurnRole?.(turnRoleForSource(data.source));
            app.setStatusBanner(message, 'processing');
            appendThinking(message, 'info', 'node.start');
            
            // Re-show typing indicator to keep UI alive during long node executions (like evaluator or assessment generation)
            app.showTyping?.();
        });

        state.eventSource.addEventListener('node.complete', e => {
            const data = safelyParseEventData(e.data);
            app.setPendingTurnRole?.(turnRoleForSource(data.source));
            appendThinking(data.message || '已完成', 'success', 'node.complete');
            if (['initial_node_selector', 'node_content_loader'].includes(data.source) && data.data?.node_id) {
                state.currentGraphNode = data.data?.node_name || state.currentGraphNode;
                state.currentGraphNodeId = data.data?.node_id || state.currentGraphNodeId || '';
                app.renderKnowledgeGraphVisualCard?.({
                    title: state.currentGraphNode,
                    id: state.currentGraphNodeId,
                });
            }
            const evidence = Array.isArray(data.data?.evidence) ? data.data.evidence : [];
            if (data.source === 'tutor' && evidence.length) {
                app.renderEvidencePanel?.(evidence, { tone: 'info', role: 'tutor' });
            }
            if (data.source === 'objective_test_scorer' && data.data?.review) {
                app.renderObjectiveQuizReviewCard?.(data.data.review, data.data.review_content || '');
            }
            if (data.source === 'wrong_question_explainer') {
                const explanations = Array.isArray(data.data?.explanations) ? data.data.explanations : [];
                const lines = ['错题订正讲解'];
                explanations.forEach((item, index) => {
                    const qid = item.question_id || `Q${index + 1}`;
                    const stem = item.stem || '';
                    const userAnswer = String(item.user_answer || '').toUpperCase() || '未作答';
                    const answerKey = String(item.answer_key || '').toUpperCase() || '未提供';
                    const explanation = item.explanation || '这题需要回到题干中的关键条件，重新区分正确概念与误区。';
                    lines.push('', stem ? `${qid}. ${stem}` : `${qid}.`, `你的答案：${userAnswer}；正确答案：${answerKey}`, explanation);
                });
                app.appendMessage?.('agent', lines.join('\n'), { kind: 'wrong_question_explanations' });
            }
            app.clearTypingIndicator?.();
        });

        state.eventSource.addEventListener('intent.detected', e => {
            const data = safelyParseEventData(e.data);
            appendThinking(data.message || '已判断当前意图', 'info', 'intent.detected');
        });

        state.eventSource.addEventListener('node.stream', e => {
            const data = safelyParseEventData(e.data);
            const chunk = data.data?.text;
            if (!chunk) return;

            const streamKind = String(data.data?.kind || '').trim();
            const role = streamKind === 'graph_rag_answer'
                ? 'graph_rag_answer'
                : streamKind === 'graph_rag_debug_report'
                ? 'graph_rag_debug_report'
                : turnRoleForSource(data.source);
            app.setPendingTurnRole?.(role);
            app.clearTypingIndicator?.();
            app.ensureAgentTurn?.(role);
            app.markTurnVisible?.();
            app.clearVisibilityFallback?.({ resetCounter: false });
            state.currentTextBuffer += chunk;
            app.throttledRender?.();
            app.scrollMessagesToBottom?.();
        });

        // ── 图谱节点状态更新 ──
        state.eventSource.addEventListener('graph.node_update', e => {
            const data = safelyParseEventData(e.data);
            const payload = data.data || {};
            if (payload.title && payload.status) {
                app.updateGraphNode?.(payload.title, payload.status, payload.type, payload.id);
            }
            if (payload.type === 'current') {
                state.currentGraphNode = payload.title;
                state.currentGraphNodeId = payload.id || state.currentGraphNodeId || '';
            }
            app.syncKnowledgeGraphVisualState?.();
            app.scheduleSidebarUpdate?.();
        });

        // ── 用户知识图谱全量同步（测评完成后触发）──
        state.eventSource.addEventListener('user_knowledge_graph.sync', e => {
            const data = safelyParseEventData(e.data);
            const kg = data.data || {};
            state.userKnowledgeGraph = { ...state.userKnowledgeGraph, ...kg };
            app.refreshUserKgMapIfOpen?.();
            app.syncKnowledgeGraphVisualState?.();
            app.scheduleSidebarUpdate?.();
        });

        state.eventSource.addEventListener('session.info', e => {
            const data = safelyParseEventData(e.data);
            appendNote(data.message || '这页有了新进展。', 'info');
            if (data.data?.requires_interrupt_confirmation) {
                state.isAwaitingInput = false;
                state.pendingInterruptConfirmation = true;
                pauseStreamingForAwaiting('等你决定是否回主线', {
                    render: () => app.renderInterruptConfirmation?.(),
                });
            }
        });

        state.eventSource.addEventListener('session.warning', e => {
            const data = safelyParseEventData(e.data);
            const message = data.message || '这里有一点需要留意。';
            appendNote(message, 'warning');
            app.setStatusBanner(message, 'warning');
        });

        state.eventSource.addEventListener('route.decision', e => {
            const data = safelyParseEventData(e.data);
            const decision = data.data?.decision || 'unknown';
            const score = data.data?.score;
            const summary = `已切换路径：${decision}${score !== undefined ? `（分数 ${score}）` : ''}`;
            appendThinking(summary, 'info', 'route.decision');
        });

        state.eventSource.addEventListener('assessment.form_ready', e => {
            const data = safelyParseEventData(e.data);
            const message = data.message || '小测已准备好。';
            const confirmedTopic = state.currentTopic || state.pendingTopicConfirmation || state.graphTopicHint || '';
            state.pendingTopicConfirmation = null;
            state.currentTopic = confirmedTopic;
            state.graphTopicHint = confirmedTopic || state.graphTopicHint;
            app.updateLearningProgress?.({ step: 2, label: '学习进度 2/5' });
            consumeAwaitingTurn(message, '等你完成小测', {
                role: 'assessment',
                showInChat: false,
                render: () => app.renderAssessmentForm(data.data?.questions || []),
            });
        });

        // ── 批量测评（步进器模式）──
        state.eventSource.addEventListener('assessment.batch', e => {
            const data = safelyParseEventData(e.data);
            const questions = data.data?.questions || [];
            app.updateLearningProgress?.({ step: 2, label: '学习进度 2/5' });
            consumeAwaitingTurn(
                data.message || '请完成自评',
                '等你完成自评',
                {
                    role: 'assessment',
                    showInChat: false,
                    render: () => app.renderAssessmentForm(questions),
                }
            );
        });

        // ── 对话式逐题测评（保留兼容）──
        state.eventSource.addEventListener('assessment.question', e => {
            const data = safelyParseEventData(e.data);
            const payload = data.data || {};
            app.updateLearningProgress?.({ step: 2, label: '学习进度 2/5' });
            // 关闭流、等待用户作答
            consumeAwaitingTurn(
                data.message || '请作答',
                '等你作答',
                {
                    role: 'assessment',
                    showInChat: false,
                    render: () => app.renderAssessmentDialogQuestion?.(payload),
                }
            );
        });

        state.eventSource.addEventListener('assessment.feedback', e => {
            const data = safelyParseEventData(e.data);
            const message = data.message || '';
            const payload = data.data || {};
            app.renderAssessmentFeedback?.(message, payload);
        });

        // ── 情绪信号 ──
        state.eventSource.addEventListener('affect.detected', e => {
            const data = safelyParseEventData(e.data);
            const payload = data.data || {};
            if (payload.primary) {
                appendThinking(`情绪信号：${payload.primary}`, 'info', 'affect');
            }
        });

        state.eventSource.addEventListener('topic.confirmation_needed', e => {
            const data = safelyParseEventData(e.data);
            const message = data.message || '先确认主题。';
            state.graphTopicHint = data.data?.proposed_topic || state.graphTopicHint;
            app.updateLearningProgress?.({ step: 1, label: '学习进度 1/5' });
            consumeAwaitingTurn(message, '等你确认这次要学的主题', {
                role: 'topic_confirmation',
                showInChat: false,
                render: () => app.renderTopicConfirmation(data.data?.proposed_topic || '', data.data || {}),
            });
        });

        state.eventSource.addEventListener('interrupt.confirmation_needed', e => {
            const data = safelyParseEventData(e.data);
            const message = data.message || '等你确认是否回主线。';
            consumeAwaitingTurn(message, '等你决定是否回主线', {
                role: 'interrupt_confirmation',
                showInChat: false,
                render: () => app.renderInterruptConfirmation?.(),
                pendingInterruptConfirmation: true,
            });
        });

        state.eventSource.addEventListener('assessment.result', e => {
            const payload = safelyParseEventData(e.data);
            const summary = summarizeAssessmentResult(payload.data || {});
            app.updateLearningProgress?.({ step: 3, label: '学习进度 3/5' });
            app.clearTypingIndicator?.();
            app.appendMessage?.('agent', summary, { kind: 'assessment_result' });
            app.setStatusBanner('评估已完成', 'success');
        });

        state.eventSource.addEventListener('profile.radar_data', e => {
            const payload = safelyParseEventData(e.data);
            app.showRadar(payload.data);
            app.setStatusBanner('起点已校准，正在接上讲解', 'processing');
        });

        state.eventSource.addEventListener('session.awaiting_input', e => {
            const data = safelyParseEventData(e.data);
            const message = data.message || '等你补充。';
            const payload = data.data || {};
            if (payload.interaction_kind === 'next_step_selector') {
                app.updateLearningProgress?.({ step: 4, label: '学习进度 4/5' });
                consumeAwaitingTurn(message, '等你决定下一步', {
                    role: 'prompt',
                    awaitingInput: true,
                    showInChat: false,
                    render: () => app.renderNextStepSelector?.(payload.options || []),
                    placeholder: '也可以直接输入：继续深入 / 换个例子 / 来一道题 / 先总结一下',
                });
                return;
            }
            if (payload.interaction_kind === 'post_eval_selector') {
                app.updateLearningProgress?.({ step: 5, label: '学习进度 5/5' });
                consumeAwaitingTurn(message, '等你决定下一步', {
                    role: 'prompt',
                    awaitingInput: true,
                    showInChat: false,
                    render: () => app.renderPostEvalSelector?.(payload.options || []),
                    placeholder: '也可以直接输入：继续拔高 / 换一道同类型 / 总结本轮收获',
                });
                return;
            }
            if (payload.interaction_kind === 'post_lesson_choice') {
                app.updateLearningProgress?.({ step: 4, label: '学习进度 4/5' });
                consumeAwaitingTurn(message, '等你决定课后步骤', {
                    role: 'prompt',
                    awaitingInput: true,
                    showInChat: false,
                    render: () => app.renderPostLessonChoice?.(payload.options || []),
                    placeholder: '比如：为什么这里要看符号？/ 能不能换个例子？',
                });
                return;
            }
            if (payload.interaction_kind === 'continue_or_homework_choice') {
                app.updateLearningProgress?.({ step: 5, label: '学习进度 5/5' });
                consumeAwaitingTurn(message, '等你决定继续还是收作业', {
                    role: 'prompt',
                    awaitingInput: true,
                    showInChat: false,
                    render: () => app.renderContinueOrHomeworkChoice?.(payload.options || []),
                    placeholder: '也可以直接输入选项',
                });
                return;
            }
            if (payload.interaction_kind === 'homework_review_choice') {
                consumeAwaitingTurn(message, '等你决定作业安排', {
                    role: 'prompt',
                    awaitingInput: true,
                    showInChat: false,
                    render: () => app.renderHomeworkReviewChoice?.(payload.options || []),
                    placeholder: '现在做作业 / 保存下次做 / 保留作业继续学习',
                });
                return;
            }
            if (payload.interaction_kind === 'homework_answers') {
                consumeAwaitingTurn(message, '等你提交作业', {
                    role: 'prompt',
                    awaitingInput: true,
                    showInChat: true,
                    placeholder: '请输入你的作业答案',
                });
                document.getElementById('chat-input')?.focus();
                return;
            }
            if (payload.interaction_kind === 'objective_test_answers' || payload.interaction_kind === 'variant_test_answers') {
                consumeAwaitingTurn(message, '等你答题', {
                    role: 'prompt',
                    awaitingInput: true,
                    showInChat: false,
                    render: () => app.renderObjectiveTestCard?.(payload.options || [], payload.interaction_kind),
                    placeholder: '也可以直接输入答案，如 ABCD',
                });
                return;
            }
            if (payload.interaction_kind === 'consolidation_choice') {
                consumeAwaitingTurn(message, '等你决定是否巩固复习', {
                    role: 'prompt',
                    awaitingInput: true,
                    showInChat: false,
                    render: () => app.renderConsolidationChoice?.(payload.options || []),
                    placeholder: '巩固复习 / 直接开始下一节点',
                });
                return;
            }
            if (payload.interaction_kind === 'temporary_question') {
                consumeAwaitingTurn(message, '等你输入临时问题', {
                    role: 'prompt',
                    awaitingInput: true,
                    showInChat: true,
                    placeholder: '输入你想问的问题',
                });
                document.getElementById('chat-input')?.focus();
                return;
            }
            app.updateLearningProgress?.({ step: 3, label: '学习进度 3/5' });
            consumeAwaitingTurn(message, message, {
                role: 'prompt',
                awaitingInput: true,
                showInChat: true,
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
            if (state.pendingInterruptConfirmation) {
                state.isAwaitingInput = false;
                finalizeStreamState('等你决定是否回主线', 'awaiting');
                app.fetchHistory();
                return;
            }
            // 在流结束时处理教学标记的副作用（掌握度更新、节点提示）
            app.applyTeachingMarkerSideEffects?.(state.currentTextBuffer);
            const endPayload = data.data || {};
            const endKind = endPayload.pending_interaction_kind || '';
            const message = data.message || '这一步先到这里。';
            if (endKind === 'session_complete') {
                consumeVisibleTurn('今天的学习到此结束。辛苦了！', 'success', { kind: 'end', role: 'prompt', clearTyping: true });
                finalizeStreamState('今天结束了', 'success');
                app.fetchHistory();
                app.scheduleSidebarUpdate?.();
                return;
            }
            if (endKind === 'post_lesson_choice') {
                app.updateLearningProgress?.({ step: 4, label: '学习进度 4/5' });
                consumeAwaitingTurn(endPayload.prompt || message, '等你决定课后步骤', {
                    role: 'prompt',
                    awaitingInput: true,
                    showInChat: false,
                    render: () => app.renderPostLessonChoice?.(endPayload.options || []),
                    placeholder: '比如：为什么这里要看符号？/ 能不能换个例子？',
                });
                app.fetchHistory();
                return;
            }
            if (endKind === 'temporary_question') {
                consumeAwaitingTurn(endPayload.prompt || message, '等你输入临时问题', {
                    role: 'prompt',
                    awaitingInput: true,
                    showInChat: true,
                    placeholder: '输入你想问的问题',
                });
                document.getElementById('chat-input')?.focus();
                app.fetchHistory();
                return;
            }
            if (endKind === 'objective_test_answers' || endKind === 'variant_test_answers') {
                consumeAwaitingTurn(endPayload.prompt || message, '等你答题', {
                    role: 'prompt',
                    awaitingInput: true,
                    showInChat: false,
                    render: () => app.renderObjectiveTestCard?.(endPayload.options || [], endKind),
                    placeholder: '也可以直接输入答案，如 ABCD',
                });
                app.fetchHistory();
                return;
            }
            if (endKind === 'continue_or_homework_choice') {
                app.updateLearningProgress?.({ step: 5, label: '学习进度 5/5' });
                consumeAwaitingTurn(endPayload.prompt || message, '等你决定继续还是收作业', {
                    role: 'prompt',
                    awaitingInput: true,
                    showInChat: false,
                    render: () => app.renderContinueOrHomeworkChoice?.(endPayload.options || []),
                    placeholder: '也可以直接输入：继续学习 / 今天不学了',
                });
                app.fetchHistory();
                return;
            }
            if (endKind === 'homework_review_choice') {
                consumeAwaitingTurn(endPayload.prompt || message, '等你决定作业安排', {
                    role: 'prompt',
                    awaitingInput: true,
                    showInChat: false,
                    render: () => app.renderHomeworkReviewChoice?.(endPayload.options || []),
                    placeholder: '现在做作业 / 保存下次做 / 保留作业继续学习',
                });
                app.fetchHistory();
                return;
            }
            if (endKind === 'homework_answers') {
                consumeAwaitingTurn(endPayload.prompt || message, '等你提交作业', {
                    role: 'prompt',
                    awaitingInput: true,
                    showInChat: true,
                    placeholder: '请输入你的作业答案',
                });
                document.getElementById('chat-input')?.focus();
                app.fetchHistory();
                return;
            }
            if (endKind === 'consolidation_choice') {
                consumeAwaitingTurn(endPayload.prompt || message, '等你决定是否巩固复习', {
                    role: 'prompt',
                    awaitingInput: true,
                    showInChat: false,
                    render: () => app.renderConsolidationChoice?.(endPayload.options || []),
                    placeholder: '巩固复习 / 直接开始下一节点',
                });
                app.fetchHistory();
                return;
            }
            // 测评答题阶段：如果页面上有未完成的答题卡，保持 awaiting 状态
            const activeQCard = document.querySelector('.q-card .q-submit:not([disabled])') || document.querySelector('.q-card .q-opt:not(.locked)');
            if (activeQCard) {
                app.clearTypingIndicator?.();
                finalizeStreamState('请继续作答', 'awaiting');
                return;
            }
            if (!state.turnHasVisibleOutput) {
                consumeVisibleTurn(message, 'success', { kind: 'end', role: 'prompt', clearTyping: true });
            } else {
                app.clearTypingIndicator?.();
            }
            state.isAwaitingInput = false;
            finalizeStreamState('已完成', 'ready');
            app.fetchHistory();
            app.scheduleSidebarUpdate?.();
        });

        state.eventSource.addEventListener('session.error', e => {
            const data = safelyParseEventData(e.data);
            const message = data.message || '没有更多错误信息。';
            consumeVisibleTurn(`出错：${message}`, 'danger', {
                kind: 'error',
                role: 'prompt',
                clearTyping: true,
            });
            state.isAwaitingInput = false;
            finalizeStreamState(`出错：${message}`, 'danger');
        });

        state.eventSource.onerror = () => {
            if (!state.eventSource) return;
            consumeVisibleTurn('连接断开。', 'danger', {
                kind: 'error',
                role: 'prompt',
                clearTyping: true,
            });
            state.isAwaitingInput = false;
            finalizeStreamState('连接断开了', 'danger');
        };
    };
})();
