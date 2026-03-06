(() => {
    const app = window.AITutorApp;
    const state = app.state;
    const PRE_TOPIC_FLOW_STATUSES = new Set(['greeting', 'topic_intake', 'meta_qa', 'smalltalk']);

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

    app.clearTypingIndicator = function clearTypingIndicator() {
        document.getElementById('typing-indicator')?.remove();
    };

    app.appendMessage = function appendMessage(role, text) {
        app.clearTypingIndicator();
        const wrap = document.createElement('div');
        wrap.className = `msg-wrapper ${role}`;
        const avatarLabel = role === 'user' ? 'U' : 'T';
        wrap.innerHTML = `
            <div class="avatar ${role}">${avatarLabel.charAt(0)}</div>
            <div class="msg-content">${marked.parse(text)}</div>
        `;
        const container = document.getElementById('messages');
        container.appendChild(wrap);
        container.scrollTop = container.scrollHeight;

        if (role === 'agent') {
            state.currentAgentMsgEl = wrap.querySelector('.msg-content');
            state.currentTextBuffer = text;
            app.renderMath(state.currentAgentMsgEl);
        }
    };

    app.appendSystemMessage = function appendSystemMessage(text) {
        if (!text) return;
        app.clearTypingIndicator();
        const wrap = document.createElement('div');
        wrap.className = 'msg-wrapper system';
        wrap.innerHTML = `
            <div class="avatar system">i</div>
            <div class="msg-content system">${marked.parse(text)}</div>
        `;
        const container = document.getElementById('messages');
        container.appendChild(wrap);
        container.scrollTop = container.scrollHeight;
    };

    app.showTyping = function showTyping() {
        app.clearTypingIndicator();
        const wrap = document.createElement('div');
        wrap.className = 'msg-wrapper agent';
        wrap.id = 'typing-indicator';
        wrap.innerHTML = `
            <div class="avatar agent">T</div>
            <div class="msg-content"><div class="typing-dots"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div></div>
        `;
        const messages = document.getElementById('messages');
        messages.appendChild(wrap);
        messages.scrollTop = messages.scrollHeight;
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
                        label: '自我评估',
                        data: data.self_scores,
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59,130,246,0.2)',
                        pointBackgroundColor: '#3b82f6',
                    },
                    {
                        label: '客观得分',
                        data: data.objective_scores,
                        borderColor: '#10a37f',
                        backgroundColor: 'rgba(16,163,127,0.2)',
                        pointBackgroundColor: '#10a37f',
                    },
                ],
            },
            options: {
                scales: {
                    r: {
                        min: 0,
                        max: 100,
                        ticks: { display: false },
                        grid: { color: 'rgba(255,255,255,0.1)' },
                        angleLines: { color: 'rgba(255,255,255,0.1)' },
                        pointLabels: { color: '#8e8ea0', font: { size: 10 } },
                    },
                },
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { color: '#ececf1', boxWidth: 12, font: { size: 11 } },
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
        div.innerHTML = `<h3>🎯 学前能力测评</h3><p style="color:var(--text-secondary); font-size:13px; margin-bottom:20px;">请完成以下 ${questions.length} 道评估题，我将据此为你制定学习画像。</p>`;

        questions.forEach(q => {
            const qDiv = document.createElement('div');
            qDiv.className = 'q-item';
            qDiv.innerHTML = `<div class="q-text">${q.id}. ${q.question}</div><div class="opt-grid" id="q-${q.id}"></div>`;
            const grid = qDiv.querySelector('.opt-grid');
            q.options.forEach(opt => {
                const btn = document.createElement('button');
                btn.className = 'opt-btn';
                btn.innerText = opt;
                btn.onclick = () => {
                    state.answers[q.id] = opt.trim().charAt(0);
                    grid.querySelectorAll('.opt-btn').forEach(b => b.classList.remove('selected'));
                    btn.classList.add('selected');
                };
                if ((state.answers[q.id] || '').toUpperCase() === opt.trim().charAt(0).toUpperCase()) {
                    btn.classList.add('selected');
                }
                grid.appendChild(btn);
            });
            div.appendChild(qDiv);
        });

        const submitBtn = document.createElement('button');
        submitBtn.className = 'btn-submit-all';
        submitBtn.innerText = '提交测评，开启学习';
        submitBtn.onclick = async () => {
            if (Object.keys(state.answers).length < questions.length) {
                alert('请先完成所有题目再提交！');
                return;
            }
            submitBtn.disabled = true;
            submitBtn.innerText = '📤 正在分析画像...';
            await fetch('/api/submit_assessment', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ thread_id: state.currentThreadId, answers: state.answers }),
            });
            app.connectSSE();
        };
        div.appendChild(submitBtn);
        container.appendChild(div);
        container.scrollTop = container.scrollHeight;
    };

    app.renderTopicConfirmation = function renderTopicConfirmation(topic) {
        state.pendingTopicConfirmation = topic;
        app.clearTypingIndicator();
        document.querySelector('.topic-confirm-card')?.remove();
        const container = document.getElementById('messages');
        const card = document.createElement('div');
        card.className = 'topic-confirm-card';
        card.innerHTML = `
            <h3>🧭 确认学习主题</h3>
            <p style="color:var(--text-secondary); font-size:13px; margin-top:10px;">我理解你当前想学习的是：</p>
            <div style="font-size:20px; margin-top:8px; font-weight:bold;">${topic}</div>
            <div class="topic-confirm-actions">
                <button class="topic-confirm-btn primary" onclick="submitTopicConfirmation(true)">是的，就学这个</button>
                <button class="topic-confirm-btn secondary" onclick="showTopicEditInput()">不是，我重新输入</button>
            </div>
            <div id="topic-edit-box" style="display:none;">
                <input id="topic-edit-input" class="topic-confirm-input" placeholder="请输入一个明确主题，例如：控制理论、矩阵求逆、PID 控制器">
                <div class="topic-confirm-actions">
                    <button class="topic-confirm-btn warn" onclick="submitTopicConfirmation(false)">提交新主题</button>
                </div>
            </div>
        `;
        container.appendChild(card);
        container.scrollTop = container.scrollHeight;
    };

    app.showTopicEditInput = function showTopicEditInput() {
        const box = document.getElementById('topic-edit-box');
        if (box) box.style.display = 'block';
    };

    app.restoreSessionState = function restoreSessionState(stateSnapshot) {
        const messages = document.getElementById('messages');
        messages.innerHTML = '';

        if (!stateSnapshot) {
            app.appendMessage('agent', '未找到可恢复状态。');
            return;
        }

        state.pendingTopicConfirmation = stateSnapshot.proposed_topic || null;
        const hasConfirmedTopic = Boolean(
            stateSnapshot.current_topic &&
            !PRE_TOPIC_FLOW_STATUSES.has(stateSnapshot.flow_status) &&
            stateSnapshot.flow_status !== 'awaiting_topic_confirmation'
        );
        const sessionSummary = hasConfirmedTopic
            ? `已恢复历史会话。当前主题：${stateSnapshot.current_topic}`
            : '已恢复历史会话。当前还没有确认的学习主题。';
        app.appendSystemMessage(sessionSummary);

        if (stateSnapshot.assessment_result) app.appendMessage('agent', stateSnapshot.assessment_result);
        if (stateSnapshot.tutor_content) app.appendMessage('agent', stateSnapshot.tutor_content);
        if (stateSnapshot.user_answer) app.appendMessage('user', stateSnapshot.user_answer);
        if (stateSnapshot.tester_question) app.appendMessage('agent', stateSnapshot.tester_question);

        if (stateSnapshot.feedback || stateSnapshot.score) {
            app.appendMessage(
                'agent',
                `最近一次评估：总分 ${stateSnapshot.score}，逻辑 ${stateSnapshot.logic_score}，概念 ${stateSnapshot.concept_score}。\n\n诊断：${stateSnapshot.feedback || '暂无。'}`
            );
        }

        if (stateSnapshot.assessment_radar && stateSnapshot.assessment_radar.dimensions) {
            app.showRadar(stateSnapshot.assessment_radar);
        }

        if (stateSnapshot.flow_status === 'awaiting_topic_confirmation' && stateSnapshot.proposed_topic) {
            app.renderTopicConfirmation(stateSnapshot.proposed_topic);
        }

        if (stateSnapshot.flow_status === 'awaiting_assessment' && (stateSnapshot.assessment_questions || []).length) {
            app.renderAssessmentForm(stateSnapshot.assessment_questions, stateSnapshot.assessment_answers || {});
        }
    };
})();
