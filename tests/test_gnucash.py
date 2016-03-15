import unittest
from unittest.mock import patch, call
from gnucash import GnuCash, make_intervals

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class TestGnuCash(unittest.TestCase):

    def test_load_accounts(self):
        # Columns:
        #   id  parent  name
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

        with patch('gnucash.GnuCashSqlite') as mock_sql:
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

    def test_balances(self):
        # Columns:
        #   id  parent  name
        accounts_cursor = [       # root1
            ('1', None, 'root'),  # |--A
            ('2', '1', 'A'),      # |  |--B
            ('3', '2', 'B'),      # |  |--C
            ('4', '2', 'C'),      # |     |--D
            ('5', '4', 'D'),      # |     |--E
            ('6', '4', 'E'),      # |
            ('7', '1', 'F')       # |--F
        ]

        with patch('gnucash.GnuCashSqlite') as mock_sql:
            mock_sql.get_accounts.return_value = accounts_cursor

            gnucash = GnuCash(mock_sql)
            accounts = gnucash.accounts
            self.assertEqual(len(accounts_cursor), len(accounts))
            root = gnucash.root_accounts[0]

            post_order_names = ['B', 'D', 'E', 'C', 'A', 'F', 'root']
            for acc in root.itertree():
                self.assertEqual(acc.name, post_order_names.pop(0), ', '.join((a.name for a in root.itertree())))

            # load_balances with one interval
            balances_cursors = [
                [('3', 1),   # B
                 ('5', 2),   # D
                 ('6', 3)]   # E
            ]
            mock_sql.get_accounts_balance.side_effect = balances_cursors
            gnucash.load_balances([datetime(2016, 1, 1), datetime(2017, 1, 1)])

            # Accounts:           ['B', 'D', 'E', 'C', 'A', 'F', 'root']
            post_order_balances = [[1], [2], [3], [5], [6], [0], [6]]
            for acc in root.itertree():
                self.assertEqual(acc.balance, post_order_balances.pop(0), acc.name)

            mock_sql.get_accounts_balance.assert_called_with(datetime(2016, 1, 1), datetime(2017, 1, 1))

            # load_balances with three intervals
            balances_cursors = [
                [('3', 1),   # B
                 ('5', 2),   # D
                 ('6', 3)],  # E

                [('3', 2),   # B
                 ('5', 3),   # D
                 ('6', 4)],  # E

                [('3', 3),   # B
                 ('5', 4),   # D
                 ('6', 5)]   # E
            ]
            mock_sql.get_accounts_balance.side_effect = balances_cursors
            gnucash.load_balances([datetime(2016, 1, 1),
                                   datetime(2016, 2, 1),
                                   datetime(2016, 3, 1),
                                   datetime(2016, 4, 1)])

            # Accounts:           ['B', 'D', 'E', 'C', 'A', 'F', 'root']
            post_order_balances = [[1, 2, 3],  # B
                                   [2, 3, 4],  # D
                                   [3, 4, 5],  # E
                                   [5, 7, 9],  # C
                                   [6, 9, 12], # A
                                   [0, 0, 0],  # F
                                   [6, 9, 12]] # root
            for acc in root.itertree():
                self.assertEqual(acc.balance, post_order_balances.pop(0), acc.name)

            mock_sql.get_accounts_balance.has_calls(call(datetime(2016, 1, 1), datetime(2016, 2, 1)),
                                                    call(datetime(2016, 2, 1), datetime(2016, 3, 1)),
                                                    call(datetime(2016, 3, 1), datetime(2016, 4, 1)))

    def test_make_intervals(self):

        with self.assertRaises(Exception):
            x = make_intervals(datetime(2016, 2, 24), timedelta(seconds=0), datetime(2016, 2, 27))

        x = make_intervals(datetime(2016, 2, 24), relativedelta(days=1), datetime(2016, 2, 26))
        self.assertEqual(x, [datetime(2016, 2, 24), datetime(2016, 2, 25), datetime(2016, 2, 26)])

        x = make_intervals(datetime(2016, 1, 31), relativedelta(months=1), datetime(2016, 4, 26))
        self.assertEqual(x, [datetime(2016, 1, 31), datetime(2016, 2, 29),
                             datetime(2016, 3, 31), datetime(2016, 4, 26)])
