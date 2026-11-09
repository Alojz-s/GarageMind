import { useEffect, useId, useRef, useState, type FormEvent } from 'react'

import {

  ADMIN_LOGIN,

  blockUser,

  createUser,

  deleteUser,

  fetchRoles,

  fetchUsers,

  resetPassword,

  unblockUser,

  updateUser,

  type Role,

  type UserListItem,

} from '../api/admin'

import Alert from '../components/Alert'

import PageHeader from '../components/PageHeader'
import { formatApiError, formatRoleLabel } from '../messages/apiErrors'



interface IssuedPassword {

  login: string

  password: string

}



const byLogin = (a: UserListItem, b: UserListItem) => a.login.localeCompare(b.login)



function IconKebab() {

  return (

    <svg className="app-icon" width="20" height="20" viewBox="0 0 20 20" aria-hidden>

      <circle cx="10" cy="4.5" r="1.6" fill="currentColor" />

      <circle cx="10" cy="10" r="1.6" fill="currentColor" />

      <circle cx="10" cy="15.5" r="1.6" fill="currentColor" />

    </svg>

  )

}



interface UserRowActionsProps {

  user: UserListItem

  busy: boolean

  open: boolean

  onOpenChange: (open: boolean) => void

  onBlock: () => void

  onReset: () => void

  onDelete: () => void

}



function UserRowActions({

  user,

  busy,

  open,

  onOpenChange,

  onBlock,

  onReset,

  onDelete,

}: UserRowActionsProps) {

  const menuId = useId()

  const rootRef = useRef<HTMLDivElement>(null)



  useEffect(() => {

    if (!open) return

    const onPointerDown = (event: MouseEvent) => {

      if (!rootRef.current?.contains(event.target as Node)) onOpenChange(false)

    }

    const onKeyDown = (event: KeyboardEvent) => {

      if (event.key === 'Escape') onOpenChange(false)

    }

    document.addEventListener('mousedown', onPointerDown)

    document.addEventListener('keydown', onKeyDown)

    return () => {

      document.removeEventListener('mousedown', onPointerDown)

      document.removeEventListener('keydown', onKeyDown)

    }

  }, [open, onOpenChange])



  const run = (action: () => void) => {

    onOpenChange(false)

    action()

  }



  return (

    <div className={`app-row-menu${open ? ' is-open' : ''}`} ref={rootRef}>

      <button

        type="button"

        className="app-icon-btn"

        aria-label={`Actions for ${user.login}`}

        aria-haspopup="menu"

        aria-expanded={open}

        aria-controls={menuId}

        disabled={busy}

        onClick={() => onOpenChange(!open)}

      >

        <IconKebab />

      </button>

      {open && (

        <div role="menu" id={menuId} className="app-row-menu__panel">

          <button

            type="button"

            role="menuitem"

            className="app-row-menu__item"

            disabled={busy}

            onClick={() => run(onBlock)}

          >

            {user.is_blocked ? 'Unblock' : 'Block'}

          </button>

          <button

            type="button"

            role="menuitem"

            className="app-row-menu__item"

            disabled={busy}

            onClick={() => run(onReset)}

          >

            Reset password

          </button>

          <button

            type="button"

            role="menuitem"

            className="app-row-menu__item app-row-menu__item--danger"

            disabled={busy}

            onClick={() => run(onDelete)}

          >

            Delete

          </button>

        </div>

      )}

    </div>

  )

}



export default function AdminUsersPage() {

  const [users, setUsers] = useState<UserListItem[]>([])

  const [roles, setRoles] = useState<Role[]>([])

  const [error, setError] = useState<string | null>(null)

  const [formError, setFormError] = useState<string | null>(null)

  const [busy, setBusy] = useState(false)

  const [issued, setIssued] = useState<IssuedPassword | null>(null)

  const [newLogin, setNewLogin] = useState('')

  const [newRoleId, setNewRoleId] = useState('')

  const [createOpen, setCreateOpen] = useState(false)

  const [actionsForUserId, setActionsForUserId] = useState<number | null>(null)

  const createDialogTitleId = useId()



  useEffect(() => {

    Promise.all([fetchUsers(), fetchRoles()])

      .then(([loadedUsers, loadedRoles]) => {

        setUsers(loadedUsers)

        setRoles(loadedRoles)

      })

      .catch((err: unknown) => setError(formatApiError(err)))

  }, [])



  useEffect(() => {

    if (!createOpen) return

    const onKeyDown = (event: KeyboardEvent) => {

      if (event.key === 'Escape') setCreateOpen(false)

    }

    window.addEventListener('keydown', onKeyDown)

    return () => window.removeEventListener('keydown', onKeyDown)

  }, [createOpen])



  const closeCreateModal = () => {

    setCreateOpen(false)

    setFormError(null)

  }



  const run = async (action: () => Promise<void>, showError = setError) => {

    setError(null)

    setFormError(null)

    setBusy(true)

    try {

      await action()

    } catch (err) {

      showError(formatApiError(err))

    } finally {

      setBusy(false)

    }

  }



  const replaceUser = (updated: UserListItem) =>

    setUsers((current) => current.map((u) => (u.id === updated.id ? updated : u)))



  const handleCreate = (event: FormEvent<HTMLFormElement>) => {

    event.preventDefault()

    void run(async () => {

      const { one_time_password, ...created } = await createUser(newLogin, Number(newRoleId))

      setUsers((current) => [...current, created].sort(byLogin))

      setIssued({ login: created.login, password: one_time_password })

      setNewLogin('')

      setNewRoleId('')

      setCreateOpen(false)

    }, setFormError)

  }



  const handleRoleChange = (user: UserListItem, roleId: number) => {

    void run(async () => replaceUser(await updateUser(user.id, roleId)))

  }



  const handleToggleBlock = (user: UserListItem) => {

    void run(async () => replaceUser(await (user.is_blocked ? unblockUser : blockUser)(user.id)))

  }



  const handleReset = (user: UserListItem) => {

    const question = `Reset password for ${user.login}? Their current password will stop working.`

    if (!window.confirm(question)) return

    void run(async () => {

      setIssued({ login: user.login, password: await resetPassword(user.id) })

    })

  }



  const handleDelete = (user: UserListItem) => {

    if (!window.confirm(`Delete user ${user.login}? This cannot be undone.`)) return

    void run(async () => {

      await deleteUser(user.id)

      setUsers((current) => current.filter((u) => u.id !== user.id))

      setIssued((current) => (current?.login === user.login ? null : current))

    })

  }



  return (

    <>

      <PageHeader title="Users" subtitle="Manage accounts, roles and access." />

      <div className="app-stack">

        {error && <Alert kind="error">{error}</Alert>}



        {issued && (

          <div className="app-otp app-otp--center" role="status">

            <p className="app-text">

              One-time password for <strong>{issued.login}</strong>:

            </p>

            <code className="app-otp__value">{issued.password}</code>

            <p className="app-text">

              Copy it now — it will not be shown again. Valid for 24 hours and single use; after

              sign-in the user must set their own password.

            </p>

            <button type="button" className="gm-btn gm-btn--sm" onClick={() => setIssued(null)}>

              Dismiss

            </button>

          </div>

        )}



        <section className="app-card">

          <div className="app-users-toolbar">

            <h2 className="app-card__title app-users-toolbar__title">Accounts</h2>

            <button

              type="button"

              className="gm-btn gm-btn--sm"

              disabled={busy}

              onClick={() => setCreateOpen(true)}

            >

              Add user

            </button>

          </div>

          <div className="app-table-wrap">

            <table className="app-table">

              <thead>

                <tr>

                  <th>Login</th>

                  <th>Role</th>

                  <th>Status</th>

                  <th className="app-table__col-actions">Actions</th>

                </tr>

              </thead>

              <tbody>

                {users.map((user) => {

                  const isProtected = user.login === ADMIN_LOGIN

                  return (

                    <tr key={user.id}>

                      <td>{user.login}</td>

                      <td>

                        {isProtected ? (

                          formatRoleLabel(user.role)

                        ) : (

                          <select

                            className="app-input app-input--compact"

                            aria-label={`Role for ${user.login}`}

                            value={user.role_id}

                            disabled={busy}

                            onChange={(e) => handleRoleChange(user, Number(e.target.value))}

                          >

                            {roles.map((role) => (

                              <option key={role.id} value={role.id}>

                                {formatRoleLabel(role.name)}

                              </option>

                            ))}

                          </select>

                        )}

                      </td>

                      <td>

                        <span

                          className={`app-badge app-badge--status app-badge--${user.is_blocked ? 'blocked' : 'active'}`}

                        >

                          {user.is_blocked ? 'Blocked' : 'Active'}

                        </span>

                      </td>

                      <td className="app-table__col-actions">

                        {!isProtected && (

                          <UserRowActions

                            user={user}

                            busy={busy}

                            open={actionsForUserId === user.id}

                            onOpenChange={(open) => setActionsForUserId(open ? user.id : null)}

                            onBlock={() => handleToggleBlock(user)}

                            onReset={() => handleReset(user)}

                            onDelete={() => handleDelete(user)}

                          />

                        )}

                      </td>

                    </tr>

                  )

                })}

              </tbody>

            </table>

          </div>

        </section>

      </div>



      {createOpen && (

        <div className="app-modal-overlay" role="presentation" onClick={closeCreateModal}>

          <form

            className="app-modal__card app-form"

            role="dialog"

            aria-modal="true"

            aria-labelledby={createDialogTitleId}

            onSubmit={handleCreate}

            onClick={(event) => event.stopPropagation()}

          >

            <h2 className="app-card__title" id={createDialogTitleId}>

              New user

            </h2>

            <label className="app-field">

              Login

              <input

                className="app-input"

                name="login"

                maxLength={64}

                autoComplete="off"

                value={newLogin}

                onChange={(e) => setNewLogin(e.target.value)}

                required

              />

            </label>

            <label className="app-field">

              Role

              <select

                className="app-input"

                name="role_id"

                value={newRoleId}

                onChange={(e) => setNewRoleId(e.target.value)}

                required

              >

                <option value="" disabled>

                  Select role

                </option>

                {roles.map((role) => (

                  <option key={role.id} value={role.id}>

                    {formatRoleLabel(role.name)}

                  </option>

                ))}

              </select>

            </label>

            {formError && <Alert kind="error">{formError}</Alert>}

            <div className="app-modal__actions">

              <button

                type="button"

                className="gm-btn gm-btn--sm gm-btn--secondary"

                disabled={busy}

                onClick={closeCreateModal}

              >

                Cancel

              </button>

              <button type="submit" className="gm-btn gm-btn--sm" disabled={busy}>

                Create account

              </button>

            </div>

          </form>

        </div>

      )}

    </>

  )

}

