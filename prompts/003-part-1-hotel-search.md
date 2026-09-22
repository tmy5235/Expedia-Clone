# Part 1 Hotel Search

## Selected instruction

> Focus only on Part 1. Use a very basic search box and results table; the interface does not need graphical styling.

## Result

The calculator was replaced with a basic hotel-name search. FastAPI reads and
joins the supplied hotel and trip CSV files, while Vue displays matching stays
in a plain labeled table with loading, error, and no-results messages. This
historical Part 1 checkpoint intentionally predates the Part 2 SQLite work.
Current search reads SQLite and supports signed-in personalized pricing;
[the Activity 3 prompt](006-accounts-personalized-pricing.md) records that later scope.
