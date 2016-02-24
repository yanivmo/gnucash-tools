import sqlite3

from datetime import datetime, timedelta
from typing import Tuple


class GnuCashSqlite:
    def __init__(self, filename):
        self._conn = sqlite3.connect(filename)

    def get_accounts(self):
        """
        Get all the accounts in the database.
        :return: A list of tuples (account_guid, parent_account_guid, account_name)
        """
        query = (
            "SELECT a.guid, a.parent_guid, a.name "
            "FROM accounts AS a "
            "ORDER BY a.name;"
        )
        return self._conn.execute(query).fetchall()

    def get_accounts_balance(self, period_start: datetime, period_end: datetime):
        """
        For each account calculate its transactions balance during the specified period.
        :param period_start:
        :param period_end:
        :return: A list of tuples (account_guid, balance)
        """
        query = (
            "SELECT a.guid, sum(s.value_num) "
            "FROM "
            "    accounts AS a INNER JOIN "
            "    splits AS s ON a.guid = s.account_guid INNER JOIN "
            "    transactions AS t ON s.tx_guid = t.guid "
            "WHERE t.post_date >= ? AND t.post_date < ? "
            "GROUP BY a.guid;"
        )
        query_params = (datetime2db(period_start), datetime2db(period_end))
        return self._conn.execute(query, query_params).fetchall()

    def get_book_dates_range(self) -> Tuple[datetime, datetime]:
        """
        Get the earliest and the latest date in the transaction date in the database.
        :return: A tuple (first_date, last_date)
        """
        query = (
            "SELECT min(t.post_date), max(t.post_date) "
            "FROM transactions AS t;"
        )
        result = self._conn.execute(query).fetchone()
        return db2datetime(result[0]), db2datetime(result[1])


TIMESTAMP_FORMAT = '%Y%m%d%H%M%S'
ONE_DAY = timedelta(days=1)


def datetime2db(dt: datetime) -> str:
    return (dt - ONE_DAY).strftime(TIMESTAMP_FORMAT)


def db2datetime(timestamp: str) -> datetime:
    return datetime.strptime(timestamp, TIMESTAMP_FORMAT) + ONE_DAY
