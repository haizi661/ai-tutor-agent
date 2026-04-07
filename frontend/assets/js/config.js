(() => {
    const app = window.AITutorApp;
    const state = app.state;

    app.populateModelOptions = function populateModelOptions(profiles, current) {
        const select = document.getElementById('model-select');
        select.innerHTML = '';
        profiles.forEach(profile => {
            const option = document.createElement('option');
            option.value = profile.id;
            option.textContent = profile.label + (profile.configured ? '' : '（尚未配置）');
            option.disabled = !profile.configured;
            select.appendChild(option);
        });

        if (current && current.chat_profile && !select.querySelector(`option[value="${current.chat_profile}"]`)) {
            const option = document.createElement('option');
            option.value = current.chat_profile;
            option.textContent = `${current.chat_profile}（当前自定义）`;
            select.appendChild(option);
        }
    };

    app.getVendorCatalog = function getVendorCatalog(vendorId) {
        return state.vendorCatalogs.find(vendor => vendor.id === vendorId) || null;
    };

    app.getStoredApiKey = function getStoredApiKey(vendorId, data = state.localConfig) {
        if (!data) return '';
        if (vendorId === 'gemini') return data.gemini_api_key || data.google_api_key || '';
        if (vendorId === 'qwen') return data.qwen_api_key || '';
        if (vendorId === 'deepseek') return data.deepseek_api_key || '';
        if (vendorId === 'openai') return data.openai_api_key || '';
        if (vendorId === 'minimax') return data.minimax_api_key || '';
        if (vendorId === 'glm') return data.glm_api_key || '';
        if (vendorId === 'custom') {
            return data.llm_provider === 'google' ? (data.google_api_key || '') : (data.openai_api_key || '');
        }
        return '';
    };

    app.getStoredApiKeyHint = function getStoredApiKeyHint(vendorId, data = state.localConfig) {
        const masked = app.getStoredApiKey(vendorId, data);
        return masked ? `已保存：${masked}` : '只在本地保存';
    };

    app.renderVendorOptions = function renderVendorOptions(selectedVendor) {
        const select = document.getElementById('local-chat-profile');
        select.innerHTML = '';
        state.vendorCatalogs.forEach(vendor => {
            const option = document.createElement('option');
            option.value = vendor.id;
            option.textContent = vendor.label + (!vendor.configured && !vendor.custom ? '（尚未配置）' : '');
            select.appendChild(option);
        });
        select.value = selectedVendor || 'gemini';
    };

    app.renderVendorModels = function renderVendorModels(vendorId, selectedModel) {
        const vendor = app.getVendorCatalog(vendorId);
        const select = document.getElementById('local-model-select');
        const keyLabel = document.getElementById('local-api-key-label');
        const keyInput = document.getElementById('local-api-key');
        const customFields = [
            document.getElementById('custom-provider-field'),
            document.getElementById('custom-model-field'),
            document.getElementById('custom-base-field'),
        ];
        const advanced = document.getElementById('local-advanced-details');

        select.innerHTML = '';
        if (vendor && vendor.models && vendor.models.length) {
            vendor.models.forEach(model => {
                const option = document.createElement('option');
                option.value = model.id;
                option.textContent = model.label;
                select.appendChild(option);
            });
            const desiredModel = selectedModel || vendor.default_model;
            if (!select.querySelector(`option[value="${desiredModel}"]`) && desiredModel) {
                const option = document.createElement('option');
                option.value = desiredModel;
                option.textContent = `${desiredModel}（当前）`;
                select.appendChild(option);
            }
            select.value = desiredModel || vendor.default_model || '';
            select.disabled = false;
        } else {
            const option = document.createElement('option');
            option.value = selectedModel || '';
            option.textContent = selectedModel || '请在高级项里手动填写模型';
            select.appendChild(option);
            select.value = selectedModel || '';
            select.disabled = true;
        }

        keyLabel.textContent = vendor ? vendor.api_key_label : 'API Key';
        keyInput.value = '';
        keyInput.placeholder = app.getStoredApiKeyHint(vendorId);

        const isCustom = vendorId === 'custom';
        customFields.forEach(field => field?.classList.toggle('config-hidden', !isCustom));
        if (!isCustom) advanced.open = false;
    };

    app.updateConfigStatus = function updateConfigStatus(data) {
        const current = data.current || data;
        const selectedProfile = (data.profiles || []).find(profile => profile.id === current.chat_profile);
        const configured = selectedProfile ? selectedProfile.configured : true;
        app.setInlineStatus(
            'config-status',
            configured
                ? `当前陪读档案：${selectedProfile ? selectedProfile.label : current.chat_profile || current.model_name}。已经开始的流程不会中途切换；新档案会在下一次开启或恢复时接手。`
                : '当前档案还不能使用，请先在本地设置里补齐可用的 API Key。',
            configured ? 'muted' : 'danger'
        );
    };

    app.fetchConfig = async function fetchConfig() {
        try {
            const res = await fetch('/api/config');
            const data = await res.json();
            state.chatProfiles = data.profiles || [];
            const current = data.current || data;
            app.populateModelOptions(state.chatProfiles, current);
            document.getElementById('model-select').value = current.chat_profile || '';
            app.updateConfigStatus(data);
        } catch (error) {
            console.error('Failed to fetch config:', error);
        }
    };

    app.fetchLocalConfig = async function fetchLocalConfig() {
        try {
            const res = await fetch('/api/config/local');
            const data = await res.json();
            state.localConfig = data;
            state.vendorCatalogs = data.vendors || [];
            app.populateLocalConfigForm(data);
            const configButton = document.getElementById('open-config-btn');
            if (configButton) {
                configButton.disabled = data.local_config_enabled === false;
                configButton.title = data.local_config_enabled === false ? '服务端已关闭前端本地设置编辑' : '';
            }
        } catch (error) {
            console.error('Failed to fetch local config:', error);
        }
    };

    app.updateModelConfig = async function updateModelConfig() {
        const profileId = document.getElementById('model-select').value;
        const res = await fetch('/api/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ profile_id: profileId }),
        });
        const data = await res.json();
        if (!res.ok) {
            alert(data.detail || '档案切换没有成功');
            return;
        }
        state.chatProfiles = data.profiles || [];
        app.populateModelOptions(state.chatProfiles, data.current || data);
        document.getElementById('model-select').value = (data.current || data).chat_profile || '';
        app.updateConfigStatus(data);
        alert('新的讲解档案已经记下来了。已经在运行的流程不会中途切换；下一次开启或恢复会话时，会自动使用新档案。');
    };

    app.populateLocalConfigForm = function populateLocalConfigForm(data) {
        if (!data) return;
        state.vendorCatalogs = data.vendors || state.vendorCatalogs;
        app.renderVendorOptions(data.selected_vendor || data.chat_profile || 'gemini');
        document.getElementById('local-llm-provider').value = data.llm_provider || 'openai';
        document.getElementById('local-openai-base').value = data.openai_api_base || '';
        document.getElementById('local-model-name').value = data.model_name || '';
        document.getElementById('local-embedding-provider').value = data.embedding_provider || 'local';
        document.getElementById('local-embedding-model').value = data.embedding_model_name || '';
        document.getElementById('local-pdf-parse-backend').value = data.pdf_parse_backend || 'auto';
        document.getElementById('local-top-k').value = data.knowledge_top_k || 3;
        document.getElementById('local-chunk-size').value = data.knowledge_chunk_size || 1000;
        document.getElementById('local-chunk-overlap').value = data.knowledge_chunk_overlap || 150;
        document.getElementById('local-vector-store-dir').value = data.vector_store_dir || 'data/chroma_db';
        document.getElementById('local-proxy-host').value = data.proxy_host || '';
        document.getElementById('local-proxy-port').value = data.proxy_port || '';
        document.getElementById('local-proxy-scheme').value = data.proxy_scheme || 'http';
        document.getElementById('local-http-proxy').value = data.http_proxy || '';
        document.getElementById('local-https-proxy').value = data.https_proxy || '';
        document.getElementById('local-mineru-proxy-mode').value = data.mineru_proxy_mode || 'inherit';
        document.getElementById('local-mineru-http-proxy').value = data.mineru_http_proxy || '';
        document.getElementById('local-mineru-https-proxy').value = data.mineru_https_proxy || '';
        document.getElementById('local-mineru-connect-timeout').value = data.mineru_connect_timeout_seconds || 5;
        app.renderVendorModels(data.selected_vendor || data.chat_profile || 'gemini', data.selected_model || data.model_name || '');
    };

    app.openLocalConfigPanel = function openLocalConfigPanel() {
        if (state.localConfig && state.localConfig.local_config_enabled === false) {
            alert('当前服务端已关闭前端本地设置编辑。');
            return;
        }
        state.lastFocusedElement = document.activeElement;
        const overlay = document.getElementById('config-overlay');
        overlay.classList.add('open');
        overlay.setAttribute('aria-hidden', 'false');
        app.setInlineStatus('local-config-status', '', 'muted');
        if (state.localConfig) app.populateLocalConfigForm(state.localConfig);
        document.getElementById('local-chat-profile')?.focus();
    };

    app.closeLocalConfigPanel = function closeLocalConfigPanel(event) {
        if (event && event.target && event.target.id !== 'config-overlay') return;
        const overlay = document.getElementById('config-overlay');
        overlay.classList.remove('open');
        overlay.setAttribute('aria-hidden', 'true');
        state.lastFocusedElement?.focus?.();
    };

    app.testConnection = async function testConnection() {
        app.setInlineStatus('local-config-status', '我在试着连一下当前配置…', 'processing');

        try {
            const res = await fetch('/api/config/test', {
                method: 'POST'
            });
            const data = await res.json();

            if (res.ok && data.status === 'ok') {
                app.setInlineStatus('local-config-status', `${data.message}（返回内容：${data.details}）`, 'success');
            } else {
                app.setInlineStatus('local-config-status', data.message, 'danger');
            }
        } catch (error) {
            app.setInlineStatus('local-config-status', `连接测试没有发出去：${error.message}`, 'danger');
        }
    };

    app.saveLocalConfig = async function saveLocalConfig() {
        const vendorId = document.getElementById('local-chat-profile').value;
        const selectedModel = document.getElementById('local-model-select').value;
        const apiKey = document.getElementById('local-api-key').value.trim();
        const payload = {
            vendor_id: vendorId,
            chat_profile: vendorId,
            api_key: apiKey,
            gemini_api_key: '',
            qwen_api_key: '',
            deepseek_api_key: '',
            minimax_api_key: '',
            glm_api_key: '',
            llm_provider: document.getElementById('local-llm-provider').value,
            openai_api_key: '',
            openai_api_base: document.getElementById('local-openai-base').value.trim(),
            model_name: vendorId === 'custom' ? document.getElementById('local-model-name').value.trim() : selectedModel,
            embedding_provider: document.getElementById('local-embedding-provider').value,
            embedding_model_name: document.getElementById('local-embedding-model').value.trim(),
            pdf_parse_backend: document.getElementById('local-pdf-parse-backend').value,
            knowledge_top_k: Number(document.getElementById('local-top-k').value || 3),
            knowledge_chunk_size: Number(document.getElementById('local-chunk-size').value || 1000),
            knowledge_chunk_overlap: Number(document.getElementById('local-chunk-overlap').value || 150),
            vector_store_dir: document.getElementById('local-vector-store-dir').value.trim(),
            proxy_host: document.getElementById('local-proxy-host').value.trim(),
            proxy_port: document.getElementById('local-proxy-port').value.trim(),
            proxy_scheme: document.getElementById('local-proxy-scheme').value,
            http_proxy: document.getElementById('local-http-proxy').value.trim(),
            https_proxy: document.getElementById('local-https-proxy').value.trim(),
            mineru_proxy_mode: document.getElementById('local-mineru-proxy-mode').value,
            mineru_http_proxy: document.getElementById('local-mineru-http-proxy').value.trim(),
            mineru_https_proxy: document.getElementById('local-mineru-https-proxy').value.trim(),
            mineru_connect_timeout_seconds: Number(document.getElementById('local-mineru-connect-timeout').value || 5),
            google_api_key: '',
        };
        if (vendorId === 'gemini') {
            payload.gemini_api_key = apiKey;
            payload.google_api_key = apiKey;
        } else if (vendorId === 'qwen') {
            payload.qwen_api_key = apiKey;
        } else if (vendorId === 'deepseek') {
            payload.deepseek_api_key = apiKey;
        } else if (vendorId === 'openai') {
            payload.openai_api_key = apiKey;
        } else if (vendorId === 'minimax') {
            payload.minimax_api_key = apiKey;
        } else if (vendorId === 'glm') {
            payload.glm_api_key = apiKey;
        } else if (vendorId === 'custom') {
            if (payload.llm_provider === 'google') {
                payload.google_api_key = apiKey;
            } else {
                payload.openai_api_key = apiKey;
            }
        }
        app.setInlineStatus('local-config-status', '我在保存这些本地设置，并重建当前运行环境…', 'processing');
        const res = await fetch('/api/config/local', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        const data = await res.json();
        if (!res.ok) {
            app.setInlineStatus('local-config-status', data.detail || '保存没有成功', 'danger');
            return;
        }
        state.localConfig = data.local;
        app.populateLocalConfigForm(state.localConfig);
        await app.fetchConfig();
        app.setInlineStatus('local-config-status', '本地设置已经保存好。新的陪读档案会在下一次开启或恢复时使用，资料检索也已经按新设置重建。', 'success');
    };
})();
