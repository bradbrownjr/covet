<script lang="ts">
    import { Modal } from '$lib/components';
    import { _ } from 'svelte-i18n';

    interface ArchivePayload {
        disposition_type: 'archived' | 'sold' | 'disposed' | 'donated';
        disposition_at?: string;
        disposition_buyer?: string;
        disposition_note?: string;
        disposition_amount?: number;
    }

    interface Props {
        open: boolean;
        itemTitle: string;
        onconfirm: (payload: ArchivePayload) => void;
        oncancel: () => void;
    }

    let { open, itemTitle, onconfirm, oncancel }: Props = $props();

    let dispositionType = $state<'archived' | 'sold' | 'disposed' | 'donated'>('archived');
    let dispositionAt = $state('');
    let dispositionAmount = $state('');
    let dispositionBuyer = $state('');
    let dispositionNote = $state('');

    $effect(() => {
        if (open) {
            dispositionType = 'archived';
            dispositionAt = new Date().toISOString().slice(0, 16);
            dispositionAmount = '';
            dispositionBuyer = '';
            dispositionNote = '';
        }
    });

    function confirm() {
        const payload: ArchivePayload = { disposition_type: dispositionType };
        if (dispositionAt) payload.disposition_at = new Date(dispositionAt).toISOString();
        if (dispositionBuyer.trim()) payload.disposition_buyer = dispositionBuyer.trim();
        if (dispositionNote.trim()) payload.disposition_note = dispositionNote.trim();
        if (dispositionAmount.trim()) payload.disposition_amount = Number(dispositionAmount);
        onconfirm(payload);
    }
</script>

<Modal {open} title={$_('collection.archive_title')} onclose={oncancel}>
    <p style="margin:0 0 0.75rem;color:var(--text-muted)">{$_('collection.archive_text', { values: { title: itemTitle || 'this item' } })}</p>
    <label style="display:flex;flex-direction:column;gap:0.25rem;font-size:0.875rem">
        {$_('collection.archive_disposition_label')}
        <select bind:value={dispositionType}>
            <option value="archived">{$_('collection.archive_archived')}</option>
            <option value="sold">{$_('collection.archive_sold')}</option>
            <option value="disposed">{$_('collection.archive_disposed')}</option>
            <option value="donated">{$_('collection.archive_donated')}</option>
        </select>
    </label>
    <label style="display:flex;flex-direction:column;gap:0.25rem;font-size:0.875rem">
        {$_('collection.archive_date_label')}
        <input type="datetime-local" bind:value={dispositionAt} />
    </label>
    <label style="display:flex;flex-direction:column;gap:0.25rem;font-size:0.875rem">
        {$_('collection.archive_amount_label')}
        <input type="number" min="0" step="0.01" bind:value={dispositionAmount} placeholder={$_('collection.archive_amount_placeholder')} />
    </label>
    <label style="display:flex;flex-direction:column;gap:0.25rem;font-size:0.875rem">
        {$_('collection.archive_buyer_label')}
        <input bind:value={dispositionBuyer} maxlength="256" placeholder={$_('collection.archive_buyer_placeholder')} />
    </label>
    <label style="display:flex;flex-direction:column;gap:0.25rem;font-size:0.875rem">
        {$_('collection.archive_note_label')}
        <input bind:value={dispositionNote} maxlength="512" placeholder={$_('collection.archive_note_placeholder')} />
    </label>
    {#snippet footer()}
        <button type="button" class="secondary" onclick={oncancel}>{$_('common.cancel')}</button>
        <button type="button" onclick={confirm}>{$_('collection.archive_confirm')}</button>
    {/snippet}
</Modal>
