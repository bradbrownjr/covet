<!-- Thin wrapper around lucide-svelte icon components.
     Usage: <Icon name="trash-2" size={18} />
            <Icon name="check" aria-label="Saved" />

     Only the icons listed in ICON_MAP are bundled. Add new icons here
     when introducing new <Icon name="..."> calls elsewhere in the app.
     (Named imports keep the build output small vs. `import * as lucide`.) -->
<script lang="ts">
    import {
        ArrowDown, ArrowUp, Bell, Check,
        ChevronLeft, ChevronRight, CircleAlert, CornerDownRight,
        DatabaseBackup, Download, FileArchive, FileSpreadsheet,
        Folder, Grid2x2, Home, List, MoreHorizontal,
        Pencil, Settings, Settings2, Sparkles, Store,
        Trash2, TriangleAlert, Upload, User, Wrench,
    } from 'lucide-svelte';

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const ICON_MAP: Record<string, any> = {
        'arrow-down': ArrowDown, 'arrow-up': ArrowUp,
        'bell': Bell, 'check': Check,
        'chevron-left': ChevronLeft, 'chevron-right': ChevronRight,
        'circle-alert': CircleAlert, 'corner-down-right': CornerDownRight,
        'database-backup': DatabaseBackup, 'download': Download,
        'file-archive': FileArchive, 'file-spreadsheet': FileSpreadsheet,
        'folder': Folder, 'grid-2x2': Grid2x2,
        'home': Home, 'list': List,
        'more-horizontal': MoreHorizontal, 'pencil': Pencil,
        'settings': Settings, 'settings-2': Settings2,
        'sparkles': Sparkles, 'store': Store,
        'trash-2': Trash2, 'triangle-alert': TriangleAlert,
        'upload': Upload, 'user': User,
        'wrench': Wrench,
    };

    interface Props {
        name: string;
        size?: number;
        strokeWidth?: number;
        color?: string;
        class?: string;
        'aria-label'?: string;
        'aria-hidden'?: boolean | 'true' | 'false';
    }

    let {
        name,
        size = 18,
        strokeWidth = 2,
        color = 'currentColor',
        class: cls = '',
        'aria-label': ariaLabel,
        'aria-hidden': ariaHidden,
    }: Props = $props();

    // lucide-svelte v1.x icon components use legacy `$$props`, so we render
    // them directly via a value-binding (Svelte 5) instead of the deprecated
    // `<svelte:component>`, which fails to forward props to legacy components.
    const IconComponent = $derived(ICON_MAP[name]);
</script>

{#if IconComponent}
    <IconComponent
        {size}
        {strokeWidth}
        {color}
        class={cls || undefined}
        aria-label={ariaLabel}
        aria-hidden={ariaHidden ?? (ariaLabel ? undefined : true)}
    />
{/if}
