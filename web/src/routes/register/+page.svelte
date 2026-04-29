<script lang="ts">
    import { goto } from '$app/navigation';
    import { api } from '$lib/api';
    import { refreshMe } from '$lib/session';

    let username = $state('');
    let email = $state('');
    let password = $state('');
    let error = $state('');
    let busy = $state(false);

    async function submit(e: Event) {
        e.preventDefault();
        busy = true;
        error = '';
        try {
            await api.post('/auth/register', { username, password, email: email || null });
            await api.post('/auth/login', { username, password });
            await refreshMe();
            await goto('/');
        } catch (e) {
            error = (e as Error).message;
        } finally {
            busy = false;
        }
    }
</script>

<div class="auth">
    <h1>Create account</h1>
    <form onsubmit={submit} class="card">
        <div class="field">
            <label for="u">Username</label>
            <input id="u" bind:value={username} required autocomplete="username" />
        </div>
        <div class="field">
            <label for="e">Email <span class="muted">(optional)</span></label>
            <input id="e" type="email" bind:value={email} autocomplete="email" />
        </div>
        <div class="field">
            <label for="p">Password</label>
            <input
                id="p"
                type="password"
                bind:value={password}
                required
                minlength="12"
                autocomplete="new-password"
            />
        </div>
        <button type="submit" disabled={busy}>{busy ? 'Creating…' : 'Create account'}</button>
        {#if error}<p class="error">{error}</p>{/if}
    </form>
    <p class="muted">Already have an account? <a href="/login">Sign in</a></p>
</div>

<style>
    .auth {
        max-width: 400px;
        margin: 4rem auto 0;
    }
</style>
