# Workflow: how to make a change

Every change follows the same loop (§2). Section §3 adds the extra steps for specific kinds of
change: find yours before you start. All commands run in Git Bash from the repository root
unless a `cd` is shown.

## 1. Start of every work session

```bash
git switch main
git pull                 # rebases, see CONTRIBUTING §1.1
make setup               # only if uv.lock or package-lock.json changed (cheap to run anyway)
make db                  # if the database is not running
make migrate             # apply migrations your teammates merged
```

## 2. The standard loop

| # | Step | Command / action |
|---|---|---|
| 1 | Pick one small task (one module, one behaviour) | Say in the group chat what you are starting, especially if it touches shared code |
| 2 | Branch from an up-to-date `main` | `git switch -c m5/vote-endpoint` (format: `<module>/<short-description>`; `ui/...`, `chore/...`, `docs/...` for non-module work) |
| 3 | Code in your module's folders | See §3 for the extra steps of your change type |
| 4 | Test locally | `make test`, plus clicking through the feature with `make dev` |
| 5 | Commit in small steps | `git commit -m "feat(m5): add vote endpoint"` (see §4) |
| 6 | Catch up with `main` | `git fetch origin && git rebase origin/main`, resolve conflicts (CONTRIBUTING §3), then `make migrate` if new migrations arrived |
| 7 | Run every check | `make check` must end with "All checks passed." |
| 8 | Push and open a pull request | `git push -u origin HEAD`; fill in the template; open it as a **draft** early if you want feedback |
| 9 | Wait for CI + one review | Answer comments with new commits (no force-push after review starts, so reviewers can see what changed) |
| 10 | Merge | **Squash and merge**; the branch is deleted automatically |
| 11 | Clean up locally | `git switch main && git pull && git branch -d m5/vote-endpoint` |

Keep branches alive for 1–3 days. Something bigger? Split it into several PRs that each keep
`main` working (e.g. model + migration first, endpoint second, UI third).

## 3. Extra steps by type of change

### 3.1 Add or change an API endpoint

1. Request/response models in `schemas.py` (this is the contract the frontend sees).
2. Logic in `service.py`; the endpoint in `router.py` only calls the service.
3. Tests in `backend/tests/<module>/`.
4. `make api-types`, then commit `frontend/openapi.json` and `frontend/src/lib/api/schema.d.ts`
   **in the same PR** (CI fails if they are stale).
5. Changed or removed a field that someone else's frontend code uses? `make lint` shows the type
   errors; fix them or coordinate with their owner before merging.

### 3.2 Add or change a database table

1. `git fetch origin && git rebase origin/main` **first**, so your migration builds on the latest one.
2. Edit your module's `models.py`.
3. `make migration m="m4 add reviews table"`.
4. **Open and read the generated file** in `backend/migrations/versions/`. Autogenerate misses some
   things (extensions, data migrations, renames that look like drop + add).
5. `make migrate`, then test. To test the downgrade: `cd backend && uv run alembic downgrade -1 && uv run alembic upgrade head`.
6. Never edit a migration that is already on `main`: add a new one.
7. `make check` reports **two heads** (someone merged a migration meanwhile)?
   `cd backend && uv run alembic merge heads -m "merge"`, then `make migrate`, then commit the
   merge file.

### 3.3 Add a dependency

1. Separate small PR, merged quickly (avoids lock-file conflicts for everyone).
2. Backend: `cd backend && uv add <package>` (dev tool: `uv add --dev <package>`; AI-only:
   `uv add --optional ai <package>`). Frontend: `cd frontend && npm install <package>`.
3. Commit `pyproject.toml` + `uv.lock` or `package.json` + `package-lock.json`.
4. Tell the team to run `make setup` after pulling.

### 3.4 Change a shared contract

Applies to `backend/app/shared/`, `backend/app/core/`, `frontend/src/lib/`, `Makefile`, CI, and
the props of `@/ui` components.

1. Announce it in the group chat first: what changes and why.
2. A PR containing only that change, plus the updates to every caller.
3. Every affected module owner reviews it (CODEOWNERS requests them automatically).
4. Merge it before building features on top of it.

### 3.5 Add a page or frontend component

1. Component in `frontend/src/features/<feature>/components/`. Data fetching goes in `hooks/` and
   API calls in `api.ts`; views receive data through props.
2. Export what other features may use from the feature's `index.ts`.
3. A new route is a thin `frontend/src/app/<route>/page.tsx` that only renders feature components.
4. Use `@/ui` components and token classes only; `make lint` rejects hard-coded colours.
5. Missing a component or variant? Ask the UI owner, or open a small PR in `src/ui` and add it to
   the `/dev/ui` page.

### 3.6 Add a setting or environment variable

1. Add the field to `backend/app/core/config.py` (backend) or read `process.env` (frontend).
2. Add it to `backend/.env.example` / `frontend/.env.example` with an empty or safe value.
3. If it is needed to run the app, document it in the variables table of the root `README.md`.
4. Tell the team: everyone has to add it to their local `.env`.
5. Never commit real keys. A key that leaked into git must be revoked and replaced, not just deleted.

### 3.7 Fix a bug

1. Write a test that reproduces the bug (it fails).
2. Fix it; the test passes.
3. Branch name `fix/...` or `<module>/fix-...`; commit type `fix`.

## 4. Commit messages

```
<type>(<scope>): <what, in imperative mood>

feat(m5): add vote endpoint
fix(m1): set secure cookie flag in production
refactor(ui): split Sheet into header and body
docs: explain migration merge
chore: add httpx dependency
test(m3): cover empty search query
```

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`. Scope: module (`m1`…`m7`), `ui`, `core`,
`ci`. One logical change per commit.

## 5. Reviewing a pull request

Aim to review within one day. Check that:

- [ ] It does what the description says, and you could run it (`git switch <branch>` + `make dev`)
- [ ] Code stays inside the author's module, or shared changes were announced (§3.4)
- [ ] Tests cover the new behaviour
- [ ] Migrations are readable, and `openapi.json` / `schema.d.ts` were regenerated if the API changed
- [ ] No Google data is stored besides `place_id` / coordinates with a fetch date
- [ ] No secrets, debug prints or commented-out code
- [ ] Comments and docs are in English; user-facing text is in Vietnamese

Use GitHub's *Request changes* only for real problems; label optional ideas as "nit:".

## 6. End of the week

- Merge every finished PR into `main` before the weekly review.
- `main` must run from a fresh clone: `make setup && make db && make migrate && make dev`.
- Back up the demo database: `make backup url="<demo database URL>"`.
