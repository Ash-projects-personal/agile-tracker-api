# How this works, in plain words

A FastAPI service over SQLite with two routers: stories and sprints.
Stories carry points and can block each other; the dependency rules are
the interesting part. Marking a story DONE returns 409 while any
blocker is open, and the block endpoint rejects self blocks and cycles,
including long rings and diamonds, which the tests exercise directly.
Sprints add velocity (points completed per closed sprint), a rolling
velocity average over a window of closed sprints, capacity utilisation,
a burndown computed from sprint data, and retrospectives that can only
be recorded once a sprint is closed.

## Verification, and the one fix

This repo was the cleanest in the audit, and the rebuild is a
verification, not a rewrite. I cloned the live repo, installed the
pinned requirements, and ran its suite: 61 tests, all passing. The
README's most specific claim, 25 new v0.4.0 tests split 9, 8, 8 across
three files, counts out exactly.

The only edits are staleness in the notes section, and interestingly
they underclaimed: the notes listed retrospective tracking as missing
while the code and tests for it were already there, and the version
line still said v0.2. The corrected README in this tree lists the
retrospective endpoints, removes retrospectives from the missing list,
and says v0.4.0. Nothing else changed.
