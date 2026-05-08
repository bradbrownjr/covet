<script lang="ts">
    import { onMount } from 'svelte';
    import { goto } from '$app/navigation';
    import { api, type SiteSetting } from '$lib/api';
    import { me } from '$lib/session';
    import { _ } from 'svelte-i18n';
    import { Button, Modal } from '$lib/components';

    const BARCODE_ADAPTER_INFO: Record<string, { label: string; description: string; keyHint?: string }> = {
        openlibrary:   { label: 'Open Library',    description: 'ISBN-10/13 lookup for books. Free, no API key required.' },
        musicbrainz:   { label: 'MusicBrainz',     description: 'Barcode lookup for music releases. Free; set TANGIBLE_MUSICBRAINZ_USER_AGENT for best results.' },
        openfoodfacts: { label: 'Open Food Facts', description: 'UPC/EAN lookup for food products. Free, no API key required.' },
        googlebooksapi:{ label: 'Google Books',    description: 'ISBN lookup via Google Books API.', keyHint: 'TANGIBLE_GOOGLE_BOOKS_API_KEY' },
        upcitemdb:     { label: 'UPCitemdb',       description: 'General product barcode lookup.', keyHint: 'TANGIBLE_UPCITEMDB_KEY' },
        discogs:       { label: 'Discogs',         description: 'Vinyl / music release lookup.', keyHint: 'TANGIBLE_DISCOGS_TOKEN' },
        tmdb:          { label: 'TMDB',            description: 'Movie and TV barcode lookup.', keyHint: 'TANGIBLE_TMDB_API_KEY' },
        igdb:          { label: 'IGDB',            description: 'Video game barcode lookup.', keyHint: 'TANGIBLE_IGDB_CLIENT_ID + TANGIBLE_IGDB_CLIENT_SECRET' },
    };
    const TESTABLE_INTEGRATION_KEYS = new Set(['discogs_token', 'tmdb_api_key', 'igdb_client_id', 'google_books_api_key', 'upcitemdb_key']);

    const SECTION_LABELS = $derived<Record<string, string>>({
        security:     $_('settings.section_security'),
        sessions:     $_('settings.section_sessions'),
        integrations: $_('settings.section_integrations'),
        email:        $_('settings.section_email'),
    });

    let siteSettings      = $state<SiteSetting[]>([]);
    let siteSettingsEdits = $state<Record<string, string>>({});
    let siteSettingsSaved = $state(false);
    let siteSettingsError = $state('');
    let siteSettingsLoaded = $state(false);
    let testResults = $state<Record<string, { status: 'idle' | 'testing' | 'ok' | 'error'; message: string }>>({});
    let barcodeAdapters = $state<string[]>([]);

    let scrubModalOpen  = $state(false);
    let scrubConfirmText = $state('');
    let scrubResult     = $state('');
    const scrubPhrase   = 'SCRUB INVENTORY';

    function siteSettingDisplayValue(s: SiteSetting): string {
        if (s.value === null) return '';
        return s.value === '***' ? '' : s.value;
    }

    function siteSettingPlaceholder(s: SiteSetting): string {
        if (s.value === '***') return 'Enter new value to change, or leave blank to keep current';
        if (s.source !== 'default' && s.value !== null && !s.sensitive) return s.value;
        return s.type === 'bool' ? 'true or false' : s.type === 'int' ? String(s.value ?? '') : '';
    }

    async function loadSiteSettings() {
        try {
            siteSettings = await api.get<SiteSetting[]>('/admin/system/settings');
            siteSettingsEdits = {};
            siteSettingsLoaded = true;
        } catch { /* non-admin or unavailable */ }
    }

    async function saveSiteSettings() {
        siteSettingsError = '';
        siteSettingsSaved = false;
        const updates: Record<string, string | null> = {};
        for (const [key, val] of Object.entries(siteSettingsEdits)) {
            updates[key] = val.trim() === '' ? null : val.trim();
        }
        for (const s of siteSettings) {
            if (s.sensitive && s.is_set && !(s.key in updates)) {
                updates[s.key] = '***';
            }
        }
        try {
            siteSettings = await api.put<SiteSetting[]>('/admin/system/settings', { updates });
            siteSettingsEdits = {};
            siteSettingsSaved = true;
        } catch (e) {
            siteSettingsError = (e as Error).message;
        }
    }

    async function clearSiteSetting(key: string) {
        try {
            await fetch(`/api/admin/system/settings/${encodeURIComponent(key)}`, {
                method: 'DELETE',
                credentials: 'include',
            });
            await loadSiteSettings();
        } catch (e) {
            siteSettingsError = (e as Error).message;
        }
    }

    async function testEmail() {
        testResults['__email__'] = { status: 'testing', message: '' };
        try {
            const res = await api.post<{ ok: boolean; message: string }>('/admin/system/test-email', {});
            testResults['__email__'] = { status: res.ok ? 'ok' : 'error', message: res.message };
        } catch (e) {
            testResults['__email__'] = { status: 'error', message: (e as Error).message };
        }
    }

    async function testIntegration(key: string) {
        testResults[key] = { status: 'testing', message: '' };
        try {
            const res = await api.post<{ ok: boolean; message: string }>(`/admin/system/test-integration/${encodeURIComponent(key)}`, {});
            testResults[key] = { status: res.ok ? 'ok' : 'error', message: res.message };
        } catch (e) {
            testResults[key] = { status: 'error', message: (e as Error).message };
        }
    }

    async function loadBarcodeAdapters() {
        try {
            const r = await api.get<{ url: string[]; barcode: string[] }>('/metadata/adapters');
            barcodeAdapters = r.barcode;
        } catch { barcodeAdapters = []; }
    }

    async function scrubInventory() {
        if (scrubConfirmText.trim().toUpperCase() !== scrubPhrase) return;
        try {
            const res = await api.post<{ scrubbed: boolean; deleted_counts: Record<string, number> }>(
                '/admin/system/scrub-inventory',
                { confirmation: scrubConfirmText }
            );
            const total = Object.values(res.deleted_counts).reduce((sum, n) => sum + n, 0);
            scrubResult = `Inventory scrub complete. Deleted ${total} rows.`;
            scrubModalOpen = false;
            scrubConfirmText = '';
        } catch (e) {
            scrubResult = (e as Error).message;
        }
    }

    onMount(async () => {
        if (!$me?.is_admin) { await goto('/settings/appearance'); return; }
        await Promise.all([loadSiteSettings(), loadBarcodeAdapters()]);
    });
</script>

<h2>{$_('settings.nav_admin')}</h2>

{#if scrubResult}<p class="ok">{scrubResult}</p>{/if}

{#if siteSettingsLoaded}
    <div class="card" style="margin-bottom: 1rem">
        <h3 style="margin-top:0">{$_('settings.server_settings_heading')}</h3>
        <p class="muted">
            {$_('settings.server_settings_description')}
            <span class="muted" style="font-size:0.8rem">{$_('settings.server_settings_env_note')}</span>
        </p>

        {#each Object.entries(SECTION_LABELS) as [section, label] (section)}
            {@const group = siteSettings.filter(s => s.section === section)}
            {#if group.length}
                <h4 style="margin:1rem 0 0.5rem">{label}</h4>
                <div class="settings-grid">
                    {#each group as s (s.key)}
                        <div class="setting-row">
                            <div class="setting-meta">
                                <span class="setting-key">{s.key}</span>
                                {#if s.env_var}<code class="env-var">{s.env_var}</code>{/if}
                                <span class="source-badge source-{s.source}">{s.source}</span>
                            </div>
                            <p class="setting-desc muted">{s.description}</p>
                            <div class="setting-input">
                                {#if s.type === 'bool'}
                                    <select
                                        value={s.key in siteSettingsEdits ? siteSettingsEdits[s.key] : (s.source === 'default' ? '' : (s.value ?? ''))}
                                        onchange={(e) => (siteSettingsEdits[s.key] = (e.target as HTMLSelectElement).value)}
                                    >
                                        <option value="">(use {s.source === 'database' ? 'env/default' : 'default'})</option>
                                        <option value="true">true</option>
                                        <option value="false">false</option>
                                    </select>
                                {:else}
                                    <div class="sensitive-wrap">
                                        {#if s.sensitive && s.is_set && !(s.key in siteSettingsEdits)}
                                            <span class="set-badge" title={$_('settings.setting_sensitive_title')}>{$_('settings.setting_sensitive_set_badge')}</span>
                                        {/if}
                                        <input
                                            type={s.sensitive ? 'password' : 'text'}
                                            autocomplete="off"
                                            value={s.key in siteSettingsEdits ? siteSettingsEdits[s.key] : siteSettingDisplayValue(s)}
                                            placeholder={siteSettingPlaceholder(s)}
                                            oninput={(e) => (siteSettingsEdits[s.key] = (e.target as HTMLInputElement).value)}
                                        />
                                    </div>
                                {/if}
                                {#if s.source === 'database'}
                                    <button class="secondary small" title={$_('settings.setting_revert_title')} onclick={() => clearSiteSetting(s.key)}>{$_('settings.setting_revert_button')}</button>
                                {/if}
                                {#if TESTABLE_INTEGRATION_KEYS.has(s.key)}
                                    <button class="secondary small" disabled={testResults[s.key]?.status === 'testing'} onclick={() => testIntegration(s.key)}>
                                        {testResults[s.key]?.status === 'testing' ? $_('settings.testing_button') : $_('settings.test_connection_button')}
                                    </button>
                                    {#if testResults[s.key]?.status === 'ok'}<span class="ok" style="font-size:0.8rem">&#10003; {testResults[s.key].message}</span>{/if}
                                    {#if testResults[s.key]?.status === 'error'}<span class="error" style="font-size:0.8rem">&#10007; {testResults[s.key].message}</span>{/if}
                                {/if}
                            </div>
                        </div>
                    {/each}
                </div>
                {#if section === 'email'}
                    <div style="margin-top:0.75rem;display:flex;align-items:center;gap:0.75rem;flex-wrap:wrap">
                        <button class="secondary small" disabled={testResults['__email__']?.status === 'testing'} onclick={testEmail}>
                            {testResults['__email__']?.status === 'testing' ? $_('settings.testing_button') : $_('settings.test_email_button')}
                        </button>
                        {#if testResults['__email__']?.status === 'ok'}<span class="ok" style="font-size:0.85rem">&#10003; {testResults['__email__'].message}</span>{/if}
                        {#if testResults['__email__']?.status === 'error'}<span class="error" style="font-size:0.85rem">&#10007; {testResults['__email__'].message}</span>{/if}
                    </div>
                {/if}
            {/if}
        {/each}

        {#if siteSettingsError}<p class="error">{siteSettingsError}</p>{/if}
        {#if siteSettingsSaved}<p class="ok">{$_('settings.settings_saved_message')}</p>{/if}
        <div style="margin-top:1rem;display:flex;gap:0.5rem">
            <button onclick={saveSiteSettings}>{$_('settings.save_settings_button')}</button>
            <button class="secondary" onclick={loadSiteSettings}>{$_('settings.reset_settings_button')}</button>
        </div>
    </div>
{/if}

<!-- Barcode & Metadata Services -->
<div class="card" style="margin-bottom: 1rem">
    <h3 style="margin-top:0">Barcode &amp; Metadata Services</h3>
    <p class="muted">
        These services are tried in order when a barcode is scanned. Built-in free services require no configuration.
    </p>
    {#if barcodeAdapters.length === 0}
        <p class="muted">No barcode adapters loaded.</p>
    {:else}
        <table style="width:100%;border-collapse:collapse;font-size:0.9rem">
            <thead>
                <tr style="text-align:left;border-bottom:1px solid var(--border)">
                    <th style="padding:0.4rem 0.5rem">Service</th>
                    <th style="padding:0.4rem 0.5rem">Covers</th>
                    <th style="padding:0.4rem 0.5rem">API key env var</th>
                </tr>
            </thead>
            <tbody>
                {#each barcodeAdapters as name}
                    {@const info = BARCODE_ADAPTER_INFO[name]}
                    <tr style="border-bottom:1px solid var(--border)">
                        <td style="padding:0.4rem 0.5rem;font-weight:500">{info?.label ?? name}</td>
                        <td style="padding:0.4rem 0.5rem;color:var(--muted)">{info?.description ?? ''}</td>
                        <td style="padding:0.4rem 0.5rem">
                            {#if info?.keyHint}
                                <code style="font-size:0.8rem">{info.keyHint}</code>
                            {:else}
                                <span class="muted">not required</span>
                            {/if}
                        </td>
                    </tr>
                {/each}
            </tbody>
        </table>
    {/if}
    <p class="muted" style="margin-top:0.75rem;font-size:0.85rem">
        Add optional API keys in the <strong>Integrations</strong> section of Server Settings above, or via environment variables.
        See <a href="https://github.com/bradbrownjr/tangible/blob/main/docs/admin-guide.md" target="_blank" rel="noopener">admin guide</a> for details.
    </p>
</div>

<!-- System Maintenance -->
<div class="card">
    <h3 style="margin-top:0">{$_('settings.system_maintenance_heading')}</h3>
    <p class="muted">{$_('settings.system_maintenance_description')}</p>
    <Button variant="danger" onclick={() => (scrubModalOpen = true)}>{$_('settings.scrub_inventory_button')}</Button>
</div>

<!-- Scrub modal -->
<Modal open={scrubModalOpen} title={$_('settings.scrub_title')} onclose={() => (scrubModalOpen = false)}>
    <p class="muted">{$_('settings.scrub_text')}</p>
    <label for="scrub-confirm" class="muted">{$_('settings.scrub_confirm_label', { values: { phrase: scrubPhrase } })}</label>
    <input id="scrub-confirm" bind:value={scrubConfirmText} placeholder={scrubPhrase} />
    {#snippet footer()}
        <button type="button" class="secondary" onclick={() => (scrubModalOpen = false)}>{$_('common.cancel')}</button>
        <Button variant="danger"
            disabled={scrubConfirmText.trim().toUpperCase() !== scrubPhrase}
            onclick={scrubInventory}
        >{$_('settings.scrub_confirm_button')}</Button>
    {/snippet}
</Modal>

<style>
    h2 { margin-top: 0; }
    .ok { color: var(--success); }

    .settings-grid { display: grid; gap: 0.75rem; }
    .setting-row {
        display: grid;
        gap: 0.2rem;
        padding: 0.65rem 0.75rem;
        border: 1px solid var(--border);
        border-radius: 8px;
        background: var(--surface-2);
    }
    .setting-meta { display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; }
    .setting-key { font-weight: 600; font-size: 0.875rem; font-family: monospace; }
    .env-var {
        font-size: 0.75rem;
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 4px;
        padding: 0.1rem 0.35rem;
        color: var(--muted);
    }
    .source-badge {
        font-size: 0.7rem;
        padding: 0.1rem 0.4rem;
        border-radius: 999px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .source-database    { background: color-mix(in srgb, var(--info) 15%, transparent); color: var(--info); }
    .source-environment { background: color-mix(in srgb, var(--success) 15%, transparent); color: var(--success); }
    .source-default     { background: var(--surface); color: var(--muted); border: 1px solid var(--border); }
    .setting-desc  { margin: 0; font-size: 0.8rem; }
    .setting-input { display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap; }
    .setting-input input, .setting-input select { flex: 1; min-width: 0; }
    button.small   { padding: 0.25rem 0.6rem; font-size: 0.8rem; }
    .sensitive-wrap { display: flex; align-items: center; gap: 0.4rem; flex: 1; min-width: 0; }
    .sensitive-wrap input { flex: 1; min-width: 0; }
    .set-badge {
        flex-shrink: 0;
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        padding: 0.15rem 0.45rem;
        border-radius: 999px;
        background: color-mix(in srgb, var(--success) 15%, transparent);
        color: var(--success);
        border: 1px solid color-mix(in srgb, var(--success) 45%, transparent);
        white-space: nowrap;
    }
</style>
