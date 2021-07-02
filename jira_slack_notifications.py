"""JIRA Notification app for macOS."""
import json
import logging
import sys
from base64 import b64encode
from datetime import datetime, timedelta
from json import JSONDecodeError
from tkinter import Tk, Label, Button, Entry, Frame

import requests

SLACK_WEBHOOK = ''  # e.g. https://hooks.slack.com/services/ABC123/ABC123/ABC123'
JIRA_SERVER = ''  # e.g. https://jira.example.com/
JIRA_FILTER = ''  # e.g. 12345
JIRA_ENDPOINT = f'{JIRA_SERVER}/jira/rest/api/latest/filter/{JIRA_FILTER}'
USER_EMAIL = ''  # The user/group email to which the issues are assigned

REGISTER = {}
WAIT_TIME = timedelta(minutes=30)

BUTTON_TEXT = {False: 'Notifications are not active', True: 'Notifications are active'}


class App(object):
    """
    The application class.
    """
    def __init__(self):
        self.slack_headers = {"Content-Type": "application/json"}
        self.jira_headers = None
        self.notification_status = False
        self.root = Tk()
        self.root.title('Notification Bot')
        self.frame = Frame(self.root)
        self.frame.pack()
        self.authenticate()
        self.notification_button = None
        self.label = None

    def authenticate(self):
        """
        Authentication method for user input.
        """
        Label(self.frame, text="Email").grid(row=0)
        Label(self.frame, text="Password").grid(row=1)
        email = Entry(self.frame)
        password = Entry(self.frame, show='*')
        email.focus()

        email.grid(row=0, column=1, padx=5, pady=5)
        password.grid(row=1, column=1, padx=5, pady=5)
        # cancel_button = Button(self.frame, text='cancel', command=self.cancel)
        # cancel_button.grid(row=2, column=0, sticky='NSEW', padx=5, pady=5)
        # ok_button = Button(self.frame, text='ok', command=lambda: self.check_authentication(email, password))
        # ok_button.grid(row=2, column=1, sticky='NSEW', padx=5, pady=5)
        self.root.bind('<Return>', lambda event: self.check_authentication(email, password))

    # def cancel(self):
    #     """
    #     Cancel button binding.
    #     """
    #     self.root.destroy()

    def check_authentication(self, email: Entry, password: Entry):
        """
        Authentication method for validation.
        :param email: user email.
        :param password: user password.
        """
        auth = "Basic " + b64encode(f'{email.get()}:{password.get()}'.encode()).decode('ascii').rstrip()
        self.jira_headers = {"Content-Type": "application/json", 'Authorization': auth}
        r = requests.get(url=JIRA_ENDPOINT, headers=self.jira_headers)
        try:
            r.json()
            r.raise_for_status()
            self.frame.destroy()
            self.launch_service()
        except JSONDecodeError:
            logging.exception(f'\n{"*" * 75}\n{datetime.now().replace(microsecond=0)} - Password Error')
            password.delete(0, 'end')
            self.authenticate()

    def launch_service(self):
        """
        Initiate polling routine.
        """
        self.frame = Frame(self.root)
        self.frame.pack()
        self.notification_button = Button(text=BUTTON_TEXT[self.notification_status], command=self.toggle_status)
        self.notification_button.pack()
        self.label = Label()
        self.label.pack(padx=20, pady=5)
        self.poll_cycle()

    def poll_cycle(self):
        """
        Polling routine.
        """
        try:
            r = requests.get(url=JIRA_ENDPOINT, headers=self.jira_headers)
            url = json.loads(r.text)['searchUrl']
            r = requests.get(url=url, headers=self.jira_headers)
            issues = json.loads(r.text)['issues']
            self.label['fg'] = 'red' if issues else 'black'
            if self.notification_status:
                self.process_notification(issues)
            self.label['text'] = f'{datetime.now().replace(microsecond=0)} | Tickets: {len(issues)}'
            logging.info(f'{datetime.now().replace(microsecond=0)} issues: {len(issues)}')
            self.root.after(59000, self.poll_cycle)
        except:
            logging.exception(f'\n{"*" * 75}\n{datetime.now().replace(microsecond=0)} - Runtime Error')
            self.root.destroy()
            sys.exit()

    def process_notification(self, issues: dict):
        """
        Send notification if any issue is found.
        :param issues: the dictionary of issues retrieved from Jira.
        """
        if not issues:
            # self.remove_expired()
            self.remove_assigned(issues)
            for issue in issues:
                if issue['fields']['assignee']['emailAddress'] == USER_EMAIL:
                    text = f"{JIRA_SERVER}/jira/browse/{issue['key']} | " \
                           f"Priority: {issue['fields']['priority']['name']}" \
                           # f" | {getpass.getuser()[:2]}"
                    if issue['key'] in REGISTER:
                        time_passed = datetime.now() - REGISTER[issue['key']]
                        if time_passed > WAIT_TIME:
                            REGISTER[issue['key']] = datetime.now()
                            text = 'Reminder: ' + text
                        else:
                            continue
                    payload = json.dumps({"text": text})
                    requests.post(url=SLACK_WEBHOOK, data=payload, headers=self.slack_headers)
                    REGISTER.update({issue['key']: datetime.now()})
                    logging.info(f'Notification sent for {issue["key"]}')
        else:
            REGISTER.clear()

    # @staticmethod
    # def remove_expired():
    #     """
    #     Remove issues that sat in the register for longer than the WAIT_TIME.
    #     """
    #     to_remove = []
    #     for issue, time in REGISTER.items():
    #         if time + WAIT_TIME < datetime.now():
    #             to_remove.append(issue)
    #     for issue in to_remove:
    #         REGISTER.pop(issue)

    @staticmethod
    def remove_assigned(issues: dict):
        """
        Remove issues that have been assigned.
        :param issues: the dictionary of issues retrieved from Jira.
        """
        for issue_key in list(REGISTER.keys()):
            if issue_key not in [issue['key'] for issue in issues]:
                REGISTER.pop(issue_key)

    def toggle_status(self):
        """
        Toggle the notification status and corresponding button text.
        """
        self.notification_status = not self.notification_status
        self.notification_button['text'] = BUTTON_TEXT[self.notification_status]


if __name__ == '__main__':
    logging.basicConfig(filename=f'wsn.log')
    app = App()
    app.root.mainloop()
