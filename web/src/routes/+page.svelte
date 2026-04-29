<script lang="ts">
    import { onMount } from 'svelte';
    import { api, type Collection } from '$lib/api';

    let collections = $state<Collection[]>([]);
    let newName = $state('');
    let error = $state('');
    let loading = $state(true);

    async function refresh() {
        try {
            collections = await api.get<Collection[]>('/collections');
        } catch (e) {
            error = (e as Error).message;
        } finally {
            loading = false;
        }
    }

    async function create(e: Event) {
        e.preventDefault();
        if (!newName.trim()) return;
        try {
            await api.post('/collections', { name: newName.trim() });
            newName = '';
            error = '';
            await refresh();
        } catch (e) {
            error = (e as Error).message;
        }
    }

    onMount(refresh);
</script>

<h1>Collections</h1>

<form onsubmit={create} class="card" style="margin-bottom: 1.5rem">
    <div class="field">
        <label for="cname">New collection</label>
        <div style="display:flex; gap:.5rem">
            <input id="cname" bind:value={newName} placeholder="e.g. Vinyl, Comics, Tools" />
            <button type="submit">Create</button>
        </div>
        {#if error}<p class="error">{error}</p>{/if}
    </div>
</form>

{#if loading}
    <p class="muted">Loading…</p>
{:else if collections.length === 0}
    <p class="muted">No collections yet. Create one above to get started.</p>
{:else}
    <div class="grid">
        {#each collections as c (c.id)}
            <a href={`/collections/${c.id}`} class="card collection">
                <h3>{c.name}</h3>
                {#if c.description}<p class="muted">{c.description}</p>{/if}
            </a>
        {/each}
    </div>
{/if}

<style>
    .collection {
        display: block;
        color: inherit;
    }
    .collection:hover {
        border-color: var(--accent);
        text-decoration: none;
    }
    h3 {
        margin: 0 0 0.5rem 0;
    }
    p {
        margin: 0;
    }
</style>
