#!/usr/bin/env python3
from urllib import request
from urllib.error import HTTPError
import datetime
from datetime import timedelta
import json
import pprint
printer = pprint.PrettyPrinter(indent=4)
pp = printer.pprint

API_BASE = "https://api.clockify.me/api/v1"


def confirm():
    """
    Ask user to enter Y or N (case-insensitive).
    :return: True if the answer is Y.
    :rtype: bool
    """
    answer = ""
    while answer not in ["y", "n"]:
        answer = input("OK to push to continue [Y/N]? ").lower()
    return answer == "y"


def report(report, config):
    for (date, description) in report:
        if date is None:
            print("Missing date for description: %s", description)
            continue
        if description is None or description == "":
            print("Missing description for date: %s", date)
            continue
        reportDay(date, description, config)


def zulu_date(date):
    return date.isoformat() + 'Z'


def reportDay(date, description, config):
    start = datetime.datetime.combine(
        date, datetime.time(hour=config['start_hour_utc']))
    end = start + timedelta(hours=config['work_hours'])
    entry = {
        "start": zulu_date(start),
        "billable": "true",
        "description": description,
        "projectId": config['project_id'],
        "taskId": config.get('task_id', None),
        "end": zulu_date(end),
    }

    try:
        response = post(
            f"{API_BASE}/workspaces/{config['workspace_id']}/time-entries", entry, config['api_key'])
        return response
    except HTTPError as e:
        msg = json.loads(e.read().decode())
        raise Exception(msg, entry) from e


def getWorkWeek(date=None):
    today = date if date else datetime.date.today()
    start_of_week = today - timedelta(days=today.isoweekday() - 1)
    if start_of_week.isoweekday() != 1:
        raise Exception("Start of week is not monday: ", start_of_week)
    work_week = [start_of_week + timedelta(days=i) for i in range(5)]
    return work_week


def post(url, body, api_key):
    req = request.Request(url, method="POST")
    req.add_header('Content-Type', 'application/json')
    req.add_header('X-Api-Key', api_key)
    data = json.dumps(body)
    data = data.encode()
    r = request.urlopen(req, data=data)
    content = r.read()
    response_body = json.loads(content)
    return r, response_body


def main():
    config = json.load(open('./config.json'))
    rep = None
    if config['mode'] == 'custom':
        rep = [(datetime.date.fromisoformat(date), description)
               for date, description in config['custom']]
    elif config['mode'] == 'week':
        week = getWorkWeek()
        rep = list(zip(week, config['week']))
    else:
        print(f"Unknown mode: {config.mode}")
        return
    pp(rep)

    if not rep:
        print("No report data. Exiting...")
        return
    if not confirm():
        print('Exiting...')
        return

    report(rep, config)
    print("Reported!")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Failed:")
        pp(e.args[0])
        pp(e.args[1])
        print("")
        raise
