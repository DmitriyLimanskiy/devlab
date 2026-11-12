import React, { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { FlaskConical, PanelLeftClose, PanelLeftOpen, BookOpen, ArrowRight } from 'lucide-react'
import { Catalog } from './features/catalog/Catalog'
import { GitPage } from './features/git/GitPage'
import { IconButton } from './shared/ui'
import { pages } from './shared/routes'
import './tokens.css'
import './styles.css'

const navigation = [
  { path: pages.catalog, label: 'Курсы', icon: BookOpen },
  { path: pages.git, label: 'Git', icon: FlaskConical },
]

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
  useEffect(() => { document.title = `${page?.label ?? 'Страница не найдена'} — Stack Forge` }, [page])
  return <div className={`workbench ${sidebarOpen ? '' : 'sidebar-collapsed'}`}>
    <header className="titlebar"><a className="brand" href={pages.catalog} aria-label="Stack Forge — каталог курсов"><FlaskConical size={21} /><span>Stack <span className="accent">Forge</span></span></a><span className="titlebar-caption">Практика на настоящих инструментах</span></header>
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
