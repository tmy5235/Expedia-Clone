# Part 2.2 submission checklist

The deliverable is one `report.md` uploaded to Canvas. The supplied revised
assignment also requires a linked screen-recorded demonstration and accessible
project/evidence links. Local storage alone does not fulfill revised Part 2.2.

## Already prepared

- Working local storage and two-stage RAG chatbot, preserving the frozen discovery API and original booking workflow.
- [Report](../report.md), setup/configuration, MVC responsibilities and limitations.
- [Research and early mockup](assignment2-rag-research.md).
- [Verification](rag-context.md), including real model calls, labeled fixed JSON/mocks, SQL/records/answers, rejected queries and persistence evidence.
- [AI disclosure](assignment2-ai-evidence.md) and [selected development prompts](../prompts/008-assignment2-rag.md).

Latest recorded checks: 228 backend tests, 47 frontend tests, lint/build and
browser verification passed. The latest suggested-question reliability fix reran those suites and verified
four real-model cases using entirely fictional fixtures.

## Final publication status

- Student reports the recording is complete; its accessible link is still needed.
- Source and evidence are published on `rag_integration`. Assessed application
  commit: `dd495d1bc8b979694eac94af5a9b32b65f4bed9c`.
- Report source/evidence links are pinned to that commit. The repository is public.
- The final remaining report edit is the recording URL. After verifying access,
  upload the root `report.md` to Canvas. Do not upload before inserting that link.

The report is already written; the student does not need to start another report
from scratch. A deployed public website, vector database and Figma file are not
specified requirements. Deadline in the supplied revision: October 8, 2026,
11:59 PM Eastern.

## Recording outline

- Show the running app, ZIP, observation date, synchronized list/map, and source attribution. Save hotels with **Add to Local**; show deduplication/saved status, removal and persistence. Explain that nightly rates and rooms are simulated course data.
- In **Compare saved hotels**, use a suggestion populated from actual saved dates/ZIP. Show a successful real-model single-night question and a two-night comparison. Default saved nights are October 10–14, 2026; checkout is excluded. Use dates present in your database.
- Expand **View supporting records & SQL**. Show the original question, first model request, proposed SQL/parameters, checked retrieval, second model request containing the question and records, and displayed answer. State what you expected and compare totals/nights/rooms with what was retrieved and displayed.
- Ask about missing dates/data, such as a stay on October 20, 2026 with the default dataset. Show an honest no-match or insufficient-data response.
- Switch explicitly to the labeled mock server for rejected-query evidence. Follow [the repeat instructions](rag-context.md#student-recording-and-final-verification); the dated DELETE question triggers a deliberate unsafe proposal. Show rejection and unchanged hotel/night rows. Do not describe this as a live LLM result.
- Refresh and restart both services using the same database. Reload the saved conversation and demonstrate that saved data and trace timestamps/steps persist. Explain any observed limitation rather than claiming every question is supported.

The current chatbot compares saved available stays using ZIP and date context.
The assignment requires local database retrieval; it does not require searching
all hotels in Geoapify or answering arbitrary database questions. The ZIP/date
interaction is this implementation's scope, not an assignment-wide rule.
