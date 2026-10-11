import sqlite3


class RegistrationDatabase:
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
        self._connection.execute(
            "INSERT OR REPLACE INTO registrations "
            "(login, password, confirm_password, is_authorized, error_message) "
            "VALUES (?, ?, ?, ?, ?)",
            (login, password, confirm_password, int(is_authorized), error_message),
        )
        self._connection.commit()
        return self.get_record(login, password, confirm_password)

    def get_record(self, login: str, password: str, confirm_password: str) -> dict | None:
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
        cursor = self._connection.execute(
            "DELETE FROM registrations "
            "WHERE login = ? AND password = ? AND confirm_password = ?",
            (login, password, confirm_password),
        )
        self._connection.commit()
        return cursor.rowcount > 0

    def count_records(self) -> int:
        cursor = self._connection.execute("SELECT COUNT(*) AS total FROM registrations")
        return cursor.fetchone()["total"]

    def close(self) -> None:
        self._connection.close()