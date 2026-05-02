# Eval Harness

Seeded evaluation cases for the code review agent.

## Run

```bash
uv run python -m evals.run_evals
```

## Dataset

`golden_dataset.json` contains test cases with:
- Known-bug diffs that should produce findings (true positives)
- Clean diffs that should produce no findings (false-positive traps)

Each case specifies expected file, line range, and severity.

## Scoring

The harness scores: detection accuracy, false positive rate,
file/line proximity, severity match, and duplicate count.