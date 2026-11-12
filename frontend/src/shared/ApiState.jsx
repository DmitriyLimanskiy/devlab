// Показать загрузку, панель ошибки или содержимое успешного ответа
export function ApiState({ state, children }) {
  if (state.loading) return <p role="status">Загрузка…</p>
  if (state.error) return <div className="api-error">
    <div className="api-error-panel" role="alert">
      <p>Не удалось загрузить данные</p>
      <button type="button" className="api-error-retry" onClick={state.retry}>Попробовать снова</button>
    </div>
  </div>
  return children(state.data)
}
