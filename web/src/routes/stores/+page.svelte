<script lang="ts">
    import ShoppingStoreManager from '$lib/ShoppingStoreManager.svelte';
    import { _ } from 'svelte-i18n';
    import { page } from '$app/state';

    const initialStoreId = $derived(page.url.searchParams.get('store'));
    const focusNew = $derived(page.url.searchParams.has('new'));
</script>

<svelte:head>
    <title>Tangible · {$_('nav.stores')}</title>
</svelte:head>

<ShoppingStoreManager standalone={true} initialStoreId={initialStoreId} focusNew={focusNew} />
