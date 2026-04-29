<script lang="ts">
    import { onMount } from 'svelte';
    import { api, ApiError, type Collection } from '$lib/api';

    let collections = $state<Collection[]>([]);
    let collectionId = $state('');

    let mode = $state<'clz' | 'csv' | 'restore'>('clz');

    // CLZ
    let clzFlavor = $state<'clz-movie' | 'clz-music' | 'clz-book' | 'clz-comic' | 'clz-game'>('clz-movie');
    let clzFile = $state<FileList | null>(null);

    // CSV
    let csvType = $state('movie');
    let csvFile = $state<FileList | null>(null);
    let csvMapping = $state(
        '{\n  "Name": "title",\n  "Year": "attr:year",\n  "Barcode": "id:barcode"\n}'
    );

    // Restore
    let restoreFile = $state<FileList | null>(null);

    let busy = $state(false);
    let result = $state('');
    let error = $state('');

    onMount(async () => {
        collections = await api.get<Collection[]>('/collections');
        if (collections.length) collectionId = collections[0].id;
    });

    async function submit(e: Event) {
        e.preventDefault();
        error = '';
        result = '';
        busy = true;
        try {
            const fd = new FormData();
            let path = '';
            if (mode === 'clz') {
                if (!clzFile?.[0]) throw new Error('Pick a file');
                fd.set('collection_id', collectionId);
                fd.set('flavor', clzFlavor);
                fd.set('file', clzFile[0]);
                path = '/imports/clz';
            } else if (mode === 'csv') {
                if (!csvFile?.[0]) throw new Error('Pick a file');
                JSON.parse(csvMapping); // sanity
                fd.set('collection_id', collectionId);
                fd.set('item_type', csvType);
                fd.set('mapping', csvMapping);
                fd.set('file', csvFile[0]);
                path = '/imports/csv';
            } else {
                if (!restoreFile?.[0]) throw new Error('Pick a file');
                fd.set('file', restoreFile[0]);
                path = '/imports/restore';
            }
            const res = await fetch(path, {
                method: 'POST',
                body: fd,
                credentials: 'include'
            });
            const body = await res.text();
            if (!res.ok) {
                throw new ApiError(res.status, body, `HTTP ${res.status}: ${body}`);
            }
            result = body;
        } catch (e) {
            error = (e as Error).message;
        } finally {
            busy = false;
        }
    }

    async function downloadBackup() {
        const res = await fetch('/imports/backup', { credentials: 'include' });
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'covet-backup.json';
        a.click();
        URL.revokeObjectURL(url);
    }
</script>

<h1>Import / Backup</h1>

<div class="card" style="margin-bottom: 1rem">
    <button class="secondary" onclick={downloadBackup}>Download JSON backup</button>
    <p class="muted" style="margin-top:.5rem">
        Includes collections, items, tags, contacts, loans &amp; share links. Photo files are not
        included; copy <code>data/photos/</code> separately.
    </p>
</div>

<div class="card">
    <div class="field">
        <label>Mode</label>
        <select bind:value={mode}>
            <option value="clz">CLZ XML import</option>
            <option value="csv">Generic CSV import</option>
            <option value="restore">Restore JSON backup</option>
        </select>
    </div>

    <form onsubmit={submit}>
        {#if mode !== 'restore'}
            <div class="field">
                <label>Target collection</label>
                <select bind:value={collectionId} required>
                    {#each collections as c}
                        <option value={c.id}>{c.name}</option>
                    {/each}
                </select>
            </div>
        {/if}

        {#if mode === 'clz'}
            <div class="field">
                <label>CLZ product</label>
                <select bind:value={clzFlavor}>
                    <option value="clz-movie">Movie Collector</option>
                    <option value="clz-music">Music Collector</option>
                    <option value="clz-book">Book Collector</option>
                    <option value="clz-comic">Comic Collector</option>
                    <option value="clz-game">Game Collector</option>
                </select>
            </div>
            <div class="field">
                <label>XML export file</label>
                <input type="file" accept=".xml,application/xml" bind:files={clzFile} />
            </div>
        {:else if mode === 'csv'}
            <div class="field">
                <label>Item type</label>
                <select bind:value={csvType}>
                    <option>movie</option>
                    <option>music</option>
                    <option>book</option>
                    <option>comic</option>
                    <option>game</option>
                    <option>other</option>
                </select>
            </div>
            <div class="field">
                <label>CSV file</label>
                <input type="file" accept=".csv,text/csv" bind:files={csvFile} />
            </div>
            <div class="field">
                <label>Column mapping (JSON)</label>
                <textarea rows="8" bind:value={csvMapping}></textarea>
                <p class="muted">
                    Targets: <code>title</code>, <code>subtitle</code>, <code>notes</code>,
                    <code>quantity</code>, <code>condition</code>, <code>currency</code>,
                    <code>location</code>, or <code>id:&lt;name&gt;</code> /
                    <code>attr:&lt;name&gt;</code>.
                </p>
            </div>
        {:else}
            <div class="field">
                <label>Backup JSON file</label>
                <input type="file" accept=".json,application/json" bind:files={restoreFile} />
            </div>
        {/if}

        <button type="submit" disabled={busy}>{busy ? 'Working…' : 'Submit'}</button>
        {#if error}<p class="error">{error}</p>{/if}
        {#if result}<pre class="success">{result}</pre>{/if}
    </form>
</div>
