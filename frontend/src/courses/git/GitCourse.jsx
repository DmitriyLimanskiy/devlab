import { useLayoutEffect, useRef, useState } from 'react'
import { GitRepository } from '../../practice/git/GitRepository'
import { useWorktree } from '../../practice/git/useWorktree'
import { usePracticeState } from '../../practice/git/usePracticeState'
import { GitBranch, Terminal, FolderOpen, ChevronDown, ChevronUp, BookOpen } from 'lucide-react'
import { Status } from '../../shared/ui'

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

function StepDescription({ step }) {
  const contentRef = useRef(null)
  const [expanded, setExpanded] = useState(false)
  const [expandedHeight, setExpandedHeight] = useState(112)
  const [overflowing, setOverflowing] = useState(false)

  useLayoutEffect(() => {
    const content = contentRef.current
    const observer = new ResizeObserver(() => setOverflowing(content.scrollHeight > 112))
    observer.observe(content)
    return () => observer.disconnect()
  }, [step])

  function toggleExpanded() {
    if (!expanded) setExpandedHeight(Math.min(360, Math.max(112, contentRef.current.scrollHeight)))
    setExpanded(value => !value)
  }

  return <section className="step-description" aria-labelledby="step-description-title">
    <header className="step-description-heading">
      <h2 id="step-description-title"><BookOpen size={17} /><span title={step?.title}>{step ? withoutFinalPeriod(step.title) : 'Описание шага'}</span></h2>
      <button type="button" className="step-description-toggle" style={{ visibility: overflowing || expanded ? 'visible' : 'hidden' }} disabled={!overflowing && !expanded} aria-expanded={expanded} aria-controls="step-description-content" onClick={toggleExpanded}>
        {expanded ? 'Свернуть' : 'Развернуть'}{expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
      </button>
    </header>
    <div id="step-description-content" className={`step-description-viewport ${expanded ? 'expanded' : ''} ${overflowing && !expanded ? 'has-overflow' : ''}`} style={{ height: expanded ? expandedHeight : 112 }} tabIndex={expanded ? 0 : undefined}>
      <div ref={contentRef} className="step-description-content">
        {step ? <StepContent content={step.content} /> : <p>Шаги курса пока не добавлены</p>}
      </div>
    </div>
  </section>
}

export function GitCourse({ title, steps, sessionId }) {
  const [selectedStepId, setSelectedStepId] = useState(steps[0]?.id ?? null)
  const selectedStep = steps.find(step => step.id === selectedStepId) ?? steps[0]
  const live = usePracticeState(sessionId)
  const worktree = useWorktree(sessionId)
  const snapshot = live.data?.snapshot
  const connected = !live.error && live.data?.status === 'active' && live.data?.cli_connected
  const status = live.error ? (worktree.data && !worktree.error ? 'Файлы доступны · история графа недоступна' : 'Нет связи с сервером') : connected ? 'CLI подключен' : live.data ? 'CLI не подключен' : 'Подключение…'
  return <section className="git-course" aria-label={title}>
    <div className="git-layout">
      <aside className="practice-panel" aria-label="Начало работы">
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
        <StepDescription step={selectedStep} />
        <div className="repository-toolbar"><span><GitBranch size={17} />Репозиторий</span><Status active={connected}>{status}</Status></div>
        <div className="directory-info"><span><FolderOpen size={16} />Рабочая директория</span><code>{worktree.data?.state?.path ?? snapshot?.state.path ?? 'Выбери папку в CLI'}</code></div>
        {live.data?.status === 'closed' && <p className="snapshot-warning">Сессия закрыта</p>}
        <GitRepository snapshot={snapshot} history={live.data?.history} worktree={worktree} />
      </div>
    </div>
  </section>
}
