<script lang="ts">
    import { page } from '$app/state';
    import { me } from '$lib/session';
    import { _ } from 'svelte-i18n';
    import Icon from '$lib/Icon.svelte';

    let { children } = $props();

    const enrollRequired = $derived(!!$me?.enrollment_required);
    const enrollParam = $derived(page.url.searchParams.has('enroll'));

    const NAV = [
        { href: '/settings/appearance',    icon: 'palette',    key: 'settings.nav_appearance' },
        { href: '/settings/notifications', icon: 'bell',       key: 'settings.nav_notifications' },
        { href: '/settings/security',      icon: 'shield',     key: 'settings.nav_security' },
        { href: '/settings/account',       icon: 'user',       key: 'settings.nav_account' },
    ];

    const currentPath = $derived(page.url.pathname);
</script>

<div class="settings-shell">
    {#if enrollRequired || enrollParam}
        <div class="banner-warn" role="alert">
            <strong>{$_('settings.enrollment_required_banner')}</strong>
            {$_('settings.enrollment_banner_message')}
        </div>
    {/if}

    <div class="settings-layout">
        <nav class="settings-nav" aria-label="Settings navigation">
            <ul>
                {#each NAV as item (item.href)}
                    <li>
                        <a
                            href={item.href}
                            class={currentPath.startsWith(item.href) ? 'active' : ''}
                            aria-current={currentPath.startsWith(item.href) ? 'page' : undefined}
                        >
                            <Icon name={item.icon} size={16} />
                            {$_(item.key)}
                        </a>
                    </li>
                {/each}
                {#if $me?.is_admin}
                    <li class="nav-divider"></li>
                    <li>
                        <a
                            href="/settings/admin"
                            class={currentPath.startsWith('/settings/admin') ? 'active' : ''}
                            aria-current={currentPath.startsWith('/settings/admin') ? 'page' : undefined}
                        >
                            <Icon name="settings-2" size={16} />
                            {$_('settings.nav_admin')}
                        </a>
                    </li>
                {/if}
            </ul>
        </nav>

        <main class="settings-content">
            {@render children()}
        </main>
    </div>
</div>

<style>
    .settings-shell {
        max-width: 64rem;
        margin: 0 auto;
        padding: var(--space-4) var(--space-3);
    }

    .banner-warn {
        background: color-mix(in srgb, var(--warning) 15%, var(--surface));
        border: 1px solid var(--warning);
        border-radius: var(--radius-md);
        padding: 0.75rem 1rem;
        margin-bottom: 1rem;
        color: var(--text);
    }

    .settings-layout {
        display: flex;
        gap: var(--space-6);
        align-items: flex-start;
    }

    .settings-nav {
        flex-shrink: 0;
        width: 13rem;
        position: sticky;
        top: var(--space-4);
    }

    .settings-nav ul {
        list-style: none;
        margin: 0;
        padding: 0;
        display: flex;
        flex-direction: column;
        gap: 2px;
    }

    .settings-nav a {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 0.75rem;
        border-radius: var(--radius-md);
        color: var(--text-muted);
        text-decoration: none;
        font-size: 0.9rem;
        transition: background 0.12s, color 0.12s;
    }

    .settings-nav a:hover {
        background: color-mix(in srgb, var(--text) 6%, transparent);
        color: var(--text);
    }

    .settings-nav a.active {
        background: color-mix(in srgb, var(--accent) 12%, transparent);
        color: var(--accent);
        font-weight: 600;
    }

    .nav-divider {
        height: 1px;
        background: var(--border);
        margin: 0.4rem 0;
    }

    .settings-content {
        flex: 1;
        min-width: 0;
    }

    @media (max-width: 640px) {
        .settings-layout {
            flex-direction: column;
            gap: var(--space-3);
        }

        .settings-nav {
            width: 100%;
            position: static;
        }

        .settings-nav ul {
            flex-direction: row;
            flex-wrap: wrap;
            gap: 4px;
        }

        .settings-nav a {
            font-size: 0.82rem;
            padding: 0.4rem 0.6rem;
        }

        .nav-divider {
            display: none;
        }
    }
</style>
