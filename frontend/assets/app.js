(() => {
    const app = window.AITutorApp;

    function formatKnowledgeModeText(data) {
        if (!data) return '知识库状态未知';
        const retrievalMode = data.retrieval_mode === 'hybrid' ? 'Hybrid 检索' : 'Vector 检索';
        const parser = data.pdf_parse_backend === 'mineru' ? 'MinerU' : 'PyMuPDF';
        const parserHint = data.pdf_parse_backend === 'mineru' ? '云解析' : '本地解析';
        return `当前模式：${retrievalMode} | PDF 解析器：${parser}（${parserHint}）`;
    }

    async function refreshKnowledgeStatus(showSystemMessage = false) {
        const banner = document.getElementById('status-banner');
        if (!banner) return;
        try {
            const res = await fetch('/api/knowledge');
            const data = await res.json();
            const text = formatKnowledgeModeText(data);
            banner.innerText = text;
            if (showSystemMessage && app.appendSystemMessage) {
                app.appendSystemMessage(`${text}\n${data.pdf_parse_notice || ''}`.trim());
            }
        } catch (error) {
            banner.innerText = '系统就绪（知识库状态获取失败）';
        }
    }

    async function initializeApp() {
        await app.fetchHistory();
        await app.fetchConfig();
        await app.fetchLocalConfig();
        await refreshKnowledgeStatus(true);
    }

    function bindDomEvents() {
        document.getElementById('chat-input').addEventListener('keypress', e => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                app.handleSend();
            }
        });

        const fileInput = document.getElementById('file-input');
        fileInput.addEventListener('change', async function onFileChange() {
            if (!this.files.length) return;
            const formData = new FormData();
            formData.append('file', this.files[0]);
            const statusEl = document.getElementById('upload-status');
            statusEl.innerText = '⏳ 正在分析知识库...';
            try {
                const res = await fetch('/api/upload', { method: 'POST', body: formData });
                const data = await res.json();
                if (data.status === 'success') {
                    const parser = data.parse_backend === 'mineru' ? 'MinerU' : 'PyMuPDF';
                    const bm25Hint = data.bm25_rebuilt ? '，BM25 已重建' : '';
                    statusEl.innerText = `✅ ${data.filename} 注入成功（解析器：${parser}${bm25Hint}）`;
                    if (app.appendSystemMessage) {
                        app.appendSystemMessage(`知识库更新完成：${data.filename}，本次使用 ${parser} 解析 PDF。`);
                    }
                } else {
                    statusEl.innerText = `❌ 上传失败${data.message ? `：${data.message}` : ''}`;
                }
                await refreshKnowledgeStatus(false);
            } catch (error) {
                statusEl.innerText = '❌ 网络错误';
            }
            this.value = '';
        });
    }

    window.updateModelConfig = () => app.updateModelConfig();
    window.openLocalConfigPanel = () => app.openLocalConfigPanel();
    window.closeLocalConfigPanel = event => app.closeLocalConfigPanel(event);
    window.saveLocalConfig = () => app.saveLocalConfig();
    window.renderVendorModels = (vendorId, selectedModel) => app.renderVendorModels(vendorId, selectedModel);
    window.startNewSession = () => app.startNewSession();
    window.pauseCurrentSession = () => app.pauseCurrentSession();
    window.loadSession = id => app.loadSession(id);
    window.deleteSession = (id, event) => app.deleteSession(id, event);
    window.handleSend = () => app.handleSend();
    window.submitTopicConfirmation = confirmed => app.submitTopicConfirmation(confirmed);
    window.submitInterruptConfirmation = confirmed => app.submitInterruptConfirmation(confirmed);
    window.showTopicEditInput = () => app.showTopicEditInput();

    window.onload = async () => {
        bindDomEvents();
        await initializeApp();
    };
})();
