import sqlite3

NAME_MAX_LENGTH = 256
MESSAGE_MAX_LENGTH = 8096


class DatabaseRepository:
    def __init__(self, db_path: str = ":memory:"):
        if not isinstance(db_path, str):
            raise TypeError("Путь к базе данных должен быть строкой.")

        self.db_path = db_path
        self._connection = sqlite3.connect(db_path)
        self._connection.row_factory = sqlite3.Row
        self._create_schema()

    def _create_schema(self) -> None:
        self._connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL CHECK (length(name) <= {NAME_MAX_LENGTH}),
                message TEXT NOT NULL CHECK (length(message) <= {MESSAGE_MAX_LENGTH})
            )
            """
        )
        self._connection.commit()

    @staticmethod
    def _validate_comment_id(comment_id: int) -> None:
        if isinstance(comment_id, bool) or not isinstance(comment_id, int):
            raise TypeError("Идентификатор сообщения должен быть целым числом.")

    @staticmethod
    def _validate_name(username: str) -> None:
        if not isinstance(username, str):
            raise TypeError("Имя пользователя должно быть строкой.")
        if not username.strip():
            raise ValueError("Имя пользователя не может быть пустым.")
        if len(username) > NAME_MAX_LENGTH:
            raise ValueError(
                f"Имя пользователя не может быть длиннее {NAME_MAX_LENGTH} символов."
            )

    @staticmethod
    def _validate_message(message: str) -> None:
        if not isinstance(message, str):
            raise TypeError("Текст сообщения должен быть строкой.")
        if not message.strip():
            raise ValueError("Текст сообщения не может быть пустым.")
        if len(message) > MESSAGE_MAX_LENGTH:
            raise ValueError(
                f"Текст сообщения не может быть длиннее {MESSAGE_MAX_LENGTH} символов."
            )

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict:
        return {"id": row["id"], "name": row["name"], "message": row["message"]}

    def get_by_id(self, comment_id: int) -> dict | None:
        self._validate_comment_id(comment_id)
        row = self._connection.execute(
            "SELECT id, name, message FROM comments WHERE id = ?",
            (comment_id,),
        ).fetchone()
        return self._row_to_dict(row) if row is not None else None

    def get_by_name(self, username: str) -> list[dict]:
        self._validate_name(username)
        rows = self._connection.execute(
            "SELECT id, name, message FROM comments WHERE name = ? ORDER BY id",
            (username,),
        ).fetchall()
        return [self._row_to_dict(row) for row in rows]

    def add(self, comment_id: int, username: str, message: str) -> bool:
        self._validate_comment_id(comment_id)
        self._validate_name(username)
        self._validate_message(message)

        if self.get_by_id(comment_id) is not None:
            raise ValueError(f"Сообщение с ID {comment_id} уже существует.")

        self._connection.execute(
            "INSERT INTO comments (id, name, message) VALUES (?, ?, ?)",
            (comment_id, username, message),
        )
        self._connection.commit()
        return True

    def update(self, comment_id: int, new_message: str) -> bool:
        self._validate_comment_id(comment_id)
        self._validate_message(new_message)

        cursor = self._connection.execute(
            "UPDATE comments SET message = ? WHERE id = ?",
            (new_message, comment_id),
        )
        self._connection.commit()
        return cursor.rowcount > 0

    def delete(self, comment_id: int) -> bool:
        self._validate_comment_id(comment_id)

        cursor = self._connection.execute(
            "DELETE FROM comments WHERE id = ?",
            (comment_id,),
        )
        self._connection.commit()
        return cursor.rowcount > 0

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> "DatabaseRepository":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()
