<script lang="ts">
    import { onMount } from 'svelte';
    import { api } from '$lib/api';
    import { me } from '$lib/session';
    import { _ } from 'svelte-i18n';
    import { Button, Modal } from '$lib/components';

    interface TOTPStatus { enabled: boolean; backup_codes_remaining: number; }

    let totpStatus       = $state<TOTPStatus | null>(null);
    let deleteAccountOpen = $state(false);
    let deletePassword   = $state('');
    let deleteTotpCode   = $state('');
    let deleteMessage    = $state('');

    async function loadTotpStatus() {
        try {
            totpStatus = await api.get<TOTPStatus>('/auth/totp');
        } catch { /* not critical */ }
    }

    async function exportAccount() {
        window.location.href = '/api/auth/me/export';
    }

    async function deleteAccount() {
        try {
            await fetch('/api/auth/me', {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ password: deletePassword, totp_code: deleteTotpCode || null }),
                credentials: 'include',
            });
            window.location.href = '/login';
        } catch (e) {
            deleteMessage = (e as Error).message;
        }
    }

    onMount(loadTotpStatus);
</script>

<h2>{$_('settings.nav_account')}</h2>

<div class="card">
    <h3 style="margin-top:0">{$_('settings.account_heading')}</h3>
    <p class="muted">{$_('settings.account_description')}</p>
    <div style="display:flex; gap:0.5rem; flex-wrap:wrap">
        <button class="secondary" onclick={exportAccount}>{$_('settings.export_data_button')}</button>
        <Button variant="danger" onclick={() => (deleteAccountOpen = true)}>{$_('settings.delete_account_button')}</Button>
    </div>
</div>

<Modal open={deleteAccountOpen} title={$_('settings.delete_account_title')} onclose={() => (deleteAccountOpen = false)}>
    <p class="muted">{$_('settings.delete_account_text')}</p>
    <div class="field"><label>{$_('settings.totp_disable_password_label')}<input type="password" bind:value={deletePassword} autocomplete="current-password" /></label></div>
    {#if totpStatus?.enabled}
        <div class="field"><label>{$_('settings.totp_disable_code_label')}<input bind:value={deleteTotpCode} maxlength={10} inputmode="numeric" placeholder={$_('settings.delete_totp_placeholder')} /></label></div>
    {/if}
    {#if deleteMessage}<p class="error">{deleteMessage}</p>{/if}
    {#snippet footer()}
        <button type="button" class="secondary" onclick={() => (deleteAccountOpen = false)}>{$_('common.cancel')}</button>
        <Button variant="danger" onclick={deleteAccount}>{$_('settings.delete_confirm_button')}</Button>
    {/snippet}
</Modal>

<style>
    h2 { margin-top: 0; }
    .field { display: grid; gap: 0.25rem; }
    .field label { font-size: 0.875rem; font-weight: 500; }
    .field input { width: 100%; }
</style>
