import { ArrowLeft, GitBranch, GitCommitHorizontal, Terminal, Folder, Layers, CircleDashed } from 'lucide-react'
import { pages } from './routes'
import { Badge, Status } from './ui'

const areas = [
  { icon: GitCommitHorizontal, title: 'История репозитория', detail: 'Коммиты, ветки и HEAD', text: 'Граф появится после подключения передачи состояния из CLI.' },
  { icon: Layers, title: 'Индекс', detail: 'Staging area', text: 'Данные о подготовленных изменениях пока не поступают.' },
  { icon: Folder, title: 'Рабочая папка', detail: 'Working directory', text: 'Данные о рабочих файлах пока не поступают.' },
]

function StepContent({ content }) {
  const blocks = content.blocks ?? []
  if (!blocks.length) return <p>Описание шага пока не добавлено.</p>
  return <div className="step-blocks">{blocks.map((block, index) => {
    if (block.type === 'text') return <p key={index}>{block.text}</p>
    if (block.type === 'code') return <pre key={index}><code>{block.text}</code></pre>
    return <p key={index}>Этот тип содержимого пока не поддерживается.</p>
  })}</div>
}

export function GitCourse({ steps, sessionId, generation }) {
  return <section className="git-course" aria-labelledby="git-title">
    <a className="back-link" href={pages.catalog}><ArrowLeft size={15} />Каталог курсов</a>
    <header className="course-heading">
      <div><h1 id="git-title"><span className="accent">Git</span> · Песочница</h1><p>Локальная практика и состояние репозитория.</p></div>
      <Badge>В разработке</Badge>
    </header>
    <div className="git-layout">
      <aside className="practice-panel" aria-label="Начало работы">
        <h2><Terminal size={18} />Локальная практика</h2>

        {steps.length ? <ol className="practice-steps">
          {steps.map(step => <li key={step.id} value={step.position}>
            <span aria-hidden="true">{step.position}</span>
            <div className="step-body"><strong>{step.title}</strong><StepContent content={step.content} /></div>
          </li>)}
        </ol> : <p className="steps-empty">Шаги курса пока не добавлены.</p>}
        <div className="practice-note"><code>state.json</code><p>Локальный снимок · передача на сервер пока недоступна.</p></div>
        <div className="practice-session" aria-label="Сессия практики">
          <span>Сессия практики</span><code>{sessionId}</code>
          <p>{generation === 0 ? 'CLI ещё не подключался.' : `Поколение подключения: ${generation}`}</p>
        </div>
        <p className="practice-footer">Выход из CLI: <code>exit</code> или <code>Ctrl+D</code>.</p>
      </aside>
      <div className="repository-workspace">
        <div className="repository-toolbar"><span><GitBranch size={17} />Репозиторий</span><Status>Нет данных CLI</Status></div>
        <div className="terminal-preview"><span className="terminal-label"><Terminal size={14} />Локальная оболочка</span><code><span className="accent">$</span> devlab</code><p>Команды выполняются в терминале на твоём компьютере.</p></div>
        {areas.map(({ icon: Icon, title, detail, text }) => <section className={`repo-panel repo-panel-${title === 'История репозитория' ? 'history' : title === 'Индекс' ? 'index' : 'files'}`} key={title}>
          <header><h2><Icon size={17} />{title}</h2><span>{detail}</span></header>
          <div className="repo-empty"><CircleDashed size={24} strokeWidth={1.3} /><p>{text}</p></div>
        </section>)}
      </div>
    </div>
  </section>
}
