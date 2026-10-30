// Контракт GET /api/v1/catalog. id — публичный slug, а не числовой ключ БД
export const courseStatusLabels = {
  planned: 'В разработке',
  available: 'Доступен',
  archived: 'В архиве',
}

export function parseCatalog(data) {
  if (!Array.isArray(data) || data.some(course =>
    !course || typeof course.id !== 'string' || !course.id ||
    typeof course.title !== 'string' || typeof course.description !== 'string' ||
    !Object.hasOwn(courseStatusLabels, course.status) ||
    !Number.isInteger(course.position) || course.position < 1
  ) || new Set(data.map(course => course.id)).size !== data.length) {
    throw new Error('Некорректный ответ каталога')
  }
  // При одинаковых позициях сохраняем порядок, полученный от backend
  return [...data].sort((a, b) => a.position - b.position)
}
