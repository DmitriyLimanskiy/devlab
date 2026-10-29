"""Параметры подключения без соединения с базой при импорте."""
import os
from sqlalchemy.engine import URL, make_url


def database_url():
    if value := os.environ.get('DATABASE_URL'):
        url = make_url(value)
        if url.drivername in {'postgres', 'postgresql'}:
            url = url.set(drivername='postgresql+psycopg')
        if url.drivername != 'postgresql+psycopg':
            raise ValueError('DATABASE_URL должен использовать postgresql+psycopg')
        return url
    password = os.environ.get('POSTGRES_PASSWORD')
    if not password:
        raise RuntimeError('Задайте DATABASE_URL или POSTGRES_PASSWORD и параметры POSTGRES_*')
    return URL.create('postgresql+psycopg',
                      username=os.environ.get('POSTGRES_USER', 'devlab'), password=password,
                      host=os.environ.get('POSTGRES_HOST', 'postgres'),
                      port=int(os.environ.get('POSTGRES_PORT', '5432')),
                      database=os.environ.get('POSTGRES_DB', 'devlab'))
