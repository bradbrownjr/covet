<!-- Confirmation dialog built on Modal.
     Usage:
       <ConfirmDialog
           bind:open
           title="Delete item?"
           message="This cannot be undone."
           confirmLabel="Delete"
           variant="danger"
           onconfirm={doDelete}
           oncancel={() => open = false}
       />
-->
<script lang="ts">
    import Modal from './Modal.svelte';
    import Button from './Button.svelte';

    interface Props {
        open?: boolean;
        title?: string;
        message?: string;
        confirmLabel?: string;
        cancelLabel?: string;
        variant?: 'primary' | 'danger';
        loading?: boolean;
        onconfirm?: () => void | Promise<void>;
        oncancel?: () => void;
    }

    let {
        open = false,
        title = 'Are you sure?',
        message,
        confirmLabel = 'Confirm',
        cancelLabel = 'Cancel',
        variant = 'danger',
        loading = false,
        onconfirm,
        oncancel,
    }: Props = $props();

    async function confirm() {
        await onconfirm?.();
    }
</script>

<Modal {open} {title} width="26rem" onclose={oncancel}>
    {#if message}
        <p style="margin:0;color:var(--text-muted)">{message}</p>
    {/if}

    {#snippet footer()}
        <Button variant="ghost" onclick={oncancel}>{cancelLabel}</Button>
        <Button {variant} {loading} onclick={confirm}>{confirmLabel}</Button>
    {/snippet}
</Modal>
