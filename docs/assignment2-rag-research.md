# Part 2 research and design — October 8, 2026

Prepared before chatbot source implementation. The pasted October 1 assignment
revision and RAG activity are the requirements; Canvas tutorial access could not
be verified without login. Existing local-storage implementation and its evidence
provide the starting point.

- [Booking.com AI Trip Planner](https://news.booking.com/bookingcom-launches-new-ai-trip-planner-to-enhance-travel-planning-experience): conversational refinement and visible hotel choices are useful. Its booking/live-price context does not apply here. Adopt follow-ups and visible supporting records, with explicit simulated-data labels.
- [OpenAI Chat Completions](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create): backend sends role-based context and can request JSON output. Use separate query and grounded-answer requests; validate JSON and SQL independently.
- [GPT-4.1 mini](https://developers.openai.com/api/docs/models/gpt-4.1-mini): documented Chat Completions and structured-output support. Configurable candidate model; account access and a successful live request still require verification.
- [Python sqlite3](https://docs.python.org/3/library/sqlite3.html) and [SQLite authorizer](https://www.sqlite.org/c3ref/set_authorizer.html): authorization runs during statement preparation. Use a read-only connection plus a default-deny authorizer, bounded work/results, and separate trusted conversation writes. A SELECT-prefix check alone is insufficient.

[Early mockup](screenshots/assignment2-rag-early-mockup.svg) preserves discovery
and adds a saved-conversation panel, question composer, pending/error/empty states
and a retrieval disclosure. Rates, stay totals and availability come only from
saved dated classroom records. Missing nights cannot imply availability; checkout
is excluded. The response must expose its supporting records for inspection.

## Implementation follow-through

The candidate/access uncertainty above records the pre-implementation research.
Subsequent real calls verified `gpt-4.1-mini` with the student’s configured key;
see [live verification and revised approaches](rag-context.md). The early mockup
is retained unchanged, with final layout differences explained in the report.
