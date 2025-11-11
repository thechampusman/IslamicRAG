# Model Recommendations for IslamicRAG

## Issue with Content Filters

Some Llama models (especially `llama3.2` and `llama3.1:8b`) have built-in safety filters that may refuse to answer questions about Islamic rulings on sensitive topics (zina, prohibited acts, etc.), even when the context is clearly educational.

## Recommended Models

### Best Choice: Uncensored Models

Use models specifically trained without content filters:

```bash
# Dolphin models (uncensored, good for education)
ollama pull dolphin-llama3:8b

# Wizard models (uncensored)
ollama pull wizard-vicuna-uncensored:13b

# Nous Hermes (uncensored, excellent for fiqh)
ollama pull nous-hermes2:34b
```

### Update Configuration

Edit `backend/core/config.py` or set environment variable:

```python
chat_model: str = "dolphin-llama3:8b"  # Instead of llama3.2
```

Or in `.env` file:
```
CHAT_MODEL=dolphin-llama3:8b
```

### Why Uncensored Models?

- Islamic education requires discussing ALL topics (including sins, crimes, prohibitions)
- Explaining Islamic law on zina, theft, alcohol, etc. is EDUCATIONAL, not promotional
- Every Islamic fiqh book discusses these - that's legitimate scholarship
- Content filters mistake religious education for promotion of illegal acts

## Model Comparison

| Model | Size | Censored? | Speed | Quality | Best For |
|-------|------|-----------|-------|---------|----------|
| llama3.2 | 3B | ✅ Yes | Fast | Good | ❌ Not recommended |
| llama3.1:8b | 8B | ✅ Yes | Medium | Good | ❌ May refuse sensitive topics |
| dolphin-llama3:8b | 8B | ❌ No | Medium | Excellent | ✅ Islamic education |
| wizard-vicuna-uncensored:13b | 13B | ❌ No | Slower | Excellent | ✅ Detailed fiqh |
| nous-hermes2:34b | 34B | ❌ No | Slow | Best | ✅ Advanced scholarship |

## Testing Your Model

Ask this question to test if the model is suitable:

```
"What does Islam say about adultery and its punishment?"
```

**Good Response:** Explains zina, Quranic evidence, hudud punishment, conditions, repentance path

**Bad Response:** "I cannot provide information on illegal activities..."

## Current System Prompts

The system has been configured with strong educational framing:
- "Islamic fiqh professor"
- "Religious education tool"
- "Explaining prohibition is not promotion"
- "Like Islamic books explaining zina"

If model still refuses with uncensored version, report as a bug.

## Alternative: Local Model Fine-tuning

For production systems, consider fine-tuning on Islamic scholarly texts:
- Tafsir collections
- Hadith commentaries
- Fiqh manuals
- Fatwa databases

This creates a model that naturally understands Islamic educational context.
