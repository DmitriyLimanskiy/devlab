import test from 'node:test'
import assert from 'node:assert/strict'
import { parseWorktree, newerWorktree } from './worktreeState.js'
const data = (generation, version, files = []) => ({ session_id: 's', generation, version, state: { kind: 'repository', path: '/repo', files } })
test('оперативные файлы и индекс проверяются независимо от графа', () => {
  const state = data(1, 2, [{ path: 'file', index: 'A', worktree: 'M', conflict: false }])
  assert.equal(parseWorktree(state, 's'), state)
  assert.throws(() => parseWorktree(state, 'other'))
  assert.throws(() => parseWorktree(data(1, 2, [{ path: 'bad', index: 'broken' }]), 's'))
})
test('поздние HTTP-ответы не заменяют новые файлы, новое поколение сбрасывает старые', () => {
  const latest = data(2, 5)
  assert.equal(newerWorktree(latest, data(1, 8)), latest)
  assert.equal(newerWorktree(latest, data(2, 4)), latest)
  const reset = { session_id: 's', generation: 3, version: 0, state: null }
  assert.equal(newerWorktree(latest, reset), reset)
  assert.equal(parseWorktree(reset, 's'), reset)
})

test('поздний пустой HTTP не стирает данные, полученные по WebSocket', () => {
  const latest = data(1, 2)
  assert.equal(newerWorktree(latest, { session_id: 's', generation: 1, version: 0, state: null }), latest)
})
