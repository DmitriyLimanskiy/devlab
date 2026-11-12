import { useState } from 'react'
import { ApiState } from '../../shared/ApiState'
import { useApi } from '../../shared/useApi'
import { api, gitCoursePage } from '../../shared/routes'
import { parseCatalog } from '../catalog/catalogData'
import { GitCourse } from './GitCourse'
import { parseGitCourse } from './courseSteps'

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
export function GitPage() {
  const state = useApi(api.git, parseCatalog)
  return <ApiState state={state}>{courses => <GitTabs courses={courses} />}</ApiState>
}
