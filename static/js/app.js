(function () {
    'use strict';

    const STEP_NAMES = {
        1: '信息填报',
        2: '资格审核',
        3: '宿舍分配',
        4: '缴费确认',
        5: '报到完成'
    };

    function escapeHtml(value) {
        const div = document.createElement('div');
        div.textContent = value == null ? '' : String(value);
        return div.innerHTML;
    }

    function toast(message, type) {
        type = type || 'info';
        let container = document.getElementById('app-toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'app-toast-container';
            container.setAttribute('aria-live', 'polite');
            document.body.appendChild(container);
        }

        const item = document.createElement('div');
        item.className = 'app-toast app-toast-' + type;
        item.setAttribute('role', 'status');
        const iconMap = {
            success: '✅',
            error: '⚠️',
            warning: '❗',
            info: 'ℹ️'
        };
        item.innerHTML = '<span class="app-toast-icon">' + (iconMap[type] || iconMap.info) +
            '</span><span class="app-toast-text">' + escapeHtml(message) + '</span>';
        container.appendChild(item);

        requestAnimationFrame(() => item.classList.add('is-visible'));
        window.setTimeout(() => {
            item.classList.remove('is-visible');
            window.setTimeout(() => {
                if (item.parentNode) item.parentNode.removeChild(item);
            }, 300);
        }, 3200);
    }

    async function fetchJSON(url, options) {
        const res = await fetch(url, options);
        let data = null;
        try {
            data = await res.json();
        } catch (err) {
            data = { success: false, message: '服务器返回了无法解析的数据' };
        }
        if (!res.ok && data && !data.message) {
            data.message = '请求失败（' + res.status + '）';
        }
        return data;
    }

    function initNav() {
        const toggle = document.querySelector('.nav-toggle');
        const navLinks = document.getElementById('navLinks');
        if (!toggle || !navLinks) return;
        toggle.addEventListener('click', () => {
            const expanded = toggle.getAttribute('aria-expanded') === 'true';
            toggle.setAttribute('aria-expanded', String(!expanded));
            navLinks.classList.toggle('is-open', !expanded);
            document.body.classList.toggle('nav-open', !expanded);
        });
    }

    function formatStep(step) {
        return STEP_NAMES[step] || String(step);
    }

    window.App = {
        escapeHtml: escapeHtml,
        toast: toast,
        fetchJSON: fetchJSON,
        initNav: initNav,
        formatStep: formatStep
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initNav);
    } else {
        initNav();
    }
})();
