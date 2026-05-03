<script lang="ts">
    import { onMount } from 'svelte';
    import { page } from '$app/state';
    import { _ } from 'svelte-i18n';
    import { api, type Collection, type Item } from '$lib/api';

    let collection = $state<Collection | null>(null);
    let items = $state<Item[]>([]);
    let loading = $state(true);
    let error = $state('');

    const slug = $derived(page.params.slug ?? '');

    async function load() {
        loading = true;
        try {
            collection = await api.get<Collection>(`/public/share/${slug}`);
            items = await api.get<Item[]>(`/public/share/${slug}/items`);
        } catch (e) {
            error = (e as Error).message;
        } finally {
            loading = false;
        }
    }

    onMount(load);
</script>

{#if loading}
    <p class="muted">{$_('common.loading')}</p>
{:else if error}
    <h1>{$_('share.not_available')}</h1>
    <p class="error">{error}</p>
    <p class="muted">{$_('share.expired_message')}</p>
{:else if collection}
    <h1>{collection.name}</h1>
    {#if collection.description}<p class="muted">{collection.description}</p>{/if}
    <p class="muted">{$_('share.read_only_note')}</p>

    {#if items.length === 0}
        <p class="muted">{$_('share.no_items')}</p>
    {:else}
        <table>
            <thead>
                <tr>
                    <th>{$_('collection.col_category')}</th>
                    <th>{$_('collection.col_title')}</th>
                    <th>{$_('collection.col_qty')}</th>
                    <th>{$_('collection.col_condition')}</th>
                </tr>
            </thead>
            <tbody>
                {#each items as i (i.id)}
                    <tr>
                        <td class="muted">{i.category_slug ?? ''}</td>
                        <td>
                            {i.title}{#if i.subtitle}
                                <span class="muted">— {i.subtitle}</span>
                            {/if}
                        </td>
                        <td>{i.quantity}</td>
                        <td>{i.condition ?? ''}</td>
                    </tr>
                {/each}
            </tbody>
        </table>
    {/if}
{/if}
