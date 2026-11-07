import { useCallback, useLayoutEffect, useState } from 'react'

// Сохранить только настройки интерфейса на время открытой страницы
const values = new Map()
const scrollPositions = new Map()

export function useViewState(key, initialValue) {
  const [value, setValue] = useState(() => values.has(key) ? values.get(key) : initialValue)
  const update = useCallback(next => {
    setValue(previous => {
      const result = typeof next === 'function' ? next(previous) : next
      values.set(key, result)
      return result
    })
  }, [key])
  return [value, update]
}

// Вернуть прокрутку при повторном открытии курса, шага или панели
export function useRememberedScroll(key, ref, ready = true) {
  useLayoutEffect(() => {
    const element = ref.current
    if (!element || !ready) return
    const position = scrollPositions.get(key)
    if (position) {
      element.scrollLeft = position.left
      element.scrollTop = position.top
    } else {
      element.scrollLeft = 0
      element.scrollTop = 0
    }
    const save = () => scrollPositions.set(key, { left: element.scrollLeft, top: element.scrollTop })
    element.addEventListener('scroll', save)
    return () => element.removeEventListener('scroll', save)
  }, [key, ref, ready])
}
