<script lang="ts">
    import { api, type User } from '$lib/api';
    import { me, refreshMe } from '$lib/session';

    let displayName = $state($me ? ($me.display_name ?? '') : '');
    let email = $state($me ? ($me.email ?? '') : '');
    let password = $state('');
    let busy = $state(false);
    let error = $state('');
    let saved = $state(false);

    // Keep form in sync if $me loads after mount.
    $effect(() => {
        if ($me) {
            displayName = $me.display_name ?? '';
            email = $me.email ?? '';
        }
    });

    async function submit(e: Event) {
        e.preventDefault();
        busy = true;
        error = '';
        saved = false;
        try {
            const body: Record<string, unknown> = {
                display_name: displayName,
                email: email || null
            };
            if (password) body.password = password;
            await api.patch<User>('/auth/me', body);
            await refreshMe();
            password = '';
            saved = true;
        } catch (e) {
            error = (e as Error).message;
        } finally {
            busy = false;
        }
    }
</script>

<div class="profile">
    <h1>Your profile</h1>
    {#if !$me}
        <p class="muted">Loading…</p>
    {:else}
        <form onsubmit={submit} class="card">
            <div class="field">
                <label>Username</label>
                <input value={$me.username} disabled />
                <p class="muted hint">Usernames can't be changed once chosen.</p>
            </div>
            <div class="field">
                <label for="n">Full name</label>
                <input id="n" bind:value={displayName} autocomplete="name" />
                <p class="muted hint">
                    Shown to other users on shared collections instead of your username.
                </p>
            </div>
            <div class="field">
                <label for="e">Email</label>
                <input id="e" type="email" bind:value={email} autocomplete="email" />
            </div>
            <div class="field">
                <label for="p">New password <span class="muted">(leave blank to keep)</span></label>
                <input
                    id="p"
                    type="password"
                    bind:value={password}
                    minlength="12"
                    autocomplete="new-password"
                />
            </div>
            <button type="submit" disabled={busy}>{busy ? 'Saving…' : 'Save changes'}</button>
            {#if saved}<p class="ok">Saved.</p>{/if}
            {#if error}<p class="error">{error}</p>{/if}
        </form>
    {/if}
</div>

<style>
    .profile {
        max-width: 480px;
        margin: 2rem auto;
    }
    .hint {
        font-size: 0.8rem;
        margin: 0.25rem 0 0;
    }
    .ok {
        color: var(--success, #22c55e);
    }
</style>
