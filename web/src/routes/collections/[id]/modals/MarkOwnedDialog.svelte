<script lang="ts">
    import { Modal } from '$lib/components';
    import { _ } from 'svelte-i18n';

    interface Props {
        open: boolean;
        itemTitle: string;
        onconfirm: (ownedAt: string, ownedPrice: string) => void;
        oncancel: () => void;
    }

    let { open, itemTitle, onconfirm, oncancel }: Props = $props();

    let ownedAt = $state('');
    let ownedPrice = $state('');

    $effect(() => {
        if (open) {
            ownedAt = new Date().toISOString().slice(0, 16);
            ownedPrice = '';
        }
    });
</script>

<Modal {open} title={$_('collection.mark_owned_title')} onclose={oncancel}>
    <p style="margin:0 0 0.75rem;color:var(--text-muted)">{$_('collection.mark_owned_text', { values: { title: itemTitle || 'this item' } })}</p>
    <label style="display:flex;flex-direction:column;gap:0.25rem;font-size:0.875rem">
        {$_('collection.mark_owned_date_label')}
        <input type="datetime-local" bind:value={ownedAt} />
    </label>
    <label style="display:flex;flex-direction:column;gap:0.25rem;font-size:0.875rem">
        {$_('collection.mark_owned_price_label')}
        <input type="number" min="0" step="0.01" bind:value={ownedPrice} placeholder={$_('collection.mark_owned_price_placeholder')} />
    </label>
    {#snippet footer()}
        <button type="button" class="secondary" onclick={oncancel}>{$_('common.cancel')}</button>
        <button type="button" onclick={() => onconfirm(ownedAt, ownedPrice)}>{$_('collection.mark_owned_confirm')}</button>
    {/snippet}
</Modal>
