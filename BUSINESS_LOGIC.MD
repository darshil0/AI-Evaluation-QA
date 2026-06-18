# Business Logic & Workflow Architecture

The **AI Evaluation QA Framework** is built on a modular architecture that separates data ingestion, model execution, scoring heuristics, and reporting. This document details the internal logic and data flow of the system.

## 1. Core Workflow Pipeline
The evaluation follows a linear but highly optimized pipeline:

1.  **Validation**: Before execution, the `ConfigurationValidator` and `PromptValidator` ensure that the environment is correctly set up, API keys are present, and prompt JSON files adhere to the required schema.
2.  **Prompt Orchestration**: The `EvaluationPipeline` loads prompts and dispatches them to the `PromptRunner`.
3.  **Concurrent Execution**: The `PromptRunner` utilizes `asyncio` to send multiple requests in parallel to LLM providers. It respects rate limits via an internal `RateLimiter` and handles errors using an asynchronous `EvaluationErrorHandler`.
4.  **Checkpointing**: As requests complete, results are saved to `data/checkpoints/` in real-time. This ensures that a network failure or crash doesn't lose progress.
5.  **Scoring & Analytics**: Raw responses are passed to the `ScoringEngine`, which applies a mixture of:
    *   **Heuristic Rules**: Pattern matching for logic, tone, and completeness.
    *   **Judge Models**: (Optional) Using LLMs to score other LLMs.
    *   **Defect Detection**: Identifying hallucinations or redundancies.
6.  **Cost Tracking**: The `CostTracker` calculates token usage and estimated costs using model-specific pricing and `tiktoken` encoding.
7.  **Reporting**: The `ReportGenerator` transforms the scored data into interactive HTML dashboards and executive summaries.

## 2. Scoring Heuristics
The framework scores responses on a 1–5 scale across four primary dimensions:

| Dimension | Logic / Heuristic |
| :--- | :--- |
| **Accuracy** | Checks for uncertainty markers, response length, and specific factual markers. |
| **Reasoning** | Analyzes logical connectors (e.g., "therefore", "consequently") and structured formatting (lists). |
| **Tone** | Monitors for positive/polite language vs. negative or dismissive markers. |
| **Completeness** | Evaluates word count thresholds and the presence of requested structural elements. |

## 3. Fault Tolerance & Error Handling
*   **Exponential Backoff**: When an API rate limit is hit (429 error), the system waits with increasing delays before retrying.
*   **Failed Request Tracking**: Requests that fail after all retries are logged but don't stop the rest of the batch.
*   **Safe Serialization**: The checkpointing logic skips rows that fail to serialize, ensuring the overall file remains valid.

## 4. Security & Sanitization
*   **Filename Safety**: All generated report filenames are sanitized to prevent directory traversal attacks.
*   **HTML Escaping**: User-provided content (prompts/responses) is escaped before being rendered in HTML reports to mitigate XSS risks.
*   **Secret Management**: The framework prevents the accidental logging of API keys or sensitive session data.

---
*This architecture is designed for production environments where reliability, speed, and clear audit trails are paramount.*
