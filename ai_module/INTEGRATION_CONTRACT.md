

# AI Module Integration Contract for Backend (Rounak)

This document specifies the interface contract between the AI Module (`ai_module/`) and the Backend (`backend/`).

---

## 1. Import Path
```python
from ai_module import generate_adaptive_content, calculate_next_level
```
*(Alternative direct module import)*:
```python
from ai_module.adaptive_tutor import generate_adaptive_content, calculate_next_level
```

---

## 2. Public Functions & Signatures

### A. Content Generation
```python
generate_adaptive_content(
    topic: str,
    difficulty: str,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None
) -> dict[str, Any]
```
* **`topic`** (`str`): Non-empty string naming the subject to learn (e.g., `"Binary Search Trees"`).
* **`difficulty`** (`str`): One of `"Beginner"`, `"Intermediate"`, or `"Advanced"`.
* **`api_key`** (`Optional[str]`): Optional key override; defaults to reading `GEMINI_API_KEY` from the environment.
* **`model_name`** (`Optional[str]`): Optional model override; defaults to reading `GEMINI_MODEL` or `"gemini-3.5-flash-lite"`.

### B. Difficulty Progression
```python
calculate_next_level(
    current_level: str,
    score_percentage: float | int
) -> str
```
* **`current_level`** (`str`): Current level (`"Beginner"`, `"Intermediate"`, or `"Advanced"`).
* **`score_percentage`** (`float` | `int`): Aggregated student quiz score between `0.0` and `100.0`.
* **Adaptive Rules**:
  * **$\text{Score} \ge 80.0\%$**: Promote one level (`Beginner` $\rightarrow$ `Intermediate` $\rightarrow$ `Advanced`, capped at `Advanced`).
  * **$\text{Score} < 50.0\%$**: Demote one level (`Advanced` $\rightarrow$ `Intermediate` $\rightarrow$ `Beginner`, floored at `Beginner`).
  * **$50.0\% \le \text{Score} < 80.0\%$**: Maintain current level.
* **Pure Logic**: Deterministic algorithmic logic. Does **not** make Gemini API calls.
* **Returns**: Updated difficulty level string (`"Beginner"`, `"Intermediate"`, or `"Advanced"`).

---

## 3. Allowed Difficulty Values
Strictly case-sensitive:
* `"Beginner"`
* `"Intermediate"`
* `"Advanced"`

---

## 4. Return Object Specification
The returned dictionary conforms directly to the Pydantic `LearningModule` schema:

```json
{
  "topic": "Python Memory Management",
  "difficulty_level": "Beginner",
  "explanation": "In Python, memory is managed automatically using a private heap, reference counting, and garbage collection...",
  "notes": [
    "Variables are references pointing to memory blocks, not the data itself.",
    "Reference counting deletes objects immediately when count drops to zero.",
    "A cyclic garbage collector resolves circular reference chains."
  ],
  "quiz": [
    {
      "question": "What happens when an object reference count drops to zero in Python?",
      "options": [
        "The object is immediately deallocated from memory",
        "The object is moved to secondary storage",
        "A MemoryError is raised by the runtime",
        "The programmer must manually call free()"
      ],
      "correct_answer": "The object is immediately deallocated from memory"
    }
    // ... exactly 12 multiple-choice questions
  ]
}
```

---

## 5. Expected Exceptions & Recommended HTTP Status Handling

| Exception | Cause | Recommended HTTP Status |
| :--- | :--- | :--- |
| `ValueError` | Empty topic, invalid difficulty string, invalid score range ($< 0$ or $> 100$), or schema validation failure. | `HTTP 422 Unprocessable Entity` or `HTTP 400 Bad Request` |
| `RuntimeError` | Gemini API network timeouts, authentication failure, or 503 high demand spike. *(All secrets are auto-redacted as `[REDACTED]`)* | `HTTP 502 Bad Gateway` or `HTTP 503 Service Unavailable` |
| `Exception` | Unexpected internal runtime failure. | `HTTP 500 Internal Server Error` |

---

## 6. Required Environment Variables & Dependencies

### Environment Variables
* `GEMINI_API_KEY`: **Required**. Google AI Studio API key.
* `GEMINI_MODEL`: **Optional**. Defaults to `"gemini-3.5-flash-lite"` (or set to `"gemini-3.8-flash"`).

### Installation
```bash
pip install -r ai_module/requirements.txt
```

---

## 7. How to Run Tests
From the project root:
```powershell
# Run all 49 automated unit tests
python -m unittest discover -s ai_module -p "test_*.py" -v

# Run offline end-to-end simulation
python ai_module/demo_end_to_end.py

# Run live API integration test (requires $env:GEMINI_API_KEY)
python ai_module/integration_test_live.py
```

---

## 8. Division of Responsibilities

### Backend Responsibilities (Rounak)
* Receiving and parsing frontend HTTP requests.
* Storing student profile, attempt history, and active sessions in database.
* Storing the answer key securely and evaluating student submissions.
* Calculating the student's score percentage:
  $$\text{score\_percentage} = \left(\frac{\text{correct\_count}}{12}\right) \times 100$$
* Calling `calculate_next_level(current_level, score_percentage)` upon quiz submission.
* Returning JSON responses to Junaid's frontend.

### AI Module Responsibilities (Our Team)
* Strict input validation and prompt engineering.
* Interfacing with the Gemini API using official `google-genai` SDK.
* Enforcing structured schema generation (12 MCQs, 3–5 notes, 4 options).
* Deterministic difficulty adaptation policy logic.
* Error sanitization to prevent credential leaks.
