from datetime import datetime

from gnucash_sqlite import GnuCashSqlite


class Account:
    def __init__(self, guid, parent_guid, name):
        self.guid = guid
        self.parent_guid = parent_guid
        self.name = name
        self.balance = 0

        self._children = []

    # @property
    # def balance(self):
    #     return self._balance
    #
    # @property
    # def balance_including_children(self):
    #     return self._balance + sum((c.balance_including_children for c in self._children))

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
        return '<Account: {} "{}">'.format(self._guid, self._name)

    def __lt__(self, other):
        return self.name < other.name


class GnuCash:

    def __init__(self, data_provider):
        self._data_provider = data_provider  # type: gnucash_sqlite.GnuCashSqlite
        self._load_accounts()

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

    def load_balances(self):
        balances = self._data_provider.get_balances(datetime(2015, 1, 31), datetime(2017, 2, 1))
        balances_by_account = {acc_id: balance for acc_id, balance in balances}

        for root in self.root_accounts:
            for acc in root.itertree():
                acc.balance = balances_by_account.get(acc.guid, 0) + sum([child.balance for child in acc.children])


def dump_account_hierarchy_with_indentation(account, indent=0):
    result = '\n{}{} {} ('.format(' '*indent, account.name, account.balance/100)
    for child_account in account.children:
        result += dump_account_hierarchy_with_indentation(child_account, indent+3)
    if account.has_children:
        result += '\n' + ' '*indent
    return result + ')'


def dump_account_hierarchy_with_full_name(account, prefix='', separator=':'):
    result = prefix + account.name + '\t' + str(account.balance/100) + '\n'
    for child_account in account.children:
        result += dump_account_hierarchy_with_full_name(child_account, prefix + account.name + separator)
    return result


if __name__ == "__main__":
    gnucash = GnuCash(GnuCashSqlite('test.gnucash'))
    gnucash.load_balances()
    # print(dump_account_hierarchy_with_full_name(gnucash.get_accounts_by_name("Expenses")[0]))
    print(dump_account_hierarchy_with_indentation(gnucash.get_accounts_by_name("Expenses")[0]))
