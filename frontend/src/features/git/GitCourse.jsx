import { useEffect, useRef } from 'react'
import Markdown from 'react-markdown'
import { useViewState, useRememberedScroll } from './useViewState'
import { GitRepository } from './GitRepository'
import { useWorktree } from './useWorktree'
import { usePracticeState } from './usePracticeState'
import { GitBranch, Terminal, FolderOpen, ChevronDown, BookOpen, X } from 'lucide-react'
import { Status } from '../../shared/ui'

// Убрать завершающие точки из текстовых подписей интерфейса
const withoutFinalPeriod = text => text.replace(/\.+\s*$/, '')

// Показать текстовые блоки и команды выбранного шага
function StepContent({ content }) {
  if (typeof content.markdown === 'string') {
    if (!content.markdown.trim()) return <p>Описание шага пока не добавлено</p>
    return <div className="step-markdown"><Markdown skipHtml>{content.markdown}</Markdown></div>
  }
  const blocks = content.blocks ?? []
  if (!blocks.length) return <p>Описание шага пока не добавлено</p>
  return <div className="step-blocks">{blocks.map((block, index) => {
    if (block.type === 'text') return <p key={index}>{withoutFinalPeriod(block.text)}</p>
    if (block.type === 'code') return <pre key={index}><code>{block.text}</code></pre>
    return <p key={index}>Этот тип содержимого пока не поддерживается</p>
  })}</div>
}

// Развернуть текст в поле репозитория, сохранив доступ к списку шагов
function StepDescription({ step, sessionId }) {
  const [expanded, setExpanded] = useViewState(`${sessionId}:instructions`, false)
  const [fontSize, setFontSize] = useViewState(`${sessionId}:fontSize`, 16)
  const triggerRef = useRef(null)
  const bodyRef = useRef(null)
  useRememberedScroll(`${sessionId}:step:${step?.id}:scroll`, bodyRef, expanded)
  function closeDescription() {
    setExpanded(false)
    triggerRef.current?.focus()
  }
  useEffect(() => {
    if (!expanded) return
    bodyRef.current?.focus({ preventScroll: true })
    const workspace = bodyRef.current.closest('.repository-workspace')
    const covered = [...workspace.children].filter(element => !element.classList.contains('step-description'))
    const previous = covered.map(element => element.inert)
    covered.forEach(element => { element.inert = true })
    const onKeyDown = event => { if (event.key === 'Escape') closeDescription() }
    window.addEventListener('keydown', onKeyDown)
    return () => {
      window.removeEventListener('keydown', onKeyDown)
      covered.forEach((element, index) => { element.inert = previous[index] })
    }
  }, [expanded])
  return <section className="step-description" aria-labelledby="step-description-title">
    <header className="step-description-heading">
      <h2 id="step-description-title"><BookOpen size={17} /><span title={step?.title}>{step ? withoutFinalPeriod(step.title) : 'Описание шага'}</span></h2>
      <button type="button" ref={triggerRef} className="step-description-toggle" tabIndex={expanded ? -1 : undefined} aria-expanded={expanded} aria-controls="step-description-content" onClick={() => setExpanded(true)}>
        Развернуть<ChevronDown size={16} />
      </button>
    </header>
    <section id="step-description-content" className="step-reader" aria-labelledby="step-reader-title" hidden={!expanded} style={{ '--step-reading-font-size': `${fontSize}px` }}>
      <header className="step-reader-heading">
        <h2 id="step-reader-title"><BookOpen size={18} />{step ? withoutFinalPeriod(step.title) : 'Описание шага'}</h2>
        <div className="step-reader-actions">
          <div className="step-font-controls" role="group" aria-label="Размер текста">
            <button type="button" className="repository-action" aria-label="Уменьшить текст" disabled={fontSize <= 14} onClick={() => setFontSize(value => value - 2)}>А−</button>
            <span aria-live="polite">{fontSize} px</span>
            <button type="button" className="repository-action" aria-label="Увеличить текст" disabled={fontSize >= 24} onClick={() => setFontSize(value => value + 2)}>А+</button>
          </div>
          <button type="button" className="repository-action" onClick={closeDescription}><X size={18} />Свернуть</button>
        </div>
      </header>
      <div ref={bodyRef} className="step-description-content step-reader-body" tabIndex={0}>
        {step ? <StepContent content={step.content} /> : <p>Шаги курса пока не добавлены</p>}
      </div>
    </section>
  </section>
}

// Собрать шаги курса и живое состояние выбранной практической сессии
export function GitCourse({ title, steps, sessionId }) {
  const [selectedStepId, setSelectedStepId] = useViewState(`${sessionId}:selectedStep`, steps[0]?.id ?? null)
  const [graphExpanded, setGraphExpanded] = useViewState(`${sessionId}:graphExpanded`, false)
  const stepsRef = useRef(null)
  useRememberedScroll(`${sessionId}:stepsScroll`, stepsRef, !graphExpanded)
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
      <aside ref={stepsRef} className="practice-panel" id="course-practice-panel" aria-label="Начало работы" hidden={graphExpanded}>
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
        {!graphExpanded && <StepDescription step={selectedStep} sessionId={sessionId} />}
        <div className="repository-toolbar">
          <span><GitBranch size={17} />Репозиторий</span>
          <div className="repository-toolbar-actions">
            <Status active={connected}>{status}</Status>
          </div>
        </div>
        <div className="directory-info"><span><FolderOpen size={16} />Рабочая директория</span><code title={worktree.data?.state?.path ?? snapshot?.state.path}>{worktree.data?.state?.path ?? snapshot?.state.path ?? 'Выбери папку в CLI'}</code></div>
        {live.data?.status === 'closed' && <p className="snapshot-warning">Сессия закрыта</p>}
        <GitRepository sessionId={sessionId} snapshot={snapshot} history={live.data?.history} worktree={worktree} graphExpanded={graphExpanded} onToggleGraph={() => setGraphExpanded(value => !value)} />
      </div>
    </div>
  </section>
}
