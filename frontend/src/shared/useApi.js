import { useEffect, useState } from 'react'

// Вернуть ответ API без дополнительного преобразования
const identity = data => data

// Загрузить и проверить данные API с отменой запроса и возможностью повтора
export function useApi(path, parse = identity) {
  const [state, setState] = useState({ loading: true, data: null, error: false })
  const [attempt, setAttempt] = useState(0)
  useEffect(() => {
    const controller = new AbortController()
    setState({ loading: true, data: null, error: false })
    fetch(path, {
      signal: controller.signal,
    })
      .then(response => {
        if (!response.ok) {
          const error = new Error('Request failed')
          error.status = response.status
          throw error
        }
        return response.json()
      })
      .then(parse)
      .then(data => {
        if (!controller.signal.aborted) setState({ loading: false, data, error: false })
      })
      .catch(error => {
        if (!controller.signal.aborted) {
          setState({ loading: false, data: null, error: true, status: error.status })
        }
      })
    return () => controller.abort()
  }, [path, attempt, parse])
  return { ...state, retry: () => setAttempt(value => value + 1) }
}
