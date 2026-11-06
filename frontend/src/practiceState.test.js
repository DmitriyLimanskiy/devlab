import test from 'node:test'
import assert from 'node:assert/strict'
import { newerState, parsePracticeState, graphLayout, graphRefs, commitCount, repositoryGraph, parseSnapshotHistory, graphConnections } from './practiceState.js'
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

test('fast-forward не создаёт развилку и не зависит от предыдущего отображения', () => {
  const commits = [{ id: 'tip', parents: ['base'] }, { id: 'base', parents: [] }]
  const graph = graphLayout(commits, ['refs/heads/main tip', 'refs/heads/dev tip'], 'tip')
  assert.equal(graph.positions.get('tip').y, graph.positions.get('base').y)
  assert.deepEqual(graph.nodes.find(n => n.id === 'tip').parents, ['base'])
})
test('merge после удаления ветки восстанавливается из единственного снимка', () => {
  const commits = [{ id: 'merge', parents: ['main', 'dev'] }, { id: 'dev', parents: ['base'] }, { id: 'main', parents: ['base'] }, { id: 'base', parents: [] }]
  const graph = graphLayout(commits, ['refs/heads/main merge'], 'merge')
  assert.notEqual(graph.positions.get('dev').y, graph.positions.get('main').y)
  assert.equal(graph.positions.get('base').y, graph.positions.get('main').y)
  assert.deepEqual(graph.nodes.find(n => n.id === 'merge').parents, ['main', 'dev'])
  assert.deepEqual(graph, graphLayout(JSON.parse(JSON.stringify(commits)), ['refs/heads/main merge'], 'merge'))
})
test('раскладка не зависит от порядка коммитов и refs', () => {
  const commits = [{ id: 'm', parents: ['a', 'b', 'c'] }, { id: 'a', parents: ['root'] }, { id: 'b', parents: ['root'] }, { id: 'c', parents: ['root'] }, { id: 'root', parents: [] }, { id: 'other', parents: [] }]
  const refs = ['refs/heads/main m', 'refs/heads/side b', 'refs/heads/other other']
  const graph = graphLayout(commits, refs, 'm')
  // Map сравнивается без зависимости от порядка вставки
  assert.deepEqual(graph, graphLayout([...commits].reverse(), [...refs].reverse(), 'm'))
  assert.equal(new Set(['a', 'b', 'c'].map(id => graph.positions.get(id).y)).size, 3)
})
test('annotated tag привязан к коммиту, старый снимок остаётся совместимым', () => {
  const refs = ['refs/tags/v1 tag-object', 'refs/tags/tree tree-object', 'refs/heads/main tip']
  assert.deepEqual(graphRefs({ refs, ref_commits: { 'refs/tags/v1': 'tip', 'refs/heads/main': 'tip' } }), [
    { name: 'tag: v1', id: 'tip' }, { name: 'tag: tree', id: 'tree-object' }, { name: 'main', id: 'tip' },
  ])
  assert.equal(graphRefs({ refs })[0].id, 'tag-object')
})
test('detached HEAD и независимые корни не теряют коммиты', () => {
  const graph = graphLayout([{ id: 'detached', parents: ['outside'] }, { id: 'main', parents: [] }], ['refs/heads/main main'], 'detached')
  assert.equal(graph.nodes.length, 2)
  assert.notEqual(graph.positions.get('main').y, graph.positions.get('detached').y)
  assert.equal(graph.positions.has('outside'), false)
})

test('новые поля снимка проверяются, прежние снимки без них принимаются', () => {
  const response = state(1, 1)
  const sha = 'a'.repeat(40)
  const repository = { kind: 'repository', path: '/tmp/repo', head_kind: 'branch', head: sha, branch: 'main', commits: [{ id: sha, parents: [] }], refs: [`refs/heads/main ${sha}`], files: [], operations: [], history_limit: 200 }
  response.snapshot.state = repository
  assert.doesNotThrow(() => parsePracticeState(response, id))
  response.snapshot.state = { ...repository, ref_commits: { 'refs/heads/main': sha }, history_boundary: [], history_truncated: false, is_shallow: true }
  assert.doesNotThrow(() => parsePracticeState(response, id))
  for (const [key, value] of [['ref_commits', []], ['ref_commits', { 'refs/heads/main': 'bad' }], ['history_boundary', ['bad']], ['history_truncated', 'yes'], ['is_shallow', 1]]) {
    response.snapshot.state = { ...repository, [key]: value }
    assert.throws(() => parsePracticeState(response, id))
  }
})

test('история сервера восстанавливает линию после fast-forward и перезагрузки', () => {
  const base = { id: 'base', parents: [] }, c = { id: 'c', parents: ['base'] }, d = { id: 'd', parents: ['c'] }
  const repo = (commits, refs, head) => ({ kind: 'repository', path: '/repo', commits, refs, head })
  const history = [
    { state: repo([base], ['refs/heads/main base'], 'base') },
    { state: repo([c, base], ['refs/heads/main base', 'refs/heads/dev c'], 'c') },
    { state: repo([d, c, base], ['refs/heads/main base', 'refs/heads/dev d'], 'd') },
    { state: repo([d, c, base], ['refs/heads/main d'], 'd') },
  ]
  const graph = repositoryGraph(history.at(-1).state, history)
  assert.notEqual(graph.positions.get('base').y, graph.positions.get('c').y)
  assert.equal(graph.positions.get('c').y, graph.positions.get('d').y)
  const copy = graph.nodes.find(n => n.id === 'd' && n.repeated)
  assert.equal(copy.y, graph.positions.get('base').y)
  assert.equal(copy.color, 'var(--accent)')
  assert.equal(graph.historicalLabels.find(l => l.name === 'dev').id, 'd')
  assert.deepEqual(graph.nodes.find(n => n.id === 'd').parents, ['c'])
  assert.deepEqual(graph, repositoryGraph(history.at(-1).state, JSON.parse(JSON.stringify(history))))
})
test('история сохраняет исчезнувшие коммиты, смена папки и git init сбрасывают линии', () => {
  const repository = { kind: 'repository', path: '/repo', head: 'base', refs: ['refs/heads/main base'], commits: [{ id: 'base', parents: [] }] }
  const earlier = { ...repository, head: 'lost', commits: [{ id: 'lost', parents: ['base'] }, ...repository.commits] }
  assert.equal(repositoryGraph(repository, [{ state: earlier }]).nodes.length, 2)
  assert.equal(repositoryGraph(repository, [{ state: earlier }, { state: { kind: 'no_repository', path: '/repo' } }]).nodes.length, 1)
  assert.equal(repositoryGraph({ ...repository, path: '/other' }, [{ state: earlier }]).nodes.length, 1)
})
test('страницы истории проверяют порядок, сессию и границу загрузки', () => {
  const snapshot = { ...state(1, 1).snapshot, id: 3 }
  const page = { snapshots: [snapshot], has_more: false }
  assert.equal(parseSnapshotHistory(page, id, 3, 0), page)
  assert.throws(() => parseSnapshotHistory(page, id, 2, 0))
  assert.throws(() => parseSnapshotHistory(page, id, 3, 3))
  assert.throws(() => parseSnapshotHistory({ snapshots: [], has_more: true }, id, 3, 0))
  assert.throws(() => parseSnapshotHistory(page, 'other', 3, 0))
})

test('fast-forward замыкает dev на main и не возвращает конечный коммит вниз при следующем commit', () => {
  const base = { id: 'base', parents: [] }, c = { id: 'c', parents: ['base'] }, d = { id: 'd', parents: ['c'] }, e = { id: 'e', parents: ['d'] }
  const repo = (commits, main, dev) => ({ kind: 'repository', path: '/repo', commits,
    refs: [`refs/heads/main ${main}`, `refs/heads/dev ${dev}`], head: main })
  const history = [
    { state: repo([base], 'base', 'base') },
    { state: repo([c, base], 'base', 'c') },
    { state: repo([d, c, base], 'base', 'd') },
    { state: repo([d, c, base], 'd', 'd') },
  ]
  const merged = repositoryGraph(history.at(-1).state, history)
  assert.equal(merged.nodes.find(n => n.id === 'd' && n.repeated).y, merged.positions.get('base').y)
  assert.equal(merged.positions.get('c').y, merged.positions.get('d').y)
  const next = repositoryGraph(repo([e, d, c, base], 'e', 'd'), history)
  const copy = next.nodes.find(n => n.id === 'd' && n.repeated)
  assert.equal(copy.y, next.positions.get('e').y)
  assert.ok(copy.x < next.positions.get('e').x)
  assert.equal(next.positions.get('c').y, next.positions.get('d').y)
  assert.deepEqual(next.nodes.find(n => n.id === 'd').parents, ['c'])
})

test('исходный коммит остаётся на dev, а main получает второе отображение SHA', () => {
  const base = { id: 'base', parents: [] }, tip = { id: 'tip', parents: ['base'] }
  const repo = (main, dev) => ({ kind: 'repository', path: '/repo', branch: 'main', head_kind: 'branch', commits: [tip, base],
    refs: [`refs/heads/main ${main}`, `refs/heads/dev ${dev}`], head: main })
  const history = [{ state: repo('base', 'tip') }, { state: repo('tip', 'tip') }]
  const graph = repositoryGraph(history.at(-1).state, history)
  const original = graph.nodes.find(node => node.id === 'tip' && !node.repeated)
  const copy = graph.nodes.find(node => node.id === 'tip' && node.repeated)
  assert.notEqual(original.y, copy.y)
  assert.equal(copy.y, graph.positions.get('base').y)
  assert.ok(original.x < copy.x)
  assert.deepEqual(original.refNames, ['dev'])
  assert.deepEqual(copy.refNames, ['main'])
  assert.equal(copy.isHead, true)
  assert.equal(original.isHead, undefined)
  assert.deepEqual(copy.parents, original.parents)
  const paths = graphConnections(graph)
  assert.ok(paths.some(path => path.source === original.key && path.target === copy.key))
  assert.ok(paths.some(path => path.source === 'base' && path.target === copy.key && path.color === 'var(--accent)'))
  assert.deepEqual(graph, repositoryGraph(history.at(-1).state, JSON.parse(JSON.stringify(history))))
})

test('нормализованные кадры содержат только новые коммиты, HEAD берётся из текущего состояния', () => {
  const base = { id: 'base', parents: [] }, tip = { id: 'tip', parents: ['base'] }
  const repo = (commits, main, dev, branch = 'main') => ({ kind: 'repository', path: '/repo', commits,
    refs: [`refs/heads/main ${main}`, `refs/heads/dev ${dev}`], head: branch === 'main' ? main : dev, branch, head_kind: 'branch' })
  const history = [
    { state: repo([base], 'base', 'base') },
    { state: repo([tip], 'base', 'tip', 'dev') },
    { state: repo([], 'tip', 'tip') },
  ]
  const graph = repositoryGraph(repo([tip, base], 'tip', 'tip', 'dev'), history)
  assert.equal(graph.nodes.filter(node => node.id === 'tip').length, 2)
  assert.deepEqual(graph.nodes.find(node => node.isHead).refNames, ['dev'])
  assert.ok(graph.nodes.find(node => node.repeated).refNames.includes('main'))
})
