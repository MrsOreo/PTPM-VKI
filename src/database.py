import sqlite3


class RegistrationDatabase:
    """
    Класс работы с базой данных (SQLite).

    Одна запись БД содержит: логин, пароль, подтверждение_пароля,
    результат_авторизации (is_authorized), сообщение_об_ошибке.
    Каждая запись идентифицируется по логину, паролю и подтверждению пароля.
    """

    def __init__(self, db_path: str = ":memory:"):
        self._connection = sqlite3.connect(db_path)
        self._connection.row_factory = sqlite3.Row
        self._create_table()

    def _create_table(self) -> None:
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS registrations (
                login           TEXT    NOT NULL,
                password        TEXT    NOT NULL,
                confirm_password TEXT   NOT NULL,
                is_authorized   INTEGER NOT NULL,
                error_message   TEXT,
                PRIMARY KEY (login, password, confirm_password)
            )
            """
        )
        self._connection.commit()

    def add_record(
        self,
        login: str,
        password: str,
        confirm_password: str,
        is_authorized: bool,
        error_message: str,
    ) -> dict:
        """
        Добавляет запись в БД. При совпадении ключа существующая запись
        заменяется новой. Возвращает сохранённую запись.
        """
        self._connection.execute(
            "INSERT OR REPLACE INTO registrations "
            "(login, password, confirm_password, is_authorized, error_message) "
            "VALUES (?, ?, ?, ?, ?)",
            (login, password, confirm_password, int(is_authorized), error_message),
        )
        self._connection.commit()
        return self.get_record(login, password, confirm_password)

    def get_record(self, login: str, password: str, confirm_password: str) -> dict | None:
        """
        Возвращает запись в виде словаря {'is_authorized', 'error_message'}
        или None, если запись отсутствует.
        """
        cursor = self._connection.execute(
            "SELECT is_authorized, error_message FROM registrations "
            "WHERE login = ? AND password = ? AND confirm_password = ?",
            (login, password, confirm_password),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return {
            "is_authorized": bool(row["is_authorized"]),
            "error_message": row["error_message"],
        }

    def delete_record(self, login: str, password: str, confirm_password: str) -> bool:
        """Удаляет запись по ключу. Возвращает True, если запись была удалена."""
        cursor = self._connection.execute(
            "DELETE FROM registrations "
            "WHERE login = ? AND password = ? AND confirm_password = ?",
            (login, password, confirm_password),
        )
        self._connection.commit()
        return cursor.rowcount > 0

    def count_records(self) -> int:
        """Возвращает общее количество записей в таблице."""
        cursor = self._connection.execute("SELECT COUNT(*) AS total FROM registrations")
        return cursor.fetchone()["total"]

    def close(self) -> None:
        """Закрывает соединение с базой данных."""
        self._connection.close()