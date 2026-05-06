<script lang="ts">
    import { Modal } from '$lib/components';
    import { _ } from 'svelte-i18n';

    interface Props {
        open: boolean;
        itemTitle: string;
        initialNote?: string;
        onconfirm: (note: string) => void;
        oncancel: () => void;
    }

    let { open, itemTitle, initialNote = '', onconfirm, oncancel }: Props = $props();

    let flagNote = $state('');

    $effect(() => {
        if (open) flagNote = initialNote;
    });
</script>

<Modal {open} title={$_('collection.flag_title')} onclose={oncancel}>
    <p style="margin:0 0 0.75rem;color:var(--text-muted)">{$_('collection.flag_text', { values: { title: itemTitle || 'This item' } })}</p>
    <label style="display:flex;flex-direction:column;gap:0.25rem;font-size:0.875rem">
        {$_('collection.flag_note_label')}
        <input bind:value={flagNote} maxlength="256" placeholder={$_('collection.flag_note_placeholder')} />
    </label>
    {#snippet footer()}
        <button type="button" class="secondary" onclick={oncancel}>{$_('common.cancel')}</button>
        <button type="button" onclick={() => onconfirm(flagNote)}>{$_('collection.flag_confirm')}</button>
    {/snippet}
</Modal>
