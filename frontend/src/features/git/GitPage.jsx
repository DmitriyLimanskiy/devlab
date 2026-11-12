import { useState } from 'react'
import { ApiState } from '../../shared/ApiState'
import { useApi } from '../../shared/useApi'
import { api, gitCoursePage } from '../../shared/routes'
import { courseStatusLabels, parseCatalog } from '../catalog/catalogData'
import { AuthForm } from '../auth/AuthForm'
import { Badge } from '../../shared/ui'

const parseGitCourses = data => parseCatalog(data).filter(course => course.id.startsWith('git-'))

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
      <article className="course-details">
        <Badge>{courseStatusLabels[course.status]}</Badge>
        <h1>{course.title}</h1>
        <p>{course.description.replace(/\.+\s*$/, '')}</p>
      </article>
    </div>
  </div>
}

// Загрузить список Git-курсов для вкладок страницы
export function GitPage({ onLogin }) {
  const state = useApi(api.catalog, parseGitCourses)
  if (state.status === 401) return <AuthForm onLogin={() => {
    state.retry()
    onLogin()
  }} />
  return <ApiState state={state}>{courses => <GitTabs courses={courses} />}</ApiState>
}
