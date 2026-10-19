from unittest.mock import MagicMock

import pytest

from db.base import BaseDB


def test_get_cursor_rolls_back_and_reraises_unknown_exception():
    pool = MagicMock()
    connection = pool.get_connection.return_value
    database = BaseDB(pool)

    with pytest.raises(RuntimeError, match="db unavailable"):
        with database.get_cursor() as _cursor:
            raise RuntimeError("db unavailable")

    connection.rollback.assert_called_once_with()
    connection.commit.assert_not_called()
    connection.close.assert_called_once_with()


def test_exec_does_not_translate_query_failure_to_empty_list():
    pool = MagicMock()
    cursor = pool.get_connection.return_value.cursor.return_value
    cursor.execute.side_effect = RuntimeError("query failed")
    database = BaseDB(pool)

    with pytest.raises(RuntimeError, match="query failed"):
        database._exec("SELECT 1")
