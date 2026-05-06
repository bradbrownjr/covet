<script lang="ts">
    import { onMount } from 'svelte';
    import { _ } from 'svelte-i18n';
    import { api } from '$lib/api';
    import Icon from '$lib/Icon.svelte';

    interface ShoppingCount {
        total: number;
        ad_hoc: number;
        depleted_items: number;
        by_type: Record<string, number>;
    }

    const TYPES: { slug: string; key: string; icon: string }[] = [
        { slug: 'groceries', key: 'lists.type.groceries', icon: 'shopping-cart' },
        { slug: 'hardware', key: 'lists.type.hardware', icon: 'wrench' },
        { slug: 'home_goods', key: 'lists.type.home_goods', icon: 'house' },
        { slug: 'wish_list', key: 'lists.type.wish_list', icon: 'star' }
    ];

    let counts = $state<Record<string, number>>({});

    onMount(async () => {
        try {
            const c = await api.get<ShoppingCount>('/lists/count');
            counts = c.by_type ?? {};
        } catch {
            counts = {};
        }
    });
</script>

<h1>{$_('nav.lists')}</h1>

<div class="tiles">
    {#each TYPES as t (t.slug)}
        <a href={`/lists/${t.slug}`} class="tile">
            <Icon name={t.icon} size={28} />
            <strong>{$_(t.key)}</strong>
            {#if counts[t.slug]}<span class="badge">{counts[t.slug]}</span>{/if}
        </a>
    {/each}
</div>

<style>
    h1 { margin: 0 0 1rem; }
    .tiles {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
        gap: 0.75rem;
    }
    .tile {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        padding: 1.5rem 0.75rem;
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 8px;
        color: inherit;
        text-decoration: none;
        position: relative;
    }
    .tile:hover { border-color: var(--accent); }
    .badge {
        position: absolute;
        top: 0.5rem;
        right: 0.5rem;
        background: var(--accent);
        color: var(--accent-contrast, white);
        border-radius: 999px;
        font-size: 0.75rem;
        padding: 0.05rem 0.45rem;
        min-width: 1.25rem;
        text-align: center;
    }
</style>
