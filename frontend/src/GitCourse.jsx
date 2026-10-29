import { ArrowLeft, GitBranch, GitCommitHorizontal, Terminal, Folder, Layers, CircleDashed } from 'lucide-react'
import { pages } from './routes'
import { Badge, Status } from './ui'

const areas = [
  { icon: GitCommitHorizontal, title: 'История репозитория', detail: 'Коммиты, ветки и HEAD', text: 'Граф появится после подключения передачи состояния из CLI.' },
  { icon: Layers, title: 'Индекс', detail: 'Staging area', text: 'Данные о подготовленных изменениях пока не поступают.' },
  { icon: Folder, title: 'Рабочая папка', detail: 'Working directory', text: 'Данные о рабочих файлах пока не поступают.' },
]

export function GitCourse() {
  return <section className="git-course" aria-labelledby="git-title">
    <a className="back-link" href={pages.catalog}><ArrowLeft size={15} />Каталог курсов</a>
    <header className="course-heading">
      <div><h1 id="git-title"><span className="accent">Git</span> · Песочница</h1><p>Локальная практика и состояние репозитория.</p></div>
      <Badge>В разработке</Badge>
    </header>
    <div className="git-layout">
      <aside className="practice-panel" aria-label="Начало работы">
        <h2><Terminal size={18} />Локальная практика</h2>

        <ol className="practice-steps">
          <li><span>1</span><div><strong>Запусти CLI</strong><code>devlab</code></div></li>
          <li><span>2</span><div><strong>Выбери папку</strong><p>Или создай репозиторий.</p></div></li>
          <li><span>3</span><div><strong>Работай в bash</strong><p>Обычные команды Git.</p></div></li>
        </ol>
        <div className="practice-note"><code>state.json</code><p>Локальный снимок · передача на сервер пока недоступна.</p></div>
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
