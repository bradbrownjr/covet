<!-- Titled section card — a labelled card block used in settings / detail pages.
     Usage:
       <SectionCard title="Danger zone">
           ... content ...
       </SectionCard>
-->
<script lang="ts">
    import type { Snippet } from 'svelte';

    interface Props {
        title?: string;
        description?: string;
        class?: string;
        actions?: Snippet;
        children: Snippet;
    }

    let { title, description, class: cls = '', actions, children }: Props = $props();
</script>

<section class="section-card card {cls}">
    {#if title || actions}
        <header class="section-card__header">
            <div>
                {#if title}<h3 class="section-card__title">{title}</h3>{/if}
                {#if description}<p class="section-card__desc">{description}</p>{/if}
            </div>
            {#if actions}
                <div class="section-card__actions">{@render actions()}</div>
            {/if}
        </header>
    {/if}
    <div class="section-card__body">
        {@render children()}
    </div>
</section>

<style>
    .section-card__header {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: var(--space-4);
        margin-bottom: var(--space-4);
    }

    .section-card__title {
        margin: 0 0 var(--space-1);
        font-size: var(--text-lg);
        font-weight: 700;
    }

    .section-card__desc {
        margin: 0;
        font-size: var(--text-sm);
        color: var(--text-muted);
    }

    .section-card__actions { flex-shrink: 0; }
</style>
