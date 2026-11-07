import React, { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { FlaskConical, PanelLeftClose, PanelLeftOpen, BookOpen, ArrowRight, GitBranch } from 'lucide-react'
import { GitCourse } from './courses/git/GitCourse'
import { parseGitCourse } from './courses/git/courseSteps'
import { IconButton, Badge } from './shared/ui'
import { pages, api, gitCoursePage } from './routes'
import { parseCatalog, courseStatusLabels } from './catalog/catalog'
import './tokens.css'
import './styles.css'

const navigation = [
  { path: pages.catalog, label: 'Курсы', icon: BookOpen },
  { path: pages.git, label: 'Git', icon: FlaskConical },
]

// Вернуть ответ API без дополнительного преобразования
const identity = data => data

// Загрузить и проверить данные API с отменой запроса и возможностью повтора
function useApi(path, parse = identity, method = 'GET', body = null) {
  const [state, setState] = useState({ loading: true, data: null, error: false })
  const [attempt, setAttempt] = useState(0)
  useEffect(() => {
    const controller = new AbortController()
    setState({ loading: true, data: null, error: false })
    fetch(path, {
      method,
      signal: controller.signal,
      ...(body !== null ? { headers: { 'Content-Type': 'application/json' }, body } : {}),
    })
      .then(response => {
        if (!response.ok) throw new Error('Request failed')
        return response.json()
      })
      .then(parse)
      .then(data => {
        if (!controller.signal.aborted) setState({ loading: false, data, error: false })
      })
      .catch(error => {
        if (error.name !== 'AbortError') setState({ loading: false, data: null, error: true })
      })
    return () => controller.abort()
  }, [path, attempt, parse, method, body])
  return { ...state, retry: () => setAttempt(value => value + 1) }
}

// Показать загрузку, панель ошибки или содержимое успешного ответа
function ApiState({ state, children }) {
  if (state.loading) return <p role="status">Загрузка…</p>
  if (state.error) return <div className="api-error">
    <div className="api-error-panel" role="alert">
      <p>Не удалось загрузить данные</p>
      <button type="button" className="api-error-retry" onClick={state.retry}>Попробовать снова</button>
    </div>
  </div>
  return children(state.data)
}

// Открыть сессию выбранного курса и передать её данные странице Git
function GitPractice({ course }) {
  const state = useApi(api.git, parseGitCourse, 'POST', JSON.stringify({ course_slug: course.id }))
  return <ApiState state={state}>{practice => <GitCourse title={course.title} steps={practice.steps} sessionId={practice.session_id} />}</ApiState>
}

// Показать вкладки Git-курсов и синхронизировать выбранный курс с URL
function GitTabs({ courses }) {
  const requested = new URLSearchParams(window.location.search).get('course')
  const [selected, setSelected] = useState(requested)
  const course = courses.find(item => item.id === selected) ?? courses[0]
  if (!course) return <p>Курсы Git пока не добавлены</p>
  // Выбрать курс и обновить адрес страницы без перезагрузки
  function selectCourse(slug) {
    setSelected(slug)
    window.history.replaceState(null, '', gitCoursePage(slug))
  }
  // Обеспечить переключение вкладок курса с клавиатуры
  function handleTabKey(event, index) {
    let next
    if (event.key === 'ArrowRight') next = (index + 1) % courses.length
    else if (event.key === 'ArrowLeft') next = (index + courses.length - 1) % courses.length
    else if (event.key === 'Home') next = 0
    else if (event.key === 'End') next = courses.length - 1
    else return
    event.preventDefault()
    selectCourse(courses[next].id)
    document.getElementById(`git-tab-${courses[next].id}`)?.focus()
  }
  return <div className="git-page">
    <div className="course-tabs" role="tablist" aria-label="Курсы Git">
      {courses.map((item, index) => <button key={item.id} id={`git-tab-${item.id}`} type="button" role="tab" aria-selected={course.id === item.id} aria-controls="git-course-panel" tabIndex={course.id === item.id ? 0 : -1} onClick={() => selectCourse(item.id)} onKeyDown={event => handleTabKey(event, index)}>
        {item.title}
      </button>)}
    </div>
    <div className="git-course-panel" id="git-course-panel" role="tabpanel" aria-labelledby={`git-tab-${course.id}`} tabIndex={0}>
      <GitPractice key={course.id} course={course} />
    </div>
  </div>
}

// Загрузить список Git-курсов для вкладок страницы
function GitPage() {
  const state = useApi(api.git, parseCatalog)
  return <ApiState state={state}>{courses => <GitTabs courses={courses} />}</ApiState>
}

// Показать каталог направлений и переходы к доступным курсам
function Catalog() {
  const state = useApi(api.catalog, parseCatalog)
  return <section className="catalog" aria-labelledby="catalog-title">
    <header className="catalog-heading"><div><h1 id="catalog-title">Курсы</h1><p>Технологии и инструменты для практики</p></div>
      {!state.loading && !state.error && <span className="catalog-count">Всего: {state.data.length}</span>}
    </header>
    <ApiState state={state}>{catalog => catalog.length ? <ul className="course-list">
      {catalog.map(course => <li className="course" key={course.id}>
        <div className="course-card-heading"><GitBranch className="course-icon" size={22} /><Badge>{courseStatusLabels[course.status]}</Badge></div>
        <div className={`course-diagram ${course.id.startsWith('git-') ? '' : 'course-diagram-general'}`} aria-hidden="true"><span className="diagram-track diagram-main" /><span className="diagram-track diagram-branch" /><i /><i /><i /><i /><i /></div>
        <div className="course-card-content"><h2>{course.title}</h2><p>{course.description.replace(/\.+\s*$/, '')}</p></div>
        {course.id.startsWith('git-') && <a className="course-open" href={gitCoursePage(course.id)} aria-label={`Открыть курс ${course.title}`}>Открыть курс<ArrowRight size={16} /></a>}
      </li>)}
    </ul> : <p>Курсы пока не добавлены</p>}</ApiState>
  </section>
}

// Нарисовать декоративный знак терминала в боковом меню
function TerminalMark() {
  return <span className="sidebar-terminal" aria-hidden="true">&gt;_</span>
}

// Собрать оболочку приложения, навигацию и выбранную страницу
function App() {
  const [sidebarOpen, setSidebarOpen] = useState(() => !window.matchMedia('(max-width: 480px)').matches)
  const requestedPath = window.location.pathname.replace(/\/$/, '') || '/'
  const path = requestedPath === '/' ? pages.catalog : requestedPath
  useEffect(() => {
    if (path !== requestedPath) window.history.replaceState(null, '', path + window.location.search + window.location.hash)
  }, [path, requestedPath])
  const page = navigation.find(item => item.path === path)
  useEffect(() => { document.title = `${page?.label ?? 'Страница не найдена'} — DevLab` }, [page])
  return <div className={`workbench ${sidebarOpen ? '' : 'sidebar-collapsed'}`}>
    <header className="titlebar"><a className="brand" href={pages.catalog} aria-label="DevLab — каталог курсов"><FlaskConical size={21} /><span>Dev<span className="accent">Lab</span></span></a><span className="titlebar-caption">Практика на настоящих инструментах</span></header>
    <aside className="sidebar">
      <div className="sidebar-header">
        {sidebarOpen && <span>Рабочее пространство</span>}
        <IconButton label={sidebarOpen ? 'Свернуть рабочее пространство' : 'Развернуть рабочее пространство'} aria-expanded={sidebarOpen} aria-controls="workspace-navigation" onClick={() => setSidebarOpen(value => !value)}>
          {sidebarOpen ? <PanelLeftClose size={18} /> : <PanelLeftOpen size={18} />}
        </IconButton>
      </div>
      <nav id="workspace-navigation" aria-label="Рабочее пространство">
        {navigation.map(({ path: href, label, icon: Icon }) => <a key={href} href={href} className={`nav-item ${path === href ? 'selected' : ''}`} aria-current={path === href ? 'page' : undefined} aria-label={label} title={sidebarOpen ? undefined : label}><Icon size={18} />{sidebarOpen && <span>{label}</span>}</a>)}
      </nav>
      {sidebarOpen && <div className="sidebar-note"><TerminalMark /><p>Изучай инструмент<br />через практику</p></div>}
    </aside>
    <main className="editor">
      <div className={`canvas ${path === pages.git ? 'canvas-git' : path === pages.catalog ? 'canvas-catalog' : ''}`}>
        {path === pages.catalog ? <Catalog /> : path === pages.git ? <GitPage /> : <section className="welcome"><h1>Страница не найдена</h1><a className="primary-link" href={pages.catalog}>К каталогу<ArrowRight size={16} /></a></section>}
      </div>
    </main>
  </div>
}

createRoot(document.getElementById('root')).render(<React.StrictMode><App /></React.StrictMode>)
