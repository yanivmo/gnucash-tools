import unittest
from unittest.mock import patch
from gnucash import GnuCash


class TestGnuCash(unittest.TestCase):
    def test_account(self):
        accounts_cursor = [
            ('1', None, 'root1'),
            ('2', '1', 'A'),
            ('3', '1', 'B'),
            ('4', None, 'root2'),
            ('5', '2', 'C')
        ]

        with patch('gnucash_sqlite.GnuCashSqlite') as mock_sql:
            mock_sql.get_accounts.return_value = accounts_cursor

            gnucash = GnuCash(mock_sql)
            accounts = gnucash.accounts
            assert len(accounts_cursor) == len(accounts), '{} != {}'.format(len(accounts_cursor), len(accounts))

            roots = gnucash.root_accounts
            assert len(roots) == 2

            assert roots[0].name == 'root1'
            assert roots[1].name == 'root2'
            assert roots[0].children[0].children[0].name == 'C'

    def test_balances(self):
        pass