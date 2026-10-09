# Assignment 2 Part 2.2 — saved-hotel RAG

Selected user instructions, October 8, 2026:

> We are going to continue this project to Part 2.2.

> Start working on the requriemrnts for this and let me know when you need me to do something

> I am using GPT-6 Astra

> What can I ask the chatbot. Everything I have asked hasnt worked. ALso make the words on the screen look a little neater

> DId you fix all documentation for this part as needed and under the same guidelines we have been following?

The supplied October 1 revision replaces local-storage-only completion with a
full two-stage RAG workflow. Preserve Add/Remove Local, ZIP context, simulated
dated rates/rooms and persistence; preserve the frozen discovery API and original
accounts/pricing/bookings. Generate SQL using the relevant schema, validate and
execute bounded read-only retrieval, then send the question and records to the
LLM for a grounded answer. Keep credentials and requests on the backend.

The in-class activity also calls for a startup-loaded prompt and persistent
role/stage/timestamp traces. The implementation uses existing dependencies,
additive schema v5, temporary-database tests and distinct live/mock evidence.
Student feedback led to collection-derived suggestions, missing-date/empty-state
guidance and clearer typography. No arbitrary-inventory query feature was added.

Development model: GPT-6 Astra, confirmed by the student. Application model:
gpt-4.1-mini, verified with real requests. The private key is excluded here.

Evidence: [research/mockup](../docs/assignment2-rag-research.md),
[runtime prompt](hotel-assistant.md), [controller](../backend/app/controllers/chat.py),
[read-only Model](../backend/app/chat_store.py), [verification](../docs/rag-context.md),
[AI disclosure](../docs/assignment2-ai-evidence.md), and [report](../report.md).
