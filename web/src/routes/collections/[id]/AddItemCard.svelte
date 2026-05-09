<script lang="ts">
    import { _ } from 'svelte-i18n';

    interface Props {
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

    let creatorInput: HTMLInputElement | undefined = $state();
    let titleInput: HTMLInputElement | undefined;
    let subtitleInput: HTMLInputElement | undefined = $state();

    // Parity with Lists Add card: form is always visible. Extra fields live
    // inside the inner "+ More options" details. The outer collapse wrapper
    // (previously a "+ Add an item" details) has been removed for visual
    // parity between /collections/[id] and /lists/[type].
    export function focusTitle() {
        queueMicrotask(() => (creatorLabel ? creatorInput : titleInput)?.focus());
    }
</script>

<form onsubmit={onSubmit} class="add-form">
    <input
        bind:this={barcodeImageInput}
        type="file"
        accept="image/*"
        style="display:none"
        onchange={onBarcodeChange}
    />
    <div class="add-row">
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
                    onSubmit(e);
                }
            }}
        />
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

    {#if creatorLabel || subtitleLabel}
        <details class="more-options">
            <summary>{$_('common.more_options')}</summary>
            <div class="more-options-grid">
                {#if creatorLabel}
                    <input
                        bind:this={creatorInput}
                        bind:value={newCreator}
                        placeholder={creatorLabel}
                        autocomplete="off"
                        class="creator-field"
                    />
                {/if}
                {#if subtitleLabel}
                    <input
                        bind:this={subtitleInput}
                        bind:value={newSubtitle}
                        placeholder={subtitleLabel}
                        autocomplete="off"
                        class="subtitle-field"
                    />
                {/if}
            </div>
        </details>
    {/if}
    {#if error}<p class="error">{error}</p>{/if}
</form>

<style>
    .add-form {
        margin: 1rem 0 1.5rem;
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }
    .add-row {
        display: flex;
        gap: 0.5rem;
        align-items: center;
        flex-wrap: wrap;
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
    .more-options {
        margin-top: 0.5rem;
        border: 1px solid var(--border);
        border-radius: var(--radius-md, 8px);
        background: var(--surface);
    }
    .more-options > summary {
        padding: 0.5rem 0.75rem;
        font-size: 0.875rem;
        color: var(--text-muted);
        cursor: pointer;
        user-select: none;
        list-style: none;
    }
    .more-options > summary::-webkit-details-marker { display: none; }
    .more-options > summary::before { content: '+ '; }
    .more-options[open] > summary::before { content: '- '; }
    .more-options-grid {
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
        padding: 0.75rem;
        border-top: 1px solid var(--border);
    }
</style>
