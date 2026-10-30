"""Диалог выбора курса и подключения перед выбором папки"""
from .api import ApiError


def choose_connection(client):
    while True:
        try:
            courses = client.catalog()
        except ApiError as error:
            print(f'  {error}')
            answer = input('  Enter — локальная работа, r — повторить: ').strip().lower()
            if answer == 'r':
                continue
            return None
        print('\n  Выберите курс:')
        for number, course in enumerate(courses, 1):
            print(f"  {number}. {course['title']}")
        print('  0. Локальная работа без сервера')
        answer = input('  Номер курса [0], r — обновить каталог: ').strip().lower()
        if answer == 'r':
            continue
        if answer in {'', '0'}:
            return None
        if not answer.isdecimal() or not 1 <= int(answer) <= len(courses):
            print('  Выберите номер из списка')
            continue
        course = courses[int(answer) - 1]
        try:
            connection = client.connect(course['id'])
        except ApiError as error:
            print(f'  {error}')
            continue
        print(f"  Подключён курс {course['title']}. Сессия: {connection.session_id}, поколение: {connection.generation}")
        return connection
