<!-- Empty state illustration with CTA.
     Usage:
       <EmptyState
           icon="box"
           heading="No items yet"
           body="Add your first item to get started."
       >
           <Button onclick={openAdd}>Add item</Button>
       </EmptyState>
-->
<script lang="ts">
    import type { Snippet } from 'svelte';
    import Icon from '$lib/Icon.svelte';

    interface Props {
        icon?: string;
        heading: string;
        body?: string;
        class?: string;
        children?: Snippet;
    }

    let { icon = 'inbox', heading, body, class: cls = '', children }: Props = $props();
</script>

<div class="empty-state {cls}">
    <span class="empty-state__icon" aria-hidden="true">
        <Icon name={icon} size={48} />
    </span>
    <h3 class="empty-state__heading">{heading}</h3>
    {#if body}
        <p class="empty-state__body">{body}</p>
    {/if}
    {#if children}
        <div class="empty-state__actions">
            {@render children()}
        </div>
    {/if}
</div>

<style>
    .empty-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: var(--space-8) var(--space-5);
        gap: var(--space-3);
        color: var(--text-muted);
    }

    .empty-state__icon { opacity: 0.35; }

    .empty-state__heading {
        margin: 0;
        font-size: var(--text-lg);
        font-weight: 700;
        color: var(--text);
    }

    .empty-state__body {
        margin: 0;
        font-size: var(--text-sm);
        max-width: 28rem;
    }

    .empty-state__actions {
        margin-top: var(--space-2);
        display: flex;
        gap: var(--space-3);
        flex-wrap: wrap;
        justify-content: center;
    }
</style>
