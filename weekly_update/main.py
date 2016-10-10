# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import collections
import json

import datetime
import requests
import time

from weekly_tools import counter_to_chart

metric_to_input = dict(mark='mark',
                       patch='patch',
                       review='review',
                       commit='commit',
                       bugr='resolved-bug',
                       bugf='filed-bug',
                       email='email')

act_fmt = {
    'mark': '{record_type:6}[{module}] {parent_url}',
    'commit': '{record_type:6}[{module}] '
    'http://github.com/openstack/{module}/commit/{commit_id} {subject}',
    'bugr': '{record_type:6}[{module}] {web_link} {status}',
    'bugf': '{record_type:6}[{module}] {web_link} {status}',
    'patch': '{record_type:6}[{module}] {parent_url} {subject}',
    'review': '{record_type:6}[{module}] {url}',
    'email': '{record_type:6}[{module}] {email_link} {subject}'}

activity_format = {
    'commit': lambda act: dict(record_type=metric_to_input[act['record_type']],
                               module=act['module'],
                               url='http://github.com/openstack/'
                                   '%(module)s/commit/%(commit_id)s' % {
                                   'module': act['module'],
                                   'commit_id': act['commit_id']},
                               summary=act['subject']),
    'mark': lambda act: dict(record_type=metric_to_input[act['record_type']],
                             module=act['module'],
                             url=act['parent_url']),
    'review': lambda act: dict(record_type=metric_to_input[act['record_type']],
                               module=act['module'],
                               url=act['url']),
    'email': lambda act: dict(record_type=metric_to_input[act['record_type']],
                              module=act['module'],
                              url=act['email_link'],
                              summary=act['subject']),
    'bugr': lambda act: dict(record_type=metric_to_input[act['record_type']],
                             module=act['module'],
                             url=act['web_link'],
                             status=act['status']),
    'bugf': lambda act: dict(record_type=metric_to_input[act['record_type']],
                             module=act['module'],
                             url=act['web_link'],
                             status=act['status']),
    'patch': lambda act: dict(record_type=metric_to_input[act['record_type']],
                              module=act['module'],
                              url=act['parent_url'],
                              summary=act['subject'])

}


def parse_activity(activity):
    record_type = activity['record_type']
    if 'parent_commitMessage' in activity and 'subject' not in activity:
        activity['subject'] = activity['parent_commitMessage'].split('\n')[0]
    elif 'parent_subject' in activity and 'subject' not in activity:
        activity['subject'] = activity['parent_subject']
    return record_type, act_fmt[record_type].format(**activity)


def unix_time(dt):
    return int(time.mktime(dt.timetuple()))


def calc_timeinterval(days):
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=days)
    return dict(start_date=unix_time(start_date),
                end_date=unix_time(end_date))


def get_report(username, metric='all', days=7, module=None):
    params = dict(release='all',
                  metric=metric,
                  project_type='all',
                  user_id=username,
                  page_size=300)
    if module:
        params['module'] = module
    params.update(calc_timeinterval(days=days))
    url = 'http://stackalytics.com/api/1.0/activity'
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()


def timestamp_to_date(dt):
    date = datetime.datetime.fromtimestamp(float(dt)).date()
    return str(date)


def prepare_counter():
    return {'mark': 0,
            'patch': 0,
            'commit': 0,
            'resolved-bug': 0,
            'filed-bug': 0,
            'email': 0,
            'review': 0}


def main():
    parser = argparse.ArgumentParser(description='Stackalytics status update.')
    parser.add_argument('username', action='store', nargs='+',
                        help='Launchpad id of user or email '
                             'if no Launchpad id is mapped.')
    parser.add_argument('--project', action='store',
                        help='project name for OpenStack')
    parser.add_argument('-d', '--days', action='store', type=int, default=7,
                        help='Number or days to take status')
    parser.add_argument('-m', '--metric', choices=('all', 'mark',
                                                   'patch', 'commit',
                                                   'resolved-bug',
                                                   'filed-bug',
                                                   'email',
                                                   'review'), default='all',
                        help='User metric which will be reported')
    parser.add_argument('--chart', action='store_true',
                        help='If True, counter will be resolved to convenient '
                             'chart format', default=True)

    args = parser.parse_args()

    status_report = collections.OrderedDict()
    user_counter = {}
    total_counter = prepare_counter()
    for username in args.username:
        report = get_report(username, metric=args.metric, days=args.days,
                            module=args.project)
        if report['activity']:
            username = report['activity'][0]['author_name']
        user_counter[username] = prepare_counter()
        for activity in sorted(report['activity'], key=lambda a: a['date']):
            if activity['record_type'] not in activity_format.keys():
                continue
            current_time = activity['date']
            current_time = timestamp_to_date(current_time)
            if current_time not in status_report:
                status_report.update({current_time: {}})
            record_type, resolved_act = parse_activity(activity)
            if username not in status_report[current_time]:
                status_report[current_time][username] = []
            status_report[current_time][username].append(resolved_act)
            user_counter[username][metric_to_input[record_type]] += 1
            total_counter[metric_to_input[record_type]] += 1

    datedict = calc_timeinterval(args.days)
    if not args.chart:
        init_msg = 'Status report from %(start)s to %(end)s:\n' % {
            'start': timestamp_to_date(datedict['start_date']),
            'end': timestamp_to_date(datedict['end_date'])}
        for i in range(len(init_msg) - 1):
            init_msg += '-'
        print init_msg
        print '\n'
    else:
        status_report['counters'] = {}
        for name, counter in user_counter.items():
            status_report['counters'][name] = map(lambda x: list(x),
                                                  counter.items())
        status_report['counters']['total'] = map(lambda x: list(x),
                                                 total_counter.items())
    print json.dumps(status_report, indent=4, sort_keys=True)
    print '\n'
    if not args.chart:
        result = ['User counters:\n--------------',
                  json.dumps(user_counter, indent=4, sort_keys=True),
                  'Total counter:\n--------------',
                  json.dumps(total_counter, indent=4, sort_keys=True)]
        print '\n\n\n'.join(result)
