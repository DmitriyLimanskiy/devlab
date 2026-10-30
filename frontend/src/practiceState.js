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
export function graphLayout(commits, refs = [], head = null) {
  const byId = new Map(commits.map(c => [c.id, c]))
  const branches = refs.filter(r => r.startsWith('refs/heads/')).map(ref => {
    const split = ref.lastIndexOf(' ')
    return { name: ref.slice(11, split), id: ref.slice(split + 1) }
  }).sort((a, b) => a.name.localeCompare(b.name))
  const main = branches.find(b => b.name === 'main') ?? branches.find(b => b.name === 'master')
  const lanes = new Map(), laneNames = [], laneColors = [], depths = new Map(), usedColors = new Set()
  const branchColors = new Map([[main?.name ?? 'HEAD', 'var(--accent)']])
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
    const lane = laneNames.length
    laneNames.push(name)
    laneColors.push(lane === 0 ? 'var(--accent)' : colorFor(name))
    while (byId.has(id) && !lanes.has(id)) {
      lanes.set(id, lane)
      id = byId.get(id).parents[0]
    }
  }
  claim(main?.id ?? head ?? commits[0]?.id, main?.name ?? 'HEAD')
  branches.filter(b => b !== main).forEach(b => claim(b.id, b.name))
  // Сохраняем боковые линии после удаления указателя ветки: родители merge
  // по-прежнему описывают настоящий DAG, имя удалённой ветки неизвестно
  commits.forEach(c => c.parents.slice(1).forEach(parent => claim(parent, `Линия ${laneNames.length + 1}`)))
  commits.forEach(c => claim(c.id, `Линия ${laneNames.length + 1}`))
  function depth(id, visiting = new Set()) {
    if (!byId.has(id) || visiting.has(id)) return -1
    if (depths.has(id)) return depths.get(id)
    visiting.add(id)
    const value = Math.max(-1, ...byId.get(id).parents.map(parent => depth(parent, visiting))) + 1
    visiting.delete(id)
    depths.set(id, value)
    return value
  }
  const positions = new Map()
  const nodes = commits.map(commit => {
    const lane = lanes.get(commit.id)
    const position = { x: 90 + depth(commit.id) * 170, y: 70 + lane * 120 }
    positions.set(commit.id, position)
    return { ...commit, ...position, lane, color: laneColors[lane] }
  })
  nodes.sort((a, b) => a.x - b.x || a.y - b.y)
  return { nodes, positions, branchColors: Object.fromEntries(branchColors), width: Math.max(320, ...nodes.map(n => n.x + 100)), height: Math.max(180, laneNames.length * 120 + 20), lanes: laneNames.map((name, i) => ({ name, color: laneColors[i] })) }
}
