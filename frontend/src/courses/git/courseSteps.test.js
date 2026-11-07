import test from 'node:test'
import assert from 'node:assert/strict'
import { parseCourseSteps } from './courseSteps.js'

const step = (id, content) => ({ id, course_id: 2, slug: `step-${id}`, title: `Шаг ${id}`, position: id, content })

test('Markdown шага сохраняется без преобразования команд и сортируется по позиции', () => {
  const markdown = '## Практика\n\n- Подготовь файл\n\n```bash\nprintf "a\\nb\\n" > file.txt\n```'
  const result = parseCourseSteps({ steps: [step(2, { markdown }), step(1, { markdown: '' })] })
  assert.deepEqual(result.map(item => item.id), [1, 2])
  assert.equal(result[1].content.markdown, markdown)
})

test('Повреждённый Markdown из API не передаётся компоненту', () => {
  for (const markdown of [null, {}, [], 123]) {
    assert.throws(() => parseCourseSteps({ steps: [step(1, { markdown })] }), /Некорректный ответ/)
  }
})

test('Старые блоки и пустое описание сохраняют совместимость', () => {
  const blocks = [{ type: 'text', text: 'Описание' }, { type: 'code', text: 'git status' }]
  assert.equal(parseCourseSteps({ steps: [step(1, { blocks }), step(2, {})] }).length, 2)
})
