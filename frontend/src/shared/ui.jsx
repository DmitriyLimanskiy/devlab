// Показать кнопку с иконкой и доступным текстовым названием
export function IconButton({ label, children, ...props }) {
  return <button className="icon-button" type="button" aria-label={label} title={label} {...props}>{children}</button>
}

// Показать компактную метку статуса курса
export function Badge({ children }) {
  return <span className="badge">{children}</span>
}
