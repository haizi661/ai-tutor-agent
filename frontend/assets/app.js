(() => {
    const app = window.AITutorApp;
    const state = app.state;
    const HEADER_COLLAPSE_STORAGE_KEY = 'ai_tutor_header_collapsed';

    function getSpeechRecognitionCtor() {
        return window.SpeechRecognition || window.webkitSpeechRecognition || null;
    }

    function getChatInput() {
        return document.getElementById('chat-input');
    }

    const PRIMARY_ACTION_ICONS = {
        send: `
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                <path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        `,
        stop: `
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                <rect x="4.25" y="4.25" width="7.5" height="7.5" rx="1.5" fill="currentColor"/>
            </svg>
        `,
    };

    function syncVoiceInputValue() {
        const input = getChatInput();
        if (!input) return;
        const nextValue = `${state.voiceInputBase || ''}${state.voiceFinalTranscript || ''}${state.voiceInterimTranscript || ''}`;
        input.value = nextValue;
        app.applyPrimaryActionState?.();
    }

    function resetVoiceTracking({ preserveInput = true } = {}) {
        if (!preserveInput) {
            state.voiceInputBase = '';
            state.voiceFinalTranscript = '';
            state.voiceInterimTranscript = '';
            syncVoiceInputValue();
            return;
        }
        const input = getChatInput();
        state.voiceInputBase = input ? input.value : '';
        state.voiceFinalTranscript = '';
        state.voiceInterimTranscript = '';
    }

    function clearVoiceNotice() {
        state.voicePendingNotice = null;
    }

    function applyHeaderCollapsedState(collapsed) {
        const nextCollapsed = Boolean(collapsed);
        document.body.classList.toggle('header-collapsed', nextCollapsed);

        const collapseButton = document.getElementById('header-collapse-btn');
        if (collapseButton) {
            collapseButton.setAttribute('aria-expanded', nextCollapsed ? 'false' : 'true');
        }

        const compactToggle = document.getElementById('header-compact-toggle');
        if (compactToggle) {
            compactToggle.hidden = !nextCollapsed;
            compactToggle.setAttribute('aria-hidden', nextCollapsed ? 'false' : 'true');
        }

        app.patchState?.({ headerCollapsed: nextCollapsed }, 'header-collapse');
    }

    function applyVoiceButtonState() {
        const micButton = document.getElementById('mic-btn');
        if (!micButton) return;
        const supported = state.voiceInputSupported !== false;
        micButton.disabled = false;
        micButton.classList.toggle('is-listening', Boolean(state.isVoiceListening));
        micButton.setAttribute('aria-pressed', state.isVoiceListening ? 'true' : 'false');
        micButton.textContent = state.isVoiceListening ? '收音中' : '语音';
        micButton.setAttribute(
            'aria-label',
            supported
                ? (state.isVoiceListening ? '停止语音输入' : '开始语音输入')
                : '当前浏览器不支持语音输入'
        );
    }

    function getPrimaryActionContext() {
        const input = getChatInput();
        const hasText = Boolean(input?.value.trim());
        if (state.isStreaming) {
            return {
                label: '停止',
                disabled: false,
                ariaLabel: '停止当前生成',
                isStop: true,
            };
        }
        if (state.isAwaitingInput || hasText) {
            return {
                label: '发送',
                disabled: false,
                ariaLabel: state.isAwaitingInput ? '发送补充内容' : '发送当前输入',
                isStop: false,
            };
        }
        return {
            label: '发送',
            disabled: true,
            ariaLabel: '输入内容后发送',
            isStop: false,
        };
    }

    app.applyPrimaryActionState = function applyPrimaryActionState() {
        const sendButton = document.getElementById('send-btn');
        if (!sendButton) return;
        const pauseButton = document.getElementById('pause-btn');
        if (pauseButton) {
            pauseButton.hidden = true;
            pauseButton.setAttribute('aria-hidden', 'true');
            pauseButton.tabIndex = -1;
        }
        const context = getPrimaryActionContext();
        const mode = context.isStop ? 'stop' : 'send';
        if (sendButton.dataset.mode !== mode) {
            sendButton.innerHTML = PRIMARY_ACTION_ICONS[mode];
            sendButton.dataset.mode = mode;
        }
        sendButton.disabled = context.disabled;
        sendButton.classList.toggle('is-stop', context.isStop);
        sendButton.setAttribute('aria-label', context.ariaLabel);
        sendButton.title = context.ariaLabel;
    };

    app.handlePrimaryAction = function handlePrimaryAction() {
        if (state.isVoiceListening) app.stopVoiceInput();
        if (state.isStreaming) {
            app.pauseCurrentSession();
            return;
        }
        const input = getChatInput();
        const hasText = Boolean(input?.value.trim());
        if (state.isAwaitingInput || hasText) app.handleSend();
    };

    app.setHeaderCollapsed = function setHeaderCollapsed(collapsed, { persist = true } = {}) {
        applyHeaderCollapsedState(collapsed);
        if (persist) {
            window.localStorage.setItem(HEADER_COLLAPSE_STORAGE_KEY, collapsed ? '1' : '0');
        }
    };

    app.toggleHeaderCollapsed = function toggleHeaderCollapsed(force) {
        const collapsed = typeof force === 'boolean' ? force : !state.headerCollapsed;
        app.setHeaderCollapsed(collapsed);
    };

    function setModalOpen(modalId, open) {
        const modal = document.getElementById(modalId);
        if (!modal) return;
        modal.classList.toggle('open', Boolean(open));
        modal.setAttribute('aria-hidden', open ? 'false' : 'true');
    }

    function setButtonActive(buttonId, active) {
        const button = document.getElementById(buttonId);
        if (!button) return;
        button.classList.toggle('active', Boolean(active));
    }

    function focusChatInput() {
        document.getElementById('chat-input')?.focus();
    }

    function applyStarterPrompt(prompt, { submit = true } = {}) {
        const input = getChatInput();
        if (!input) return;
        input.value = String(prompt || '').trim();
        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.focus();
        if (submit) app.handlePrimaryAction?.();
    }

    function buildKnowledgeGraphUrl({ embedded = true } = {}) {
        const params = new URLSearchParams();
        const topic = (state.currentTopic || state.graphTopicHint || '').trim();
        const focus = (state.currentGraphNode || state.currentTopicFocus || '').trim();
        if (topic) params.set('topic', topic);
        if (focus) params.set('focus', focus);
        if (embedded) params.set('embedded', '1');
        return `/knowledge-graph/a2/viewer/index.html?${params.toString()}`;
    }

    app.openKnowledgeGraphModal = function openKnowledgeGraphModal() {
        const iframe = document.getElementById('knowledge-graph-frame');
        if (iframe) {
            const nextSrc = buildKnowledgeGraphUrl({ embedded: true });
            if (iframe.dataset.src !== nextSrc) {
                iframe.src = nextSrc;
                iframe.dataset.src = nextSrc;
            }
        }
        setModalOpen('knowledge-graph-modal', true);
        setButtonActive('open-graph-modal-btn', true);
        app.patchState?.({ knowledgeGraphModalOpen: true }, 'knowledge-graph-modal');
    };

    app.refreshKnowledgeGraphModal = function refreshKnowledgeGraphModal() {
        const iframe = document.getElementById('knowledge-graph-frame');
        if (!iframe) return;
        const nextSrc = buildKnowledgeGraphUrl({ embedded: true });
        iframe.src = nextSrc;
        iframe.dataset.src = nextSrc;
    };

    app.closeKnowledgeGraphModal = function closeKnowledgeGraphModal(event) {
        if (event && event.target && event.target !== event.currentTarget) return;
        setModalOpen('knowledge-graph-modal', false);
        setButtonActive('open-graph-modal-btn', false);
        app.patchState?.({ knowledgeGraphModalOpen: false }, 'knowledge-graph-modal');
        focusChatInput();
    };

    app.openKnowledgeGraphStandalone = function openKnowledgeGraphStandalone() {
        window.open(buildKnowledgeGraphUrl({ embedded: false }), '_blank', 'noopener,noreferrer');
    };

    app.openRadarModal = function openRadarModal() {
        setModalOpen('radar-modal', true);
        setButtonActive('open-radar-modal-btn', true);
        app.patchState?.({ radarModalOpen: true }, 'radar-modal');
        if (state.latestRadarData) {
            app.showRadar?.(state.latestRadarData);
        }
    };

    app.closeRadarModal = function closeRadarModal(event) {
        if (event && event.target && event.target !== event.currentTarget) return;
        setModalOpen('radar-modal', false);
        setButtonActive('open-radar-modal-btn', false);
        app.patchState?.({ radarModalOpen: false }, 'radar-modal');
        focusChatInput();
    };

    app.stopVoiceInput = function stopVoiceInput(options = {}) {
        const { preserveInput = true } = options;
        const recognition = state.speechRecognition;
        if (recognition) {
            state.voiceStopInitiated = true;
            recognition.onresult = null;
            recognition.onerror = null;
            recognition.onend = null;
            recognition.stop();
        }
        state.speechRecognition = null;
        state.isVoiceListening = false;
        applyVoiceButtonState();
        resetVoiceTracking({ preserveInput });
        app.applyPrimaryActionState?.();
    };

    app.startVoiceInput = function startVoiceInput() {
        const SpeechRecognitionCtor = getSpeechRecognitionCtor();
        if (!SpeechRecognitionCtor) {
            state.voiceInputSupported = false;
            applyVoiceButtonState();
            app.setStatusBanner('当前浏览器不支持语音输入', 'warning');
            app.appendSystemMessage('当前浏览器不支持语音输入。', 'warning');
            return;
        }

        if (state.isVoiceListening) return;

        const input = getChatInput();
        state.voiceInputSupported = true;
        state.voiceStopInitiated = false;
        state.voiceInputBase = input ? input.value : '';
        state.voiceFinalTranscript = '';
        state.voiceInterimTranscript = '';

        const recognition = new SpeechRecognitionCtor();
        recognition.lang = 'zh-CN';
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.maxAlternatives = 1;

        recognition.onstart = () => {
            state.isVoiceListening = true;
            clearVoiceNotice();
            applyVoiceButtonState();
            app.applyPrimaryActionState?.();
            app.setStatusBanner('我在听', 'info');
            app.appendSystemMessage('我在听。', 'info');
        };

        recognition.onresult = event => {
            let finalTranscript = '';
            let interimTranscript = '';
            for (let i = 0; i < event.results.length; i += 1) {
                const result = event.results[i];
                const transcript = result[0]?.transcript || '';
                if (result.isFinal) finalTranscript += transcript;
                else interimTranscript += transcript;
            }
            state.voiceFinalTranscript = finalTranscript;
            state.voiceInterimTranscript = interimTranscript;
            syncVoiceInputValue();
        };

        recognition.onerror = event => {
            state.isVoiceListening = false;
            state.speechRecognition = null;
            state.voiceStopInitiated = false;
            state.voicePendingNotice = 'error';
            applyVoiceButtonState();
            resetVoiceTracking();
            app.applyPrimaryActionState?.();

            const errorMessages = {
                'audio-capture': '没有检测到麦克风。',
                'network': '语音识别连接断开。',
                'not-allowed': '麦克风权限未开启。',
                'service-not-allowed': '当前环境不允许语音输入。',
                'no-speech': '没有识别到清晰语音。',
                'aborted': '',
            };
            const message = errorMessages[event.error] ?? '语音输入失败。';
            if (!message) return;
            app.setStatusBanner(message, event.error === 'network' ? 'warning' : 'info');
            app.appendSystemMessage(message, event.error === 'network' ? 'warning' : 'info');
        };

        recognition.onend = () => {
            const shouldShowNotice = !state.voiceStopInitiated && !state.voicePendingNotice;
            state.speechRecognition = null;
            state.isVoiceListening = false;
            state.voiceStopInitiated = false;
            applyVoiceButtonState();
            resetVoiceTracking();
            app.applyPrimaryActionState?.();
            if (shouldShowNotice) {
                const hasResult = Boolean((state.voiceInputBase || '').trim());
                const message = hasResult
                    ? '内容已写入输入框。'
                    : '语音输入已结束。';
                app.setStatusBanner(message, 'info');
                app.appendSystemMessage(message, 'info');
            }
            clearVoiceNotice();
        };

        state.speechRecognition = recognition;
        applyVoiceButtonState();
        recognition.start();
    };

    app.toggleVoiceInput = function toggleVoiceInput() {
        if (state.isVoiceListening) {
            state.voicePendingNotice = 'manual-stop';
            app.stopVoiceInput();
            app.setStatusBanner('已停止收音', 'info');
            app.appendSystemMessage('已停止收音。', 'info');
            clearVoiceNotice();
            return;
        }
        app.startVoiceInput();
    };

    const SIDEBAR_COLLAPSE_STORAGE_KEY = 'ai_tutor_sidebar_collapsed';

    function setHeaderMoreMenuOpen(open) {
        const menu = document.getElementById('header-more-menu');
        const trigger = document.getElementById('header-more-btn');
        if (!menu || !trigger) return;
        const nextOpen = Boolean(open);
        menu.hidden = !nextOpen;
        trigger.setAttribute('aria-expanded', nextOpen ? 'true' : 'false');
    }

    function updateSidebarToggleButton(collapsed) {
        const toggleButton = document.getElementById('sidebar-toggle-btn');
        if (!toggleButton) return;
        const nextCollapsed = Boolean(collapsed);
        toggleButton.setAttribute('aria-expanded', nextCollapsed ? 'false' : 'true');
        toggleButton.setAttribute('aria-label', nextCollapsed ? '展开侧边栏' : '收起侧边栏');
        toggleButton.title = nextCollapsed ? '展开侧边栏' : '收起侧边栏';
        toggleButton.classList.toggle('is-collapsed', nextCollapsed);
    }

    function setUserMenuOpen(open) {
        const slot = document.getElementById('sb-user-slot');
        const panel = document.getElementById('sb-user-menu-panel');
        const trigger = document.getElementById('sb-userbar-btn');
        if (!slot || !panel || !trigger) return;
        const nextOpen = Boolean(open);
        slot.classList.toggle('is-open', nextOpen);
        panel.hidden = !nextOpen;
        trigger.setAttribute('aria-expanded', nextOpen ? 'true' : 'false');
    }

    app.toggleUserMenu = function toggleUserMenu(force) {
        const panel = document.getElementById('sb-user-menu-panel');
        if (!panel) return;
        const shouldOpen = typeof force === 'boolean' ? force : panel.hidden;
        if (shouldOpen && document.getElementById('sidebar')?.classList.contains('sidebar--collapsed')) {
            app.toggleSidebar?.(false);
        }
        setUserMenuOpen(shouldOpen);
    };

    app.handleUserMenuAction = function handleUserMenuAction(action) {
        app.toggleUserMenu(false);

        if (action === 'personalize') {
            app.openLocalConfigPanel?.('personalization');
            return;
        }

        if (action === 'profile') {
            app.openLocalConfigPanel?.('account');
            return;
        }

        if (action === 'settings') {
            app.openLocalConfigPanel?.('applications');
            return;
        }

        if (action === 'help') {
            app.setStatusBanner('帮助入口暂未拆页；当前可用入口已保留在侧边栏。', 'info');
            app.appendSystemMessage?.('当前可直接使用：上传资料、切换模型、本地设置、知识图谱。', 'info');
            return;
        }

        if (action === 'signout') {
            window.localStorage.removeItem('ai_tutor_last_thread_id');
            app.setStatusBanner('当前没有真实登录态，已清空默认恢复入口。', 'success');
        }
    };

    app.toggleHeaderMoreMenu = function toggleHeaderMoreMenu(force) {
        const menu = document.getElementById('header-more-menu');
        if (!menu) return;
        const shouldOpen = typeof force === 'boolean' ? force : menu.hidden;
        setHeaderMoreMenuOpen(shouldOpen);
    };

    app.shareCurrentSession = async function shareCurrentSession() {
        const title = String(state.currentTopic || document.getElementById('header-thread-title')?.textContent || '新对话').trim();
        const shareData = {
            title: `AI Tutor · ${title}`,
            text: title === '新对话' ? '来一起开始新的控制理论学习页。' : `一起看这页学习记录：${title}`,
            url: window.location.href,
        };

        try {
            if (navigator.share) {
                await navigator.share(shareData);
            } else if (navigator.clipboard?.writeText) {
                await navigator.clipboard.writeText(`${shareData.title}\n${shareData.text}\n${shareData.url}`);
                app.setStatusBanner('分享内容已复制', 'success');
            } else {
                throw new Error('share-not-supported');
            }
        } catch (error) {
            if (error?.name === 'AbortError') return;
            if (!navigator.clipboard?.writeText) {
                app.setStatusBanner('当前环境不支持分享，请手动复制链接', 'warning');
                return;
            }
            try {
                await navigator.clipboard.writeText(`${shareData.title}\n${shareData.text}\n${shareData.url}`);
                app.setStatusBanner('分享内容已复制', 'success');
            } catch (_clipboardError) {
                app.setStatusBanner('分享失败，请稍后重试', 'warning');
            }
        }
    };

    app.triggerKnowledgeUpload = function triggerKnowledgeUpload() {
        document.getElementById('file-input')?.click();
    };

    app.focusKnowledgeShelf = function focusKnowledgeShelf() {
        const shelf = document.getElementById('knowledge-shelf');
        if (!shelf) return;
        if (document.getElementById('sidebar')?.classList.contains('sidebar--collapsed')) {
            app.toggleSidebar?.(false);
        }
        shelf.scrollIntoView({ behavior: 'smooth', block: 'start' });
        app.setStatusBanner('已定位到资料区', 'info');
    };

    app.toggleThinkingMode = function toggleThinkingMode(force, { silent = false } = {}) {
        const nextThinkingMode = typeof force === 'boolean' ? force : !Boolean(state.thinkingMode);
        state.thinkingMode = nextThinkingMode;
        const button = document.getElementById('thinking-toggle-btn');
        if (button) {
            button.classList.toggle('is-active', nextThinkingMode);
            button.setAttribute('aria-pressed', nextThinkingMode ? 'true' : 'false');
            button.title = nextThinkingMode ? '当前为思考模式' : '当前为标准模式';
        }
        if (!silent) {
            app.setStatusBanner(nextThinkingMode ? '已切换到思考模式' : '已切换到标准模式', 'info');
        }
    };

    app.toggleSidebar = function toggleSidebar(force) {
        const sidebar = document.getElementById('sidebar');
        if (!sidebar) return;
        const collapsed = typeof force === 'boolean' ? force : !sidebar.classList.contains('sidebar--collapsed');
        sidebar.classList.toggle('sidebar--collapsed', collapsed);
        document.body.classList.toggle('sidebar-collapsed', collapsed);
        if (collapsed) {
            app.toggleHistorySearch?.(false);
            app.toggleUserMenu?.(false);
        }
        updateSidebarToggleButton(collapsed);
        window.localStorage.setItem(SIDEBAR_COLLAPSE_STORAGE_KEY, collapsed ? '1' : '0');
    };

    async function initializeApp() {
        state.voiceInputSupported = Boolean(getSpeechRecognitionCtor());
        applyVoiceButtonState();
        app.setHeaderCollapsed(window.localStorage.getItem(HEADER_COLLAPSE_STORAGE_KEY) === '1', { persist: false });
        document.body.classList.remove('sidebar-collapsed');
        updateSidebarToggleButton(false);
        app.toggleThinkingMode(false, { silent: true });
        app.toggleHeaderMoreMenu(false);
        if (window.localStorage.getItem(SIDEBAR_COLLAPSE_STORAGE_KEY) === '1') {
            app.toggleSidebar(true);
        }
        await app.fetchHistory();
        await app.restoreLastSessionIfAny?.();
        await app.fetchKnowledgeFiles?.();
        await app.fetchConfig();
        await app.fetchLocalConfig();
        app.renderUserKnowledgeMap?.();
        app.updateSidebarState?.();
        app.refreshChatSurfaceState?.();
        app.setStatusBanner('', 'ready');
        app.setInlineStatus('upload-status', '', 'muted');
        app.updateLearningProgress?.({ step: 1, label: '学习进度 1/5' });
        app.applyPrimaryActionState();
    }

    function bindDomEvents() {
        const chatInput = document.getElementById('chat-input');
        chatInput.addEventListener('keypress', e => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                app.handlePrimaryAction();
                // Reset height after send
                setTimeout(() => {
                    chatInput.style.height = 'auto';
                }, 0);
            }
        });
        chatInput.addEventListener('input', function() {
            // Auto-resize logic
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
            app.applyPrimaryActionState();
        });

        document.addEventListener('keydown', e => {
            if (e.key === 'Escape') {
                app.toggleHeaderMoreMenu(false);
                app.toggleUserMenu(false);
            }
            if (e.key === 'Escape' && document.getElementById('config-overlay').classList.contains('open')) {
                app.closeLocalConfigPanel();
                return;
            }
            if (e.key === 'Escape' && state.knowledgeGraphModalOpen) {
                app.closeKnowledgeGraphModal();
                return;
            }
            if (e.key === 'Escape' && state.radarModalOpen) {
                app.closeRadarModal();
            }
        });

        document.addEventListener('visibilitychange', () => {
            if (document.hidden && state.isVoiceListening) {
                state.voicePendingNotice = 'hidden';
                app.stopVoiceInput();
                app.setStatusBanner('页面切到后台，已停止收音', 'info');
                app.appendSystemMessage('页面切到后台，已停止收音。', 'info');
                clearVoiceNotice();
            }
        });

        const fileInput = document.getElementById('file-input');
        fileInput.addEventListener('change', async function onFileChange() {
            if (!this.files.length) return;
            await app.uploadKnowledgeFile?.(this.files[0]);
            this.value = '';
        });

        document.addEventListener('click', event => {
            const menu = document.getElementById('header-more-menu');
            const trigger = document.getElementById('header-more-btn');
            if (!menu || !trigger || menu.hidden) return;
            if (menu.contains(event.target) || trigger.contains(event.target)) return;
            app.toggleHeaderMoreMenu(false);
        });

        document.addEventListener('click', event => {
            const slot = document.getElementById('sb-user-slot');
            const panel = document.getElementById('sb-user-menu-panel');
            if (!slot || !panel || panel.hidden) return;
            if (slot.contains(event.target)) return;
            app.toggleUserMenu(false);
        });

        document.querySelectorAll('[data-starter-prompt]').forEach(button => {
            button.addEventListener('click', () => {
                applyStarterPrompt(button.dataset.starterPrompt || '');
            });
        });

        document.querySelectorAll('[data-landing-action="graph"]').forEach(button => {
            button.addEventListener('click', () => {
                app.openKnowledgeGraphModal?.();
            });
        });

        window.addEventListener('message', event => {
            const payload = event.data || {};
            if (payload?.type === 'a2-graph-viewer:learn-node') {
                const topic = String(payload.nodeId || '').trim();
                if (!topic) return;
                const input = document.getElementById('chat-input');
                if (input) {
                    input.value = `继续讲 ${topic}`;
                    input.focus();
                    input.dispatchEvent(new Event('input', { bubbles: true }));
                }
                app.setStatusBanner(`已带回：${topic}`, 'info');
                return;
            }
            if (payload?.type === 'a2-graph-viewer:status') {
                const subtitle = document.getElementById('knowledge-graph-subtitle');
                if (subtitle && payload.message) subtitle.textContent = String(payload.message);
            }
        });
    }

    window.updateModelConfig = () => app.updateModelConfig();
    window.openLocalConfigPanel = sectionId => app.openLocalConfigPanel(sectionId);
    window.closeLocalConfigPanel = event => app.closeLocalConfigPanel(event);
    window.saveLocalConfig = () => app.saveLocalConfig();
    window.testConnection = () => app.testConnection();
    window.renderVendorModels = (vendorId, selectedModel) => app.renderVendorModels(vendorId, selectedModel);
    window.startNewSession = () => app.startNewSession();
    window.pauseCurrentSession = () => app.pauseCurrentSession();
    window.toggleVoiceInput = () => app.toggleVoiceInput();
    window.loadSession = id => app.loadSession(id);
    window.deleteSession = (id, event) => app.deleteSession(id, event);
    window.handlePrimaryAction = () => app.handlePrimaryAction();
    window.handleSend = () => app.handleSend();
    window.toggleHeaderCollapsed = force => app.toggleHeaderCollapsed(force);
    window.toggleHeaderMoreMenu = force => app.toggleHeaderMoreMenu(force);
    window.toggleSidebar = force => app.toggleSidebar(force);
    window.shareCurrentSession = () => app.shareCurrentSession();
    window.triggerKnowledgeUpload = () => app.triggerKnowledgeUpload();
    window.focusKnowledgeShelf = () => app.focusKnowledgeShelf();
    window.toggleHistorySearch = force => app.toggleHistorySearch(force);
    window.toggleThinkingMode = force => app.toggleThinkingMode(force);
    window.toggleUserMenu = force => app.toggleUserMenu(force);
    window.handleUserMenuAction = action => app.handleUserMenuAction(action);
    window.openKnowledgeGraphModal = () => app.openKnowledgeGraphModal();
    window.closeKnowledgeGraphModal = event => app.closeKnowledgeGraphModal(event);
    window.refreshKnowledgeGraphModal = () => app.refreshKnowledgeGraphModal();
    window.openKnowledgeGraphStandalone = () => app.openKnowledgeGraphStandalone();
    window.openRadarModal = () => app.openRadarModal();
    window.closeRadarModal = event => app.closeRadarModal(event);
    window.submitTopicConfirmation = (confirmed, startMode) => app.submitTopicConfirmation(confirmed, startMode);
    window.submitAwaitingChoice = (answer, visibleText) => app.submitAwaitingChoice(answer, visibleText);
    window.submitInterruptConfirmation = confirmed => app.submitInterruptConfirmation(confirmed);
    window.showTopicEditInput = () => app.showTopicEditInput();

    window.onload = async () => {
        bindDomEvents();
        await initializeApp();
    };
})();
