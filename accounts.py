import sqlite3


class Account:
    def __init__(self, guid, parent_guid, name, balance):
        self._guid = guid
        self._parent_guid = parent_guid
        self._name = name
        self._balance = balance if balance is not None else 0
        self._children = []

    @property
    def name(self):
        return self._name

    @property
    def guid(self):
        return self._guid

    @property
    def parent_guid(self):
        return self._parent_guid

    @property
    def is_root(self):
        return self._parent_guid is None

    @property
    def balance(self):
        return self._balance

    @property
    def balance_including_children(self):
        return self._balance + sum((c.balance_including_children for c in self._children))

    @property
    def has_children(self):
        return len(self._children) > 0

    @property
    def children(self):
        return self._children

    def set_children(self, children):
        self._children = sorted(children)

    def __repr__(self):
        return '<Account: {} "{}">'.format(self._guid, self._name)

    def __lt__(self, other):
        return self.name < other.name


class GnuCash:

    def __init__(self, filename):
        self._conn = sqlite3.connect(filename)
        self._load_accounts()

    def _load_accounts(self):
        accounts_query = (
            "SELECT a.guid, a.parent_guid, a.name, sum(s.value_num) "
            "FROM accounts AS a LEFT JOIN splits AS s ON a.guid = s.account_guid "
            "GROUP BY a.guid ORDER BY a.name;"
        )
        self._accounts = [Account(*row) for row in self._conn.execute(accounts_query).fetchall()]
        self._accounts_by_id = {acc.guid: acc for acc in self._accounts}
        self._root_accounts = [acc for acc in self._accounts if acc.is_root]

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


def dump_account_hierarchy_with_indentation(account, indent=0):
    result = '\n{}{} {} ('.format(' '*indent, account.name, account.balance_including_children/100)
    for child_account in account.children:
        result += get_balances(child_account, indent+3)
    if account.has_children:
        result += '\n' + ' '*indent
    return result + ')'


def dump_account_hierarchy_with_full_name(account, prefix='', separator=':'):
    result = prefix + account.name + '\t' + str(account.balance_including_children/100) + '\n'
    for child_account in account.children:
        result += dump_account_hierarchy_with_full_name(child_account, prefix + account.name + separator)
    return result


if __name__ == "__main__":
    gnucash = GnuCash('test.gnucash')
    print(dump_account_hierarchy_with_full_name(gnucash.get_accounts_by_name("Expenses")[0]))
