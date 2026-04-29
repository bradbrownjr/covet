<script lang="ts">
    import { onMount } from 'svelte';
    import { api, type Category, type Collection } from '$lib/api';
    import { loadCategories, rootCategories } from '$lib/categories';

    let collections = $state<Collection[]>([]);
    let categories = $state<Category[]>([]);
    let error = $state('');
    let loading = $state(true);

    // Wizard state
    let pickerOpen = $state(false);
    let chosen = $state<{ slug: string | null; name: string; description: string } | null>(null);
    let formName = $state('');
    let formDescription = $state('');
    let creating = $state(false);

    const roots = $derived(rootCategories(categories));

    async function refresh() {
        try {
            collections = await api.get<Collection[]>('/collections');
            if (categories.length === 0) categories = await loadCategories();
        } catch (e) {
            error = (e as Error).message;
        } finally {
            loading = false;
        }
    }

    function openPicker() {
        pickerOpen = true;
        chosen = null;
    }

    function pickPreset(root: Category) {
        chosen = { slug: root.slug, name: root.name, description: root.description ?? '' };
        formName = root.name;
        formDescription = root.description ?? '';
    }

    function pickCustom() {
        chosen = { slug: null, name: '', description: '' };
        formName = '';
        formDescription = '';
    }

    function cancel() {
        pickerOpen = false;
        chosen = null;
        formName = '';
        formDescription = '';
        error = '';
    }

    async function create(e: Event) {
        e.preventDefault();
        if (!formName.trim()) return;
        creating = true;
        try {
            await api.post('/collections', {
                name: formName.trim(),
                description: formDescription.trim() || null,
                default_category_slug: chosen?.slug ?? null
            });
            cancel();
            await refresh();
        } catch (e) {
            error = (e as Error).message;
        } finally {
            creating = false;
        }
    }

    onMount(refresh);
</script>

<h1>Collections</h1>

{#if !pickerOpen}
    <div style="margin-bottom: 1.5rem">
        <button type="button" onclick={openPicker}>+ New collection</button>
    </div>
{:else if !chosen}
    <div class="card" style="margin-bottom: 1.5rem">
        <h3 style="margin-top:0">What are you collecting?</h3>
        <p class="muted" style="margin-top:0">
            Pick a starting point — you can rename, mix, and add other categories later.
        </p>
        <div class="presets">
            {#each roots as r (r.id)}
                <button type="button" class="preset" onclick={() => pickPreset(r)}>
                    <strong>{r.name}</strong>
                    {#if r.description}<span class="muted">{r.description}</span>{/if}
                </button>
            {/each}
            <button type="button" class="preset preset-custom" onclick={pickCustom}>
                <strong>Custom</strong>
                <span class="muted">Name it whatever you want and pick categories per item.</span>
            </button>
        </div>
        <p style="margin-top:1rem">
            <button type="button" class="link" onclick={cancel}>Cancel</button>
        </p>
    </div>
{:else}
    <form onsubmit={create} class="card" style="margin-bottom: 1.5rem">
        <h3 style="margin-top:0">
            {chosen.slug ? `New ${chosen.name} collection` : 'New custom collection'}
        </h3>
        <div class="field">
            <label for="cname">Name</label>
            <input id="cname" bind:value={formName} placeholder="e.g. My LPs" required />
        </div>
        <div class="field">
            <label for="cdesc">Description (optional)</label>
            <input id="cdesc" bind:value={formDescription} />
        </div>
        {#if chosen.slug}
            <p class="muted" style="margin: .25rem 0 1rem">
                New items in this collection default to <code>{chosen.slug}</code>; you can pick a
                different category per item.
            </p>
        {/if}
        {#if error}<p class="error">{error}</p>{/if}
        <div style="display:flex; gap:.5rem">
            <button type="submit" disabled={creating}>{creating ? 'Creating…' : 'Create'}</button>
            <button type="button" class="link" onclick={cancel}>Cancel</button>
        </div>
    </form>
{/if}

{#if loading}
    <p class="muted">Loading…</p>
{:else if collections.length === 0}
    <p class="muted">No collections yet. Click <strong>New collection</strong> to get started.</p>
{:else}
    <div class="grid">
        {#each collections as c (c.id)}
            <a href={`/collections/${c.id}`} class="card collection">
                <h3>{c.name}</h3>
                {#if c.description}<p class="muted">{c.description}</p>{/if}
                {#if c.default_category_slug}
                    <p class="badge">{c.default_category_slug}</p>
                {/if}
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
    .presets {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
        gap: 0.5rem;
    }
    .preset {
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        gap: 0.25rem;
        padding: 0.75rem;
        text-align: left;
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 6px;
        cursor: pointer;
        color: inherit;
    }
    .preset:hover {
        border-color: var(--accent);
    }
    .preset-custom {
        border-style: dashed;
    }
    .badge {
        display: inline-block;
        margin-top: 0.5rem;
        padding: 0.1rem 0.4rem;
        font-size: 0.75rem;
        border: 1px solid var(--border);
        border-radius: 4px;
        color: var(--muted);
    }
    .link {
        background: none;
        border: none;
        padding: 0;
        color: var(--accent);
        cursor: pointer;
    }
</style>
