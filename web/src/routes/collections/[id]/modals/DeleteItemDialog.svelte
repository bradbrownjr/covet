<script lang="ts">
    import { ConfirmDialog } from '$lib/components';
    import { _ } from 'svelte-i18n';

    interface Props {
        open: boolean;
        itemTitle: string;
        onconfirm: () => void;
        oncancel: () => void;
    }

    let { open, itemTitle, onconfirm, oncancel }: Props = $props();
</script>

<ConfirmDialog
    {open}
    title={$_('collection.delete_item_title')}
    variant="danger"
    confirmLabel={$_('common.delete')}
    message={$_('collection.delete_item_text', { values: { title: itemTitle || 'This item' } })}
    {onconfirm}
    {oncancel}
/>
