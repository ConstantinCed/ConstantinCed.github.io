# ConstantinCed.github.io

Personal website at https://constantinced.github.io/.

## Automatic publications

The `Update publications and publish website` GitHub Actions workflow checks arXiv
once a day at 15:23 UTC (8:23 a.m. Pacific daylight time / 7:23 a.m. standard time).
New papers are added newest first, committed to `main`, and published to Pages.
The query searches `au:Cedillo`, then verifies the full author name before adding
anything. Revised versions do not create duplicates. Existing entries, titles,
author formatting, and equal-contribution notes remain exactly as written.

The workflow can also be run from Actions → Update publications and publish
website → Run workflow. An arXiv outage or invalid response leaves the site intact
and fails the run visibly in Actions. Future daily runs try again.

The workflow publishes directly using a Pages artifact because commits made with
`GITHUB_TOKEN` do not themselves trigger GitHub Pages builds. Direct deployment
has been verified with this repository’s existing Pages configuration. No personal
access token or other secret is needed.

GitHub may disable scheduled workflows after 60 days without repository activity.
If that happens, open the workflow in Actions and click **Enable workflow**, then
**Run workflow** to catch up. Running a daily check alone does not prevent this.

Edit publication entries directly in `index.html` between the publications
comments. To refresh locally (Python 3.12; no third-party dependencies):

```sh
python -m unittest discover -s tests -v
python scripts/update_publications.py
```

For an offline run against a saved arXiv Atom response:

```sh
python scripts/update_publications.py --feed /path/to/feed.xml
```
