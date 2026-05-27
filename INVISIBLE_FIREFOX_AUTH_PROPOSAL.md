# Invisible Firefox auth_token Extractor (proposal)

> Status: Draft proposal
> Created: 2026-05-26
> Tracking discussion: TBD

## Goal

Optional helper module that lets users perform the X login flow in a real browser once, then dumps the resulting cookies to a file that twikit's existing `load_cookies` can read directly. No change to twikit's HTTP core.

## Motivation

`ToProtectYourAccount.md` already recommends `save_cookies` / `load_cookies` to avoid repeated `login` calls (which are heavily monitored and trigger bans). The first login still has to happen somewhere though, and increasingly X's login flow requires JS challenges (Castle Token, ondemand.s.js fingerprinting) that pure HTTP can't pass cleanly. Relevant open PRs that touch this surface: #324, #393, #410.

A small helper that opens a stealth browser, performs the login, and writes a `cookies.json` that twikit then loads, would let users get a working auth_token + ct0 without touching twikit's HTTP layer at all.

## Proposed module

A new optional `twikit.helpers.invisible_firefox` module that calls `invisible_playwright` (https://github.com/feder-cr/invisible_playwright). The wrapper drives a patched Firefox 150 (https://github.com/feder-cr/invisible_firefox, MPL-2, same license as Firefox upstream, fingerprint patches at the C++ source level so no JS shims to detect).

Used as:

```python
from twikit.helpers.invisible_firefox import login_to_cookies
login_to_cookies(username, email, password, output="cookies.json")

# then the usual twikit path
client = Client(language="en-US")
client.load_cookies("cookies.json")
```

## Out of scope

No change to twikit's HTTP core. No change to existing `login` / `save_cookies` / `load_cookies` methods. Optional dependency only loaded when the helper is imported.

## Maintenance

Issues against the helper backend route to feder-cr/invisible_playwright. Only ask of this repo would be the small helper module plus a docs entry.
