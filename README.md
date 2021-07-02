# Jira Slack Notifications

## Get a Slack notification when a Jira issue is assigned to you or you team.

### Install requirements

From the project root, install requirements as follows

```
python -m pip install -r requirements.txt
```

### Add your settings

Open the *jira_slack_notifications.py* file and add your Jira and Slack settings.

- SLACK_WEBHOOK: following this [guide](https://api.slack.com/messaging/webhooks) to setup you Slack webhook

- JIRA_SERVER: the Jira server you wish to use, e.g. https://jira.example.com/

- JIRA_FILTER: the Jira filter to which you wish to subscribe, e.g. 12345

- USER_EMAIL: the user/group email to which the issues are assigned

### Run the app

Run the app with the following command

```
python jira_slack_notifications.py
```
