import argparse

from gnucash import GnuCashSqlite


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Reset the history of the import wizard')
    parser.add_argument('gnucash_file', help='GnuCash sqlite file')

    args = parser.parse_args()

    gnucash = GnuCashSqlite(args.gnucash_file)
    gnucash.reset_import_wizard()

