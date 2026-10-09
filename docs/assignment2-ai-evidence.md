# Hotel Finder — AI development evidence

The September 29 sections below preserve Part 1 evidence. Current Part 2
disclosure and revisions follow in the October 8 section at the end.

Tool: OpenAI Codex desktop coding agent. Model: **GPT-6 Astra**, confirmed by the
user from the task model selector. Work recorded September 29, 2026.

Codex assisted with research, the early SVG mockup, FastAPI/Vue implementation,
verification and documentation. Official documentation was researched through web
browsing; file and terminal tools handled code changes and automated checks;
computer-use tools verified the running interface. No additional AI agent or
image-generation model was used. The user selected the scope and interface,
approved the Leaflet installation, reviewed the app and supplied the demo recording.

## Selected prompts and evidence

| User instruction | Result |
| --- | --- |
| “For today we only want to implement part 1” | [Discovery design](assignment2-design.md) separates external places from sample stays; no shortlist persistence. |
| “Read these directions and get an understanding… Report to me with next steps” | [Research and early mockup](assignment2-research.md) preceded implementation. |
| “Okay we can proceed with work” | [Discovery controller](../backend/app/controllers/discovery.py), [Vue page](../frontend/src/components/HotelDiscovery.vue) and [map](../frontend/src/components/HotelMap.vue). |
| “Approve Leaflet 1.9.4 installation” | Checked the environment, installed the approved exact version, verified npm tree and build. |
| “make the layout or interface more simple like this image” | Simplified header, ZIP search card and responsive list/map layout. |
| “Just use Hotel Finder as the name” / “Remove the word hotel in the middle image” | Hotel icon, teal decorative illustration and short headline. |
| “remove any redundant assignment descriptions” | App-focused documentation, consolidated verification and a smaller screenshot set. |

## Corrections and revised approaches

1. **Map initialization:** the first live search returned hotel cards but failed
   to render the map. Marker elements were configured before the map had a view.
   Setting bounds before creating/configuring markers fixed the error. Subsequent
   live and simulated browser checks displayed tiles, pins, center and radius.
2. **Keyboard selection:** Leaflet's default Enter action opened a popup without
   selecting the corresponding card. Explicit Enter/Space handlers now emit the
   provider place ID. Desktop and mobile browser checks confirmed both views agree.
3. **Dependency installation:** the initial sandboxed npm attempt stalled and was
   stopped. The already-approved exact installation then completed with network
   access. `npm ls leaflet --depth=0` confirmed version 1.9.4.
4. **Interface revision:** the early design became a simpler hotel-focused page.
   Center coordinates moved into a disclosure, selected hotel coordinates stayed
   visible, and the original booking interface moved to `/?demo=booking`.

The [verification record](assignment2-verification.md) documents inputs, expected
and observed results, and remaining limitations. Credentials and full provider
request URLs are excluded from the evidence.

## Part 2.2 — October 8, 2026

Development tool/model: OpenAI Codex desktop, **GPT-6 Astra**, confirmed by the
student. Application model: **gpt-4.1-mini** through backend OpenAI requests.
The deterministic `fixture-model-no-network` test double is not an LLM.
No subagents, image-generation tools or new dependencies were used for this work.

Codex assisted with the research, early SVG mockup, two-stage controller,
read-only SQL validation, additive SQLite migration, Vue interface, automated
and browser verification, and documentation. The student supplied requirements
and the private key, confirmed the development model, and tested the interface.
The student reports that the narrated recording is complete. Its accessible URL
and the assessed publication are being finalized in the report.

[Selected Part 2 instructions](../prompts/008-assignment2-rag.md) link to the
implementation and evidence. The [report AI evidence log](../report.md#ai-disclosure-and-evidence-log)
records failed and revised approaches: conflicting stage prompts returned SQL
instead of an answer; incomplete single-night metadata was rejected; an active
cursor retained a read lock during error persistence. Separate prompts, clarified
date rules and cursor cleanup corrected these failures, with regression coverage.
Student testing also prompted date/empty-collection guidance and cleaner text.

[Live and mock evidence](rag-context.md) are distinguished. Real calls verified
the question → proposed SQL → validated retrieval → second model request →
displayed answer workflow. No credentials are included in the evidence.
