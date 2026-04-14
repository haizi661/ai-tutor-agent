(() => {
    const app = window.AITutorApp;

    function formatFileSize(bytes) {
        if (typeof bytes !== 'number' || Number.isNaN(bytes) || bytes < 0) return '未知大小';
        if (bytes < 1024) return `${bytes} B`;
        const kb = bytes / 1024;
        if (kb < 1024) return `${kb.toFixed(1)} KB`;
        const mb = kb / 1024;
        return `${mb.toFixed(1)} MB`;
    }

    function escapeHtml(text) {
        return String(text)
            .replaceAll('&', '&amp;')
            .replaceAll('<', '&lt;')
            .replaceAll('>', '&gt;')
            .replaceAll('"', '&quot;')
            .replaceAll("'", '&#39;');
    }

    function renderKnowledgeShelf() {
        const container = document.getElementById('knowledge-shelf');
        if (!container) return;

        const files = app.state.knowledgeFiles || [];
        if (!files.length) {
            container.innerHTML = '<div class="knowledge-empty">还没有参考资料。</div>';
            return;
        }

        const rows = files.map(item => {
            const safeFilename = escapeHtml(item.filename);
            const chunkSuffix = Number.isInteger(item.chunk_count) ? `${item.chunk_count}段 · ` : '';
            return `
                <div class="knowledge-item ref-item">
                    <div class="ref-icon" aria-hidden="true">
                        <svg viewBox="0 0 16 16"><path d="M3 2h10v12H3V2zm2 3h6M5 8h6M5 11h4"/></svg>
                    </div>
                    <div class="knowledge-main ref-info" title="${safeFilename}">
                        <div class="knowledge-name ref-name">${safeFilename}</div>
                        <div class="knowledge-meta ref-meta">${chunkSuffix}${formatFileSize(item.size_bytes)}</div>
                    </div>
                    <button type="button" class="knowledge-delete" data-filename="${safeFilename}" aria-label="删除资料 ${safeFilename}">移除</button>
                </div>
            `;
        }).join('');

        container.innerHTML = `<div class="knowledge-list">${rows}</div>`;
    }

    async function fetchKnowledgeFiles() {
        try {
            const res = await fetch('/api/knowledge/files');
            const data = await res.json();
            app.patchState({ knowledgeFiles: data.items || [] }, 'knowledge.fetch');
        } catch (_error) {
            app.patchState({ knowledgeFiles: [] }, 'knowledge.fetch.error');
        }
    }

    async function deleteKnowledgeFile(filename) {
        if (!filename) return;
        if (!confirm(`确定移除这份资料吗？\n${filename}`)) return;

        app.setInlineStatus('upload-status', '正在移除…', 'processing');
        try {
            const res = await fetch(`/api/knowledge/files/${encodeURIComponent(filename)}`, { method: 'DELETE' });
            const data = await res.json();
            if (data.status !== 'success') {
                app.setInlineStatus('upload-status', data.message || '移除失败', 'danger');
                return;
            }
            app.setInlineStatus('upload-status', `${filename} 已移除`, 'success');
            await fetchKnowledgeFiles();
        } catch (_error) {
            app.setInlineStatus('upload-status', '移除失败', 'danger');
        }
    }

    async function uploadKnowledgeFile(file) {
        if (!file) return;
        const formData = new FormData();
        formData.append('file', file);
        app.setInlineStatus('upload-status', '正在整理资料…', 'processing');
        try {
            const res = await fetch('/api/upload', { method: 'POST', body: formData });
            const data = await res.json();
            app.setInlineStatus(
                'upload-status',
                data.status === 'success' ? `${data.filename} 已加入资料区` : '添加失败',
                data.status === 'success' ? 'success' : 'danger'
            );
            if (data.status === 'success') {
                await fetchKnowledgeFiles();
            }
        } catch (_error) {
            app.setInlineStatus('upload-status', '上传失败', 'danger');
        }
    }

    async function clearKnowledgeFiles() {
        const files = app.state.knowledgeFiles || [];
        if (!files.length) {
            app.setInlineStatus('upload-status', '资料区为空', 'muted');
            return;
        }
        if (!confirm('确定清空所有资料吗？这会同时删除对应向量。')) return;

        app.setInlineStatus('upload-status', '正在清空…', 'processing');
        try {
            const res = await fetch('/api/knowledge/files', { method: 'DELETE' });
            const data = await res.json();
            if (data.status !== 'success') {
                app.setInlineStatus('upload-status', data.message || '清空失败', 'danger');
                return;
            }
            app.setInlineStatus('upload-status', `已清空 ${data.removed || 0} 份资料`, 'success');
            await fetchKnowledgeFiles();
        } catch (_error) {
            app.setInlineStatus('upload-status', '清空失败', 'danger');
        }
    }

    app.fetchKnowledgeFiles = fetchKnowledgeFiles;
    app.uploadKnowledgeFile = uploadKnowledgeFile;

    app.subscribeState((state, source) => {
        if (!source.startsWith('knowledge.')) return;
        renderKnowledgeShelf(state.knowledgeFiles || []);
    });

    document.addEventListener('click', event => {
        const button = event.target.closest('.knowledge-delete');
        if (!button) return;
        deleteKnowledgeFile(button.dataset.filename || '');
    });

    document.getElementById('clear-knowledge-btn')?.addEventListener('click', () => {
        clearKnowledgeFiles();
    });

    app.renderKnowledgeShelf = renderKnowledgeShelf;
})();
