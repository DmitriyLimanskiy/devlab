import { useLayoutEffect, useRef } from 'react'
import { GitBranch, GitCommitHorizontal, Folder, Layers, CircleDashed, ChevronRight } from 'lucide-react'
import { commitCount, repositoryGraph, graphRefs, graphConnections } from './practiceState'

const statuses = { M: 'Изменён', A: 'Добавлен', D: 'Удалён', R: 'Переименован', C: 'Скопирован', U: 'Конфликт', '?': 'Не отслеживается', '!': 'Игнорируется', T: 'Изменён тип', X: 'Неизвестный статус' }
// Показать пояснение об отсутствии данных в панели репозитория
function Empty({ children }) { return <div className="repo-empty"><CircleDashed size={24} strokeWidth={1.3} /><p>{children}</p></div> }
// Оформить панель репозитория с заголовком и дополнительной подписью
function Panel({ icon: Icon, title, detail, type, children }) {
  return <section className={`repo-panel repo-panel-${type}`}><header><h2><Icon size={17} />{title}</h2><span>{detail}</span></header>{children}</section>
}
// Показать граф коммитов, refs и признаки ограниченной истории
function History({ state, previous, history }) {
  const graph = repositoryGraph(state, history)
  if (!graph.nodes.length) return <Empty>Пока нет коммитов · HEAD → {state.branch ?? '—'}</Empty>
  const { nodes, positions, width, height, branchColors, historicalLabels } = graph
  const refs = graphRefs(state)
  const outside = refs.filter(ref => !positions.has(ref.id))
  const connections = graphConnections(graph)
  return <>
    <div className="history-scroll" role="region" aria-label="Граф коммитов от старых слева к новым справа" tabIndex={0}>
      <div className="commit-history" style={{ width, height }}>
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
      <code>{file.original_path && <><span className="original-path">{file.original_path}</span> → </>}{file.path}</code>
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
export function GitRepository({ snapshot, history, worktree }) {
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
  const previous = memory.current.previous
  const repository = current?.kind === 'repository'
  const empty = !current ? 'Запусти devlab и выбери папку' : current.kind === 'no_repository' ? 'В выбранной папке нет репозитория Git · выполни git init' : 'Не удалось прочитать Git · ожидаем обновление'
  return <div ref={root} className="git-repository">
    {repository && <div className="git-summary"><span><GitBranch size={15} />{current.head_kind === 'detached' ? `Detached HEAD · ${current.head.slice(0, 8)}` : current.branch}</span><span>{current.head_kind === 'unborn' ? 'Ветка без коммитов' : commitCount(current.commits.length)}</span>{current.operations.map(operation => <span className="operation" key={operation}>{operation}</span>)}</div>}
    <Panel icon={GitCommitHorizontal} title="История репозитория" detail="Коммиты, ветки и HEAD" type="history">{repository ? <History key={`${snapshot.session_id}:${current.path}`} state={current} previous={previous} history={history} /> : <Empty>{empty}</Empty>}</Panel>
    <WorkingFiles worktree={worktree} />
  </div>
}
