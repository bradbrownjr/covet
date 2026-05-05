<!-- Inline alert / banner.
     Variants: info (default) | success | warning | danger
     Usage: <Alert variant="danger">Something went wrong.</Alert>
            <Alert variant="success" dismissible onclose={clear}>Saved!</Alert>
-->
<script lang="ts">
    import type { Snippet } from 'svelte';
    import Icon from '$lib/Icon.svelte';

    interface Props {
        variant?: 'info' | 'success' | 'warning' | 'danger';
        dismissible?: boolean;
        onclose?: () => void;
        class?: string;
        children: Snippet;
    }

    let { variant = 'info', dismissible = false, onclose, class: cls = '', children }: Props =
        $props();

    const ICONS: Record<string, string> = {
        info: 'info',
        success: 'check-circle',
        warning: 'triangle-alert',
        danger: 'circle-x',
    };
</script>

<div class="alert alert--{variant} {cls}" role="alert">
    <Icon name={ICONS[variant]} size={16} aria-hidden={true} />
    <span class="alert__body">{@render children()}</span>
    {#if dismissible}
        <button
            type="button"
            class="alert__close"
            aria-label="Dismiss"
            onclick={() => onclose?.()}
        >
            <Icon name="x" size={14} />
        </button>
    {/if}
</div>

<style>
    .alert {
        display: flex;
        align-items: flex-start;
        gap: var(--space-2);
        padding: var(--space-3) var(--space-4);
        border-radius: var(--radius-md);
        font-size: var(--text-sm);
        border: 1px solid transparent;
    }

    .alert--info    {
        background: color-mix(in srgb, var(--info)    12%, var(--surface));
        border-color: color-mix(in srgb, var(--info)    30%, transparent);
        color: var(--info);
    }
    .alert--success {
        background: color-mix(in srgb, var(--success) 12%, var(--surface));
        border-color: color-mix(in srgb, var(--success) 30%, transparent);
        color: var(--success);
    }
    .alert--warning {
        background: color-mix(in srgb, var(--warning) 12%, var(--surface));
        border-color: color-mix(in srgb, var(--warning) 30%, transparent);
        color: var(--warning);
    }
    .alert--danger  {
        background: color-mix(in srgb, var(--danger)  12%, var(--surface));
        border-color: color-mix(in srgb, var(--danger)  30%, transparent);
        color: var(--danger);
    }

    .alert__body { flex: 1; color: var(--text); }

    .alert__close {
        flex-shrink: 0;
        background: transparent;
        border: none;
        cursor: pointer;
        color: currentColor;
        padding: 0;
        min-height: auto;
        display: flex;
        align-items: center;
        opacity: 0.7;
    }
    .alert__close:hover { opacity: 1; }
</style>
