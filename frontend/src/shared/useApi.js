import { useEffect, useState } from 'react'

// Вернуть ответ API без дополнительного преобразования
const identity = data => data

// Загрузить и проверить данные API с отменой запроса и возможностью повтора
export function useApi(path, parse = identity, method = 'GET', body = null) {
  const [state, setState] = useState({ loading: true, data: null, error: false })
  const [attempt, setAttempt] = useState(0)
  useEffect(() => {
    const controller = new AbortController()
    setState({ loading: true, data: null, error: false })
    fetch(path, {
      method,
      signal: controller.signal,
      ...(body !== null ? { headers: { 'Content-Type': 'application/json' }, body } : {}),
    })
      .then(response => {
        if (!response.ok) throw new Error('Request failed')
        return response.json()
      })
      .then(parse)
      .then(data => {
        if (!controller.signal.aborted) setState({ loading: false, data, error: false })
      })
      .catch(error => {
        if (error.name !== 'AbortError') setState({ loading: false, data: null, error: true })
      })
    return () => controller.abort()
  }, [path, attempt, parse, method, body])
  return { ...state, retry: () => setAttempt(value => value + 1) }
}
