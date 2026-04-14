(() => {
    const app = window.AITutorApp;
    const state = app.state;
    const PRE_TOPIC_FLOW_STATUSES = new Set(['greeting', 'topic_intake', 'meta_qa', 'smalltalk']);
    const LAST_THREAD_STORAGE_KEY = 'ai_tutor_last_thread_id';
    const historyUiState = {
        items: [],
        searchQuery: '',
        showAll: false,
        openMenuThreadId: '',
    };

    function normalizeHistoryQuery(value) {
        return (value || '').trim().toLowerCase();
    }

    function closeHistoryMenu() {
        const openRow = document.querySelector('.topic-item.menu-open');
        if (!openRow) {
            historyUiState.openMenuThreadId = '';
            return;
        }
        openRow.classList.remove('menu-open');
        const menu = openRow.querySelector('.history-menu');
        if (menu) {
            menu.hidden = true;
            menu.classList.remove('open');
        }
        const trigger = openRow.querySelector('.history-menu-trigger');
        if (trigger) trigger.setAttribute('aria-expanded', 'false');
        historyUiState.openMenuThreadId = '';
    }

    function toggleHistoryMenu(row, threadId) {
        if (!row) return;
        if (historyUiState.openMenuThreadId === threadId) {
            closeHistoryMenu();
            return;
        }
        closeHistoryMenu();
        const menu = row.querySelector('.history-menu');
        if (!menu) return;
        row.classList.add('menu-open');
        menu.hidden = false;
        menu.classList.add('open');
        const trigger = row.querySelector('.history-menu-trigger');
        if (trigger) trigger.setAttribute('aria-expanded', 'true');
        historyUiState.openMenuThreadId = threadId;
    }

    function filterHistoryItems(items) {
        const query = normalizeHistoryQuery(historyUiState.searchQuery);
        if (!query) return items;
        return items.filter(entry => {
            const label = (entry.display_title || entry.current_topic || entry.thread_id || '').toLowerCase();
            return label.includes(query);
        });
    }

    function ensureHistorySearchBindings() {
        const wrap = document.getElementById('sidebar-search-wrap');
        const input = document.getElementById('history-search-input');
        const toggle = document.getElementById('sidebar-search-toggle');
        if (!wrap || !input || !toggle || input.dataset.bound === '1') return;

        input.dataset.bound = '1';
        toggle.setAttribute('aria-expanded', 'false');

        input.addEventListener('input', event => {
            historyUiState.searchQuery = event.target.value || '';
            historyUiState.showAll = false;
            app.renderHistoryList?.();
        });

        input.addEventListener('keydown', event => {
            if (event.key === 'Escape') {
                event.preventDefault();
                app.toggleHistorySearch?.(false);
                toggle.focus();
            }
        });

        document.addEventListener('click', event => {
            if (!event.target.closest('.history-actions')) closeHistoryMenu();
            if (!wrap.contains(event.target) && !input.hidden && !input.value.trim()) {
                app.toggleHistorySearch?.(false);
            }
        });

        document.addEventListener('keydown', event => {
            if (event.key === 'Escape') closeHistoryMenu();
        });
    }

    app.toggleHistorySearch = function toggleHistorySearch(force) {
        const wrap = document.getElementById('sidebar-search-wrap');
        const input = document.getElementById('history-search-input');
        const toggle = document.getElementById('sidebar-search-toggle');
        if (!wrap || !input || !toggle) return;

        const shouldOpen = typeof force === 'boolean' ? force : input.hidden;
        if (shouldOpen && document.getElementById('sidebar')?.classList.contains('sidebar--collapsed')) {
            app.toggleSidebar?.(false);
        }
        wrap.classList.toggle('is-searching', shouldOpen);
        input.hidden = !shouldOpen;
        toggle.setAttribute('aria-expanded', shouldOpen ? 'true' : 'false');

        if (shouldOpen) {
            window.requestAnimationFrame(() => input.focus());
            return;
        }

        if (input.value) {
            input.value = '';
            historyUiState.searchQuery = '';
            historyUiState.showAll = false;
            app.renderHistoryList?.();
        }
    };

    function resetRuntimeView() {
        if (state.eventSource) state.eventSource.close();
        state.eventSource = null;
        state.pendingTopicConfirmation = null;
        state.pendingTopicConfirmationDetails = null;
        state.pendingInterruptConfirmation = false;
        state.isAwaitingInput = false;
        state.isStreaming = false;
        state.currentTopic = '';
        state.currentTopicFocus = '';
        state.graphTopicHint = '';
        state.currentGraphNode = '';
        state.userKnowledgeGraph = {};
        state.latestRadarData = null;
        app.setChatInputPlaceholder?.();
        app.clearTypingIndicator?.();
        app.finalizeAgentTurn?.();
        document.getElementById('messages').innerHTML = '';
        document.getElementById('chat-input').value = '';
        app.updateLearningProgress?.({ step: 1, label: '学习进度 1/5' });
        app.closeRadarModal?.();
        app.closeKnowledgeGraphModal?.();
        app.updateSidebarState?.();
        app.refreshChatSurfaceState?.();
    }

    async function persistHistoryEntryTitle(threadId, nextTitle) {
        const res = await fetch(`/api/history/${threadId}/title`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: nextTitle }),
        });
        const data = await res.json();
        if (!res.ok) {
            app.setStatusBanner?.(data.detail || '目录改名失败', 'danger');
            return false;
        }
        app.setStatusBanner?.(data.custom_title ? '目录名已更新' : '已恢复自动命名', 'success');
        return true;
    }

    function startInlineRename(row, textButton, threadId, currentLabel, customTitle = '') {
        if (!row || row.classList.contains('is-editing')) return;
        closeHistoryMenu();
        row.classList.add('is-editing');

        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'history-title-input';
        input.value = customTitle || currentLabel || '';
        input.maxLength = 48;
        input.setAttribute('aria-label', `修改目录名 ${currentLabel}`);

        let finished = false;
        const finish = async mode => {
            if (finished) return;
            finished = true;
            if (mode === 'cancel') {
                app.fetchHistory();
                return;
            }
            const ok = await persistHistoryEntryTitle(threadId, input.value);
            app.fetchHistory();
            if (!ok) return;
        };

        input.addEventListener('keydown', event => {
            if (event.key === 'Enter') {
                event.preventDefault();
                input.blur();
            } else if (event.key === 'Escape') {
                event.preventDefault();
                finish('cancel');
            }
        });

        input.addEventListener('blur', () => {
            finish('save');
        });

        textButton.replaceWith(input);
        window.requestAnimationFrame(() => {
            input.focus();
            input.select();
        });
    }

    const MAX_VISIBLE_HISTORY = 6;

    function relativeTime(ts) {
        if (!ts) return '';
        const now = Date.now();
        const d = typeof ts === 'string' ? new Date(ts).getTime() : ts;
        if (isNaN(d)) return '';
        const diff = Math.max(0, now - d);
        const mins = Math.floor(diff / 60000);
        if (mins < 1) return '刚刚';
        if (mins < 60) return `${mins}分钟前`;
        const hours = Math.floor(mins / 60);
        if (hours < 24) return `${hours}小时前`;
        const days = Math.floor(hours / 24);
        if (days < 7) return `${days}天前`;
        return new Date(d).toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' });
    }

    function renderHistoryItems(items) {
        const list = document.getElementById('history-list');
        if (!list) return;
        list.innerHTML = '';

        if (!items.length) {
            const empty = document.createElement('div');
            empty.className = 'history-group topic-empty';
            empty.textContent = historyUiState.searchQuery.trim() ? '没有匹配的学习页' : '还没有学习记录';
            list.appendChild(empty);
            return;
        }

        const showAll = historyUiState.showAll || historyUiState.searchQuery.trim();
        const visible = showAll ? items : items.slice(0, MAX_VISIBLE_HISTORY);

        visible.forEach((entry, index) => {
            const id = entry.thread_id;
            const label = entry.display_title || entry.current_topic || id;
            const customTitle = entry.custom_title || '';
            const timeText = relativeTime(entry.updated_at || entry.updatedAt || entry.created_at || '');
            const stateLabel = label === '未确认主题'
                ? '待开始'
                : (label.startsWith('待确认：') ? '待确认' : '学习页');
            const row = document.createElement('div');
            row.className = `history-item topic-item ${id === state.currentThreadId ? 'active' : ''}`;
            row.dataset.threadId = id;
            if (label === '未确认主题') row.dataset.historyState = 'unconfirmed';
            else if (label.startsWith('待确认：')) row.dataset.historyState = 'pending';
            else row.dataset.historyState = 'topic';

            const textButton = document.createElement('button');
            textButton.type = 'button';
            textButton.className = 'history-text';
            textButton.setAttribute('aria-label', `恢复学习页 ${label}`);
            textButton.setAttribute('aria-posinset', String(index + 1));
            textButton.setAttribute('aria-setsize', String(items.length));
            textButton.onclick = () => app.loadSession(id);

            const titleEl = document.createElement('span');
            titleEl.className = 'history-title';
            titleEl.textContent = label;
            textButton.appendChild(titleEl);

            if (stateLabel || timeText) {
                const metaEl = document.createElement('span');
                metaEl.className = 'history-meta';

                if (stateLabel) {
                    const stateEl = document.createElement('span');
                    stateEl.className = 'history-state-pill';
                    stateEl.textContent = stateLabel;
                    metaEl.appendChild(stateEl);
                }

                if (timeText) {
                    const timeEl = document.createElement('span');
                    timeEl.className = 'history-item-time';
                    timeEl.textContent = timeText;
                    metaEl.appendChild(timeEl);
                }

                textButton.appendChild(metaEl);
            }

            if (timeText && !textButton.querySelector('.history-item-time')) {
                const timeEl = document.createElement('span');
                timeEl.className = 'history-item-time';
                timeEl.textContent = timeText;
                textButton.appendChild(timeEl);
            }

            const actions = document.createElement('div');
            actions.className = 'history-actions';

            const menuTrigger = document.createElement('button');
            menuTrigger.type = 'button';
            menuTrigger.className = 'history-menu-trigger';
            menuTrigger.setAttribute('aria-label', `打开 ${label} 的操作菜单`);
            menuTrigger.setAttribute('aria-haspopup', 'menu');
            menuTrigger.setAttribute('aria-expanded', 'false');
            menuTrigger.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                    <circle cx="3.25" cy="8" r="1.1" fill="currentColor"/>
                    <circle cx="8" cy="8" r="1.1" fill="currentColor"/>
                    <circle cx="12.75" cy="8" r="1.1" fill="currentColor"/>
                </svg>
            `;
            menuTrigger.onclick = event => {
                event.stopPropagation();
                toggleHistoryMenu(row, id);
            };

            const menu = document.createElement('div');
            menu.className = 'history-menu';
            menu.hidden = true;
            menu.setAttribute('role', 'menu');

            const renameButton = document.createElement('button');
            renameButton.type = 'button';
            renameButton.className = 'history-menu-btn';
            renameButton.innerHTML = `
                <span class="history-menu-icon" aria-hidden="true">
                    <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                        <path d="M9.85 2.1L11.9 4.15M2.25 11.75L4.9 11.15L11.25 4.8C11.58 4.47 11.58 3.93 11.25 3.6L10.4 2.75C10.07 2.42 9.53 2.42 9.2 2.75L2.85 9.1L2.25 11.75Z" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </span>
                <span>重命名</span>
            `;
            renameButton.onclick = event => {
                event.stopPropagation();
                startInlineRename(row, textButton, id, label, customTitle);
            };

            const deleteButton = document.createElement('button');
            deleteButton.type = 'button';
            deleteButton.className = 'history-menu-btn history-menu-btn--danger';
            deleteButton.innerHTML = `
                <span class="history-menu-icon" aria-hidden="true">
                    <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                        <path d="M2.75 4.1H11.25M5.15 2.35H8.85M5.15 6.1V9.45M8.85 6.1V9.45M3.45 4.1L3.9 10.2C3.95 10.93 4.56 11.5 5.29 11.5H8.71C9.44 11.5 10.05 10.93 10.1 10.2L10.55 4.1" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </span>
                <span>删除</span>
            `;
            deleteButton.onclick = event => app.deleteSession(id, event, label);

            menu.appendChild(renameButton);
            menu.appendChild(deleteButton);
            actions.appendChild(menuTrigger);
            actions.appendChild(menu);

            row.appendChild(textButton);
            row.appendChild(actions);
            list.appendChild(row);
        });

        // "查看全部" button when items exceed limit
        if (!showAll && items.length > MAX_VISIBLE_HISTORY) {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'sb-show-all-btn';
            btn.textContent = `查看全部 (${items.length})`;
            btn.onclick = () => {
                historyUiState.showAll = true;
                app.renderHistoryList();
            };
            list.appendChild(btn);
        } else if (showAll && !historyUiState.searchQuery.trim() && items.length > MAX_VISIBLE_HISTORY) {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'sb-show-all-btn';
            btn.textContent = '收起';
            btn.onclick = () => {
                historyUiState.showAll = false;
                app.renderHistoryList();
            };
            list.appendChild(btn);
        }
    }

    app.renderHistoryList = function renderHistoryList() {
        closeHistoryMenu();
        renderHistoryItems(filterHistoryItems(historyUiState.items));
    };

    app.fetchHistory = async function fetchHistory() {
        const res = await fetch('/api/history');
        const data = await res.json();
        historyUiState.items = data.items || (data.threads || []).map(id => ({ thread_id: id, current_topic: '' }));
        if (!historyUiState.searchQuery.trim()) {
            historyUiState.showAll = false;
        }
        ensureHistorySearchBindings();
        app.renderHistoryList();
    };

    app.startNewSession = function startNewSession() {
        if (state.isVoiceListening) app.stopVoiceInput();
        resetRuntimeView();
        state.currentThreadId = app.makeThreadId();
        window.localStorage.setItem(LAST_THREAD_STORAGE_KEY, state.currentThreadId);
        app.setStatusBanner('新页已打开', 'ready');
        app.applyPrimaryActionState?.();
        app.updateSidebarState?.();
        app.refreshChatSurfaceState?.();
        app.fetchHistory();
    };

    app.deleteSession = async function deleteSession(id, event, label = id) {
        if (event) event.stopPropagation();
        closeHistoryMenu();
        if (!confirm(`确定要删掉这页学习记录吗？\n${label}`)) return;
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
            const awaitingInputState = runtime.awaiting_input_state || {};

            if (runtime.awaiting_input) {
                state.isAwaitingInput = true;
                app.setChatInputPlaceholder?.('输入你的解答，或先追问一个临时问题…');
                if (awaitingInputState.interaction_kind === 'next_step_selector') {
                    app.renderNextStepSelector?.(awaitingInputState.options || []);
                    app.setChatInputPlaceholder?.('也可以直接输入：继续深入 / 换个例子 / 来一道题 / 先总结一下');
                    app.setStatusBanner('等你决定下一步', 'awaiting');
                } else if (awaitingInputState.interaction_kind === 'post_eval_selector') {
                    app.renderPostEvalSelector?.(awaitingInputState.options || []);
                    app.setChatInputPlaceholder?.('也可以直接输入：继续拔高 / 换一道同类型 / 总结本轮收获');
                    app.setStatusBanner('等你决定下一步', 'awaiting');
                } else if (
                    data.state?.is_assessed
                    && data.state?.tutor_content
                    && !data.state?.tester_question
                    && data.state?.flow_status !== 'awaiting_interrupt_confirmation'
                ) {
                    app.renderNextStepSelector?.();
                    app.setChatInputPlaceholder?.('也可以直接输入：继续深入 / 换个例子 / 来一道题 / 先总结一下');
                    app.setStatusBanner('等你决定下一步', 'awaiting');
                } else {
                    app.setStatusBanner('等你继续', 'awaiting');
                }
            } else if (data.state.flow_status === 'awaiting_next_step_selector') {
                state.isAwaitingInput = true;
                app.setChatInputPlaceholder?.('也可以直接输入：继续深入 / 换个例子 / 来一道题 / 先总结一下');
                app.setStatusBanner('等你决定下一步', 'awaiting');
            } else if (data.state.flow_status === 'awaiting_post_eval_selector') {
                state.isAwaitingInput = true;
                app.setChatInputPlaceholder?.('也可以直接输入：继续拔高 / 换一道同类型 / 总结本轮收获');
                app.setStatusBanner('等你决定下一步', 'awaiting');
            } else if (runtime.is_running) {
                app.setChatInputPlaceholder?.();
                app.setStatusBanner('正在接回这页', 'processing');
                app.connectSSE?.();
            } else if (PRE_TOPIC_FLOW_STATUSES.has(data.state.flow_status)) {
                app.setChatInputPlaceholder?.();
                app.setStatusBanner('已回到这页', 'info');
            } else if (data.state.flow_status === 'awaiting_topic_confirmation') {
                app.setChatInputPlaceholder?.();
                app.setStatusBanner('等你确认主题', 'awaiting');
            } else if (data.state.flow_status === 'awaiting_interrupt_confirmation') {
                app.setChatInputPlaceholder?.();
                app.setStatusBanner('等你决定是否回主线', 'awaiting');
            } else if (data.state.flow_status === 'awaiting_assessment') {
                app.setChatInputPlaceholder?.();
                app.setStatusBanner('等你完成小测', 'awaiting');
            } else if (data.state.flow_status === 'assessment_dialog') {
                app.setChatInputPlaceholder?.();
                app.setStatusBanner('测评进行中', 'awaiting');
                // 重连 SSE 让后端重发当前题目
                app.connectSSE?.();
            } else {
                app.setChatInputPlaceholder?.();
                app.setStatusBanner('已回到这页', 'info');
            }
        } catch (err) {
            app.appendMessage('agent', `恢复失败：${err.message}`);
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

    ensureHistorySearchBindings();
})();
