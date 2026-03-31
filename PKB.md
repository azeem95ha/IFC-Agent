# Project Knowledge Base

## 2026-03-31

- Lesson: the repository-level instructions require persistent project notes in `context.md` and `PKB.md`, but those files were missing.
  Resolution: created both files immediately during phase 1 and recorded the migration context plus implementation notes.

- Lesson: phase 1 needs session metadata without exposing sensitive fields like API keys or raw model objects.
  Resolution: introduced a dataclass `Session` for internal state and a separate Pydantic `SessionMeta` response model for API responses.

- Lesson: session expiry must also clean filesystem artifacts, not only remove in-memory state.
  Resolution: `SessionManager.cleanup_expired()` and `delete()` both remove the session entry and recursively delete that session's storage directory.

- Lesson: mutable session objects must be returned by the session manager, otherwise later tool and agent mutations would be lost.
  Resolution: `SessionManager.create()` and `get()` now return the live `Session` instance instead of a copied dataclass.

- Lesson: import paths must work both from the repository root (`backend.main`) and from the backend module layout expected by `uvicorn main:app`.
  Resolution: backend imports use package-relative imports with a local fallback path.

- Lesson: the Windows sandbox intermittently fails on `apply_patch` and some commands executed with `workdir=backend`, even when file contents are valid.
  Resolution: completed the affected edits with direct file writes and verified the API behavior with `TestClient` from the repository root.

- Lesson: the IFC tool migration depends on helpers that were previously implicit in the Streamlit monolith, especially active-model lookup, session reinitialization, IFC value conversion, and cached IFC entity loading.
  Resolution: extracted those behaviors into `backend/tools/common.py` so the three tool modules can stay Streamlit-free while preserving the original behavior.

- Lesson: copying shared assets in parallel with directory creation can race on this environment.
  Resolution: create backend directories first, then copy `prompt.md` and `ifc_entities.pkl` after the target path exists.

- Lesson: phase 2 verification should prove importability, not only file creation.
  Resolution: imported the new query, geometry, authoring, and entity-schema modules under Python 3.11 and confirmed there are no `streamlit` imports or `@tool` decorators in `backend/`.

- Lesson: in this installed LangChain version, `tool()` cannot infer a schema directly from `functools.partial` objects.
  Resolution: phase 3 binds session context by generating explicit async wrapper functions, then copies the original tool signatures and annotations onto those wrappers before registering them as LangChain tools.

- Lesson: SSE verification should cover the streamed wire format, not only normal route imports.
  Resolution: exercised `/api/sessions/{session_id}/chat` with FastAPI `TestClient` and confirmed it emits `data: {...}` events followed by `done` for the no-model case.

- Lesson: `ifcopenshell.file` in this environment does not implement `len(model)`.
  Resolution: entity counts for uploaded and downloaded models are computed with `sum(1 for _ in model)` instead of `len(model)`.

- Lesson: a failed response-model construction after successful IFC parsing can leave partially updated session state if the mutation happens too early.
  Resolution: phase 4 computes `ModelInfo` completely before mutating the session, then updates the session only after the upload flow is known to be valid.

- Lesson: a JSON field named `schema` on a Pydantic model triggers a warning because it shadows a `BaseModel` attribute.
  Resolution: `ModelInfo` stores the field internally as `schema_name` and exposes it on the API with the alias `schema`.

- Lesson: in this PowerShell setup, `npm` resolves to `npm.ps1`, which is blocked by the machine execution policy.
  Resolution: use `npm.cmd` for frontend package commands.

- Lesson: Vite/Tailwind verification can fail inside this sandbox because native binaries and child process spawning hit `EPERM` restrictions.
  Resolution: run `npm run build` outside the sandbox when verifying the frontend build.

- Lesson: some frontend dependencies ship without TypeScript declarations.
  Resolution: add a local `frontend/src/vite-env.d.ts` module declaration for `react-highlight` when needed instead of blocking the build.

- Lesson: phase 6 cleanup should verify explicit error-path behavior, not only success paths.
  Resolution: exercised wrong file type upload (`422`), oversized upload (`413`), and no-model chat streaming before closing the migration.

- Lesson: even when the frontend build passes, the generated JS bundle can still be heavier than desired.
  Resolution: phase 6 closes the migration as functional, but bundle splitting remains a sensible follow-up optimization because Vite reports a large chunk warning.

- Lesson: Gemini/LangChain can return `AIMessage.content` as a list of structured content blocks instead of a plain string.
  Resolution: normalize the final agent message in `backend/services/agent_service.py` by extracting `text` fields from content blocks before sending SSE `message` events to the frontend.
