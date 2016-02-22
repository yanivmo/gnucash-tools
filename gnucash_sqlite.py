import sqlite3
import datetime


class GnuCashSqlite:

    TIMESTAMP_FORMAT = '%Y%m%d%H%M%S'

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

    def get_balances(self, period_start: datetime.date, period_end: datetime.date):
        query = (
            "SELECT a.guid, a.name, sum(s.value_num) "
            "FROM "
            "    accounts AS a INNER JOIN "
            "    splits AS s ON a.guid = s.account_guid INNER JOIN "
            "    transactions AS t ON s.tx_guid = t.guid "
            "WHERE t.post_date >= ? AND t.post_date < ? "
            "GROUP BY a.guid;"
        )
        query_params = (period_start.strftime(self.TIMESTAMP_FORMAT), period_end.strftime(self.TIMESTAMP_FORMAT))
        return self._conn.execute(query, query_params).fetchall()
