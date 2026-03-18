(() => {
    const app = window.AITutorApp;
    const state = app.state;

    app.populateModelOptions = function populateModelOptions(profiles, current) {
        const select = document.getElementById('model-select');
        select.innerHTML = '';
        profiles.forEach(profile => {
            const option = document.createElement('option');
            option.value = profile.id;
            option.textContent = profile.label + (profile.configured ? '' : '（未配置）');
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
        return masked ? `已保存：${masked}` : '仅本地保存';
    };

    app.renderVendorOptions = function renderVendorOptions(selectedVendor) {
        const select = document.getElementById('local-chat-profile');
        select.innerHTML = '';
        state.vendorCatalogs.forEach(vendor => {
            const option = document.createElement('option');
            option.value = vendor.id;
            option.textContent = vendor.label + (!vendor.configured && !vendor.custom ? '（未配置）' : '');
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
            option.textContent = selectedModel || '请在高级设置中手动填写模型';
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
        const el = document.getElementById('config-status');
        el.innerText = configured
            ? `当前档案：${selectedProfile ? selectedProfile.label : current.chat_profile || current.model_name}。已启动的后台流程不会中途切换，新的档案会在下一次启动或恢复时使用。`
            : '当前档案未配置可用 API Key，请先在服务端 .env 补齐密钥';
        el.style.color = configured ? 'var(--text-secondary)' : 'var(--accent-red)';
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
                configButton.title = data.local_config_enabled === false ? '服务端已禁用前端本地配置编辑' : '';
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
            alert(data.detail || '引擎切换失败');
            return;
        }
        state.chatProfiles = data.profiles || [];
        app.populateModelOptions(state.chatProfiles, data.current || data);
        document.getElementById('model-select').value = (data.current || data).chat_profile || '';
        app.updateConfigStatus(data);
        alert('模型档案已切换。当前已经在运行的后台流程不会中途换脑；你下一次启动会话，或从暂停点恢复时，会使用新档案。');
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
        document.getElementById('local-top-k').value = data.knowledge_top_k || 3;
        document.getElementById('local-chunk-size').value = data.knowledge_chunk_size || 1000;
        document.getElementById('local-chunk-overlap').value = data.knowledge_chunk_overlap || 150;
        document.getElementById('local-http-proxy').value = data.http_proxy || '';
        document.getElementById('local-https-proxy').value = data.https_proxy || '';
        app.renderVendorModels(data.selected_vendor || data.chat_profile || 'gemini', data.selected_model || data.model_name || '');
    };

    app.openLocalConfigPanel = function openLocalConfigPanel() {
        if (state.localConfig && state.localConfig.local_config_enabled === false) {
            alert('当前服务端已禁用前端本地配置编辑。');
            return;
        }
        document.getElementById('config-overlay').classList.add('open');
        document.getElementById('local-config-status').innerText = '';
        if (state.localConfig) app.populateLocalConfigForm(state.localConfig);
    };

    app.closeLocalConfigPanel = function closeLocalConfigPanel(event) {
        if (event && event.target && event.target.id !== 'config-overlay') return;
        document.getElementById('config-overlay').classList.remove('open');
    };

    app.testConnection = async function testConnection() {
        const status = document.getElementById('local-config-status');
        status.innerText = '正在测试当前连接...';
        status.style.color = 'var(--text-secondary)';
        
        try {
            const res = await fetch('/api/config/test', {
                method: 'POST'
            });
            const data = await res.json();
            
            if (res.ok && data.status === 'ok') {
                status.innerText = `✅ ${data.message} (回应: ${data.details})`;
                status.style.color = 'var(--accent-green)';
            } else {
                status.innerText = `❌ ${data.message}`;
                status.style.color = 'var(--accent-red)';
            }
        } catch (error) {
            status.innerText = `❌ 测试请求失败: ${error.message}`;
            status.style.color = 'var(--accent-red)';
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
            knowledge_top_k: Number(document.getElementById('local-top-k').value || 3),
            knowledge_chunk_size: Number(document.getElementById('local-chunk-size').value || 1000),
            knowledge_chunk_overlap: Number(document.getElementById('local-chunk-overlap').value || 150),
            http_proxy: document.getElementById('local-http-proxy').value.trim(),
            https_proxy: document.getElementById('local-https-proxy').value.trim(),
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
        const status = document.getElementById('local-config-status');
        status.innerText = '正在保存本地配置并重建运行时...';
        const res = await fetch('/api/config/local', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        const data = await res.json();
        if (!res.ok) {
            status.innerText = data.detail || '保存失败';
            status.style.color = 'var(--accent-red)';
            return;
        }
        state.localConfig = data.local;
        app.populateLocalConfigForm(state.localConfig);
        await app.fetchConfig();
        status.innerText = '本地配置已保存。聊天档案会在下一次启动或恢复时使用；RAG 已按新配置重建。';
        status.style.color = 'var(--accent-green)';
    };
})();
