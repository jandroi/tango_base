# Testing Principles

> Canonical reference for all testing in this office.
> Version: 2026-04-20
> These principles allow us to delegate supervision to tests — they must be comprehensive enough that passing tests means the feature works for every user path.

---

## Core Philosophy

Tests are our automated supervisors. If a feature has passing tests, any agent or human should be able to trust that the feature works without manually checking it. This only works if tests cover **every interaction a user can have**, not just the happy path.

A test suite that only checks "can I create a record" is worthless. A test suite that checks create, read, update, delete, permissions, edge cases, navigation, and error states — that's a supervisor.

---

## Principle 1: Exhaustive Interaction Coverage

Every view or endpoint must be tested for **every possible user interaction**, not just the primary action.

For a view, the test suite must cover:

| Category | Examples |
|---|---|
| **Access** | Authenticated, unauthenticated, wrong permissions, superuser |
| **Navigation** | Open the page, go back, go forward, breadcrumb links, navbar links |
| **Actions** | Every button, every link, every form submit, every filter, every sort |
| **Form inputs** | Valid data, empty fields, special characters (`<script>`, `'; DROP`, unicode), max length, min length |
| **State variations** | Empty list, single item, many items, paginated, filtered to zero results |
| **Error paths** | 404 (bad PK), 403 (wrong user), 405 (wrong HTTP method), validation errors |
| **Redirects** | After create → correct destination, after delete → correct destination, after login → original page |

**Rule:** If a user can click it, type in it, or navigate to it — there must be a test for it.

---

## Principle 2: Structured, Descriptive Logging

Tests must use a logging framework, not bare `print()` or generic `"Error"` messages. Every test failure must tell the reader **exactly where and why** it failed so any agent or human can fix it without detective work.

### Requirements

- Use Python's `logging` module with a dedicated test logger.
- Every test class sets up its logger: `logger = logging.getLogger(__name__)`
- Log entries must include:
  - **What** was being tested (the action)
  - **Where** the failure occurred (view name, URL, model)
  - **Expected vs. actual** result
  - **Context** (which user, which object, what state)

### Example — Good vs. Bad

```python
# BAD — useless on failure
self.assertEqual(response.status_code, 200)

# GOOD — any agent or human can fix this
logger.info("Testing PropertyDetailView access for authenticated user (property_id=%s)", self.property.pk)
self.assertEqual(
    response.status_code, 200,
    f"PropertyDetailView returned {response.status_code} for authenticated user. "
    f"URL: {url}, User: {self.user.email}, Property: {self.property.pk}"
)
```

### Log Levels in Tests

| Level | When to use |
|---|---|
| `INFO` | Test starting, key assertions passing |
| `WARNING` | Unexpected but non-fatal behavior |
| `ERROR` | Assertion failure context (logged before the assert) |

---

## Principle 3: Intuitive, Self-Documenting Tests

Every test must be readable by a human or agent who has never seen the codebase. No one should need to wonder "what is this testing?" or "how does this work?"

### Naming Convention

```python
# Pattern: test_<what>_<condition>_<expected_result>
def test_record_detail_unauthenticated_redirects_to_login(self):
def test_record_create_special_characters_in_name_saves_correctly(self):
def test_list_empty_shows_no_results_message(self):
def test_record_delete_wrong_user_returns_403(self):
```

### Structure: Arrange-Act-Assert with Comments

```python
def test_record_create_special_characters_in_name_saves_correctly(self):
    """Creating a record with special characters in the name should save without error."""
    # Arrange
    self.client.force_login(self.user)
    form_data = {"name": "Acme & Co <Test> 'Quotes' \"Double\"", "parent": self.parent.pk}

    # Act
    response = self.client.post(reverse("<app>:<model>_create"), form_data)

    # Assert
    self.assertEqual(response.status_code, 302, "Record with special characters should save and redirect")
    self.assertTrue(Record.objects.filter(name=form_data["name"]).exists())
```

### Rules

- Every test method has a one-line docstring saying what it proves.
- Use `Arrange / Act / Assert` section comments.
- Use descriptive assertion messages — the message is what surfaces in CI logs.
- No magic numbers or unexplained fixtures. If a test needs 3 objects, say why.
- Test data should be obviously fake (`"Test Acme"`, `"user@test.com"`) — never ambiguous.

---

## Principle 4: Tests as Specification

The test file for a view should read like a specification of that view's behavior. Anyone should be able to open the test file and understand:

1. What the view does
2. Who can access it
3. What happens on success
4. What happens on failure
5. What edge cases exist

### Test Class Organization

```python
class PropertyDetailViewTests(TestCase):
    """PropertyDetailView — displays a single property's details."""

    # --- Access ---
    def test_authenticated_user_can_view(self): ...
    def test_unauthenticated_user_redirected_to_login(self): ...
    def test_nonexistent_property_returns_404(self): ...

    # --- Content ---
    def test_displays_property_name(self): ...
    def test_displays_related_buildings(self): ...
    def test_empty_buildings_shows_message(self): ...

    # --- Navigation ---
    def test_back_link_goes_to_property_list(self): ...
    def test_edit_link_goes_to_property_edit(self): ...
    def test_navbar_links_are_present(self): ...
```

---

## Principle 5: No Gaps, No Waste

- **No gaps:** If a view exists, it has tests. If a form exists, it has tests. No untested code reaches ship.
- **No waste:** Don't test Django internals (e.g., "does `CharField` store strings?"). Test *your* behavior on top of Django.
- **No duplication:** If two tests assert the same thing, delete one. Each test proves exactly one thing.

---

## Verification Checklist

Before declaring tests complete, verify:

- [ ] Every view has access tests (auth, unauth, permissions)
- [ ] Every form has valid + invalid + edge case tests
- [ ] Every redirect is tested (correct destination after every action)
- [ ] Special characters tested in every text input
- [ ] Empty states tested (no items, no results after filter)
- [ ] Error states tested (404, 403, 405, validation errors)
- [ ] All assertions have descriptive failure messages
- [ ] All tests use the logging framework
- [ ] Test names follow `test_<what>_<condition>_<expected>` pattern
- [ ] Test file reads like a feature specification
