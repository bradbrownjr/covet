<!-- Small status label / tag chip.
     Variants: default | success | warning | danger | info
     Usage: <Badge variant="success">Active</Badge>
-->
<script lang="ts">
    import type { Snippet } from 'svelte';

    interface Props {
        variant?: 'default' | 'success' | 'warning' | 'danger' | 'info';
        class?: string;
        children: Snippet;
    }

    let { variant = 'default', class: cls = '', children }: Props = $props();
</script>

<span class="badge badge--{variant} {cls}">
    {@render children()}
</span>

<style>
    .badge {
        display: inline-flex;
        align-items: center;
        gap: var(--space-1);
        font-size: var(--text-xs);
        font-weight: 600;
        padding: 0.2em 0.55em;
        border-radius: var(--radius-full);
        line-height: 1;
        white-space: nowrap;
    }

    .badge--default { background: var(--surface-2); color: var(--text-muted); }
    .badge--success { background: color-mix(in srgb, var(--success) 18%, transparent); color: var(--success); }
    .badge--warning { background: color-mix(in srgb, var(--warning) 18%, transparent); color: var(--warning); }
    .badge--danger  { background: color-mix(in srgb, var(--danger)  18%, transparent); color: var(--danger); }
    .badge--info    { background: color-mix(in srgb, var(--info)    18%, transparent); color: var(--info); }
</style>
