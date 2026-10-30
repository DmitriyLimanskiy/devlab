"""HTTP-клиент подключения CLI. Не зависит от PTY и локального наблюдения."""
from dataclasses import dataclass, field
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
from uuid import UUID


class ApiError(Exception):
    """Сообщение, безопасное для вывода без ключа и тела HTTP-ответа."""

    def __init__(self, message, *, retryable=True):
        super().__init__(message)
        self.retryable = retryable


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


@dataclass(frozen=True)
class Connection:
    session_id: str
    generation: int
    key: str = field(repr=False)


class ApiClient:
    def __init__(self, server_url: str, timeout: float = 3):
        try:
            parsed = urlsplit(server_url)
            parsed.port
        except ValueError:
            raise ApiError('Некорректный адрес DEVLAB_SERVER_URL.') from None
        if (parsed.scheme not in {'http', 'https'} or not parsed.hostname or
                parsed.username or parsed.password or parsed.query or parsed.fragment or
                parsed.path not in {'', '/'}):
            raise ApiError('DEVLAB_SERVER_URL должен содержать адрес сервера, например http://127.0.0.1:8080')
        self.server_url = server_url.rstrip('/')
        self.timeout = timeout
        self.opener = build_opener(NoRedirects())

    def request(self, path, payload=None, key=None):
        headers = {'Accept': 'application/json'}
        data = None
        if payload is not None:
            data = json.dumps(payload, ensure_ascii=True).encode()
            headers['Content-Type'] = 'application/json'
        if key is not None:
            headers['Authorization'] = 'Bearer ' + key
        request = Request(self.server_url + '/api/v1' + path, data=data, headers=headers)
        try:
            with self.opener.open(request, timeout=self.timeout) as response:
                body = response.read(2_000_001)
                if len(body) > 2_000_000:
                    raise ApiError('Слишком большой ответ сервера')
                return json.loads(body)
        except HTTPError as error:
            error.close()
            if error.code == 404 and path == '/cli-connect':
                raise ApiError('Нет активной сессии. Откройте выбранный курс в браузере и повторите подключение.') from None
            if error.code == 401:
                raise ApiError('Ключ подключения больше не действует.', retryable=False) from None
            if error.code == 409:
                raise ApiError('Сервер отклонил поколение или версию снимка.', retryable=False) from None
            raise ApiError(f'Сервер вернул HTTP {error.code}.',
                           retryable=error.code >= 500 or error.code in {408, 429}) from None
        except (URLError, OSError, TimeoutError):
            raise ApiError('Сервер недоступен или не ответил вовремя.') from None
        except (ValueError, UnicodeError):
            raise ApiError('Сервер вернул некорректный JSON.') from None

    def catalog(self):
        data = self.request('/catalog')
        if not isinstance(data, list) or any(
            not isinstance(course, dict) or not isinstance(course.get('id'), str) or not course['id'] or
            not isinstance(course.get('title'), str) or
            type(course.get('position')) is not int or course['position'] < 1
            for course in data
        ):
            raise ApiError('Некорректный формат каталога.')
        if len({course['id'] for course in data}) != len(data):
            raise ApiError('Каталог содержит повторные курсы.')
        return sorted(data, key=lambda course: course['position'])

    def connect(self, slug):
        data = self.request('/cli-connect', {'course_slug': slug})
        try:
            session_id = str(UUID(data['session_id']))
            generation, key = data['generation'], data['key']
            if type(generation) is not int or not 1 <= generation <= 9223372036854775807:
                raise ValueError
            if not isinstance(key, str) or not key or any(c.isspace() for c in key):
                raise ValueError
        except (KeyError, ValueError, TypeError, AttributeError):
            raise ApiError('Некорректный ответ подключения CLI.') from None
        return Connection(session_id, generation, key)

    def send_snapshot(self, connection, state, version):
        payload = {'schema_version': 1, 'session_id': connection.session_id,
                   'generation': connection.generation, 'version': version, 'state': state}
        data = self.request('/cli-send-snapshot', payload, connection.key)
        if (not isinstance(data, dict) or data.get('session_id') != connection.session_id or
                type(data.get('generation')) is not int or data['generation'] != connection.generation or
                type(data.get('version')) is not int or data['version'] != version):
            raise ApiError('Сервер не подтвердил отправленную версию снимка.')

    def send_initial(self, connection, state):
        self.send_snapshot(connection, state, 1)
