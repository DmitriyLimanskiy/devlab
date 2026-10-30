import { useEffect, useState } from 'react'
import { practiceApi, practiceEvents } from './routes'
import { parsePracticeState, newerState } from './practiceState'

export function usePracticeState(sessionId) {
  const [result, setResult] = useState({ data: null, connection: 'connecting', error: false, presenceDeadline: 0 })
  useEffect(() => {
    let disposed = false, socket, reconnect, poll, controller, reading = false, dirty = false, delay = 1000
    setResult({ data: null, connection: 'connecting', error: false, presenceDeadline: 0 })
    const connection = value => !disposed && setResult(old => ({ ...old, connection: value }))
    async function refresh() {
      if (disposed) return
      if (reading) { dirty = true; return }
      reading = true
      controller = new AbortController()
      const timeout = setTimeout(() => controller.abort(), 8000)
      try {
        const response = await fetch(practiceApi(sessionId), { signal: controller.signal, cache: 'no-store' })
        if (!response.ok) throw new Error('Снимок недоступен')
        const data = parsePracticeState(await response.json(), sessionId)
        if (!disposed) setResult(old => ({ ...old, data: newerState(old.data, data), error: false, presenceDeadline: Date.now() + data.cli_lease_seconds * 1000 }))
      } catch (error) {
        if (!disposed) setResult(old => ({ ...old, error: true }))
      } finally {
        clearTimeout(timeout)
        reading = false
        if (dirty && !disposed) { dirty = false; refresh() }
      }
    }
    function connect() {
      if (disposed) return
      const url = new URL(practiceEvents(sessionId), window.location.href)
      url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
      socket = new WebSocket(url)
      socket.onmessage = event => {
        try {
          const message = JSON.parse(event.data)
          if (message.type === 'ready') { delay = 1000; connection('live'); refresh() }
          if (message.type === 'state_changed') refresh()
        } catch { socket.close() }
      }
      socket.onclose = () => {
        if (disposed) return
        connection('reconnecting')
        refresh()
        reconnect = setTimeout(connect, delay)
        delay = Math.min(delay * 2, 15000)
      }
      socket.onerror = () => socket.close()
    }
    // HTTP работает и при недоступном WebSocket; сверка восстанавливает пропуски
    refresh()
    connect()
    poll = setInterval(refresh, 10000)
    const expiry = setInterval(() => setResult(old => old.data?.cli_connected && Date.now() >= old.presenceDeadline ? { ...old, data: { ...old.data, cli_connected: false } } : old), 1000)
    const resume = () => { if (document.visibilityState === 'visible') refresh() }
    document.addEventListener('visibilitychange', resume)
    return () => {
      disposed = true
      clearTimeout(reconnect); clearInterval(poll); clearInterval(expiry); controller?.abort(); socket?.close()
      document.removeEventListener('visibilitychange', resume)
    }
  }, [sessionId])
  return result
}
