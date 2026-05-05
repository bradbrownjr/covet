<!-- Horizontal tab bar.
     Usage:
       <script>
         let tab = $state('overview');
       </script>
       <Tabs bind:active={tab} tabs={[
           { id: 'overview', label: 'Overview' },
           { id: 'history',  label: 'History', count: 3 },
       ]} />
       {#if tab === 'overview'} ... {/if}
-->
<script lang="ts">
    export interface Tab {
        id: string;
        label: string;
        /** Optional count badge */
        count?: number;
        /** Optional lucide icon name */
        icon?: string;
    }

    interface Props {
        tabs: Tab[];
        active?: string;
        onchange?: (id: string) => void;
    }

    let { tabs, active = $bindable(tabs[0]?.id ?? ''), onchange }: Props = $props();

    function select(id: string) {
        active = id;
        onchange?.(id);
    }
</script>

<div class="tabs" role="tablist">
    {#each tabs as tab (tab.id)}
        <button
            type="button"
            role="tab"
            class="tab"
            class:tab--active={active === tab.id}
            aria-selected={active === tab.id}
            onclick={() => select(tab.id)}
        >
            {tab.label}
            {#if tab.count !== undefined}
                <span class="tab__count">{tab.count}</span>
            {/if}
        </button>
    {/each}
</div>

<style>
    .tabs {
        display: flex;
        gap: 0;
        border-bottom: 1px solid var(--border);
        overflow-x: auto;
        scrollbar-width: none;
    }
    .tabs::-webkit-scrollbar { display: none; }

    .tab {
        background: transparent;
        border: none;
        border-bottom: 2px solid transparent;
        padding: var(--space-3) var(--space-4);
        font-size: var(--text-sm);
        font-weight: 500;
        color: var(--text-muted);
        cursor: pointer;
        white-space: nowrap;
        min-height: auto;
        border-radius: 0;
        display: inline-flex;
        align-items: center;
        gap: var(--space-2);
        transition: color 0.15s, border-color 0.15s;
        margin-bottom: -1px;
    }
    .tab:hover { color: var(--text); }
    .tab--active {
        color: var(--accent);
        border-bottom-color: var(--accent);
    }

    .tab__count {
        font-size: var(--text-xs);
        font-weight: 700;
        background: var(--surface-2);
        color: var(--text-muted);
        padding: 0.1em 0.4em;
        border-radius: var(--radius-full);
    }
    .tab--active .tab__count {
        background: color-mix(in srgb, var(--accent) 15%, transparent);
        color: var(--accent);
    }
</style>
