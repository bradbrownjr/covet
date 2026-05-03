<script lang="ts">
    import { onMount } from 'svelte';
    import { page } from '$app/state';
    import { _ } from 'svelte-i18n';
    import {
        api,
        type AuditLogEntry,
        type Collection,
        type Invitation,
        type InvitationCreated,
        type Membership,
        type Role,
        type ShareLink
    } from '$lib/api';

    let collection = $state<Collection | null>(null);
    let members = $state<Membership[]>([]);
    let shareLinks = $state<ShareLink[]>([]);
    let invitations = $state<Invitation[]>([]);
    let auditLog = $state<AuditLogEntry[]>([]);
    let lastInviteUrl = $state<string | null>(null);
    let loading = $state(true);
    let error = $state('');

    let newIdent = $state('');
    let newRole: Role = $state('viewer');
    let newLinkLabel = $state('');
    let newInviteEmail = $state('');
    let newInviteRole: Role = $state('viewer');
        let confirmDialog = $state<'remove-member' | 'revoke-share' | 'revoke-invite' | null>(null);
        let pendingMember = $state<Membership | null>(null);
        let pendingShare = $state<ShareLink | null>(null);
        let pendingInvite = $state<Invitation | null>(null);

    const cid = $derived(page.params.id ?? '');

    async function load() {
        loading = true;
        error = '';
        try {
            collection = await api.get<Collection>(`/collections/${cid}`);
            members = await api.get<Membership[]>(`/collections/${cid}/members`);
            try {
                shareLinks = await api.get<ShareLink[]>(`/collections/${cid}/share-links`);
            } catch {
                shareLinks = [];
            }
            try {
                invitations = await api.get<Invitation[]>(
                    `/collections/${cid}/invitations`
                );
            } catch {
                invitations = [];
            }
            try {
                auditLog = await api.get<AuditLogEntry[]>(
                    `/audit?collection_id=${cid}&limit=50`
                );
            } catch {
                auditLog = [];
            }
        } catch (e) {
            error = (e as Error).message;
        } finally {
            loading = false;
        }
    }

    async function addMember(e: Event) {
        e.preventDefault();
        if (!newIdent.trim()) return;
        try {
            await api.post(`/collections/${cid}/members`, {
                user_identifier: newIdent.trim(),
                role: newRole
            });
            newIdent = '';
            newRole = 'viewer';
            await load();
        } catch (e) {
            error = (e as Error).message;
        }
    }

    async function changeRole(m: Membership, role: Role) {
        try {
            await api.patch(`/collections/${cid}/members/${m.id}`, { role });
            await load();
        } catch (e) {
            error = (e as Error).message;
        }
    }

    function requestRemoveMember(m: Membership) {
        pendingMember = m;
        confirmDialog = 'remove-member';
    }

    async function removeMemberConfirmed() {
        if (!pendingMember) return;
        try {
            await api.delete(`/collections/${cid}/members/${pendingMember.id}`);
            pendingMember = null;
            confirmDialog = null;
            await load();
        } catch (e) {
            error = (e as Error).message;
        }
    }

    async function createShareLink(e: Event) {
        e.preventDefault();
        try {
            await api.post(`/collections/${cid}/share-links`, {
                label: newLinkLabel.trim() || null
            });
            newLinkLabel = '';
            await load();
        } catch (e) {
            error = (e as Error).message;
        }
    }

    function requestRevokeShareLink(link: ShareLink) {
        pendingShare = link;
        confirmDialog = 'revoke-share';
    }

    async function revokeShareLinkConfirmed() {
        if (!pendingShare) return;
        try {
            await api.delete(`/collections/${cid}/share-links/${pendingShare.id}`);
            pendingShare = null;
            confirmDialog = null;
            await load();
        } catch (e) {
            error = (e as Error).message;
        }
    }

    function shareUrl(slug: string): string {
        if (typeof window === 'undefined') return `/share/${slug}`;
        return `${window.location.origin}/share/${slug}`;
    }

    function inviteUrl(token: string): string {
        if (typeof window === 'undefined') return `/invite/${token}`;
        return `${window.location.origin}/invite/${token}`;
    }

    async function createInvitation(e: Event) {
        e.preventDefault();
        try {
            const created = await api.post<InvitationCreated>(
                `/collections/${cid}/invitations`,
                {
                    role: newInviteRole,
                    email: newInviteEmail.trim() || null
                }
            );
            lastInviteUrl = inviteUrl(created.token);
            newInviteEmail = '';
            await load();
        } catch (e) {
            error = (e as Error).message;
        }
    }

    function requestRevokeInvitation(inv: Invitation) {
        pendingInvite = inv;
        confirmDialog = 'revoke-invite';
    }

    async function revokeInvitationConfirmed() {
        if (!pendingInvite) return;
        try {
            await api.delete(`/collections/${cid}/invitations/${pendingInvite.id}`);
            pendingInvite = null;
            confirmDialog = null;
            await load();
        } catch (e) {
            error = (e as Error).message;
        }
    }

    onMount(load);
</script>

{#if collection}
    <h1>{collection.name}</h1>
    {#if collection.description}<p class="muted">{collection.description}</p>{/if}

    <nav class="subnav" aria-label="Collection sections">
        <a class="tab" href="/collections/{cid}">Items</a>
        <a class="tab" href="/collections/{cid}/templates">Templates</a>
        <a class="tab" href="/collections/{cid}/locations">Locations</a>
        <a class="tab" href="/collections/{cid}/bundles">Bundles</a>
        <a class="tab" href="/collections/{cid}/chores">Chores</a>
        <a class="tab tab-active" href="/collections/{cid}/members" aria-current="page">Members</a>
    </nav>

    {#if error}<p class="error">{error}</p>{/if}

    <form onsubmit={addMember} class="card" style="margin: 1rem 0">
        <div style="display:grid; grid-template-columns: 1fr 140px auto; gap:.5rem">
            <input bind:value={newIdent} placeholder={$_('members.add_placeholder')} />
            <select bind:value={newRole}>
                <option value="viewer">{$_('members.role_viewer')}</option>
                <option value="editor">{$_('members.role_editor')}</option>
            </select>
            <button type="submit">{$_('members.add_button')}</button>
        </div>
    </form>

    {#if loading}
        <p class="muted">{$_('common.loading')}</p>
    {:else}
        <table>
            <thead>
                <tr>
                    <th>{$_('members.col_user')}</th>
                    <th>{$_('members.col_email')}</th>
                    <th>{$_('members.col_role')}</th>
                    <th></th>
                </tr>
            </thead>
            <tbody>
                {#each members as m (m.id)}
                    <tr>
                        <td>{m.display_name ?? m.username}</td>
                        <td class="muted">{m.email ?? ''}</td>
                        <td>
                            {#if m.role === 'owner'}
                                <span class="muted">{$_('members.role_owner')}</span>
                            {:else}
                                <select
                                    value={m.role}
                                    onchange={(e) =>
                                        changeRole(m, (e.currentTarget as HTMLSelectElement).value as Role)}
                                >
                                    <option value="viewer">{$_('members.role_viewer')}</option>
                                    <option value="editor">{$_('members.role_editor')}</option>
                                </select>
                            {/if}
                        </td>
                        <td>
                            {#if m.role !== 'owner'}
                                    <button class="danger" onclick={() => requestRemoveMember(m)}>{$_('members.remove_button')}</button>
                            {/if}
                        </td>
                    </tr>
                {/each}
            </tbody>
        </table>
    {/if}

    <h2 style="margin-top:2rem">{$_('members.invitations_heading')}</h2>
    <p class="muted">
        {$_('members.invitations_description')}
    </p>

    <form onsubmit={createInvitation} class="card" style="margin: 1rem 0">
        <div style="display:grid; grid-template-columns: 1fr 140px auto; gap:.5rem">
            <input
                type="email"
                bind:value={newInviteEmail}
                placeholder={$_('members.invite_email_placeholder')}
            />
            <select bind:value={newInviteRole}>
                <option value="viewer">{$_('members.role_viewer')}</option>
                <option value="editor">{$_('members.role_editor')}</option>
            </select>
            <button type="submit">{$_('members.create_invite_button')}</button>
        </div>
    </form>

    {#if lastInviteUrl}
        <p>
            <strong>{$_('members.one_time_link_label')}</strong>
            <code>{lastInviteUrl}</code>
            <span class="muted"> ({$_('members.copy_now_note')})</span>
        </p>
    {/if}

    {#if invitations.length === 0}
        <p class="muted">{$_('members.no_invitations')}</p>
    {:else}
        <table>
            <thead>
                <tr>
                    <th>{$_('members.col_invite_email')}</th>
                    <th>{$_('members.col_invite_role')}</th>
                    <th>{$_('members.col_invite_expires')}</th>
                    <th>{$_('members.col_invite_status')}</th>
                    <th></th>
                </tr>
            </thead>
            <tbody>
                {#each invitations as inv (inv.id)}
                    <tr>
                        <td>{inv.email ?? ''}</td>
                        <td>{inv.role}</td>
                        <td class="muted">{inv.expires_at ?? $_('common.never')}</td>
                        <td>
                            {#if inv.accepted_at}
                                <span class="muted">{$_('members.invite_accepted')}</span>
                            {:else}
                                {$_('members.invite_pending')}
                            {/if}
                        </td>
                        <td>
                            <button class="danger" onclick={() => requestRevokeInvitation(inv)}>
                                {$_('members.revoke_invite_button')}
                            </button>
                        </td>
                    </tr>
                {/each}
            </tbody>
        </table>
    {/if}

    <h2 style="margin-top:2rem">{$_('members.share_links_heading')}</h2>
    <p class="muted">
        {$_('members.share_links_description')}
    </p>

    <form onsubmit={createShareLink} class="card" style="margin: 1rem 0">
        <div style="display:grid; grid-template-columns: 1fr auto; gap:.5rem">
            <input bind:value={newLinkLabel} placeholder={$_('members.share_link_label_placeholder')} />
            <button type="submit">{$_('members.create_share_button')}</button>
        </div>
    </form>

    {#if shareLinks.length === 0}
        <p class="muted">{$_('members.no_share_links')}</p>
    {:else}
        <table>
            <thead>
                <tr>
                    <th>{$_('members.col_share_label')}</th>
                    <th>{$_('members.col_share_url')}</th>
                    <th>{$_('members.col_share_expires')}</th>
                    <th></th>
                </tr>
            </thead>
            <tbody>
                {#each shareLinks as l (l.id)}
                    <tr>
                        <td>{l.label ?? ''}</td>
                        <td>
                            <a href={shareUrl(l.slug)} target="_blank" rel="noopener">
                                {shareUrl(l.slug)}
                            </a>
                        </td>
                        <td class="muted">{l.expires_at ?? $_('common.never')}</td>
                        <td>
                            <button class="danger" onclick={() => requestRevokeShareLink(l)}>
                                {$_('members.revoke_share_button')}
                            </button>
                        </td>
                    </tr>
                {/each}
            </tbody>
        </table>
    {/if}
    <h2 style="margin-top:2rem">{$_('members.activity_heading')}</h2>
    <p class="muted">{$_('members.activity_description')}</p>
    {#if auditLog.length === 0}
        <p class="muted">{$_('members.no_activity')}</p>
    {:else}
        <table>
            <thead>
                <tr>
                    <th>{$_('members.col_activity_when')}</th>
                    <th>{$_('members.col_activity_action')}</th>
                    <th>{$_('members.col_activity_target')}</th>
                </tr>
            </thead>
            <tbody>
                {#each auditLog as entry (entry.id)}
                    <tr>
                        <td class="muted">{entry.created_at}</td>
                        <td><code>{entry.action}</code></td>
                        <td class="muted">
                            {entry.target_type ?? ''}{entry.target_id ? ' ' + entry.target_id : ''}
                        </td>
                    </tr>
                {/each}
            </tbody>
        </table>
    {/if}
{:else if !loading}
    <p class="error">{$_('collection.not_found')}</p>
{/if}

{#if confirmDialog === 'remove-member'}
    <div class="modal-backdrop" role="presentation" onclick={() => (confirmDialog = null)}>
        <div class="modal" role="dialog" aria-modal="true" aria-labelledby="remove-member-title" onclick={(e) => e.stopPropagation()}>
            <h3 id="remove-member-title">{$_('members.remove_member_title')}</h3>
            <p class="muted">{$_('members.remove_member_text', {values: {username: pendingMember?.username ?? ''}})}</p>
            <div class="modal-actions">
                <button type="button" class="secondary" onclick={() => (confirmDialog = null)}>{$_('common.cancel')}</button>
                <button type="button" class="danger" onclick={removeMemberConfirmed}>{$_('members.remove_button')}</button>
            </div>
        </div>
    </div>
{/if}

{#if confirmDialog === 'revoke-share'}
    <div class="modal-backdrop" role="presentation" onclick={() => (confirmDialog = null)}>
        <div class="modal" role="dialog" aria-modal="true" aria-labelledby="revoke-share-title" onclick={(e) => e.stopPropagation()}>
            <h3 id="revoke-share-title">{$_('members.revoke_share_title')}</h3>
            <p class="muted">{$_('members.revoke_share_text')}</p>
            <div class="modal-actions">
                <button type="button" class="secondary" onclick={() => (confirmDialog = null)}>{$_('common.cancel')}</button>
                <button type="button" class="danger" onclick={revokeShareLinkConfirmed}>{$_('members.revoke_share_button')}</button>
            </div>
        </div>
    </div>
{/if}

{#if confirmDialog === 'revoke-invite'}
    <div class="modal-backdrop" role="presentation" onclick={() => (confirmDialog = null)}>
        <div class="modal" role="dialog" aria-modal="true" aria-labelledby="revoke-invite-title" onclick={(e) => e.stopPropagation()}>
            <h3 id="revoke-invite-title">{$_('members.revoke_invite_title')}</h3>
            <p class="muted">{$_('members.revoke_invite_text')}</p>
            <div class="modal-actions">
                <button type="button" class="secondary" onclick={() => (confirmDialog = null)}>{$_('common.cancel')}</button>
                <button type="button" class="danger" onclick={revokeInvitationConfirmed}>{$_('members.revoke_invite_button')}</button>
            </div>
        </div>
    </div>
{/if}

<style>
    .subnav {
        display: flex;
        gap: 0.25rem;
        flex-wrap: wrap;
        margin: 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid var(--border);
    }
    .tab {
        display: inline-flex;
        align-items: center;
        padding: 0.4rem 0.8rem;
        font: inherit;
        font-weight: 500;
        color: var(--fg);
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 6px;
        text-decoration: none;
        cursor: pointer;
    }
    .tab:hover {
        border-color: var(--accent);
    }
    .tab-active {
        background: var(--accent);
        color: var(--accent-fg, white);
        border-color: var(--accent);
    }
        .modal-backdrop {
            position: fixed;
            inset: 0;
            background: rgba(0, 0, 0, 0.45);
            display: grid;
            place-items: center;
            padding: 1rem;
            z-index: 40;
        }
        .modal {
            width: min(34rem, 100%);
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1rem;
            display: grid;
            gap: 0.75rem;
        }
        .modal-actions {
            display: flex;
            justify-content: flex-end;
            gap: 0.5rem;
        }
</style>
