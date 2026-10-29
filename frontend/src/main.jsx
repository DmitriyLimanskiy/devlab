import React, { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { FlaskConical, PanelLeftClose, PanelLeftOpen, House, BookOpen, ArrowRight } from 'lucide-react'
import { IconButton, Badge } from './ui'
import { pages, api } from './routes'
import './tokens.css'
import './styles.css'

const navigation = [
  { path: pages.home, label: 'Главная', icon: House },
  { path: pages.courses, label: 'Курсы', icon: BookOpen },
]

function useApi(path) {
  const [state, setState] = useState({ loading: true, data: null, error: false })
  const [attempt, setAttempt] = useState(0)
  useEffect(() => {
    const controller = new AbortController()
    setState({ loading: true, data: null, error: false })
    fetch(path, { signal: controller.signal })
      .then(response => {
        if (!response.ok) throw new Error('Request failed')
        return response.json()
      })
      .then(data => setState({ loading: false, data, error: false }))
      .catch(error => {
        if (error.name !== 'AbortError') setState({ loading: false, data: null, error: true })
      })
    return () => controller.abort()
  }, [path, attempt])
  return { ...state, retry: () => setAttempt(value => value + 1) }
}

function ApiState({ state, children }) {
  if (state.loading) return <p role="status">Загрузка…</p>
  if (state.error) return <div role="alert"><p>Не удалось загрузить данные.</p><button className="text-button" onClick={state.retry}>Попробовать снова</button></div>
  return children(state.data)
}

function Home() {
  const state = useApi(api.home)
  return <section className="welcome">
    <FlaskConical className="welcome-mark" size={40} strokeWidth={1.4} />
    <h1>DevLab</h1>
    <ApiState state={state}>{data => <p>{data.description}</p>}</ApiState>
    <a className="primary-link" href={pages.courses}>Перейти к курсам<ArrowRight size={16} /></a>
  </section>
}

function Courses() {
  const state = useApi(api.courses)
  return <section className="courses" aria-labelledby="courses-title">
    <h1 id="courses-title">Курсы</h1>
    <ApiState state={state}>{courses => courses.length ? <ul className="course-list">
      {courses.map(course => <li className="course" key={course.id}>
        <BookOpen className="course-icon" size={22} />
        <div><h2>{course.title}</h2><p>{course.description}</p></div>
        <Badge>{course.status === 'planned' ? 'В разработке' : course.status}</Badge>
      </li>)}
    </ul> : <p>Курсы пока не добавлены.</p>}</ApiState>
  </section>
}

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const path = window.location.pathname.replace(/\/$/, '') || '/'
  const page = navigation.find(item => item.path === path)
  const PageIcon = page?.icon ?? House
  useEffect(() => { document.title = `${page?.label ?? 'Страница не найдена'} — DevLab` }, [page])
  return <div className={`workbench ${sidebarOpen ? '' : 'sidebar-collapsed'}`}>
    <header className="titlebar"><a className="brand" href={pages.home} aria-label="DevLab — главная"><FlaskConical size={21} /><span>Dev<span className="accent">Lab</span></span></a></header>
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
    </aside>
    <main className="editor">
      <div className="tabbar"><div className="tab"><PageIcon size={15} /><span>{page?.label ?? '404'}</span></div></div>
      <div className={`canvas ${path === pages.courses ? 'canvas-courses' : ''}`}>
        {path === pages.home ? <Home /> : path === pages.courses ? <Courses /> : <section className="welcome"><h1>Страница не найдена</h1><a className="primary-link" href={pages.home}>На главную<ArrowRight size={16} /></a></section>}
      </div>
    </main>
  </div>
}

createRoot(document.getElementById('root')).render(<React.StrictMode><App /></React.StrictMode>)
