import { useLayoutEffect, useRef } from 'react'
import { GitBranch, GitCommitHorizontal, Folder, Layers, CircleDashed, ChevronRight } from 'lucide-react'
import { commitCount, graphLayout } from './practiceState'

const statuses = { M: 'Изменён', A: 'Добавлен', D: 'Удалён', R: 'Переименован', C: 'Скопирован', U: 'Конфликт', '?': 'Не отслеживается', '!': 'Игнорируется', T: 'Изменён тип', X: 'Неизвестный статус' }
function Empty({ children }) { return <div className="repo-empty"><CircleDashed size={24} strokeWidth={1.3} /><p>{children}</p></div> }
function Panel({ icon: Icon, title, detail, type, children }) {
  return <section className={`repo-panel repo-panel-${type}`}><header><h2><Icon size={17} />{title}</h2><span>{detail}</span></header>{children}</section>
}
function History({ state, previous }) {
  if (!state.commits.length) return <Empty>Пока нет коммитов · HEAD → {state.branch ?? '—'}</Empty>
  const { nodes, positions, width, height, branchColors } = graphLayout(state.commits, state.refs, state.head)
  const refs = state.refs.map(ref => { const split = ref.lastIndexOf(' '); return { name: ref.slice(0, split).replace('refs/heads/', '').replace('refs/tags/', 'tag: '), id: ref.slice(split + 1) } })
  const outside = refs.filter(ref => !positions.has(ref.id))
  const byId = new Map(nodes.map(n => [n.id, n]))
  return <>
    <div className="history-scroll" role="region" aria-label="Граф коммитов от старых слева к новым справа" tabIndex={0}>
      <div className="commit-history" style={{ width, height }}>
        <svg width={width} height={height} aria-hidden="true" className="commit-graph">
          {nodes.flatMap(node => node.parents.map((parent, index) => {
            const source = byId.get(parent)
            const color = index > 0 && source ? source.color : node.color
            return <path key={`${parent}-${node.id}`} style={{ stroke: color }} className={source ? '' : 'graph-boundary'} d={source ? `M${source.x},${source.y} C${source.x + 80},${source.y} ${node.x - 80},${node.y} ${node.x},${node.y}` : `M${node.x - 42},${node.y} H${node.x}`} />
          }))}
          {nodes.map(node => <circle key={node.id} cx={node.x} cy={node.y} r={node.id === state.head ? 7 : 5} style={{ stroke: node.color, fill: node.id === state.head ? node.color : 'var(--bg-base)' }} />)}
        </svg>
        <ol className="commit-list">{nodes.map(node => {
          const labels = refs.filter(ref => ref.id === node.id).map(ref => ref.name)
          const changed = previous && (!previous.commits.some(c => c.id === node.id) || (node.id === state.head && previous.head !== state.head) || previous.refs.filter(r => r.endsWith(` ${node.id}`)).join() !== state.refs.filter(r => r.endsWith(` ${node.id}`)).join())
          return <li key={node.id} className={changed ? 'git-change' : ''} style={{ left: node.x, top: node.y, '--branch-color': node.color }}>
            <div className="commit-labels">{node.id === state.head && <span className="ref-label head-label">HEAD</span>}{labels.map(label => <span title={label} className="ref-label" style={{ color: branchColors[label] ?? 'var(--warning)' }} key={label}>{label}</span>)}</div>
            <code title={node.id}>{node.id.slice(0, 8)}</code>
            {node.parents.length > 1 && <span className="commit-detail">Слияние</span>}
          </li>
        })}</ol>
      </div>
    </div>
    {outside.length > 0 && <p className="history-note">Вне истории: {outside.map(r => `${r.name} → ${r.id.slice(0, 8)}`).join(', ')}</p>}
  </>
}
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
export function GitRepository({ snapshot }) {
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
  }, [snapshot])
  const previous = memory.current.previous
  const repository = current?.kind === 'repository'
  const empty = !current ? 'Запусти devlab и выбери папку' : current.kind === 'no_repository' ? 'В выбранной папке нет репозитория Git · выполни git init' : 'Не удалось прочитать Git · ожидаем обновление'
  return <div ref={root} className="git-repository">
    {repository && <div className="git-summary"><span><GitBranch size={15} />{current.head_kind === 'detached' ? `Detached HEAD · ${current.head.slice(0, 8)}` : current.branch}</span><span>{current.head_kind === 'unborn' ? 'Ветка без коммитов' : commitCount(current.commits.length)}</span>{current.operations.map(operation => <span className="operation" key={operation}>{operation}</span>)}</div>}
    <Panel icon={GitCommitHorizontal} title="История репозитория" detail="Коммиты, ветки и HEAD" type="history">{repository ? <History state={current} previous={previous} /> : <Empty>{empty}</Empty>}</Panel>
    <div className="git-file-flow">
      <Panel icon={Folder} title="Рабочая папка" detail="Working directory" type="files">{repository ? <Files files={current.files} column="worktree" previous={previous} /> : <Empty>Нет данных рабочих файлов</Empty>}</Panel>
      <ChevronRight className="staging-chevron" size={28} strokeWidth={1.5} aria-hidden="true" />
      <Panel icon={Layers} title="Индекс" detail="Staging area" type="index">{repository ? <Files files={current.files} column="index" previous={previous} /> : <Empty>Нет данных индекса</Empty>}</Panel>
    </div>
  </div>
}
