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
            container.innerHTML = '<div class="knowledge-empty">书架还是空的，先上传一份资料吧。</div>';
            return;
        }

        const rows = files.map(item => {
            const safeFilename = escapeHtml(item.filename);
            const chunkSuffix = Number.isInteger(item.chunk_count) ? ` · ${item.chunk_count} 段` : '';
            return `
                <div class="knowledge-item">
                    <div class="knowledge-main" title="${safeFilename}">
                        <div class="knowledge-name">${safeFilename}</div>
                        <div class="knowledge-meta">${formatFileSize(item.size_bytes)}${chunkSuffix}</div>
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
        if (!confirm(`确定要从书架移除这份资料吗？\n${filename}`)) return;

        app.setInlineStatus('upload-status', '正在从书架移除资料…', 'processing');
        try {
            const res = await fetch(`/api/knowledge/files/${encodeURIComponent(filename)}`, { method: 'DELETE' });
            const data = await res.json();
            if (data.status !== 'success') {
                app.setInlineStatus('upload-status', data.message || '移除失败，请稍后重试', 'danger');
                return;
            }
            app.setInlineStatus('upload-status', `${filename} 已从书架移除`, 'success');
            await fetchKnowledgeFiles();
        } catch (_error) {
            app.setInlineStatus('upload-status', '移除失败，网络可能暂时断开', 'danger');
        }
    }

    async function uploadKnowledgeFile(file) {
        if (!file) return;
        const formData = new FormData();
        formData.append('file', file);
        app.setInlineStatus('upload-status', '我在整理这份资料，请稍等一下…', 'processing');
        try {
            const res = await fetch('/api/upload', { method: 'POST', body: formData });
            const data = await res.json();
            app.setInlineStatus(
                'upload-status',
                data.status === 'success' ? `${data.filename} 已经放进参考资料里了` : '这份资料暂时没有添加成功',
                data.status === 'success' ? 'success' : 'danger'
            );
            if (data.status === 'success') {
                await fetchKnowledgeFiles();
            }
        } catch (_error) {
            app.setInlineStatus('upload-status', '上传时网络断开了，请稍后再试', 'danger');
        }
    }

    async function clearKnowledgeFiles() {
        const files = app.state.knowledgeFiles || [];
        if (!files.length) {
            app.setInlineStatus('upload-status', '书架已经是空的', 'muted');
            return;
        }
        if (!confirm('确定要清空书架里的所有资料吗？此操作不可恢复。')) return;

        app.setInlineStatus('upload-status', '正在清空书架…', 'processing');
        try {
            const res = await fetch('/api/knowledge/files', { method: 'DELETE' });
            const data = await res.json();
            if (data.status !== 'success') {
                app.setInlineStatus('upload-status', data.message || '清空失败，请稍后重试', 'danger');
                return;
            }
            app.setInlineStatus('upload-status', `已清空 ${data.removed || 0} 份资料`, 'success');
            await fetchKnowledgeFiles();
        } catch (_error) {
            app.setInlineStatus('upload-status', '清空失败，网络可能暂时断开', 'danger');
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
