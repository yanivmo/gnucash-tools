import json

from datetime import datetime
from dateutil.relativedelta import relativedelta
from typing import List

from gnucash_sqlite import GnuCashSqlite


class Account:
    def __init__(self, guid, parent_guid, name):
        self.guid = guid
        self.parent_guid = parent_guid
        self.name = name
        self.balance = []

        self._children = []

    @property
    def is_root(self):
        return self.parent_guid is None

    @property
    def has_children(self):
        return len(self._children) > 0

    @property
    def children(self):
        return self._children

    def set_children(self, children):
        self._children = sorted(children)

    def itertree(self):
        """
        Post-order accounts tree iteration
        :return: Accounts generator
        """
        for child in self._children:
            yield from child.itertree()
        yield self

    def __repr__(self):
        return '<Account: {} "{}">'.format(self.guid, self.name)

    def __lt__(self, other):
        return self.name < other.name

    def report_indented(self, indent=0):
        result = '\n{}{} {} ('.format(' '*indent, self.name, [x/100 for x in self.balance])
        for child_account in self.children:
            result += child_account.report_indented(indent+3)
        if self.has_children:
            result += '\n' + ' '*indent
        return result + ')'

    def report_flat(self, prefix='', separator=':'):
        result = prefix + self.name + '\t' + str([x/100 for x in self.balance]) + '\n'
        for child_account in self.children:
            result += child_account.report_flat(prefix + self.name + separator, separator)
        return result

    def report_structured(self):
        return {
            'name': self.name,
            'balance': [x/100 for x in self.balance],
            'children': [ch.report_structured() for ch in self.children]
        }

class GnuCash:

    def __init__(self, data_provider):
        self._data_provider = data_provider  # type: GnuCashSqlite
        self._load_accounts()
        self._balance_intervals = []
        # self._earliest_transaction, self._latest_transaction = self._data_provider.get_book_dates_range()

    def _load_accounts(self):
        acc_cursor = self._data_provider.get_accounts()
        self._accounts = [Account(*row) for row in acc_cursor]
        self._accounts_by_id = {acc.guid: acc for acc in self._accounts}
        self._root_accounts = [acc for acc in self._accounts if acc.is_root]

        # Build the accounts hierarchy
        unprocessed_accounts = self._root_accounts[:]
        while unprocessed_accounts:
            parent = unprocessed_accounts.pop()  # type:Account
            children = [acc for acc in self._accounts if acc.parent_guid == parent.guid]
            parent.set_children(children)
            unprocessed_accounts.extend(children)

    @property
    def accounts(self):
        return self._accounts

    @property
    def root_accounts(self):
        return self._root_accounts

    def get_accounts_by_name(self, name):
        return [acc for acc in self._accounts if acc.name == name]

    def load_balances(self, intervals: List[datetime]):
        self._balance_intervals = []
        self._reset_balances()
        for interval in zip(intervals, intervals[1:]):
            self._append_balances(*interval)

    def _append_balances(self, period_start, period_end):
        self._balance_intervals.append((period_start, period_end))
        balances = self._data_provider.get_accounts_balance(period_start, period_end)
        balances_by_account = {acc_id: balance for acc_id, balance in balances}

        for root in self.root_accounts:
            for acc in root.itertree():
                children_balance = sum([child.balance[-1] for child in acc.children])
                acc.balance.append(balances_by_account.get(acc.guid, 0) + children_balance)

    def _reset_balances(self):
        for acc in self._accounts:
            acc.balance = []


def make_intervals(start, interval, end):
    assert start < end
    assert start + interval > start

    intervals = []
    x = start
    n = 1
    while x < end:
        intervals.append(x)
        x = start + n*interval
        n += 1
    intervals.append(end)
    return intervals


if __name__ == "__main__":
    gnucash = GnuCash(GnuCashSqlite('test2.gnucash'))
    gnucash.load_balances(make_intervals(datetime(2015, 1, 1), relativedelta(months=1), datetime(2016, 1, 1)))
    # print(dump_account_hierarchy_with_full_name(gnucash.get_accounts_by_name("Expenses")[0]))
    # print(gnucash.get_accounts_by_name("Expenses")[0].report_flat())
    print(json.dumps(gnucash.get_accounts_by_name("Expenses")[0].report_structured()))
