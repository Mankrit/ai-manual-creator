# MODULE: User Settings

The **User Settings** module lets an authenticated user personalize their profile within the Mock Secure App. From the Settings page the user can change their **display name**, pick an **app theme** (Light, Dark, or System Default), and toggle **email notifications** on or off. Preferences are persisted locally so they survive page reloads.

This document has two parts:
1. **User Guide** — how to use the feature end-to-end.
2. **Technical Guide** — how the feature is implemented in the codebase.

---

## 1. User Guide (How to Use)

### 1.1 Logging in first

The Settings page is protected, so you must log in before you can reach it.

1. Open the application and arrive at the **Login Page**.
2. Enter your email and password (email must contain `@`, password must be 6+ characters).
3. Click the blue **Sign In** button.

![Login page with credentials filled and Sign In highlighted](01_login_page.png)

After a successful login, you are taken to the Dashboard.

### 1.2 Opening Settings from the Dashboard

On the Dashboard, you will see a welcome message with your email and two action buttons. Click the blue **Settings** button to open the Settings page.

![Dashboard with Settings button highlighted](03_dashboard.png)

> **Note:** If you somehow reach `settings.html` without being logged in, the page will show an *"Access Denied"* alert and bounce you back to the login screen.

### 1.3 The Profile Settings page

The Settings page is titled **Profile Settings** and contains three preference controls plus two action buttons.

![Initial Profile Settings page](04_settings_initial.png)

| Field | Type | Default | Description |
|---|---|---|---|
| Display Name | Text input | *(empty)* | The name shown to identify your profile. |
| App Theme | Dropdown | Light Mode | Choose **Light**, **Dark**, or **System Default**. |
| Receive email notifications | Checkbox | ✅ Checked | Toggle whether you want to receive email updates. |
| Back to Dashboard | Button | — | Returns you to the Dashboard without saving. |
| Save Settings | Button | — | Persists your changes. |

### 1.4 Changing your preferences

1. Click into the **Display Name** field and type the name you want to use.
2. Open the **App Theme** dropdown and pick *Light Mode*, *Dark Mode*, or *System Default*.
3. Tick or untick the **Receive email notifications** checkbox to set your preference.

![Form with a display name entered and notifications toggled](06_settings_form_filled.png)

### 1.5 Saving your changes

When you are happy with your choices, click the blue **Save Settings** button.

A green confirmation banner — *"Settings saved successfully!"* — appears below the buttons for a few seconds to confirm your changes were persisted.

![Success message after saving](07_settings_saved_success.png)

Your preferences are remembered the next time you visit the page (the form pre-fills with your last saved values).

### 1.6 Going back without saving

If you want to return to the Dashboard without keeping your edits, click the gray **Back to Dashboard** button.

![Back to Dashboard button highlighted](08_settings_with_back_btn.png)

You will be returned to the Dashboard where you can log out or revisit Settings later.

---

## 2. Technical Guide (Under the Hood)

The User Settings module is a single-page client-side feature built with vanilla HTML, inline CSS, and inline JavaScript. There is **no backend API** — all persistence is done through `localStorage`.

### 2.1 Files involved

| File | Role |
|---|---|
| `login.html` | Creates the `user_session` localStorage key that gates access to settings. |
| `dashboard.html` | Hosts the **Settings** button that navigates to `settings.html`. |
| `settings.html` | The entire Settings UI, validation, persistence logic, and access guard. |

### 2.2 Access control

Before the settings UI is shown, `settings.html` runs a guard at the top of its `<script>` block:

```javascript
const session = localStorage.getItem('user_session');
if (!session) {
    alert('Access Denied. Please log in first.');
    window.location.href = 'login.html';
}
```

The same guard exists in `dashboard.html`. The `user_session` key is created in `login.html` via `localStorage.setItem('user_session', email)` on a successful login, and removed in `dashboard.html`'s `handleLogout()`.

**Login validation rules (from `login.html`):**
- `email.includes('@')` must be `true`.
- `password.length >= 6` must be `true`.

If either check fails, `#error-msg` (`<div id="error-msg" class="error-message">Invalid email or password!</div>`) is shown by toggling `style.display = 'block'`.

### 2.3 Page structure (`settings.html`)

| Element | Selector | Type | Purpose |
|---|---|---|---|
| Display Name field | `#display-name` | `<input type="text">` | Stores the user's display name. |
| Theme dropdown | `#theme-select` | `<select>` | Options: `light`, `dark`, `system`. |
| Notifications toggle | `#receive-notifications` | `<input type="checkbox">` | Defaults to `checked`. |
| Save button | `#save-btn` | `<button>` (class `btn-save`) | Triggers `saveSettings()`. |
| Back button | `#back-btn` | `<button>` (class `btn-back`) | Triggers `goBack()`. |
| Success banner | `#success-msg` | `<div class="success-message">` | Hidden by default; shown for 3 s after save. |

The whole form is wrapped in `<div class="settings-container">` and styled with inline CSS in the `<style>` block.

### 2.4 State management — `localStorage` schema

The module persists user preferences under three localStorage keys. There is no backend, no JSON serialization, and no encryption.

| Key | Type stored | Default if missing | Read on load | Written on save |
|---|---|---|---|---|
| `settings_display_name` | `string` | `''` (empty) | `localStorage.getItem('settings_display_name') || ''` | `displayName` |
| `settings_theme` | `string` (`'light'`/`'dark'`/`'system'`) | `'light'` | `localStorage.getItem('settings_theme') || 'light'` | `theme` |
| `settings_notifications` | `string` (`'true'`/`'false'`) | `'true'` (the check `!== 'false'` evaluates true) | `localStorage.getItem('settings_notifications') !== 'false'` | `String(notifications)` |

Note that `localStorage` only stores strings — the boolean checkbox state is coerced to/from its string form on every save and load.

### 2.5 Lifecycle hooks

#### On `DOMContentLoaded` (initialization)

```javascript
document.addEventListener("DOMContentLoaded", () => {
    const savedName    = localStorage.getItem('settings_display_name') || '';
    const savedTheme   = localStorage.getItem('settings_theme') || 'light';
    const savedNotify  = localStorage.getItem('settings_notifications') !== 'false';

    document.getElementById('display-name').value         = savedName;
    document.getElementById('theme-select').value         = savedTheme;
    document.getElementById('receive-notifications').checked = savedNotify;
});
```

This hydrates the form from localStorage so returning users see their last saved values.

#### `saveSettings()` — invoked by `#save-btn`

1. Reads the three input values from the DOM.
2. Writes them to localStorage under the three keys above.
3. Reveals `#success-msg` by setting `style.display = 'block'`.
4. Hides the banner again after 3,000 ms via `setTimeout`.

There is **no client-side validation** on the Display Name (e.g. no max length, no trimming, no required-field check) — whatever is in the input is saved verbatim.

#### `goBack()` — invoked by `#back-btn`

A simple `window.location.href = 'dashboard.html'` redirect. Uncommitted form changes are **discarded**.

### 2.6 Navigation graph

```
login.html ──(Sign In, sets user_session)──▶ dashboard.html
                                                  │
                              (Settings button)  │  (Logout clears user_session)
                                                  ▼
                                            settings.html
                                                  │
                       (Save Settings)           │  (Back to Dashboard)
                          persists to            │
                          localStorage           ▼
                                            dashboard.html
```

### 2.7 Known limitations / extension points

- **No backend.** Settings are device-local. Clearing browser storage resets preferences.
- **No input validation** on `display-name` (empty strings, whitespace, and very long values are all accepted).
- **No theme application.** Although the `settings_theme` value is persisted, the app does not actually apply a CSS theme based on it — it is currently stored only.
- **Notification preference is stored but unused** by any visible feature in the current codebase.
- **No CSRF / XSS hardening** is needed because there is no server-side endpoint, but any future migration to a real backend should validate and sanitize the `display-name` value.
