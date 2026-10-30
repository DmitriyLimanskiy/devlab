import test from 'node:test'
import assert from 'node:assert/strict'
import { newerState, parsePracticeState, graphLayout, commitCount } from './practiceState.js'
const id = '12345678-1234-1234-1234-123456789abc'
const state = (generation, version) => ({ session_id: id, status: 'active', cli_connected: false, cli_lease_seconds: 0, generation, connected_at: null, snapshot: { session_id: id, schema_version: 1, generation, version, received_at: '2026-10-31T12:00:00Z', state: { kind: 'no_repository', path: '/tmp/repo' } } })
test('проверка ответа, пустого снимка и повреждённых данных', () => {
  assert.equal(parsePracticeState(state(1, 1), id).snapshot.version, 1)
  assert.equal(parsePracticeState({ ...state(1, 1), snapshot: null }, id).snapshot, null)
  assert.throws(() => parsePracticeState(state(1, 1), 'other'))
  assert.throws(() => parsePracticeState({ ...state(1, 1), snapshot: {} }, id))
})
test('старые HTTP-ответы и версии предыдущего поколения не заменяют новые', () => {
  const latest = state(2, 5)
  assert.equal(newerState(latest, state(1, 10)), latest)
  assert.equal(newerState(latest, state(2, 4)), latest)
  assert.equal(newerState(latest, state(3, 1)).snapshot.generation, 3)
})
test('граф содержит каждое ребро merge и сохраняет границу истории', () => {
  const graph = graphLayout([{ id: 'merge', parents: ['a', 'b'] }, { id: 'a', parents: ['base'] }, { id: 'b', parents: ['base'] }, { id: 'base', parents: ['outside'] }])
  assert.equal(graph.nodes.length, 4)
  assert.notEqual(graph.positions.get('a').y, graph.positions.get('b').y)
  assert.ok(graph.positions.get('base').x < graph.positions.get('a').x)
  assert.ok(graph.positions.get('a').x < graph.positions.get('merge').x)
  assert.notEqual(graph.nodes.find(n => n.id === 'a').color, graph.nodes.find(n => n.id === 'b').color)
  assert.equal(graph.positions.has('outside'), false)
})

test('склонение количества коммитов', () => {
  for (const [number, expected] of [[0, '0 коммитов'], [1, '1 коммит'], [2, '2 коммита'], [4, '4 коммита'], [5, '5 коммитов'], [11, '11 коммитов'], [14, '14 коммитов'], [21, '21 коммит'], [22, '22 коммита'], [111, '111 коммитов']]) assert.equal(commitCount(number), expected)
})
test('main сохраняет основную линию и цвет независимо от текущего HEAD', () => {
  const commits = [{ id: 'feature', parents: ['base'] }, { id: 'main', parents: ['base'] }, { id: 'base', parents: [] }]
  const graph = graphLayout(commits, ['refs/heads/main main', 'refs/heads/dev feature'], 'feature')
  assert.equal(graph.nodes.find(n => n.id === 'main').color, 'var(--accent)')
  assert.equal(graph.positions.get('base').y, graph.positions.get('main').y)
  assert.notEqual(graph.positions.get('feature').y, graph.positions.get('main').y)
})
