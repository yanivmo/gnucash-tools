import unittest
from unittest.mock import patch
from gnucash import GnuCash, make_intervals

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class TestGnuCash(unittest.TestCase):

    def test_accounts(self):
        accounts_cursor = [       # root1
            ('1', None, 'root1'), # |--A
            ('2', '1', 'A'),      # |  |--C
            ('3', '1', 'B'),      # |
            ('4', None, 'root2'), # |--B
            ('5', '2', 'C'),      # |  |--D
            ('6', '3', 'D'),      # |  |--E
            ('7', '3', 'E'),      # |
            ('8', '1', 'F')       # |--F
        ]                         # root 2
        balances_cursor = [
            ('3', 1),  # B
            ('6', 2),  # D
            ('7', 3)   # E
        ]

        with patch('gnucash_sqlite.GnuCashSqlite') as mock_sql:
            mock_sql.get_accounts.return_value = accounts_cursor

            gnucash = GnuCash(mock_sql)
            accounts = gnucash.accounts
            self.assertEqual(len(accounts_cursor), len(accounts))

            roots = gnucash.root_accounts
            self.assertEqual(len(roots), 2)

            self.assertEqual(roots[0].name, 'root1')
            self.assertEqual(roots[1].name, 'root2')

            post_order_names = ['C', 'A', 'D', 'E', 'B', 'F', 'root1']
            for acc in roots[0].itertree():
                self.assertEqual(acc.name, post_order_names.pop(0))

            mock_sql.get_accounts_balance.return_value = balances_cursor
            gnucash.load_balances()
            post_order_balances = [[0], [0], [2], [3], [6], [0], [6]]
            for acc in roots[0].itertree():
                self.assertEqual(acc.balance, post_order_balances.pop(0), acc.name)

    def test_make_intervals(self):

        with self.assertRaises(Exception):
            x = make_intervals(datetime(2016, 2, 24), timedelta(seconds=0), datetime(2016, 2, 27))

        x = make_intervals(datetime(2016, 2, 24), relativedelta(days=1), datetime(2016, 2, 26))
        self.assertEqual(x, [datetime(2016, 2, 24), datetime(2016, 2, 25), datetime(2016, 2, 26)])

        x = make_intervals(datetime(2016, 1, 31), relativedelta(months=1), datetime(2016, 4, 26))
        self.assertEqual(x, [datetime(2016, 1, 31), datetime(2016, 2, 29),
                             datetime(2016, 3, 31), datetime(2016, 4, 26)])
