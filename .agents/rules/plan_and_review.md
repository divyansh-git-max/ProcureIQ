# Plan-Only Execution with User Coding & Review

## Activation
- **Always On**

## Rule Details
1. **No Direct Code Generation**: When a planning command (e.g. `/plan` or `/planning`) is used and subsequently approved by the user, the agent **must not** generate or modify code files directly.
2. **Instructional Focus**: Instead, the agent must provide detailed, structured, step-by-step instructions, design layouts, and clear code snippets explaining how and what to code.
3. **User Coding Hand-off**: The user will perform the actual coding and file edits in the workspace.
4. **Code Review & Feedback**: Once the user has written the code and asks for review/feedback, the agent will inspect the modified files, identify any bugs, lints, or security issues, and suggest fixes or refinements.
5. **Interactive Checklists**: The agent must maintain a checklist of subtasks using standard markdown checkboxes (`- [ ]`) in a `task.md` file (or in responses) so the user can track progress and tick off completed items.
