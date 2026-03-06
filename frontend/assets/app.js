(() => {
    const app = window.AITutorApp;

    async function initializeApp() {
        await app.fetchHistory();
        await app.fetchConfig();
        await app.fetchLocalConfig();
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
                statusEl.innerText = data.status === 'success' ? `✅ ${data.filename} 注入成功` : '❌ 上传失败';
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
    window.showTopicEditInput = () => app.showTopicEditInput();

    window.onload = async () => {
        bindDomEvents();
        await initializeApp();
    };
})();
