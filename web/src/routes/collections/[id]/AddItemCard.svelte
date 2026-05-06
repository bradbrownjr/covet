<script lang="ts">
    import { _ } from 'svelte-i18n';
    import type { Category } from '$lib/api';

    interface Props {
        isFocused: boolean;
        roots: Category[];
        leaves: Category[];
        creatorLabel: string | null;
        subtitleLabel: string | null;
        newRoot: string;
        newLeaf: string;
        newQuery: string;
        newCreator: string;
        newSubtitle: string;
        scraping: boolean;
        error: string;
        detected: 'url' | 'isbn' | 'ean' | 'title';
        onSubmit: (e: Event) => void;
        onLookup: () => void;
        onBarcodeChange: (e: Event) => void;
    }

    let {
        isFocused,
        roots,
        leaves,
        creatorLabel,
        subtitleLabel,
        newRoot = $bindable(),
        newLeaf = $bindable(),
        newQuery = $bindable(),
        newCreator = $bindable(),
        newSubtitle = $bindable(),
        scraping,
        error,
        detected,
        onSubmit,
        onLookup,
        onBarcodeChange,
    }: Props = $props();

    let barcodeImageInput: HTMLInputElement | undefined;

    let creatorInput: HTMLInputElement | undefined;
    let titleInput: HTMLInputElement | undefined;
    let subtitleInput: HTMLInputElement | undefined;

    export function focusTitle() {
        (creatorLabel ? creatorInput : titleInput)?.focus();
    }
</script>

<form onsubmit={onSubmit} class="card add-form">
    <input
        bind:this={barcodeImageInput}
        type="file"
        accept="image/*"
        style="display:none"
        onchange={onBarcodeChange}
    />
    <label class="add-label" for="addq">
        {$_('collection.add_item_label')}
        <span class="muted">— {$_('collection.add_item_help')}</span>
    </label>
    <div class="add-row">
        {#if !isFocused}
            <select bind:value={newRoot} title="Category root">
                {#each roots as r (r.id)}
                    <option value={r.slug}>{r.name}</option>
                {/each}
            </select>
        {/if}
        <select bind:value={newLeaf} title="Category">
            {#each leaves as l (l.id)}
                <option value={l.slug}>{l.name}</option>
            {/each}
        </select>
        {#if creatorLabel}
            <input
                bind:this={creatorInput}
                bind:value={newCreator}
                placeholder={creatorLabel}
                autocomplete="off"
                class="creator-field"
                onkeydown={(e) => { if (e.key === 'Enter') { e.preventDefault(); titleInput?.focus(); } }}
            />
        {/if}
        <input
            id="addq"
            bind:this={titleInput}
            bind:value={newQuery}
            placeholder={$_('collection.item_title_placeholder')}
            autocomplete="off"
            class="title-field"
            onkeydown={(e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    if (subtitleLabel && subtitleInput) subtitleInput.focus();
                    else onSubmit(e);
                }
            }}
        />
        {#if subtitleLabel}
            <input
                bind:this={subtitleInput}
                bind:value={newSubtitle}
                placeholder={subtitleLabel}
                autocomplete="off"
                class="subtitle-field"
                onkeydown={(e) => { if (e.key === 'Enter') { e.preventDefault(); onSubmit(e); } }}
            />
        {/if}
        {#if detected !== 'title' && newQuery.trim()}
            <button type="button" onclick={onLookup} disabled={scraping}>
                {scraping ? $_('collection.looking_up_button') : $_('collection.lookup_button', { values: { type: detected.toUpperCase() } })}
            </button>
        {/if}
        <button type="button" class="secondary" onclick={() => barcodeImageInput?.click()} disabled={scraping}>
            {$_('collection.scan_image_button')}
        </button>
        <button type="submit" disabled={scraping || !newQuery.trim()}>{$_('collection.add_button')}</button>
    </div>
    {#if error}<p class="error">{error}</p>{/if}
</form>

<style>
    .add-form {
        margin: 1rem 0;
    }
    .add-label {
        display: block;
        margin-bottom: 0.5rem;
        font-weight: 500;
    }
    .add-row {
        display: flex;
        gap: 0.5rem;
        align-items: center;
        flex-wrap: wrap;
    }
    .add-row select {
        flex: 0 0 auto;
        min-width: 130px;
        max-width: 180px;
    }
    .creator-field {
        flex: 1 1 150px;
        min-width: 120px;
        max-width: 210px;
    }
    .title-field {
        flex: 2 1 180px;
        min-width: 140px;
    }
    .subtitle-field {
        flex: 2 1 180px;
        min-width: 140px;
    }
</style>
