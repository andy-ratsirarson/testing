# Browser Automation Service

A lightweight FastAPI backend that executes declarative browser automation steps by fetching and parsing HTML with `requests` + `BeautifulSoup`. No real browser required.

Supports **Human-in-the-Loop (HiL)** confirmation for sensitive form submissions, with execution state persisted to markdown files.

## Features

- **Navigate** to URLs
- **Fill and submit forms** by title, with optional HiL confirmation
- **Click buttons and links** by name
- Sequential step execution with per-step results
- File-based state persistence for pause/resume flows

## Quick Start

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn src.main:app --reload
```

API docs available at [http://localhost:8000/docs](http://localhost:8000/docs).

## API

### `POST /execute`

Execute a sequence of browser automation steps.

```json
{
  "steps": [
    {"type": "navigate", "url": "http://example.com"},
    {"type": "fill_form", "title": "Registration", "fields": {"firstname": "John", "lastname": "Doe"}, "hil": false},
    {"type": "click", "target": "link", "name": "Next Page"}
  ]
}
```

**Response:**

```json
{
  "execution_id": "some-uuid",
  "status": "completed",
  "results": [
    {"step_index": 0, "type": "navigate", "status": "success"},
    {"step_index": 1, "type": "fill_form", "status": "success"},
    {"step_index": 2, "type": "click", "status": "success"}
  ]
}
```

### `POST /execute/continue/{execution_id}`

Resume a paused HiL execution.

```json
{"action": "continue"}
```

Or cancel it:

```json
{"action": "cancel"}
```

## Step Types

| Step | Fields | Description |
|------|--------|-------------|
| `navigate` | `url` | Fetch the page at the given URL |
| `fill_form` | `title`, `fields`, `hil` | Find a form by its heading/title, fill the fields, and submit. If `hil: true`, pause for confirmation before submitting |
| `click` | `target` (`button` or `link`), `name` | Click a button or follow a link by its text |

## Human-in-the-Loop (HiL)

When a `fill_form` step has `hil: true`:

1. The form fields are filled but **not submitted**
2. The API returns `status: "waiting_for_confirmation"` with an `execution_id`
3. Call `POST /execute/continue/{execution_id}` with `{"action": "continue"}` to submit, or `{"action": "cancel"}` to skip
4. Execution state is persisted to a `.md` file in `executions/` so it survives server restarts

## Testing

```bash
pytest tests/ -v
```

The test suite includes a sample HTML page with a registration form, served by a local test server during tests.

## Output Folders

### `executions/`

Stores a markdown file for each completed automation run. Each file records the execution status, timestamp, and per-step results.

**Sample output** (`executions/<uuid>.md`):

```markdown
# Execution 96e16730-632d-4ddf-b6a5-9792c887d4f3

**Status**: completed

**Timestamp**: 2026-04-06T11:28:51.935086

## Results

- ✅ Step 0 (navigate): success — Navigated to http://127.0.0.1:8005/sample
- ✅ Step 1 (fill_form): success — Form 'Registration' submitted
```

### `submissions/`

Stores a markdown file for each form submission received by the `/submit` endpoint. Each file captures the timestamp and all submitted field values.

**Sample output** (`submissions/<uuid>.md`):

```markdown
# Submission bd4d9417-1100-44ef-886d-37e80e07ac26

**Timestamp**: 2026-04-06T11:28:35.786907

## Fields

- **firstname**: John
- **lastname**: Doe
- **csrf_token**: abc123
```

## Limitations

- **SSR only** -- does not execute JavaScript. Only works with server-rendered HTML.
- **Single execution** -- file-based storage has no concurrency safety.
- **Session not persisted across HiL** -- on resume, navigate steps are replayed to rebuild cookies.
