import { useState } from 'react'
import { api, pages } from '../../shared/routes'

export function LogoutButton() {
  const [pending, setPending] = useState(false)
  const [failed, setFailed] = useState(false)

  async function logout() {
    setPending(true)
    setFailed(false)
    try {
      const response = await fetch(api.logout, { method: 'POST' })
      if (!response.ok) throw new Error('Logout failed')
      window.location.replace(pages.catalog)
    } catch {
      setFailed(true)
      setPending(false)
    }
  }

  return <div className="titlebar-auth">
    {failed && <span role="alert">Не удалось выйти</span>}
    <button type="button" className="primary-link" disabled={pending} onClick={logout}>
      {pending ? 'Выходим…' : 'Выйти'}
    </button>
  </div>
}
