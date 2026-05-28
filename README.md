# MV Carbon Tracker

This repo checks several carbon / RGGI-related webpages every 30 minutes and emails Grant and Anna when any monitored page changes.

## Sender

`moleculecarbonnews@gmail.com`

## Recipients

- `grant@molecule-ventures.com`
- `anna@molecule-ventures.com`
- `nick@molecule-ventures.com`

## Email subject line

`MV Carbon Tracker: RGGI Website Changes`

## Monitored pages

- Virginia DEQ Carbon Trading  
  https://www.deq.virginia.gov/air-energy/greenhouse-gases/carbon-trading

- RGGI New Participation  
  https://www.rggi.org/program-overview-and-design/new-participation

- RGGI Releases  
  https://www.rggi.org/news-releases/rggi-releases

- Virginia Town Hall Chapter 1751  
  https://townhall.virginia.gov/l/ViewChapter.cfm?ChapterID=1751

## Important setup note

Do **not** hardcode the Gmail app password in the code.

Add it as a GitHub repository secret:

- Secret name: `EMAIL_PASSWORD`
- Secret value: the 16-character Google App Password for `moleculecarbonnews@gmail.com`

## Upload instructions

Your repo should look like this:

```text
.github/
  workflows/
    monitor.yml
README.md
monitor.py
requirements.txt
```

The workflow file must be located at:

```text
.github/workflows/monitor.yml
```

If `monitor.yml` is in the main/root folder, GitHub Actions will not recognize it.

## First run

The first run saves the baseline version of each webpage. It usually will not send an email.

Future runs email the recipients only if one or more pages change.

## Manual test

1. Go to the repo's **Actions** tab.
2. Click **MV Carbon Tracker**.
3. Click **Run workflow**.
4. Confirm the run succeeds.

The workflow also runs automatically every 30 minutes.
