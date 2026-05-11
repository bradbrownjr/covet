<script lang="ts">
    import { goto } from '$app/navigation';
    import { page } from '$app/state';
    import { onMount } from 'svelte';
    import { _ } from 'svelte-i18n';
    import { api, type UserListType } from '$lib/api';

    interface Props { children: import('svelte').Snippet; }
    let { children }: Props = $props();

    const TABS = [
        { id: 'all',        labelKey: 'lists.tab_all' },
        { id: 'groceries',  labelKey: 'lists.type.groceries' },
        { id: 'hardware',   labelKey: 'lists.type.hardware' },
        { id: 'home_goods', labelKey: 'lists.type.home_goods' },
        { id: 'wish_list',  labelKey: 'lists.type.wish_list' },
    ] as const;

    // Custom (user-defined) list types fetched from the server.
    let customTypes = $state<UserListType[]>([]);
    let showAddModal = $state(false);
    let newLabel = $state('');
    let adding = $state(false);

    async function loadCustomTypes() {
        try {
            customTypes = await api.get<UserListType[]>('/lists/types', true);
        } catch { /* silently ignore — built-in tabs still work */ }
    }

    async function createType() {
        if (!newLabel.trim() || adding) return;
        adding = true;
        try {
            const created = await api.post<UserListType>('/lists/types', { label: newLabel.trim() });
            customTypes = [...customTypes, created];
            newLabel = '';
            showAddModal = false;
            goto(`/lists/${created.slug}`);
        } catch {
            // errors shown by api client automatically
        } finally {
            adding = false;
        }
    }

    async function deleteCustomType(t: UserListType) {
        if (!confirm($_('lists.add_type_delete_confirm'))) return;
        try {
            await api.delete(`/lists/types/${t.id}`);
            customTypes = customTypes.filter((c) => c.id !== t.id);
            if (activeType === t.slug) goto('/lists');
        } catch { /* toast shown by client */ }
    }

    // Combine built-in + custom for swipe/keyboard nav
    const allTabIds = $derived([
        ...TABS.map((t) => t.id),
        ...customTypes.map((t) => t.slug),
    ]);

    let tabsEl: HTMLDivElement | undefined = $state();

    const activeType = $derived.by(() => {
        const m = page.url.pathname.match(/^\/lists\/([^/]+)/);
        return m ? m[1] : 'all';
    });

    // Scroll active tab into view
    $effect(() => {
        if (!tabsEl || !activeType) return;
        const btn = tabsEl.querySelector<HTMLButtonElement>(`[data-id="${activeType}"]`);
        btn?.scrollIntoView({ block: 'nearest', inline: 'center', behavior: 'smooth' });
    });

    // --- Swipe navigation ---
    let swipeStartX = 0;
    let swipeStartY = 0;
    let swiping = false;

    function onPointerDown(e: PointerEvent) {
        swipeStartX = e.clientX;
        swipeStartY = e.clientY;
        swiping = true;
    }

    function onPointerUp(e: PointerEvent) {
        if (!swiping) return;
        swiping = false;
        const dx = e.clientX - swipeStartX;
        const dy = e.clientY - swipeStartY;
        if (Math.abs(dx) < 50 || Math.abs(dy) > Math.abs(dx) * 0.7) return;

        const idx = allTabIds.indexOf(activeType as string);
        if (idx === -1) return;

        if (dx < 0 && idx < allTabIds.length - 1) {
            const next = allTabIds[idx + 1];
            goto(next === 'all' ? '/lists' : `/lists/${next}`);
        } else if (dx > 0 && idx > 0) {
            const prev = allTabIds[idx - 1];
            goto(prev === 'all' ? '/lists' : `/lists/${prev}`);
        }
    }

    function onKeydown(e: KeyboardEvent) {
        if (!tabsEl?.contains(e.target as Node)) return;
        const idx = allTabIds.indexOf(activeType as string);
        if (idx === -1) return;
        if (e.key === 'ArrowRight' && idx < allTabIds.length - 1) {
            e.preventDefault();
            const next = allTabIds[idx + 1];
            goto(next === 'all' ? '/lists' : `/lists/${next}`);
        } else if (e.key === 'ArrowLeft' && idx > 0) {
            e.preventDefault();
            const prev = allTabIds[idx - 1];
            goto(prev === 'all' ? '/lists' : `/lists/${prev}`);
        }
    }

    const LS_KEY = 'tangible:lastListTab';

    // Persist last-viewed list type
    $effect(() => {
        if (activeType) localStorage.setItem(LS_KEY, activeType);
    });

    onMount(() => {
        loadCustomTypes();
        window.addEventListener('keydown', onKeydown);
        return () => window.removeEventListener('keydown', onKeydown);
    });
</script>

<div class="lists-tabs-layout">
    <div class="tab-strip-wrap" bind:this={tabsEl} role="tablist" aria-label={$_('nav.lists')}>
        {#each TABS as t (t.id)}
            <button
                type="button"
                role="tab"
                class="tab"
                class:tab--active={activeType === t.id}
                aria-selected={activeType === t.id}
                data-id={t.id}
                onclick={() => goto(t.id === 'all' ? '/lists' : `/lists/${t.id}`)}
            >
                {$_(t.labelKey)}
            </button>
        {/each}
        {#each customTypes as ct (ct.id)}
            <button
                type="button"
                role="tab"
                class="tab tab--custom"
                class:tab--active={activeType === ct.slug}
                aria-selected={activeType === ct.slug}
                data-id={ct.slug}
                onclick={() => goto(`/lists/${ct.slug}`)}
            >
                {ct.label}
                <span
                    class="tab-del"
                    role="button"
                    tabindex="0"
                    aria-label="Remove {ct.label}"
                    onclick={(e) => { e.stopPropagation(); deleteCustomType(ct); }}
                    onkeydown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); e.stopPropagation(); deleteCustomType(ct); } }}
                >×</span>
            </button>
        {/each}
        <button
            type="button"
            class="tab tab--add"
            aria-label={$_('lists.add_type_btn')}
            title={$_('lists.add_type_btn')}
            onclick={() => { newLabel = ''; showAddModal = true; }}
        >+</button>
    </div>

    <div
        class="tab-content"
        onpointerdown={onPointerDown}
        onpointerup={onPointerUp}
        role="tabpanel"
        tabindex="0"
        aria-label={activeType}
    >
        {@render children()}
    </div>
</div>

{#if showAddModal}
    <div
        class="modal-backdrop"
        role="presentation"
        onclick={() => { showAddModal = false; }}
        onkeydown={(e) => { if (e.key === 'Escape') showAddModal = false; }}
    >
        <div
            class="modal"
            role="dialog"
            tabindex="-1"
            aria-modal="true"
            aria-labelledby="add-type-title"
            onclick={(e) => e.stopPropagation()}
            onkeydown={(e) => e.stopPropagation()}
        >
            <h2 id="add-type-title">{$_('lists.add_type_title')}</h2>
            <label for="new-type-label">{$_('lists.add_type_label_label')}</label>
            <input
                id="new-type-label"
                type="text"
                class="modal-input"
                placeholder={$_('lists.add_type_label_placeholder')}
                bind:value={newLabel}
                onkeydown={(e) => { if (e.key === 'Enter') createType(); }}
            />
            <div class="modal-actions">
                <button type="button" class="btn-secondary" onclick={() => { showAddModal = false; }}>
                    {$_('common.cancel')}
                </button>
                <button type="button" class="btn-primary" disabled={!newLabel.trim() || adding} onclick={createType}>
                    {adding ? '…' : $_('lists.add_type_confirm')}
                </button>
            </div>
        </div>
    </div>
{/if}

<style>
    .lists-tabs-layout {
        display: flex;
        flex-direction: column;
        min-height: 0;
    }

    .tab-strip-wrap {
        display: flex;
        gap: 0;
        border-bottom: 1px solid var(--border);
        overflow-x: auto;
        scrollbar-width: none;
        flex-shrink: 0;
        margin-bottom: 1.25rem;
    }
    .tab-strip-wrap::-webkit-scrollbar { display: none; }

    .tab {
        background: transparent;
        border: none;
        border-bottom: 2px solid transparent;
        padding: 0 var(--space-4);
        min-height: var(--tap-min);
        font-size: var(--text-sm);
        font-weight: 500;
        color: var(--text-muted);
        cursor: pointer;
        white-space: nowrap;
        border-radius: 0;
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        transition: color 0.15s, border-color 0.15s;
        margin-bottom: -1px;
    }
    .tab:hover { color: var(--text); }
    .tab--active {
        color: var(--accent);
        border-bottom-color: var(--accent);
    }
    .tab--add {
        color: var(--text-muted);
        font-size: 1.2rem;
        padding: 0 0.75rem;
        opacity: 0.6;
    }
    .tab--add:hover { opacity: 1; color: var(--accent); }

    .tab-del {
        font-size: 0.85rem;
        line-height: 1;
        opacity: 0.5;
        padding: 0 0.15rem;
        border-radius: 2px;
        cursor: pointer;
    }
    .tab-del:hover { opacity: 1; color: var(--danger, #e53e3e); }

    .tab-content {
        touch-action: pan-y;
    }

    /* Add-type modal */
    .modal-backdrop {
        position: fixed;
        inset: 0;
        background: rgba(0,0,0,0.45);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 200;
    }
    .modal {
        background: var(--surface);
        border-radius: var(--radius-lg, 0.75rem);
        padding: 1.5rem;
        width: min(380px, calc(100vw - 2rem));
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
        box-shadow: var(--shadow-lg, 0 8px 32px rgba(0,0,0,0.2));
    }
    .modal h2 {
        margin: 0;
        font-size: var(--text-lg, 1.125rem);
    }
    .modal label {
        font-size: var(--text-sm);
        color: var(--text-muted);
    }
    .modal-input {
        width: 100%;
        padding: 0.5rem 0.75rem;
        border: 1px solid var(--border);
        border-radius: var(--radius, 0.375rem);
        font-size: var(--text-base, 1rem);
        background: var(--surface);
        color: var(--text);
        box-sizing: border-box;
    }
    .modal-input:focus { outline: 2px solid var(--accent); outline-offset: 1px; }
    .modal-actions {
        display: flex;
        justify-content: flex-end;
        gap: 0.5rem;
        margin-top: 0.25rem;
    }
    .btn-primary {
        background: var(--accent);
        color: var(--accent-fg, #fff);
        border: none;
        border-radius: var(--radius);
        padding: 0.45rem 1.1rem;
        font-weight: 600;
        cursor: pointer;
    }
    .btn-primary:disabled { opacity: 0.5; cursor: default; }
    .btn-secondary {
        background: transparent;
        color: var(--text-muted);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 0.45rem 1.1rem;
        cursor: pointer;
    }

    @media (prefers-reduced-motion: reduce) {
        .tab { transition: none; }
    }
</style>
