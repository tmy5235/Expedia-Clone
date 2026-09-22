# Part 2 MVC, accounts, and personalized pricing

Implement the Activity 3 extension on a new branch while preserving Part 2
booking functions and the fictional supplied data. Identify Model, View, and
Controller changes before implementation. Add unique accounts, login/logout,
and a shared persistent search-history table linked to users. For signed-in
nonempty submissions, count the same normalized query per user per calendar day
in a documented time zone, including the current search. Searches 1–3 use the
stored base price; search 4 onward returns base × 1.20 once. Preserve base prices,
existing IDs, booking relationships, and restart persistence. Demonstrate account
errors, isolation, pricing, and a View → Controller → Model trace. Ask before
installing anything. DB Browser for SQLite installation was approved.


## Result

Implemented the version-2 SQLite migration, server-managed accounts/sessions,
shared search history, explicit MVC controllers, and Vue account controls.
Verified 28 backend tests and 14 frontend tests plus lint/build, browser pricing
and booking CRUD, and restart persistence. The [report](../report.md) traces the
$100 → $120 result through View, Controllers, and Model.

## Publication instruction

After auditing every project Markdown file and passing the checks, commit and
push the revision to GitHub and prepare the updated report for course submission.
The user will upload the report through the course site.
