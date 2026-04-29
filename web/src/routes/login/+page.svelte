<script lang="ts">
    import { goto } from '$app/navigation';
    import { api } from '$lib/api';
    import { publicConfig, refreshMe } from '$lib/session';

    let username = $state('');
    let password = $state('');
    let error = $state('');
    let busy = $state(false);

    async function submit(e: Event) {
        e.preventDefault();
        busy = true;
        error = '';
        try {
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
    <h1>Sign in</h1>
    <form onsubmit={submit} class="card">
        <div class="field">
            <label for="u">Username</label>
            <input id="u" bind:value={username} required autocomplete="username" />
        </div>
        <div class="field">
            <label for="p">Password</label>
            <input
                id="p"
                type="password"
                bind:value={password}
                required
                autocomplete="current-password"
            />
        </div>
        <button type="submit" disabled={busy}>{busy ? 'Signing in…' : 'Sign in'}</button>
        {#if error}<p class="error">{error}</p>{/if}
    </form>

    {#if $publicConfig?.registration_enabled}
        <p class="muted">No account? <a href="/register">Register</a></p>
    {/if}

    {#if $publicConfig?.oidc_providers?.length}
        <h3>Or sign in with:</h3>
        <ul>
            {#each $publicConfig.oidc_providers as p}
                <li><a href={`/auth/oidc/${p.name}/login`}>{p.label}</a></li>
            {/each}
        </ul>
    {/if}
</div>

<style>
    .auth {
        max-width: 400px;
        margin: 4rem auto 0;
    }
</style>
