# Self-Learning System - Metrics & Feedback

This directory contains the self-learning system that improves agent performance based on team feedback.

## How It Works

1. **Automatic Recording:** Every agent run is automatically recorded in `runs/`
2. **Team Feedback:** Developers provide feedback using `/syntek-dev-suite:learning-feedback`
3. **Analysis:** After 50+ runs, the system analyzes patterns and suggests improvements
4. **Auto-Optimization:** High-confidence improvements are applied automatically (configurable)

## Directory Structure

```
METRICS/
├── config.json              # System configuration
├── runs/                    # Agent run records (JSON)
├── feedback/                # User feedback records (JSON)
├── aggregates/              # Daily/weekly summaries
│   ├── daily/              # Daily performance metrics
│   └── weekly/             # Weekly trend analysis
├── variants/                # A/B test prompt variants
├── optimisations/           # LLM-generated improvements
│   ├── pending/            # Awaiting review/application
│   ├── applied/            # Successfully applied
│   └── rejected/           # Rejected by humans or tests
└── templates/               # Analysis prompt templates
```

## Configuration

Edit `config.json` to control behavior:

```json
{
  "enabled": true,                    // Master switch
  "auto_optimisation_enabled": true,  // Auto-apply improvements
  "min_runs_for_analysis": 50        // Minimum runs before analysis
}
```

## Using the System

### Providing Feedback

After an agent runs, provide feedback:

```bash
/syntek-dev-suite:learning-feedback
```

Choose:
- 👍 **Good** - Agent met expectations
- 👎 **Bad** - Agent didn't meet expectations
- 🐛 **Bug** - Agent had errors or unexpected behavior

Add a comment explaining what was good/bad/buggy.

### Viewing Optimizations

See pending improvements:

```bash
/syntek-dev-suite:learning-optimise
```

### Running A/B Tests

Test different prompt approaches:

```bash
/syntek-dev-suite:learning-ab-test
```

## Data Retention

- **Runs:** Kept for 90 days
- **Feedback:** Kept permanently (anonymized)
- **Aggregates:** Kept permanently
- **Optimizations:** Kept permanently

## Privacy

All data is stored locally in this repository. No data is sent to external services.

## Disabling the System

To disable completely:

```json
{
  "enabled": false
}
```

Or disable auto-optimization but keep metrics:

```json
{
  "enabled": true,
  "auto_optimisation_enabled": false
}
```
