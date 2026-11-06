const integer = value => Number.isSafeInteger(value) && value >= 0
const hash = value => typeof value === 'string' && /^(?:[a-f0-9]{40}|[a-f0-9]{64})$/.test(value)
export function parsePracticeState(data, sessionId) {
  if (!data || data.session_id !== sessionId || !integer(data.generation) ||
      !['active', 'closed'].includes(data.status) || typeof data.cli_connected !== 'boolean' ||
      !Number.isFinite(data.cli_lease_seconds) || data.cli_lease_seconds < 0 || data.cli_lease_seconds > 35 ||
      (data.connected_at !== null && !Number.isFinite(Date.parse(data.connected_at)))) throw new Error('Некорректная сессия')
  if (data.snapshot !== null) {
    const s = data.snapshot, state = s?.state
    if (!s || s.session_id !== sessionId || s.schema_version !== 1 || !integer(s.generation) || s.generation < 1 ||
        s.generation > data.generation || !integer(s.version) || s.version < 1 || !Number.isFinite(Date.parse(s.received_at)) ||
        !state || typeof state.path !== 'string' || !['repository', 'no_repository', 'unavailable'].includes(state.kind)) throw new Error('Некорректный снимок')
    if (state.kind === 'repository' && (
      !['branch', 'unborn', 'detached'].includes(state.head_kind) || !(state.head === null || hash(state.head)) ||
      !(state.branch === null || typeof state.branch === 'string') || !Array.isArray(state.commits) ||
      state.commits.some(c => !hash(c.id) || !Array.isArray(c.parents) || c.parents.some(p => !hash(p))) ||
      !Array.isArray(state.refs) || state.refs.some(r => typeof r !== 'string' || !/^refs\/(heads|tags)\/\S+ [a-f0-9]{40}(?:[a-f0-9]{24})?$/.test(r)) ||
      !Array.isArray(state.files) || state.files.some(f => typeof f.path !== 'string' || typeof f.conflict !== 'boolean' ||
        ![' ', 'M', 'A', 'D', 'R', 'C', 'U', '?', '!', 'T', 'X'].includes(f.index) ||
        ![' ', 'M', 'A', 'D', 'R', 'C', 'U', '?', '!', 'T', 'X'].includes(f.worktree) ||
        !(f.original_path == null || typeof f.original_path === 'string')) ||
      (state.ref_commits !== undefined && (!state.ref_commits || Array.isArray(state.ref_commits) || typeof state.ref_commits !== 'object' ||
        Object.entries(state.ref_commits).some(([name, id]) => !/^refs\/(heads|tags)\/\S+$/.test(name) || !hash(id)))) ||
      (state.history_truncated !== undefined && typeof state.history_truncated !== 'boolean') ||
      (state.is_shallow !== undefined && typeof state.is_shallow !== 'boolean') ||
      (state.history_boundary !== undefined && (!Array.isArray(state.history_boundary) || state.history_boundary.some(id => !hash(id)))) ||
      !Array.isArray(state.operations) || state.operations.some(o => typeof o !== 'string') || !integer(state.history_limit)
    )) throw new Error('Некорректное состояние Git')
  }
  return data
}
export function newerState(old, next) {
  if (!old) return next
  if (next.generation < old.generation) return old
  const a = old.snapshot, b = next.snapshot
  if (a && (!b || b.generation < a.generation || (b.generation === a.generation && b.version < a.version))) return old
  return next
}

export function commitCount(count) {
  const lastTwo = count % 100, last = count % 10
  return `${count} ${lastTwo >= 11 && lastTwo <= 14 ? 'коммитов' : last === 1 ? 'коммит' : last >= 2 && last <= 4 ? 'коммита' : 'коммитов'}`
}

const branchPalette = ['var(--branch-violet)', 'var(--branch-orange)', 'var(--branch-green)', 'var(--branch-pink)']
export function graphLayout(commits, refs = [], head = null, previous = null) {
  const byId = new Map(commits.map(c => [c.id, c]))
  const branches = refs.filter(r => r.startsWith('refs/heads/')).map(ref => {
    const split = ref.lastIndexOf(' ')
    return { name: ref.slice(11, split), id: ref.slice(split + 1) }
  }).sort((a, b) => a.name.localeCompare(b.name))
  const main = branches.find(b => b.name === 'main') ?? branches.find(b => b.name === 'master')
  const lanes = new Map(), laneNames = [], laneColors = [], depths = new Map(), usedColors = new Set()
  if (previous) {
    previous.lanes.forEach(lane => { laneNames.push(lane.name); laneColors.push(lane.color); usedColors.add(lane.color) })
    previous.nodes.forEach(node => { if (byId.has(node.id)) lanes.set(node.id, node.lane) })
  }
  const branchColors = new Map(laneNames.map((name, i) => [name, laneColors[i]]))
  branchColors.set(main?.name ?? 'HEAD', 'var(--accent)')
  usedColors.add('var(--accent)')
  function colorFor(name) {
    if (branchColors.has(name)) return branchColors.get(name)
    let colorHash = 0
    for (const char of name) colorHash = (colorHash * 31 + char.charCodeAt(0)) >>> 0
    const preferred = branchPalette[colorHash % branchPalette.length]
    const color = !usedColors.has(preferred) ? preferred : branchPalette.find(c => !usedColors.has(c)) ?? `hsl(${(branchColors.size * 137.508) % 360} 70% 68%)`
    branchColors.set(name, color)
    usedColors.add(color)
    return color
  }
  branches.forEach(b => colorFor(b.name))
  function claim(id, name) {
    if (!byId.has(id) || lanes.has(id)) return
    let lane = laneNames.indexOf(name)
    if (lane < 0) {
      lane = laneNames.length
      laneNames.push(name)
      laneColors.push(lane === 0 ? 'var(--accent)' : colorFor(name))
    }
    while (byId.has(id) && !lanes.has(id)) {
      lanes.set(id, lane)
      id = byId.get(id).parents[0]
    }
  }
  function depth(id, visiting = new Set()) {
    if (!byId.has(id) || visiting.has(id)) return -1
    if (depths.has(id)) return depths.get(id)
    visiting.add(id)
    const value = Math.max(-1, ...byId.get(id).parents.map(parent => depth(parent, visiting))) + 1
    visiting.delete(id)
    depths.set(id, value)
    return value
  }
  // Порядок входного массива не влияет на раскладку одинакового DAG
  const ordered = [...commits].sort((a, b) => depth(b.id) - depth(a.id) || a.id.localeCompare(b.id))
  claim(main?.id ?? head ?? ordered[0]?.id, main?.name ?? 'HEAD')
  branches.filter(b => b !== main).forEach(b => claim(b.id, b.name))
  // Сохраняем боковые линии после удаления указателя ветки: родители merge
  // по-прежнему описывают настоящий DAG, имя удалённой ветки неизвестно
  ordered.forEach(c => c.parents.slice(1).forEach(parent => claim(parent, `Линия ${laneNames.length + 1}`)))
  ordered.forEach(c => claim(c.id, `Линия ${laneNames.length + 1}`))
  const branchFlows = [...(previous?.branchFlows ?? [])]
  for (const branch of branches) {
    const from = previous?.branchTips?.[branch.name]
    const oldTip = previous?.nodes.find(node => node.id === from)
    const newTip = previous?.nodes.find(node => node.id === branch.id)
    if (!oldTip || !newTip || oldTip.lane === newTip.lane || from === branch.id) continue
    let cursor = branch.id
    const visited = new Set()
    while (cursor !== from && byId.has(cursor) && !visited.has(cursor)) {
      visited.add(cursor)
      cursor = byId.get(cursor).parents[0]
    }
    if (cursor !== from) continue
    const key = `${branch.name}:${from}:${branch.id}`
    if (!branchFlows.some(flow => flow.key === key)) branchFlows.push({
      key, from, to: branch.id, name: branch.name,
      color: previous.lanes[newTip.lane].color,
      targetColor: previous.lanes[oldTip.lane].color,
    })
  }
  const positions = new Map()
  const nodes = commits.map(commit => {
    const lane = lanes.get(commit.id)
    const position = { x: 90 + depth(commit.id) * 170, y: 70 + lane * 120 }
    positions.set(commit.id, position)
    return { ...commit, ...position, lane, color: laneColors[lane] }
  })
  // Прореживаем пустые линии, чтобы ограниченная история не наращивала высоту
  const visibleLanes = [...new Set([0, ...nodes.map(n => n.lane)])].sort((a, b) => a - b)
  nodes.forEach(node => {
    node.lane = visibleLanes.indexOf(node.lane)
    node.y = 70 + node.lane * 120
    positions.set(node.id, { x: node.x, y: node.y })
  })
  const renderedLanes = visibleLanes.map(i => ({ name: laneNames[i], color: laneColors[i] }))
  const historicalLabels = renderedLanes.flatMap((lane, index) => {
    if (index === 0 || !lane.name || lane.name === 'HEAD' || lane.name.startsWith('Линия ')) return []
    const tip = nodes.filter(n => n.lane === index).sort((a, b) => b.x - a.x)[0]
    return tip && !branches.some(b => b.name === lane.name && b.id === tip.id)
      ? [{ id: tip.id, name: lane.name, color: lane.color }] : []
  })
  nodes.sort((a, b) => a.x - b.x || a.y - b.y)
  return { nodes, positions, branchColors: Object.fromEntries(branchColors), width: Math.max(320, ...nodes.map(n => n.x + 100)), height: Math.max(180, renderedLanes.length * 120 + 20, branchFlows.length ? 260 : 0), lanes: renderedLanes, historicalLabels, branchFlows, branchTips: Object.fromEntries(branches.map(b => [b.name, b.id])) }
}

export function graphRefs(state) {
  return state.refs.map(ref => {
    const split = ref.lastIndexOf(' ')
    const fullName = ref.slice(0, split)
    return {
      name: fullName.replace('refs/heads/', '').replace('refs/tags/', 'tag: '),
      id: state.ref_commits?.[fullName] ?? ref.slice(split + 1),
    }
  })
}

// История загружается с сервера; локальное хранилище не участвует в раскладке
export function repositoryGraph(state, history = []) {
  let graph = null, path = null
  let commits = new Map()
  for (const snapshot of [...history, { state }]) {
    const current = snapshot.state
    if (current.kind !== 'repository' || current.path !== path) {
      graph = null
      commits = new Map()
    }
    path = current.path
    if (current.kind !== 'repository') continue
    current.commits.forEach(commit => commits.set(commit.id, commit))
    graph = graphLayout([...commits.values()], current.refs, current.head, graph)
  }
  return displayGraph(graph ?? graphLayout([]), state)
}

export function parseSnapshotHistory(page, sessionId, throughId, afterId) {
  if (!page || !Array.isArray(page.snapshots) || typeof page.has_more !== 'boolean') throw new Error('Некорректная история')
  let cursor = afterId
  for (const snapshot of page.snapshots) {
    if (!integer(snapshot.id) || snapshot.id <= cursor || snapshot.id > throughId) throw new Error('Некорректный порядок истории')
    parsePracticeState({ session_id: sessionId, status: 'active', generation: snapshot.generation,
      cli_connected: false, cli_lease_seconds: 0, connected_at: null, snapshot }, sessionId)
    cursor = snapshot.id
  }
  if (page.has_more && !page.snapshots.length) throw new Error('Пустая страница истории')
  return page
}

function displayGraph(graph, state) {
  const nodes = graph.nodes.map(node => ({ ...node, key: node.id, refNames: [] }))
  const byId = new Map(nodes.map(node => [node.id, node]))
  const edges = []
  for (const flow of graph.branchFlows) {
    const original = byId.get(flow.to)
    const from = [...nodes].reverse().find(node => node.id === flow.from && node.refBranch === flow.name) ?? byId.get(flow.from)
    if (!original || !from) continue
    const copy = { ...original, key: `copy:${flow.key}`, lane: from.lane, y: from.y,
      color: flow.targetColor, repeated: true, refBranch: flow.name, refNames: [] }
    nodes.push(copy)
    edges.push({ source: original.key, target: copy.key, color: flow.color,
      title: 'Тот же коммит на линии принимающей ветки' })
    edges.push({ source: from.key, target: copy.key, color: flow.targetColor,
      title: `Наблюдавшееся продвижение ветки ${flow.name}` })
  }
  for (const node of nodes.filter(node => !node.repeated)) {
    node.parents.forEach((parent, index) => {
      const source = [...nodes].reverse().find(candidate => candidate.id === parent && candidate.lane === node.lane) ?? byId.get(parent)
      edges.push({ source: source?.key, target: node.key, boundary: !source,
        color: index > 0 && source ? source.color : node.color })
    })
  }
  const byKey = new Map(nodes.map(node => [node.key, node]))
  const positioned = new Set()
  function position(node, visiting = new Set()) {
    if (positioned.has(node.key) || visiting.has(node.key)) return
    visiting.add(node.key)
    for (const edge of edges.filter(edge => edge.target === node.key && edge.source)) {
      const parent = byKey.get(edge.source)
      position(parent, visiting)
      node.x = Math.max(node.x, parent.x + 170)
    }
    visiting.delete(node.key)
    positioned.add(node.key)
  }
  nodes.forEach(node => position(node))
  for (const ref of graphRefs(state)) {
    const copy = [...nodes].reverse().find(node => node.id === ref.id && node.refBranch === ref.name)
    const target = copy ?? byId.get(ref.id)
    if (target) target.refNames.push(ref.name)
  }
  const headRef = state.head_kind === 'detached' ? null : state.branch
  const headNode = nodes.find(node => node.id === state.head && headRef && node.refNames.includes(headRef)) ?? byId.get(state.head)
  if (headNode) headNode.isHead = true
  nodes.sort((a, b) => a.x - b.x || a.y - b.y)
  return { ...graph, nodes, edges, positions: new Map(nodes.map(node => [node.key, { x: node.x, y: node.y }])),
    width: Math.max(320, ...nodes.map(node => node.x + 100)) }
}

export function graphConnections(graph) {
  const byKey = new Map(graph.nodes.map(node => [node.key, node]))
  return graph.edges.map((edge, index) => {
    const source = byKey.get(edge.source), target = byKey.get(edge.target)
    return { ...edge, key: `edge-${index}`, d: source
      ? `M${source.x},${source.y} C${source.x + 80},${source.y} ${target.x - 80},${target.y} ${target.x},${target.y}`
      : `M${target.x - 42},${target.y} H${target.x}` }
  })
}
