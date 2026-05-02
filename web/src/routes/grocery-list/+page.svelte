<script lang="ts">
    import { onMount } from 'svelte';
    import { api, type Collection } from '$lib/api';

    interface FeedEntry {
        id: string;
        source: { kind: 'ad_hoc' | 'depleted_item'; item_id: string | null };
        collection_id: string;
        name: string;
        subtitle: string | null;
        quantity: number;
        unit: string | null;
        notes: string | null;
        linked_item_id: string | null;
        purchased_at: string | null;
        created_at: string;
    }

    let feed = $state<FeedEntry[]>([]);
    let collections = $state<Map<string, Collection>>(new Map());
    let loading = $state(true);
    let error = $state('');

    let newCollectionId = $state('');
    let newName = $state('');
    let newQuantity = $state(1);
    let newUnit = $state('');
    let newNotes = $state('');
    let adding = $state(false);

    async function load() {
        loading = true;
        try {
            const [fetched, fetchedCollections] = await Promise.all([
                api.get<FeedEntry[]>('/grocery'),
                api.get<Collection[]>('/collections'),
            ]);
            feed = fetched;
            collections = new Map(fetchedCollections.map((c) => [c.id, c]));
            if (!newCollectionId && fetchedCollections.length > 0) {
                newCollectionId = fetchedCollections[0].id;
            }
        } catch (e) {
            error = (e as Error).message;
        } finally {
            loading = false;
        }
    }

    async function addItem(e: SubmitEvent) {
        e.preventDefault();
        if (!newCollectionId || !newName.trim()) return;
        adding = true;
        try {
            await api.post('/grocery', {
                collection_id: newCollectionId,
                name: newName.trim(),
                quantity: Math.max(1, newQuantity || 1),
                unit: newUnit.trim() || null,
                notes: newNotes.trim() || null,
            });
            newName = '';
            newQuantity = 1;
            newUnit = '';
            newNotes = '';
            await load();
        } catch (err) {
            error = (err as Error).message;
        } finally {
            adding = false;
        }
    }

    async function markPurchased(entry: FeedEntry) {
        try {
            if (entry.source.kind === 'ad_hoc') {
                await api.post(`/grocery/${entry.id}/purchase`, {
                    purchased_at: new Date().toISOString(),
                });
            } else if (entry.linked_item_id) {
                await api.post(`/items/${entry.linked_item_id}/restock`, {
                    quantity: 1,
                    purchased_at: new Date().toISOString(),
                });
            }
            await load();
        } catch (err) {
            error = (err as Error).message;
        }
    }

    async function removeItem(entry: FeedEntry) {
        if (entry.source.kind !== 'ad_hoc') return;
        try {
            await api.delete(`/grocery/${entry.id}`);
            feed = feed.filter((e) => e.id !== entry.id);
        } catch (err) {
            error = (err as Error).message;
        }
    }

    onMount(load);
</script>

<h1>Grocery List</h1>
<p class="muted">Items added by you, plus anything marked depleted across your shared collections.</p>

<form class="add-form" onsubmit={addItem}>
    <select bind:value={newCollectionId} required>
        {#each [...collections.values()] as c (c.id)}
            <option value={c.id}>{c.name}</option>
        {/each}
    </select>
    <input type="text" bind:value={newName} placeholder="Add item (e.g. Bananas)" required />
    <input type="number" min="1" bind:value={newQuantity} class="qty" />
    <input type="text" bind:value={newUnit} placeholder="unit" class="unit" />
    <input type="text" bind:value={newNotes} placeholder="notes" class="notes" />
    <button type="submit" disabled={adding || !newName.trim()}>{adding ? 'Adding…' : 'Add'}</button>
</form>

{#if loading}
    <p class="muted">Loading…</p>
{:else if error}
    <p class="error">{error}</p>
{:else if feed.length === 0}
    <p class="muted">Nothing on the list — all clear!</p>
{:else}
    <table>
        <thead>
            <tr>
                <th>Item</th>
                <th>Qty</th>
                <th>Collection</th>
                <th>Source</th>
                <th></th>
            </tr>
        </thead>
        <tbody>
            {#each feed as entry (entry.id)}
                <tr>
                    <td>
                        <strong>{entry.name}</strong>
                        {#if entry.subtitle}<span class="muted"> · {entry.subtitle}</span>{/if}
                        {#if entry.notes}<div class="muted small">{entry.notes}</div>{/if}
                    </td>
                    <td>{entry.quantity}{entry.unit ? ' ' + entry.unit : ''}</td>
                    <td>
                        <a href="/collections/{entry.collection_id}">
                            {collections.get(entry.collection_id)?.name ?? entry.collection_id}
                        </a>
                    </td>
                    <td class="muted small">
                        {entry.source.kind === 'depleted_item' ? 'depleted' : 'manual'}
                        {#if entry.linked_item_id && entry.source.kind === 'ad_hoc'}
                            &nbsp;· linked
                        {/if}
                    </td>
                    <td class="actions">
                        <button type="button" onclick={() => markPurchased(entry)}>
                            Mark purchased
                        </button>
                        {#if entry.source.kind === 'ad_hoc'}
                            <button type="button" class="secondary" onclick={() => removeItem(entry)}>
                                Remove
                            </button>
                        {/if}
                    </td>
                </tr>
            {/each}
        </tbody>
    </table>
{/if}

<style>
    .add-form {
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
        margin: 1rem 0 1.5rem;
    }
    .add-form input.qty { width: 4rem; }
    .add-form input.unit { width: 6rem; }
    .add-form input.notes { flex: 1; min-width: 12rem; }
    table { width: 100%; border-collapse: collapse; }
    th, td { padding: 0.5rem; border-bottom: 1px solid var(--border, #e5e7eb); text-align: left; }
    .small { font-size: 0.85rem; }
    .actions { white-space: nowrap; display: flex; gap: 0.4rem; }
</style>
