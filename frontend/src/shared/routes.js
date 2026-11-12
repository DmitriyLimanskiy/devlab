export const pages = { catalog: '/catalog', git: '/git-course' }
export const api = {
  catalog: '/api/v1/catalog',
  login: '/api/v1/auth/login',
  register: '/api/v1/auth/register',
  me: '/api/v1/auth/me',
  logout: '/api/v1/auth/logout',
}

// Сформировать адрес страницы выбранного Git-курса
export const gitCoursePage = slug => `${pages.git}?course=${encodeURIComponent(slug)}`
