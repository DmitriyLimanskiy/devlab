import { useEffect, useState } from 'react'
import { GitRepository } from '../../practice/git/GitRepository'
import { useWorktree } from '../../practice/git/useWorktree'
import { usePracticeState } from '../../practice/git/usePracticeState'
import { GitBranch, Terminal, FolderOpen, ChevronDown, ChevronUp, BookOpen } from 'lucide-react'
import { Status } from '../../shared/ui'

// Убрать завершающие точки из текстовых подписей интерфейса
const withoutFinalPeriod = text => text.replace(/\.+\s*$/, '')

// Показать текстовые блоки и команды выбранного шага
function StepContent({ content }) {
  const blocks = content.blocks ?? []
  if (!blocks.length) return <p>Описание шага пока не добавлено</p>
  return <div className="step-blocks">{blocks.map((block, index) => {
    if (block.type === 'text') return <p key={index}>{withoutFinalPeriod(block.text)}</p>
    if (block.type === 'code') return <pre key={index}><code>{block.text}</code></pre>
    return <p key={index}>Этот тип содержимого пока не поддерживается</p>
  })}</div>
}

// Показать свёрнутую полосу описания с возможностью раскрыть содержимое
function StepDescription({ step }) {
  const [expanded, setExpanded] = useState(false)
  return <section className="step-description" aria-labelledby="step-description-title">
    <header className="step-description-heading">
      <h2 id="step-description-title"><BookOpen size={17} /><span title={step?.title}>{step ? withoutFinalPeriod(step.title) : 'Описание шага'}</span></h2>
      <button type="button" className="step-description-toggle" aria-expanded={expanded} aria-controls="step-description-content" onClick={() => setExpanded(value => !value)}>
        {expanded ? 'Свернуть' : 'Развернуть'}{expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
      </button>
    </header>
    <div id="step-description-content" className="step-description-viewport expanded" hidden={!expanded} tabIndex={expanded ? 0 : undefined}>
      <div className="step-description-content">
        {step ? <StepContent content={step.content} /> : <p>Шаги курса пока не добавлены</p>}
      </div>
    </div>
  </section>
}

// Собрать шаги курса и живое состояние выбранной практической сессии
export function GitCourse({ title, steps, sessionId }) {
  const [selectedStepId, setSelectedStepId] = useState(steps[0]?.id ?? null)
  const [graphExpanded, setGraphExpanded] = useState(false)
  useEffect(() => {
    if (!graphExpanded) return
    // Escape возвращает обычную компоновку из режима просмотра графа
    const exitGraph = event => { if (event.key === 'Escape') setGraphExpanded(false) }
    window.addEventListener('keydown', exitGraph)
    return () => window.removeEventListener('keydown', exitGraph)
  }, [graphExpanded])
  const selectedStep = steps.find(step => step.id === selectedStepId) ?? steps[0]
  const live = usePracticeState(sessionId)
  const worktree = useWorktree(sessionId)
  const snapshot = live.data?.snapshot
  const connected = !live.error && live.data?.status === 'active' && live.data?.cli_connected
  const status = live.error ? (worktree.data && !worktree.error ? 'Файлы доступны · история графа недоступна' : 'Нет связи с сервером') : connected ? 'CLI подключен' : live.data ? 'CLI не подключен' : 'Подключение…'
  return <section className={`git-course ${graphExpanded ? 'graph-expanded' : ''}`} aria-label={title}>
    <div className="git-layout">
      <aside className="practice-panel" id="course-practice-panel" aria-label="Начало работы" hidden={graphExpanded}>
        <h2><Terminal size={18} />Локальная практика</h2>

        {steps.length ? <ol className="practice-steps">
          {steps.map(step => <li key={step.id} value={step.position}>
            <button type="button" className="practice-step" aria-pressed={selectedStep?.id === step.id} aria-controls="step-description-content" onClick={() => setSelectedStepId(step.id)}>
              <span className="practice-step-number" aria-hidden="true">{step.position}</span>
              <span className="practice-step-title">{withoutFinalPeriod(step.title)}</span>
            </button>
          </li>)}
        </ol> : <p className="steps-empty">Шаги курса пока не добавлены</p>}
        <p className="practice-footer">Выход из CLI: <code>exit</code> или <code>Ctrl+D</code></p>
      </aside>
      <div className="repository-workspace">
        {!graphExpanded && <StepDescription key={selectedStep?.id} step={selectedStep} />}
        <div className="repository-toolbar">
          <span><GitBranch size={17} />Репозиторий</span>
          <div className="repository-toolbar-actions">
            <Status active={connected}>{status}</Status>
          </div>
        </div>
        <div className="directory-info"><span><FolderOpen size={16} />Рабочая директория</span><code title={worktree.data?.state?.path ?? snapshot?.state.path}>{worktree.data?.state?.path ?? snapshot?.state.path ?? 'Выбери папку в CLI'}</code></div>
        {live.data?.status === 'closed' && <p className="snapshot-warning">Сессия закрыта</p>}
        <GitRepository snapshot={snapshot} history={live.data?.history} worktree={worktree} graphExpanded={graphExpanded} onToggleGraph={() => setGraphExpanded(value => !value)} />
      </div>
    </div>
  </section>
}
