import argparse
import json


def print_chart_format(json_data, total=False):
    if total:
        print json_data.values()
    else:
        for k, v in json_data.items():
            print '%s' % k
            print v.values()
            print '\n'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Stackalytics status update.')
    parser.add_argument('-p', '--filepath', help='Path to file with status',
                        action='store')
    parser.add_argument('-d', '--data', help='JSON data with status',
                        action='store')
    parser.add_argument('-t', '--total', action='store_true',
                        help='If True, total counter will be resolved',
                        default=False)
    args = parser.parse_args()
    if args.filepath is None == args.data is None:
        raise argparse.ArgumentTypeError('Either filepath or data should '
                                         'be specified')

    json_data = None
    if args.filepath:
        f = open(args.filepath)
        json_data = json.load(f)
    elif args.data:
        json_data = json.loads(args.data)
    print_chart_format(json_data, args.total)
