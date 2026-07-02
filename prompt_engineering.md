# Prompt Engineering Standards

The **AI Evaluation QA Framework** utilizes structured prompt engineering to ensure high-quality interactions with LLMs.

## 1. Evaluation Prompt Structure
The framework supports structured prompt JSON files that include:
- **Unique IDs**: For tracking and regression analysis.
- **Categorization**: To enable domain-specific scoring rules.
- **Expected Answers**: For automated accuracy validation.
- **Weights**: To prioritize critical test cases.

## 2. Meta-Prompting for System Architecture
The framework itself was architected using a "System Meta-Prompt" that enforced:
- **Role Persona**: Lead Software Architect.
- **Objective Constraints**: 100% coverage, asyncio.
- **Modular Decomposition**: Explicit component definitions.
- **Standard Enforcement**: PEP 8, Makefile, Docker.

## 3. Heuristic Guidance
Prompts are analyzed for:
- **Logical Connectors**: Encouraging chain-of-thought reasoning.
- **Evidence Attribution**: Incentivizing grounded responses.
- **Tone Alignment**: Ensuring context-appropriate voice.

## 4. Iterative Refinement
The evaluation pipeline provides the feedback loop necessary for iterative prompt engineering:
1. **Execute**: Run prompts across multiple models.
2. **Score**: Automatically evaluate based on the rubric.
3. **Analyze**: Identify defects and performance gaps.
4. **Refine**: Update prompts based on empirical data.
