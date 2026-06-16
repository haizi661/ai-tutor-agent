(() => {
    const app = window.AITutorApp;
    const state = app.state;

    const TOKEN_KEY = 'ai_tutor_access_token';

    function getAuthHeaders() {
        if (!state.accessToken) return {};
        return { Authorization: `Bearer ${state.accessToken}` };
    }

    function setAuthUser(user, token) {
        state.currentUser = user || null;
        state.accessToken = token || '';
        if (token) {
            localStorage.setItem(TOKEN_KEY, token);
        } else {
            localStorage.removeItem(TOKEN_KEY);
        }
        const label = document.getElementById('auth-user-label');
        if (label) label.innerText = state.currentUser ? `已登录：${state.currentUser.username}` : '未登录';
    }

    function setAuthStatus(text) {
        const el = document.getElementById('auth-status');
        if (el) el.innerText = text || '';
    }

    function setRegisterStatus(text) {
        const el = document.getElementById('register-status');
        if (el) el.innerText = text || '';
    }

    function toggleAuthOverlay(open) {
        const overlay = document.getElementById('auth-overlay');
        if (!overlay) return;
        overlay.classList.toggle('open', Boolean(open));
    }

    function toggleRegisterOverlay(open) {
        const overlay = document.getElementById('register-overlay');
        if (!overlay) return;
        overlay.classList.toggle('open', Boolean(open));
    }

    async function rawAuthFetch(url, options = {}) {
        const headers = { ...(options.headers || {}), ...getAuthHeaders() };
        return fetch(url, { ...options, headers });
    }

    app.apiFetch = async function apiFetch(url, options = {}, { requireAuth = true } = {}) {
        const headers = { ...(options.headers || {}) };
        if (requireAuth) Object.assign(headers, getAuthHeaders());
        const response = await fetch(url, { ...options, headers });
        if (response.status === 401 && requireAuth) {
            setAuthUser(null, '');
            toggleAuthOverlay(true);
            setAuthStatus('登录已失效，请重新登录。');
        }
        return response;
    };

    app.makeAuthedEventSourceUrl = function makeAuthedEventSourceUrl(path) {
        const token = state.accessToken;
        if (!token) return path;
        const joiner = path.includes('?') ? '&' : '?';
        return `${path}${joiner}access_token=${encodeURIComponent(token)}`;
    };

    app.login = async function login() {
        const username = (document.getElementById('auth-username')?.value || '').trim();
        const password = (document.getElementById('auth-password')?.value || '').trim();
        if (!username || !password) {
            setAuthStatus('请输入用户名和密码。');
            return;
        }
        setAuthStatus('正在登录...');
        const res = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password }),
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
            setAuthStatus(data.detail || '登录失败');
            return;
        }
        setAuthUser(data.user, data.access_token);
        setAuthStatus('');
        toggleAuthOverlay(false);
        await app.fetchHistory();
    };

    app.register = async function register() {
        const username = (document.getElementById('register-username')?.value || '').trim();
        const password = (document.getElementById('register-password')?.value || '').trim();
        const confirmPassword = (document.getElementById('register-password-confirm')?.value || '').trim();
        if (!username || !password || !confirmPassword) {
            setRegisterStatus('请完整填写注册信息。');
            return;
        }
        if (password !== confirmPassword) {
            setRegisterStatus('两次输入的密码不一致。');
            return;
        }
        setRegisterStatus('正在创建账号...');
        const res = await fetch('/api/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password }),
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
            setRegisterStatus(data.detail || '注册失败');
            return;
        }
        document.getElementById('auth-username').value = username;
        document.getElementById('auth-password').value = '';
        document.getElementById('register-password').value = '';
        document.getElementById('register-password-confirm').value = '';
        setRegisterStatus('');
        toggleRegisterOverlay(false);
        toggleAuthOverlay(true);
        setAuthStatus('账号创建成功，请登录。');
    };

    app.openRegisterWindow = function openRegisterWindow() {
        setRegisterStatus('');
        toggleRegisterOverlay(true);
    };

    app.closeRegisterWindow = function closeRegisterWindow() {
        toggleRegisterOverlay(false);
    };

    app.logout = async function logout() {
        try {
            await rawAuthFetch('/api/auth/logout', { method: 'POST' });
        } catch (_) {}
        if (state.eventSource) {
            state.eventSource.close();
            state.eventSource = null;
        }
        setAuthUser(null, '');
        state.currentThreadId = '';
        document.getElementById('messages').innerHTML = `
            <div class="msg-wrapper agent">
                <div class="avatar agent">T</div>
                <div class="msg-content">你好！我是你的私人伴学导师。你想开始学习哪个知识点？或者选择左侧的历史进度。</div>
            </div>
        `;
        document.getElementById('history-list').innerHTML = '';
        toggleAuthOverlay(true);
        toggleRegisterOverlay(false);
        setAuthStatus('你已退出登录。');
    };

    app.ensureAuthenticated = async function ensureAuthenticated() {
        const token = localStorage.getItem(TOKEN_KEY) || '';
        if (!token) {
            setAuthUser(null, '');
            toggleAuthOverlay(true);
            toggleRegisterOverlay(false);
            return false;
        }

        state.accessToken = token;
        const res = await rawAuthFetch('/api/auth/me');
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
            setAuthUser(null, '');
            toggleAuthOverlay(true);
            toggleRegisterOverlay(false);
            return false;
        }
        setAuthUser(data.user, token);
        toggleAuthOverlay(false);
        toggleRegisterOverlay(false);
        return true;
    };
})();
