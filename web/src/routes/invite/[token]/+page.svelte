<script lang="ts">
    import { onMount } from 'svelte';
    import { page } from '$app/state';
    import { goto } from '$app/navigation';
    import { _ } from 'svelte-i18n';
    import { api, userLabel, type InvitationPreview } from '$lib/api';
    import { me } from '$lib/session';

    let preview = $state<InvitationPreview | null>(null);
    let loading = $state(true);
    let error = $state('');
    let accepting = $state(false);

    const token = $derived(page.params.token ?? '');

    async function load() {
        loading = true;
        try {
            preview = await api.get<InvitationPreview>(`/invitations/${token}`);
        } catch (e) {
            error = (e as Error).message;
        } finally {
            loading = false;
        }
    }

    async function accept() {
        accepting = true;
        try {
            await api.post(`/invitations/${token}/accept`);
            await goto(`/collections/${preview!.collection_id}`);
        } catch (e) {
            error = (e as Error).message;
            accepting = false;
        }
    }

    onMount(load);
</script>

<h1>{$_('invite.title')}</h1>

{#if loading}
    <p class="muted">{$_('common.loading')}</p>
{:else if error}
    <p class="error">{error}</p>
    <p class="muted">{$_('invite.expired_message')}</p>
{:else if preview}
    <div class="card">
        <p>
            {$_('invite.joined_as', {values: {name: preview.collection_name, role: preview.role}})}
        </p>

        {#if $me}
            <p class="muted">{$_('invite.signed_in_as', {values: {user: userLabel($me)}})}</p>
            <button onclick={accept} disabled={accepting}>
                {accepting ? $_('invite.accepting_button') : $_('invite.accept_button')}
            </button>
        {:else}
            <p>{$_('invite.sign_in_prompt')}</p>
            <a href="/login?next={encodeURIComponent(`/invite/${token}`)}">{$_('invite.sign_in_link')}</a>
            ·
            <a href="/register">{$_('invite.create_account_link')}</a>
        {/if}
    </div>
{/if}
