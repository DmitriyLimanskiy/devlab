import { useLayoutEffect, useMemo, useRef, useState } from 'react'
import { GitBranch, GitCommitHorizontal, Folder, Layers, CircleDashed, ChevronRight, ChevronDown, Maximize2, Minimize2, Minus, Plus, LocateFixed } from 'lucide-react'
import { commitCount, repositoryGraph, graphRefs, graphConnections } from './practiceState'

const statuses = { M: 'Изменён', A: 'Добавлен', D: 'Удалён', R: 'Переименован', C: 'Скопирован', U: 'Конфликт', '?': 'Не отслеживается', '!': 'Игнорируется', T: 'Изменён тип', X: 'Неизвестный статус' }
// Показать пояснение об отсутствии данных в панели репозитория
function Empty({ children }) { return <div className="repo-empty"><CircleDashed size={24} strokeWidth={1.3} /><p>{children}</p></div> }
// Оформить панель репозитория с заголовком и дополнительной подписью
function Panel({ icon: Icon, title, detail, actions, type, children }) {
  return <section className={`repo-panel repo-panel-${type}`}><header><h2><Icon size={17} />{title}</h2><div className="repo-panel-actions">{detail && <span>{detail}</span>}{actions}</div></header>{children}</section>
}
// Показать граф коммитов, refs и признаки ограниченной истории
function History({ state, previous, history }) {
  const graph = useMemo(() => repositoryGraph(state, history), [state, history])
  const scrollRef = useRef(null)
  const [zoom, setZoom] = useState(1)
  const [fit, setFit] = useState(false)
  const [viewport, setViewport] = useState({ width: 0, height: 0 })
  useLayoutEffect(() => {
    const element = scrollRef.current
    if (!element) return
    const observer = new ResizeObserver(() => {
      const next = { width: element.clientWidth, height: element.clientHeight }
      setViewport(old => old.width === next.width && old.height === next.height ? old : next)
    })
    observer.observe(element)
    return () => observer.disconnect()
  }, [graph.nodes.length > 0])
  useLayoutEffect(() => {
    if (!fit || !viewport.width || !viewport.height) return
    setZoom(Math.max(0.05, Math.min(1, (viewport.width - 20) / graph.width, (viewport.height - 20) / graph.height)))
  }, [fit, viewport, graph.width, graph.height])
  // Изменить масштаб вручную и выйти из автоматического вписывания
  function changeZoom(delta) {
    setFit(false)
    setZoom(old => Math.max(0.05, Math.min(1.5, Math.round((old + delta) * 100) / 100)))
  }
  // Переместить видимую область к текущему HEAD без изменения раскладки графа
  function showHead() {
    const node = graph.nodes.find(item => item.isHead)
    if (!node) return
    scrollRef.current?.scrollTo({ left: Math.max(0, node.x * zoom - viewport.width / 2), top: Math.max(0, node.y * zoom - viewport.height / 2), behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth' })
  }
  if (!graph.nodes.length) return <Empty>Пока нет коммитов · HEAD → {state.branch ?? '—'}</Empty>
  const { nodes, positions, width, height, branchColors, historicalLabels } = graph
  const refs = graphRefs(state)
  const outside = refs.filter(ref => !positions.has(ref.id))
  const connections = graphConnections(graph)
  return <>
    <div className="graph-controls" role="group" aria-label="Управление графом">
      <button type="button" className="graph-control" aria-label="Уменьшить граф" disabled={zoom <= 0.05} onClick={() => changeZoom(-0.1)}><Minus size={15} /></button>
      <button type="button" className="graph-control graph-zoom" title="Вернуть масштаб 100%" onClick={() => { setFit(false); setZoom(1) }}>{Math.round(zoom * 100)}%</button>
      <button type="button" className="graph-control" aria-label="Увеличить граф" disabled={zoom >= 1.5} onClick={() => changeZoom(0.1)}><Plus size={15} /></button>
      <button type="button" className="graph-control" aria-pressed={fit} onClick={() => { setFit(true); scrollRef.current?.scrollTo({ left: 0, top: 0 }) }}>Вписать</button>
      <button type="button" className="graph-control graph-head" onClick={showHead}><LocateFixed size={15} />К HEAD</button>
    </div>
    <div ref={scrollRef} className="history-scroll" role="region" aria-label="Граф коммитов от старых слева к новым справа" tabIndex={0}>
      <div className="graph-stage" style={{ width: Math.max(viewport.width, width * zoom), height: Math.max(viewport.height, height * zoom) }}>
      <div className="commit-history" style={{ width, height, transform: `scale(${zoom})` }}>
        <svg width={width} height={height} aria-hidden="true" className="commit-graph">
          {connections.map(path => <path key={path.key} style={{ stroke: path.color }} className={path.boundary ? 'graph-boundary' : ''} d={path.d}>{path.title && <title>{path.title}</title>}</path>)}
          {nodes.map(node => <circle key={node.key} cx={node.x} cy={node.y} r={node.isHead ? 7 : 5} style={{ stroke: node.color, fill: node.isHead ? node.color : 'var(--bg-base)' }} />)}
        </svg>
        <ol className="commit-list">{nodes.map(node => {
          const labels = node.refNames
          const changed = previous && (!previous.commits.some(c => c.id === node.id) || (node.id === state.head && previous.head !== state.head) || previous.refs.filter(r => r.endsWith(` ${node.id}`)).join() !== state.refs.filter(r => r.endsWith(` ${node.id}`)).join())
          return <li key={node.key} className={changed ? 'git-change' : ''} style={{ left: node.x, top: node.y, '--branch-color': node.color }}>
            <div className="commit-labels">{node.isHead && <span className="ref-label head-label">HEAD</span>}{labels.map(label => <span title={label} className="ref-label" style={{ color: branchColors[label] ?? 'var(--warning)' }} key={label}>{label}</span>)}{historicalLabels.filter(label => label.id === node.id && !node.repeated).map(label => <span className="ref-label historical-ref" key={`history-${label.name}`} style={{ color: label.color }} title="Ранее наблюдавшийся указатель ветки">{label.name} · история</span>)}</div>
            <code title={node.repeated ? `${node.id} · тот же коммит на принимающей ветке` : node.id}>{node.id.slice(0, 8)}</code>
            {node.repeated && <span className="commit-detail">Продолжение ветки</span>}
            {!state.commits.some(commit => commit.id === node.id) && <span className="commit-detail">В истории наблюдений</span>}
            {node.parents.length > 1 && <span className="commit-detail">Слияние</span>}
          </li>
        })}</ol>
      </div>
      </div>
    </div>
    {state.history_truncated && <p className="history-note">Показаны последние {state.history_limit} коммитов · более ранняя история за пределами снимка</p>}
    {state.is_shallow && <p className="history-note">Неполная история Git · репозиторий клонирован с ограничением глубины</p>}
    {outside.length > 0 && <p className="history-note">Вне истории: {outside.map(r => `${r.name} → ${r.id.slice(0, 8)}`).join(', ')}</p>}
  </>
}
// Показать статусы файлов выбранного столбца с подсветкой изменений
function Files({ files, column, previous }) {
  const items = files.filter(f => f.conflict || (f[column] !== ' ' && f[column] !== '!' && (column !== 'index' || f[column] !== '?')))
  if (!items.length) return <Empty>{column === 'index' ? 'Подготовленных изменений нет' : 'Рабочая папка без изменений'}</Empty>
  return <ul className="git-files">{items.map(file => {
    const old = previous?.files.find(f => f.path === file.path)
    const changed = previous && (!old || old[column] !== file[column] || old.conflict !== file.conflict || old.original_path !== file.original_path)
    return <li key={file.path} className={`${file.conflict ? 'file-conflict' : ''} ${changed ? 'git-change' : ''}`}>
      <span className="file-status">{file.conflict ? 'Конфликт' : statuses[file[column]]}</span>
      <code title={file.original_path ? `${file.original_path} → ${file.path}` : file.path}>{file.original_path && <><span className="original-path">{file.original_path}</span> → </>}{file.path}</code>
    </li>
  })}</ul>
}
// Показать рабочую папку и индекс из отдельного оперативного канала
function WorkingFiles({ worktree }) {
  const state = worktree?.data?.state
  const memory = useRef(null)
  const previous = memory.current?.kind === 'repository' && memory.current.path === state?.path ? memory.current : null
  useLayoutEffect(() => { memory.current = state }, [state])
  const repository = state?.kind === 'repository'
  const empty = !state ? 'Ожидаем данные файлов от CLI' : state.kind === 'no_repository' ? 'В выбранной папке нет репозитория Git' : 'Не удалось прочитать рабочую папку'
  return <>
    {worktree?.error && <p className="snapshot-warning">Не удалось обновить файлы · показаны последние полученные данные</p>}
    <div className="git-file-flow">
      <Panel icon={Folder} title="Рабочая папка" detail="Working directory" type="files">{repository ? <Files files={state.files} column="worktree" previous={previous} /> : <Empty>{empty}</Empty>}</Panel>
      <ChevronRight className="staging-chevron" size={28} strokeWidth={1.5} aria-hidden="true" />
      <Panel icon={Layers} title="Индекс" detail="Staging area" type="index">{repository ? <Files files={state.files} column="index" previous={previous} /> : <Empty>{empty}</Empty>}</Panel>
    </div>
  </>
}

// Объединить граф и файловые панели с анимацией изменений снимка
export function GitRepository({ snapshot, history, worktree, graphExpanded, onToggleGraph }) {
  const current = snapshot?.state
  const memory = useRef({ snapshot: null, previous: null })
  if (memory.current.snapshot !== snapshot) {
    const old = memory.current.snapshot?.state
    memory.current = { snapshot, previous: old?.kind === 'repository' && old.path === current?.path ? old : null }
  }
  const root = useRef(null)
  useLayoutEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    const animations = [...(root.current?.querySelectorAll('.git-change') ?? [])].map(element =>
      element.animate([{ backgroundColor: getComputedStyle(element).getPropertyValue('--change-highlight').trim() }, { backgroundColor: 'transparent' }], { duration: parseFloat(getComputedStyle(element).getPropertyValue('--motion-change')) || 650, easing: 'ease-out' }))
    return () => animations.forEach(animation => animation.cancel())
  }, [snapshot, worktree?.data])
  const files = worktree?.data?.state?.files
  const conflicts = files?.filter(file => file.conflict).length ?? 0
  const previous = memory.current.previous
  const repository = current?.kind === 'repository'
  const empty = !current ? 'Запусти devlab и выбери папку' : current.kind === 'no_repository' ? 'В выбранной папке нет репозитория Git · выполни git init' : 'Не удалось прочитать Git · ожидаем обновление'
  return <div ref={root} className="git-repository">
    {repository && <div className="git-summary"><span><GitBranch size={15} />{current.head_kind === 'detached' ? `Detached HEAD · ${current.head.slice(0, 8)}` : current.branch}</span><span>{current.head_kind === 'unborn' ? 'Ветка без коммитов' : commitCount(current.commits.length)}</span>{current.operations.map(operation => <span className="operation" key={operation}>{operation}</span>)}</div>}
    <Panel icon={GitCommitHorizontal} title="История репозитория" detail="Коммиты, ветки и HEAD" type="history" actions={<button type="button" className="repository-action" onClick={onToggleGraph} aria-pressed={graphExpanded} title={graphExpanded ? 'Вернуть панели (Esc)' : 'Развернуть граф на рабочую область'}>{graphExpanded ? <Minimize2 size={15} /> : <Maximize2 size={15} />}{graphExpanded ? 'Вернуть панели' : 'Развернуть граф'}</button>}>{repository ? <History key={`${snapshot.session_id}:${current.path}`} state={current} previous={previous} history={history} /> : <Empty>{empty}</Empty>}</Panel>
    <details className="worktree-drawer" open>
      <summary>
        <span><Folder size={16} />Файлы и индекс</span>
        <span className="worktree-summary">{worktree?.error ? 'Не удалось обновить файлы' : files ? `Изменений: ${files.length}` : 'Ожидаем данные CLI'}</span>
        {conflicts > 0 && <span className="operation">Конфликтов: {conflicts}</span>}
        <ChevronDown size={16} className="drawer-chevron" aria-hidden="true" />
      </summary>
      <WorkingFiles worktree={worktree} />
    </details>
  </div>
}
