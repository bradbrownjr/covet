<script lang="ts">
    import { onMount } from 'svelte';
    import { api } from '$lib/api';
    import { _ } from 'svelte-i18n';

    interface NotificationPref {
        kind: string;
        email_enabled: boolean;
        push_enabled: boolean;
        browser_enabled: boolean;
        lead_days: number;
    }

    const KIND_LABELS = $derived<Record<string, string>>({
        maintenance_due: $_('settings.kind_maintenance_due'),
        chore_due:       $_('settings.kind_chore_due'),
        item_use_by:     $_('settings.kind_item_use_by'),
        item_expires:    $_('settings.kind_item_expires'),
        lot_use_by:      $_('settings.kind_lot_use_by'),
        low_stock:       $_('settings.kind_low_stock'),
    });

    let notifPrefs  = $state<NotificationPref[]>([]);
    let digestQueued = $state(false);
    let digestMessage = $state('');
    let error = $state('');

    async function load() {
        try {
            notifPrefs = await api.get<NotificationPref[]>('/notifications');
        } catch (e) {
            error = (e as Error).message;
        }
    }

    async function saveNotifPref(kind: string, updates: Partial<Omit<NotificationPref, 'kind'>>) {
        try {
            const current = notifPrefs.find(p => p.kind === kind)!;
            const payload = {
                email_enabled:   current.email_enabled,
                push_enabled:    current.push_enabled,
                browser_enabled: current.browser_enabled,
                lead_days:       current.lead_days,
                ...updates,
            };
            const updated = await api.put<NotificationPref>(`/notifications/${kind}`, payload);
            notifPrefs = notifPrefs.map(p => p.kind === kind ? updated : p);
        } catch (e) {
            error = (e as Error).message;
        }
    }

    async function requestBrowserPermission() {
        if (typeof Notification === 'undefined') {
            digestMessage = 'Browser notifications are not supported in this browser.';
            return;
        }
        const perm = await Notification.requestPermission();
        digestMessage = perm === 'granted'
            ? 'Browser notifications enabled.'
            : 'Permission denied — check your browser settings.';
    }

    async function sendDigest() {
        digestMessage = '';
        digestQueued = false;
        try {
            const res = await api.post<{ queued: boolean; count?: number; reason?: string }>('/notifications/send-digest', undefined);
            if (res.queued) {
                digestQueued = true;
                digestMessage = `Digest queued — ${res.count} alert${res.count !== 1 ? 's' : ''} will be emailed to you shortly.`;
            } else {
                digestMessage = res.reason === 'no_alerts'
                    ? 'No alerts match your enabled preferences right now.'
                    : 'No notification preferences enabled.';
            }
        } catch (e) {
            error = (e as Error).message;
        }
    }

    onMount(load);
</script>

<h2>{$_('settings.nav_notifications')}</h2>

{#if error}<p class="error">{error}</p>{/if}

<div class="card">
    <h3 style="margin-top:0">{$_('settings.notifications_heading')}</h3>
    <p class="muted">{$_('settings.notifications_description')}</p>

    {#if notifPrefs.length > 0}
        <table class="notif-table">
            <thead>
                <tr>
                    <th>{$_('settings.notif_col_type')}</th>
                    <th title={$_('settings.notif_col_email')}>{$_('settings.notif_col_email')}</th>
                    <th title="Browser notification when the app is open">{$_('settings.notif_col_browser')}</th>
                    <th title="Daily notification on the Android app">{$_('settings.notif_col_app')}</th>
                    <th>{$_('settings.notif_col_lead')}</th>
                </tr>
            </thead>
            <tbody>
                {#each notifPrefs as p (p.kind)}
                    <tr>
                        <td>{KIND_LABELS[p.kind] ?? p.kind}</td>
                        <td>
                            <input type="checkbox" checked={p.email_enabled}
                                onchange={(e) => saveNotifPref(p.kind, { email_enabled: (e.target as HTMLInputElement).checked })} />
                        </td>
                        <td>
                            <input type="checkbox" checked={p.browser_enabled}
                                onchange={(e) => saveNotifPref(p.kind, { browser_enabled: (e.target as HTMLInputElement).checked })} />
                        </td>
                        <td>
                            <input type="checkbox" checked={p.push_enabled}
                                onchange={(e) => saveNotifPref(p.kind, { push_enabled: (e.target as HTMLInputElement).checked })} />
                        </td>
                        <td>
                            <input type="number" min="1" max="365" value={p.lead_days} style="width:5rem"
                                onchange={(e) => saveNotifPref(p.kind, { lead_days: parseInt((e.target as HTMLInputElement).value) || 7 })} />
                        </td>
                    </tr>
                {/each}
            </tbody>
        </table>
    {/if}

    <div style="margin-top:0.75rem;display:flex;gap:0.75rem;align-items:center;flex-wrap:wrap">
        <button onclick={sendDigest}>{$_('settings.send_digest_button')}</button>
        <button class="secondary" onclick={requestBrowserPermission}>{$_('settings.browser_permission_button')}</button>
        {#if digestMessage}
            <span class={digestQueued ? 'ok' : 'muted'}>{digestMessage}</span>
        {/if}
    </div>
</div>

<style>
    h2 { margin-top: 0; }
    .ok { color: var(--success); }

    .notif-table { border-collapse: collapse; width: 100%; }
    .notif-table thead tr { border-bottom: 1px solid var(--border); }
    .notif-table th, .notif-table td {
        padding: 0.4rem 0.6rem;
        text-align: left;
        font-size: 0.875rem;
    }
</style>
