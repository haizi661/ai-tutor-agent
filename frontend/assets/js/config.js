(() => {
    const app = window.AITutorApp;
    const state = app.state;

    function getConfiguredProfileById(profileId) {
        return state.chatProfiles.find(profile => profile.id === profileId) || null;
    }

    function getProfileModelLabel(profile, modelName) {
        if (!profile) return modelName || '未选择';
        const matchedModel = Array.isArray(profile.models)
            ? profile.models.find(model => model.id === modelName)
            : null;
        return matchedModel?.label || modelName || profile.label || '未选择';
    }

    const CONFIG_SECTION_META = {
        general: {
            title: '常规',
            subtitle: '查看当前运行方式和本地模式概况。',
        },
        notifications: {
            title: '通知',
            subtitle: '管理提醒、推送和消息通知入口。',
        },
        personalization: {
            title: '个性化',
            subtitle: '调整界面风格、默认节奏和展示偏好。',
        },
        applications: {
            title: '应用',
            subtitle: '管理模型来源、接口连接和本地运行方式。',
        },
        schedule: {
            title: '安排',
            subtitle: '后续会把学习日程和自动复习计划接到这里。',
        },
        billing: {
            title: '订单',
            subtitle: '当前版本没有接入云端购买与订阅系统。',
        },
        data: {
            title: '数据管理',
            subtitle: '控制资料检索、切块策略和本地向量目录。',
        },
        security: {
            title: '安全',
            subtitle: '管理代理、网络访问和 MinerU 相关连接参数。',
        },
        family: {
            title: '家长控制',
            subtitle: '当前版本没有接入家长控制和分级权限。',
        },
        account: {
            title: '帐户',
            subtitle: '查看当前本地档案、模型和账户形态。',
        },
    };

    const NOTIFICATION_PREFS_STORAGE_KEY = 'ai_tutor_notification_prefs';
    const UI_PREFS_STORAGE_KEY = 'ai_tutor_ui_prefs';
    const ACCOUNT_PREFS_STORAGE_KEY = 'ai_tutor_account_prefs';

    const DEFAULT_NOTIFICATION_PREFS = {
        show_banner: true,
        show_progress_events: true,
        desktop_enabled: false,
        sound_enabled: false,
        reminder_cycle: 'off',
    };

    const DEFAULT_UI_PREFS = {
        density: 'comfortable',
        show_landing: true,
        show_event_chips: true,
        hide_status_banner: false,
        reduce_motion: false,
    };

    const DEFAULT_ACCOUNT_PREFS = {
        display_name: '学习者',
        plan_label: 'Plus',
    };

    function readStoredPrefs(storageKey, defaults) {
        try {
            const raw = window.localStorage.getItem(storageKey);
            if (!raw) return { ...defaults };
            const parsed = JSON.parse(raw);
            if (!parsed || typeof parsed !== 'object') return { ...defaults };
            return { ...defaults, ...parsed };
        } catch (_error) {
            return { ...defaults };
        }
    }

    function writeStoredPrefs(storageKey, value) {
        try {
            window.localStorage.setItem(storageKey, JSON.stringify(value));
        } catch (_error) {
            // Ignore storage failures and keep UI responsive.
        }
    }

    function getNotificationPrefs() {
        return readStoredPrefs(NOTIFICATION_PREFS_STORAGE_KEY, DEFAULT_NOTIFICATION_PREFS);
    }

    function getUiPrefs() {
        return readStoredPrefs(UI_PREFS_STORAGE_KEY, DEFAULT_UI_PREFS);
    }

    function getAccountPrefs() {
        return readStoredPrefs(ACCOUNT_PREFS_STORAGE_KEY, DEFAULT_ACCOUNT_PREFS);
    }

    function applyNotificationPrefs(prefs = getNotificationPrefs()) {
        document.body.classList.toggle('ui-notify-hide-banner', !prefs.show_banner);
        document.body.classList.toggle('ui-notify-hide-events', !prefs.show_progress_events);
    }

    function applyUiPrefs(prefs = getUiPrefs()) {
        document.body.dataset.uiDensity = prefs.density || 'comfortable';
        document.body.classList.toggle('ui-hide-landing', !prefs.show_landing);
        document.body.classList.toggle('ui-hide-config-event-chips', !prefs.show_event_chips);
        document.body.classList.toggle('ui-hide-status-banner', Boolean(prefs.hide_status_banner));
        document.body.classList.toggle('ui-reduce-motion-pref', Boolean(prefs.reduce_motion));
    }

    function applyAccountPrefs(prefs = getAccountPrefs()) {
        const displayName = String(prefs.display_name || DEFAULT_ACCOUNT_PREFS.display_name).trim() || DEFAULT_ACCOUNT_PREFS.display_name;
        const planLabel = String(prefs.plan_label || DEFAULT_ACCOUNT_PREFS.plan_label).trim() || DEFAULT_ACCOUNT_PREFS.plan_label;

        document.querySelectorAll('.sb-user-name, .sb-user-menu-name').forEach(node => {
            node.textContent = displayName;
        });
        document.querySelectorAll('.sb-user-plan, .sb-user-menu-plan').forEach(node => {
            node.textContent = planLabel;
        });

        const accountDisplayName = document.getElementById('config-account-display-name');
        if (accountDisplayName) accountDisplayName.textContent = displayName;

        const accountNameInput = document.getElementById('settings-account-name');
        if (accountNameInput && accountNameInput !== document.activeElement) accountNameInput.value = displayName;

        const accountPlanSelect = document.getElementById('settings-account-plan');
        if (accountPlanSelect && accountPlanSelect.value !== planLabel) accountPlanSelect.value = planLabel;
    }

    function updateNotificationPermissionLabel() {
        const label = document.getElementById('settings-notify-permission');
        if (!label) return;

        if (typeof Notification === 'undefined') {
            label.textContent = '桌面通知权限状态：当前浏览器环境不支持。';
            return;
        }

        const permissionText = {
            granted: '已允许',
            denied: '已拒绝',
            default: '尚未决定',
        }[Notification.permission] || '尚未决定';

        label.textContent = `桌面通知权限状态：${permissionText}。`;
    }

    function syncPreferenceControls() {
        const notificationPrefs = getNotificationPrefs();
        const uiPrefs = getUiPrefs();
        const accountPrefs = getAccountPrefs();

        const notifyBanner = document.getElementById('settings-notify-banner');
        const notifyProgress = document.getElementById('settings-notify-progress');
        const notifyDesktop = document.getElementById('settings-notify-desktop');
        const notifySound = document.getElementById('settings-notify-sound');
        const notifyReminder = document.getElementById('settings-notify-reminder-cycle');
        const uiDensity = document.getElementById('settings-ui-density');
        const uiShowLanding = document.getElementById('settings-ui-show-landing');
        const uiShowEventChips = document.getElementById('settings-ui-show-event-chips');
        const uiHideStatusBanner = document.getElementById('settings-ui-hide-status-banner');
        const uiReduceMotion = document.getElementById('settings-ui-reduce-motion');
        const accountName = document.getElementById('settings-account-name');
        const accountPlan = document.getElementById('settings-account-plan');

        if (notifyBanner) notifyBanner.checked = Boolean(notificationPrefs.show_banner);
        if (notifyProgress) notifyProgress.checked = Boolean(notificationPrefs.show_progress_events);
        if (notifyDesktop) notifyDesktop.checked = Boolean(notificationPrefs.desktop_enabled);
        if (notifySound) notifySound.checked = Boolean(notificationPrefs.sound_enabled);
        if (notifyReminder) notifyReminder.value = notificationPrefs.reminder_cycle || 'off';
        if (uiDensity) uiDensity.value = uiPrefs.density || 'comfortable';
        if (uiShowLanding) uiShowLanding.checked = Boolean(uiPrefs.show_landing);
        if (uiShowEventChips) uiShowEventChips.checked = Boolean(uiPrefs.show_event_chips);
        if (uiHideStatusBanner) uiHideStatusBanner.checked = Boolean(uiPrefs.hide_status_banner);
        if (uiReduceMotion) uiReduceMotion.checked = Boolean(uiPrefs.reduce_motion);
        if (accountName && accountName !== document.activeElement) accountName.value = accountPrefs.display_name || DEFAULT_ACCOUNT_PREFS.display_name;
        if (accountPlan) accountPlan.value = accountPrefs.plan_label || DEFAULT_ACCOUNT_PREFS.plan_label;
        updateNotificationPermissionLabel();
    }

    function readNotificationPrefsFromDom() {
        return {
            show_banner: Boolean(document.getElementById('settings-notify-banner')?.checked),
            show_progress_events: Boolean(document.getElementById('settings-notify-progress')?.checked),
            desktop_enabled: Boolean(document.getElementById('settings-notify-desktop')?.checked),
            sound_enabled: Boolean(document.getElementById('settings-notify-sound')?.checked),
            reminder_cycle: document.getElementById('settings-notify-reminder-cycle')?.value || 'off',
        };
    }

    function readUiPrefsFromDom() {
        return {
            density: document.getElementById('settings-ui-density')?.value || 'comfortable',
            show_landing: Boolean(document.getElementById('settings-ui-show-landing')?.checked),
            show_event_chips: Boolean(document.getElementById('settings-ui-show-event-chips')?.checked),
            hide_status_banner: Boolean(document.getElementById('settings-ui-hide-status-banner')?.checked),
            reduce_motion: Boolean(document.getElementById('settings-ui-reduce-motion')?.checked),
        };
    }

    function readAccountPrefsFromDom() {
        return {
            display_name: document.getElementById('settings-account-name')?.value?.trim() || DEFAULT_ACCOUNT_PREFS.display_name,
            plan_label: document.getElementById('settings-account-plan')?.value || DEFAULT_ACCOUNT_PREFS.plan_label,
        };
    }

    function updateAccountEnvironmentSummary() {
        const storeEl = document.getElementById('config-account-store');
        if (storeEl) {
            storeEl.textContent = state.localConfig?.vector_store_dir || document.getElementById('local-vector-store-dir')?.value || 'data/chroma_db';
        }
    }

    function persistNotificationPrefs(notify = readNotificationPrefsFromDom()) {
        writeStoredPrefs(NOTIFICATION_PREFS_STORAGE_KEY, notify);
        applyNotificationPrefs(notify);
        updateNotificationPermissionLabel();
    }

    function persistUiPrefs(ui = readUiPrefsFromDom()) {
        writeStoredPrefs(UI_PREFS_STORAGE_KEY, ui);
        applyUiPrefs(ui);
    }

    function persistAccountPrefs(account = readAccountPrefsFromDom()) {
        writeStoredPrefs(ACCOUNT_PREFS_STORAGE_KEY, account);
        applyAccountPrefs(account);
    }

    async function syncDesktopNotificationPermission(enabled) {
        if (!enabled || typeof Notification === 'undefined' || Notification.permission !== 'default') {
            updateNotificationPermissionLabel();
            return;
        }

        try {
            await Notification.requestPermission();
        } catch (_error) {
            // Some browsers reject the permission promise in restricted contexts.
        }
        updateNotificationPermissionLabel();
    }

    function bindLocalPreferenceControls() {
        if (document.body.dataset.localPrefsBound === '1') return;
        document.body.dataset.localPrefsBound = '1';

        [
            'settings-notify-banner',
            'settings-notify-progress',
            'settings-notify-sound',
            'settings-notify-reminder-cycle',
        ].forEach(id => {
            document.getElementById(id)?.addEventListener('change', () => {
                persistNotificationPrefs();
            });
        });

        document.getElementById('settings-notify-desktop')?.addEventListener('change', async () => {
            const prefs = readNotificationPrefsFromDom();
            persistNotificationPrefs(prefs);
            await syncDesktopNotificationPermission(prefs.desktop_enabled);
        });

        [
            'settings-ui-density',
            'settings-ui-show-landing',
            'settings-ui-show-event-chips',
            'settings-ui-hide-status-banner',
            'settings-ui-reduce-motion',
        ].forEach(id => {
            document.getElementById(id)?.addEventListener('change', () => {
                persistUiPrefs();
            });
        });

        document.getElementById('settings-account-name')?.addEventListener('input', () => {
            persistAccountPrefs();
        });
        document.getElementById('settings-account-plan')?.addEventListener('change', () => {
            persistAccountPrefs();
        });
    }

    app.hydrateLocalClientSettings = function hydrateLocalClientSettings() {
        applyNotificationPrefs();
        applyUiPrefs();
        applyAccountPrefs();
        syncPreferenceControls();
        updateAccountEnvironmentSummary();
        bindLocalPreferenceControls();
    };

    function getResolvedConfigSection(sectionId) {
        return CONFIG_SECTION_META[sectionId] ? sectionId : 'applications';
    }

    function focusLocalConfigSection(sectionId) {
        const section = document.querySelector(`[data-config-section="${sectionId}"]`);
        const primaryField = section?.querySelector('input:not([type="hidden"]), select, textarea, button');
        const activeTab = document.querySelector(`[data-config-section-tab="${sectionId}"]`);
        if (sectionId === 'applications') {
            document.getElementById('local-chat-profile')?.focus();
            return;
        }
        primaryField?.focus?.() || activeTab?.focus?.();
    }

    function updateConfigHeader(sectionId) {
        const meta = CONFIG_SECTION_META[getResolvedConfigSection(sectionId)];
        const title = document.getElementById('local-config-title');
        const subtitle = document.getElementById('local-config-subtitle');
        if (title) title.textContent = meta.title;
        if (subtitle) subtitle.textContent = meta.subtitle;
    }

    function syncLocalConfigAccountSummary(vendorId) {
        const resolvedVendorId = vendorId
            || document.getElementById('local-chat-profile')?.value
            || state.localConfig?.selected_vendor
            || state.localConfig?.chat_profile
            || '';
        const vendor = app.getVendorCatalog(resolvedVendorId);
        const modelSelect = document.getElementById('local-model-select');
        const customModelInput = document.getElementById('local-model-name');
        const selectedModel = modelSelect?.value
            || customModelInput?.value?.trim()
            || state.localConfig?.selected_model
            || state.localConfig?.model_name
            || '';
        const profileEl = document.getElementById('config-account-profile');
        const modelEl = document.getElementById('config-account-model');

        if (profileEl) profileEl.textContent = vendor?.label || resolvedVendorId || '未选择';
        if (modelEl) modelEl.textContent = getProfileModelLabel(vendor, selectedModel);
        updateAccountEnvironmentSummary();
    }

    function closeModelPicker() {
        const picker = document.getElementById('model-picker');
        const trigger = document.getElementById('model-picker-trigger');
        const menu = document.getElementById('model-picker-menu');
        if (!picker || !trigger || !menu) return;
        picker.classList.remove('is-open');
        menu.hidden = true;
        trigger.setAttribute('aria-expanded', 'false');
    }

    function toggleModelPicker(force) {
        const picker = document.getElementById('model-picker');
        const trigger = document.getElementById('model-picker-trigger');
        const menu = document.getElementById('model-picker-menu');
        if (!picker || !trigger || !menu) return;
        const shouldOpen = typeof force === 'boolean' ? force : !picker.classList.contains('is-open');
        picker.classList.toggle('is-open', shouldOpen);
        menu.hidden = !shouldOpen;
        trigger.setAttribute('aria-expanded', shouldOpen ? 'true' : 'false');
    }

    function ensureModelPickerBindings() {
        const picker = document.getElementById('model-picker');
        const trigger = document.getElementById('model-picker-trigger');
        if (!picker || !trigger || picker.dataset.bound === '1') return;
        picker.dataset.bound = '1';

        trigger.addEventListener('click', event => {
            event.stopPropagation();
            toggleModelPicker();
        });

        document.addEventListener('click', event => {
            if (!picker.contains(event.target)) closeModelPicker();
        });

        document.addEventListener('keydown', event => {
            if (event.key === 'Escape') closeModelPicker();
        });
    }

    app.renderModelPicker = function renderModelPicker(profiles, current) {
        ensureModelPickerBindings();
        const list = document.getElementById('model-picker-list');
        const currentEl = document.getElementById('model-picker-current');
        const vendorEl = document.getElementById('model-picker-vendor');
        if (!list || !currentEl || !vendorEl) return;

        const currentProfileId = current?.chat_profile || '';
        const currentProfile = profiles.find(profile => profile.id === currentProfileId) || null;
        currentEl.textContent = getProfileModelLabel(currentProfile, current?.model_name || '');
        vendorEl.textContent = currentProfile?.label || '档案';

        list.innerHTML = '';
        profiles.forEach(profile => {
            const item = document.createElement('button');
            item.type = 'button';
            item.className = `model-picker-option${profile.id === currentProfileId ? ' is-active' : ''}${profile.configured ? '' : ' is-disabled'}`;
            item.setAttribute('role', 'option');
            item.setAttribute('aria-selected', profile.id === currentProfileId ? 'true' : 'false');
            item.innerHTML = `
                <div class="model-picker-option-copy">
                    <div class="model-picker-option-head">
                        <span class="model-picker-option-title">${profile.label}</span>
                        ${profile.configured ? '' : '<span class="model-picker-option-badge">未配置</span>'}
                    </div>
                    <div class="model-picker-option-desc">${profile.description || getProfileModelLabel(profile, profile.model_name)}</div>
                </div>
                <span class="model-picker-option-check" aria-hidden="true">${profile.id === currentProfileId ? '✓' : ''}</span>
            `;

            item.addEventListener('click', async () => {
                if (!profile.configured) {
                    closeModelPicker();
                    app.openLocalConfigPanel?.();
                    return;
                }
                if (profile.id === currentProfileId) {
                    closeModelPicker();
                    return;
                }
                closeModelPicker();
                await app.updateModelConfig(profile.id);
            });

            list.appendChild(item);
        });
    };

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

        app.renderModelPicker(profiles, current);
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
        if (advanced && 'open' in advanced) advanced.open = isCustom;
        syncLocalConfigAccountSummary(vendorId);
    };

    app.switchLocalConfigSection = function switchLocalConfigSection(sectionId = 'applications', options = {}) {
        const resolvedSection = getResolvedConfigSection(sectionId);
        const shouldFocus = Boolean(options.focus);

        document.querySelectorAll('[data-config-section]').forEach(section => {
            const active = section.dataset.configSection === resolvedSection;
            section.classList.toggle('is-active', active);
            section.hidden = !active;
            section.setAttribute('aria-hidden', active ? 'false' : 'true');
        });

        document.querySelectorAll('[data-config-section-tab]').forEach(tab => {
            const active = tab.dataset.configSectionTab === resolvedSection;
            tab.classList.toggle('is-active', active);
            tab.setAttribute('aria-current', active ? 'page' : 'false');
        });

        updateConfigHeader(resolvedSection);
        state.activeLocalConfigSection = resolvedSection;
        if (shouldFocus) focusLocalConfigSection(resolvedSection);
    };

    app.updateConfigStatus = function updateConfigStatus(data) {
        const current = data.current || data;
        const selectedProfile = (data.profiles || []).find(profile => profile.id === current.chat_profile);
        const configured = selectedProfile ? selectedProfile.configured : true;
        app.setInlineStatus(
            'config-status',
            configured
                ? `${selectedProfile ? selectedProfile.label : current.chat_profile || current.model_name}`
                : '当前档案不可用',
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
            state.currentChatProfile = current.chat_profile || '';
            state.currentModelName = current.model_name || '';
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

    app.updateModelConfig = async function updateModelConfig(profileOverride) {
        const profileId = profileOverride || document.getElementById('model-select').value;
        const res = await fetch('/api/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ profile_id: profileId }),
        });
        const data = await res.json();
        if (!res.ok) {
            app.setStatusBanner?.(data.detail || '档案切换没有成功', 'danger');
            return;
        }
        state.chatProfiles = data.profiles || [];
        app.populateModelOptions(state.chatProfiles, data.current || data);
        document.getElementById('model-select').value = (data.current || data).chat_profile || '';
        state.currentChatProfile = (data.current || data).chat_profile || '';
        state.currentModelName = (data.current || data).model_name || '';
        app.updateConfigStatus(data);
        closeModelPicker();
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
        syncLocalConfigAccountSummary(data.selected_vendor || data.chat_profile || '');
    };

    app.openLocalConfigPanel = function openLocalConfigPanel(sectionId = 'applications') {
        if (state.localConfig && state.localConfig.local_config_enabled === false) {
            alert('当前服务端已关闭本地设置编辑。');
            return;
        }
        state.lastFocusedElement = document.activeElement;
        const overlay = document.getElementById('config-overlay');
        overlay.classList.add('open');
        overlay.setAttribute('aria-hidden', 'false');
        app.setButtonActive?.('open-config-btn', true);
        app.setInlineStatus('local-config-status', '', 'muted');
        if (state.localConfig) app.populateLocalConfigForm(state.localConfig);
        app.hydrateLocalClientSettings?.();
        app.switchLocalConfigSection?.(sectionId || state.activeLocalConfigSection || 'applications', { focus: true });
    };

    app.closeLocalConfigPanel = function closeLocalConfigPanel(event) {
        if (event && event.target && event.target.id !== 'config-overlay') return;
        const overlay = document.getElementById('config-overlay');
        overlay.classList.remove('open');
        overlay.setAttribute('aria-hidden', 'true');
        app.setButtonActive?.('open-config-btn', false);
        state.lastFocusedElement?.focus?.();
    };

    app.testConnection = async function testConnection() {
        app.setInlineStatus('local-config-status', '正在测试连接…', 'processing');

        try {
            const res = await fetch('/api/config/test', {
                method: 'POST'
            });
            const data = await res.json();

            if (res.ok && data.status === 'ok') {
                app.setInlineStatus('local-config-status', data.message || '连接成功', 'success');
            } else {
                app.setInlineStatus('local-config-status', data.message, 'danger');
            }
        } catch (error) {
            app.setInlineStatus('local-config-status', `连接失败：${error.message}`, 'danger');
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
        app.setInlineStatus('local-config-status', '正在保存并重建…', 'processing');
        const res = await fetch('/api/config/local', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        const data = await res.json();
        if (!res.ok) {
            app.setInlineStatus('local-config-status', data.detail || '保存失败', 'danger');
            return;
        }
        state.localConfig = data.local;
        app.populateLocalConfigForm(state.localConfig);
        updateAccountEnvironmentSummary();
        await app.fetchConfig();
        app.setInlineStatus('local-config-status', '已保存并重建。', 'success');
    };

    window.switchLocalConfigSection = (sectionId) => app.switchLocalConfigSection(sectionId, { focus: true });
    window.syncLocalConfigAccountSummary = () => syncLocalConfigAccountSummary();

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            app.hydrateLocalClientSettings?.();
        }, { once: true });
    } else {
        app.hydrateLocalClientSettings?.();
    }
})();
