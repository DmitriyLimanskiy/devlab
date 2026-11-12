import { useEffect, useRef, useState } from 'react'
import { api } from '../../shared/routes'

export function AuthForm({ onLogin }) {
  const [registering, setRegistering] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [pending, setPending] = useState(false)
  const request = useRef(null)

  useEffect(() => () => request.current?.abort(), [])

  async function submit(event) {
    event.preventDefault()
    if (request.current) return

    const controller = new AbortController()
    request.current = controller
    setPending(true)
    setError('')
    setNotice('')
    try {
      const response = await fetch(registering ? api.register : api.login, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim(), password }),
        signal: controller.signal,
      })
      if (controller.signal.aborted) return
      if (!response.ok) {
        if (response.status === 401) setError('Неверная почта или пароль')
        else if (response.status === 409) setError('На эту почту уже зарегистрирован аккаунт')
        else if (response.status === 422) setError('Проверьте адрес почты и длину пароля')
        else setError('Не удалось отправить запрос. Попробуйте снова')
        return
      }

      setPassword('')
      if (registering) {
        setRegistering(false)
        setNotice('Аккаунт создан. Введите пароль для входа')
      } else {
        onLogin()
      }
    } catch {
      if (!controller.signal.aborted) setError('Не удалось связаться с сервером. Попробуйте снова')
    } finally {
      request.current = null
      if (!controller.signal.aborted) setPending(false)
    }
  }

  function switchMode() {
    setRegistering(value => !value)
    setPassword('')
    setError('')
    setNotice('')
  }

  return <section className="auth-panel" aria-labelledby="auth-title">
    <h1 id="auth-title">{registering ? 'Регистрация' : 'Вход в Stack Forge'}</h1>
    <form className="auth-form" onSubmit={submit} aria-busy={pending}>
      <label>
        Электронная почта
        <input name="email" type="email" autoComplete="username" required maxLength={254}
          value={email} onChange={event => setEmail(event.target.value)} disabled={pending} />
      </label>
      <label>
        Пароль
        <input name="password" type="password" autoComplete={registering ? 'new-password' : 'current-password'}
          required minLength={8} maxLength={128} value={password}
          onChange={event => setPassword(event.target.value)} disabled={pending} />
      </label>
      {notice && <p role="status">{notice}</p>}
      {error && <p className="auth-error" role="alert">{error}</p>}
      <button type="submit" className="primary-link" disabled={pending}>
        {pending ? 'Отправляем…' : registering ? 'Создать аккаунт' : 'Войти'}
      </button>
      <button type="button" className="auth-switch" onClick={switchMode} disabled={pending}>
        {registering ? 'Уже есть аккаунт? Войти' : 'Создать аккаунт'}
      </button>
    </form>
  </section>
}
