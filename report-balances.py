import argparse
import errno
import json
import sys

from datetime import datetime

from dateutil.relativedelta import relativedelta

from gnucash import GnuCashSqlite, GnuCash, make_intervals


# Date parser for argparse
def date_type(text):
    return datetime.strptime(text, '%Y-%m-%d')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Output balances in monthly intervals',
                                     epilog='All dates are in YYYY-MM-DD format.')
    parser.add_argument('gnucash_file', help='GnuCash sqlite file')
    parser.add_argument('-r', '--root_account', default='Expenses',
                        help='the report will be generated for all the descendants of this account; default: "Expenses"')
    parser.add_argument('-s', '--start', help='start date of the report; the start of this year by default', type=date_type)
    parser.add_argument('-e', '--end', help='bnd date of the report; the end of this year by default', type=date_type)
    parser.add_argument('-o', '--output_format', help='output format; JSON by default', choices=['json', 'csv'], default='json')
    parser.add_argument('-b', '--beautify', help='beautify the JSON output', action='store_true', default=False)
    parser.add_argument('-v', '--verbose', help='explain what happens', action='store_true', default=False)

    args = parser.parse_args()

    year = datetime.now().year
    start = args.start if args.start else datetime(year, 1, 1)
    end = args.end if args.end else datetime(year+1, 1, 1)

    if args.verbose:
        print('Arguments:')
        print('\tgnucash_file:', args.gnucash_file, sep='\t')
        print('\troot_account:', args.root_account, sep='\t')
        print('\tstart:\t', start, sep='\t')
        print('\tend:\t', end, sep='\t')
        print('\toutput_format:', args.output_format, sep='\t')
        print('\tbeautify:', args.beautify, sep='\t')
        print('Results:')

    gnucash = GnuCash(GnuCashSqlite(args.gnucash_file))
    intervals = make_intervals(start, relativedelta(months=1), end)
    gnucash.load_balances(intervals)

    accounts = gnucash.get_accounts_by_name(args.root_account)
    if not accounts:
        print('ERROR: Account "' + args.root_account + '" does not exist')
        sys.exit(errno.EINVAL)

    if args.output_format == 'json':
        indent = None
        if args.beautify:
            indent = 2

        results = {'dates': [str(d) for d in intervals], 'accounts': accounts[0].get_structure()}
        print(json.dumps(results, indent=indent))
    else:
        print(accounts[0].report_flat())

    sys.exit(0)
