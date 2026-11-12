import { ArrowRight, GitBranch } from 'lucide-react'
import { ApiState } from '../../shared/ApiState'
import { useApi } from '../../shared/useApi'
import { api, gitCoursePage } from '../../shared/routes'
import { Badge } from '../../shared/ui'
import { AuthForm } from '../auth/AuthForm'
import { parseCatalog, courseStatusLabels } from './catalogData'

// Показать каталог направлений и переходы к доступным курсам
export function Catalog({ onLogin }) {
  const state = useApi(api.catalog, parseCatalog)
  if (state.status === 401) return <AuthForm onLogin={() => {
    state.retry()
    onLogin()
  }} />

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
