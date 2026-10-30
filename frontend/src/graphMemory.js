// Только оформление наблюдавшихся коммитов, без архива снимков и файлов
export function layoutMemory(graph) {
  return { nodes: graph.nodes.map(({ id, lane }) => ({ id, lane })), lanes: graph.lanes }
}
export function readLayoutMemory(key) {
  try {
    if (!key) return null
    const data = JSON.parse(sessionStorage.getItem(key))
    if (!data || !Array.isArray(data.nodes) || data.nodes.length > 200 || !Array.isArray(data.lanes) || !data.lanes.length || data.lanes.length > 201 ||
        data.lanes.some(l => typeof l.name !== 'string' || typeof l.color !== 'string') ||
        data.nodes.some(n => typeof n.id !== 'string' || !Number.isInteger(n.lane) || n.lane < 0 || n.lane >= data.lanes.length)) return null
    return data
  } catch { return null }
}
export function saveLayoutMemory(key, graph) {
  try { if (key) sessionStorage.setItem(key, JSON.stringify(layoutMemory(graph))) } catch { /* Блокировка хранилища не мешает визуализации */ }
}
