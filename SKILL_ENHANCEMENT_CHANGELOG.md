# DevSmart Skill Enhancement

## Added

- Strong Machine PRD schema: business rules, permissions, domain/database separation, API contracts, errors, tests and traceability.
- Deterministic Machine PRD consistency gates for stable IDs, references, error codes, API completeness and blocking questions.
- `devsmart.architecture.generate` and `devsmart.architecture.validate`.
- `devsmart.codegen.plan` and `devsmart.codegen.validate-plan` with DAG, write scope and requirement coverage checks.
- `devsmart.feedback.diagnose` and `devsmart.feedback.repair` with structured diagnosis and anti-cheating repair constraints.
- End-to-end workflow definition at `backend/workflows/llm_code_generation.yaml`.

## Important boundary

The workflow now defines the `execute_code_tasks` task-loop contract, but the current repository does not yet contain a sandboxed filesystem/command executor or a unified-diff applier. Those runtime components must be connected before DevSmart can autonomously write files, run commands and apply repairs.
