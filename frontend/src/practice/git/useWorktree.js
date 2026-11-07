import { useEffect, useState } from 'react'
import { worktreeApi, worktreeEvents } from '../../routes'
import { newerWorktree, parseWorktree } from './worktreeState'

// Получать оперативные файлы независимо от загрузки истории графа
export function useWorktree(sessionId) {
  const [result, setResult] = useState({ data: null, error: false })
  useEffect(() => {
    let disposed = false, controller, socket, reconnect, reading = false, dirty = false, delay = 1000
    setResult({ data: null, error: false })
    // Перечитать состояние через HTTP, объединяя одновременные запросы обновления
    async function refresh() {
      if (disposed) return
      if (reading) { dirty = true; return }
      reading = true
      controller = new AbortController()
      const timeout = setTimeout(() => controller.abort(), 5000)
      try {
        const response = await fetch(worktreeApi(sessionId), { signal: controller.signal, cache: 'no-store' })
        if (!response.ok) throw new Error('Рабочая папка недоступна')
        const data = parseWorktree(await response.json(), sessionId)
        if (!disposed) setResult(old => ({ data: newerWorktree(old.data, data), error: false }))
      } catch {
        if (!disposed) setResult(old => ({ ...old, error: true }))
      } finally {
        clearTimeout(timeout)
        reading = false
        if (dirty && !disposed) { dirty = false; refresh() }
      }
    }
    // Открыть WebSocket-подписку с восстановлением после разрыва связи
    function connect() {
      if (disposed) return
      const url = new URL(worktreeEvents(sessionId), window.location.href)
      url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
      socket = new WebSocket(url)
      socket.onmessage = event => {
        try {
          const message = JSON.parse(event.data)
          if (message.type === 'ready') { delay = 1000; refresh() }
          if (message.type === 'worktree_changed') {
            const data = parseWorktree(message.worktree, sessionId)
            setResult(old => ({ data: newerWorktree(old.data, data), error: false }))
          }
        } catch { socket.close() }
      }
      socket.onclose = () => {
        if (disposed) return
        refresh()
        reconnect = setTimeout(connect, delay)
        delay = Math.min(delay * 2, 15000)
      }
      socket.onerror = () => socket.close()
    }
    refresh()
    connect()
    const poll = setInterval(refresh, 10000)
    // Обновить данные при возвращении пользователя к видимой странице
    const resume = () => { if (document.visibilityState === 'visible') refresh() }
    document.addEventListener('visibilitychange', resume)
    return () => {
      disposed = true
      controller?.abort(); socket?.close(); clearTimeout(reconnect); clearInterval(poll)
      document.removeEventListener('visibilitychange', resume)
    }
  }, [sessionId])
  return result
}
