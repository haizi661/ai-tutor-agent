from pathlib import Path


INDEX_HTML = Path("frontend/index.html")
CONFIG_JS = Path("frontend/assets/js/config.js")
STYLES = Path("frontend/assets/styles.css")


def test_sidebar_user_card_opens_account_profile_settings():
    html = INDEX_HTML.read_text(encoding="utf-8")
    userbar = html.split('id="sb-userbar-btn"', 1)[1].split("</button>", 1)[0]

    assert "配置个人资料" in userbar
    assert "handleUserMenuAction('profile')" in userbar


def test_account_profile_editor_supports_name_avatar_choice_and_upload():
    html = INDEX_HTML.read_text(encoding="utf-8")
    config = CONFIG_JS.read_text(encoding="utf-8")
    styles = STYLES.read_text(encoding="utf-8")

    assert "settings-account-name" in html
    assert "settings-account-plan" in html
    assert "settings-account-avatar-preview" in html
    assert "settings-account-avatar-grid" in html
    assert "settings-account-avatar-upload" in html
    assert "triggerAccountAvatarUpload()" in html
    assert "resetAccountAvatar()" in html

    for avatar in ["default", "initial", "blue", "green", "rose", "amber"]:
        assert f'data-avatar-choice="{avatar}"' in html

    assert "avatar_kind: 'default'" in config
    assert "avatar_value: ''" in config
    assert "applyAvatarToNode" in config
    assert "persistAccountAvatar" in config
    assert "FileReader" in config
    assert "file.size > 1024 * 1024" in config
    assert "window.triggerAccountAvatarUpload" in config
    assert "window.resetAccountAvatar" in config

    assert ".account-profile-editor" in styles
    assert ".account-avatar-preview" in styles
    assert ".account-avatar-choice.is-active" in styles
    assert ".account-avatar--upload" in styles
    assert "#sidebar .sb-user-avatar.account-avatar--initial" in styles
