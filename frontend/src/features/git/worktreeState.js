// Проверить неотрицательное целое число, безопасное для JavaScript
const integer = value => Number.isSafeInteger(value) && value >= 0
const statuses = [' ', 'M', 'A', 'D', 'R', 'C', 'U', '?', '!', 'T', 'X']
// Проверить пакет оперативных статусов файлов и индекса
export function parseWorktree(data, sessionId) {
  if (!data || data.session_id !== sessionId || !integer(data.generation) || !integer(data.version)) throw new Error('Некорректное состояние файлов')
  const state = data.state
  if (state === null) {
    if (data.version !== 0) throw new Error('Некорректная версия файлов')
    return data
  }
  if (!data.generation || !data.version || !state || typeof state.path !== 'string' ||
      !['repository', 'no_repository', 'unavailable'].includes(state.kind)) throw new Error('Некорректная рабочая папка')
  if (state.kind === 'repository' && (!Array.isArray(state.files) || state.files.some(file =>
    typeof file.path !== 'string' || typeof file.conflict !== 'boolean' || !statuses.includes(file.index) || !statuses.includes(file.worktree) ||
    !(file.original_path == null || typeof file.original_path === 'string')))) throw new Error('Некорректные статусы файлов')
  return data
}
// Выбрать актуальные файлы, не стирая push запоздалым HTTP-ответом
export function newerWorktree(old, next) {
  if (!old || next.generation > old.generation) return next
  if (next.generation < old.generation) return old
  // Поздний пустой HTTP-ответ не должен стирать уже полученный push
  if (next.version === 0) return old
  return next.version >= old.version ? next : old
}
