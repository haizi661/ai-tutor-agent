(() => {
    const app = window.AITutorApp;
    const state = app.state;

    function getSpeechRecognitionCtor() {
        return window.SpeechRecognition || window.webkitSpeechRecognition || null;
    }

    function getChatInput() {
        return document.getElementById('chat-input');
    }

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
        sendButton.textContent = context.label;
        sendButton.disabled = context.disabled;
        sendButton.classList.toggle('is-stop', context.isStop);
        sendButton.setAttribute('aria-label', context.ariaLabel);
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
            app.setStatusBanner('当前浏览器暂不支持语音输入，仍可手动输入', 'warning');
            app.appendSystemMessage('当前浏览器暂不支持语音输入，仍可继续手动输入。', 'warning');
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
            app.setStatusBanner('我在听，你可以开口说了', 'info');
            app.appendSystemMessage('我在听，你可以先说，我会把识别结果写进输入框里。', 'info');
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
                'audio-capture': '没有检测到可用的麦克风设备，先继续手动输入也可以。',
                'network': '语音识别连接暂时断了一下，先继续手动输入也可以。',
                'not-allowed': '你刚刚拒绝了麦克风权限，所以这次先继续手动输入。',
                'service-not-allowed': '当前环境暂时不允许使用语音输入，先继续手动输入。',
                'no-speech': '刚才没有识别到清晰语音，你可以再试一次，或直接手动输入。',
                'aborted': '',
            };
            const message = errorMessages[event.error] ?? '语音输入暂时没有成功，先继续手动输入也可以。';
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
                    ? '语音已经写进输入框了；确认无误后，再手动发送就可以。'
                    : '这次语音输入已经结束；如果还没写出来，可以直接手动补充。';
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
            app.setStatusBanner('我先把收音停下了；内容还留在输入框里，不会自动发送', 'info');
            app.appendSystemMessage('我先把收音停下了；内容还留在输入框里，你确认后再手动发送。', 'info');
            clearVoiceNotice();
            return;
        }
        app.startVoiceInput();
    };

    async function initializeApp() {
        state.voiceInputSupported = Boolean(getSpeechRecognitionCtor());
        applyVoiceButtonState();
        await app.fetchHistory();
        await app.restoreLastSessionIfAny?.();
        await app.fetchKnowledgeFiles?.();
        await app.fetchConfig();
        await app.fetchLocalConfig();
        app.setStatusBanner('可以从一个想弄懂的问题开始', 'ready');
        app.setInlineStatus('upload-status', '', 'muted');
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
            if (e.key === 'Escape' && document.getElementById('config-overlay').classList.contains('open')) {
                app.closeLocalConfigPanel();
            }
        });

        document.addEventListener('visibilitychange', () => {
            if (document.hidden && state.isVoiceListening) {
                state.voicePendingNotice = 'hidden';
                app.stopVoiceInput();
                app.setStatusBanner('页面切到后台后，我先替你停掉了语音输入', 'info');
                app.appendSystemMessage('页面切到后台后，我先替你停掉了语音输入；输入框里的内容还在。', 'info');
                clearVoiceNotice();
            }
        });

        const fileInput = document.getElementById('file-input');
        fileInput.addEventListener('change', async function onFileChange() {
            if (!this.files.length) return;
            await app.uploadKnowledgeFile?.(this.files[0]);
            this.value = '';
        });
    }

    window.updateModelConfig = () => app.updateModelConfig();
    window.openLocalConfigPanel = () => app.openLocalConfigPanel();
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
    window.submitTopicConfirmation = confirmed => app.submitTopicConfirmation(confirmed);
    window.showTopicEditInput = () => app.showTopicEditInput();

    window.onload = async () => {
        bindDomEvents();
        await initializeApp();
    };
})();
