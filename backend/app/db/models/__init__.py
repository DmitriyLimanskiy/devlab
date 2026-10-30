"""Регистрация всех SQLAlchemy-таблиц в общей metadata приложения."""
from .course import Course, CourseStep
from .practice import PracticeSession, PracticeSnapshot

__all__ = ['Course', 'CourseStep', 'PracticeSession', 'PracticeSnapshot']
