import { GitRepository } from './GitRepository'
import { usePracticeState } from './usePracticeState'
import { ArrowLeft, GitBranch, Terminal, FolderOpen } from 'lucide-react'
import { pages } from './routes'
import { Badge, Status } from './ui'

const withoutFinalPeriod = text => text.replace(/\.+\s*$/, '')

function StepContent({ content }) {
  const blocks = content.blocks ?? []
  if (!blocks.length) return <p>Описание шага пока не добавлено</p>
  return <div className="step-blocks">{blocks.map((block, index) => {
    if (block.type === 'text') return <p key={index}>{withoutFinalPeriod(block.text)}</p>
    if (block.type === 'code') return <pre key={index}><code>{block.text}</code></pre>
    return <p key={index}>Этот тип содержимого пока не поддерживается</p>
  })}</div>
}

export function GitCourse({ steps, sessionId, generation }) {
  const live = usePracticeState(sessionId)
  const snapshot = live.data?.snapshot
  const currentGeneration = live.data?.generation ?? generation
  const connected = !live.error && live.data?.status === 'active' && live.data?.cli_connected
  const status = live.error ? 'Нет связи с сервером' : connected ? 'CLI подключен' : live.data ? 'CLI не подключен' : 'Подключение…'
  return <section className="git-course" aria-labelledby="git-title">
    <a className="back-link" href={pages.catalog}><ArrowLeft size={15} />Каталог курсов</a>
    <header className="course-heading">
      <div><h1 id="git-title"><span className="accent">Git</span> · Песочница</h1></div>
      <Badge>В разработке</Badge>
    </header>
    <div className="git-layout">
      <aside className="practice-panel" aria-label="Начало работы">
        <h2><Terminal size={18} />Локальная практика</h2>

        {steps.length ? <ol className="practice-steps">
          {steps.map(step => <li key={step.id} value={step.position}>
            <span aria-hidden="true">{step.position}</span>
            <div className="step-body"><strong>{withoutFinalPeriod(step.title)}</strong><StepContent content={step.content} /></div>
          </li>)}
        </ol> : <p className="steps-empty">Шаги курса пока не добавлены</p>}
        <p className="practice-footer">Выход из CLI: <code>exit</code> или <code>Ctrl+D</code></p>
      </aside>
      <div className="repository-workspace">
        <div className="repository-toolbar"><span><GitBranch size={17} />Репозиторий</span><Status active={connected}>{status}</Status></div>
        <div className="directory-info"><span><FolderOpen size={16} />Рабочая директория</span><code>{snapshot?.state.path ?? 'Выбери папку в CLI'}</code></div>
        {snapshot && snapshot.generation < currentGeneration && <p className="snapshot-warning">Ожидаем состояние нового подключения</p>}
        {live.data?.status === 'closed' && <p className="snapshot-warning">Сессия закрыта</p>}
        <GitRepository snapshot={snapshot} />
      </div>
    </div>
  </section>
}
