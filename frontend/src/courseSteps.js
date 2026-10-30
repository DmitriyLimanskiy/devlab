export function parseCourseSteps(data) {
  const steps = data?.steps
  if (!Array.isArray(steps) || steps.some(step =>
    !step || !Number.isInteger(step.id) || !Number.isInteger(step.course_id) ||
    typeof step.slug !== 'string' || typeof step.title !== 'string' ||
    !Number.isInteger(step.position) || step.position < 1 ||
    !step.content || typeof step.content !== 'object' || Array.isArray(step.content) ||
    (step.content.blocks !== undefined && (!Array.isArray(step.content.blocks) ||
      step.content.blocks.some(block => !block || typeof block.type !== 'string' ||
        (['text', 'code'].includes(block.type) && typeof block.text !== 'string'))))
  ) || new Set(steps.map(step => step.id)).size !== steps.length) {
    throw new Error('Некорректный ответ со шагами курса')
  }
  return [...steps].sort((a, b) => a.position - b.position || a.id - b.id)
}

// POST /git-course возвращает сессию и шаги одним ответом
export function parseGitCourse(data) {
  if (!data || typeof data.session_id !== 'string' ||
      !/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(data.session_id) ||
      !Number.isSafeInteger(data.generation) || data.generation < 0) {
    throw new Error('Некорректный ответ сессии курса')
  }
  return { session_id: data.session_id, generation: data.generation, steps: parseCourseSteps(data) }
}
