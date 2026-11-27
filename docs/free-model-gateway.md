# Free model gateway

Reusable composite action for text inference on trusted Linux GitHub Actions jobs. No persistent server required. Default is local only; external providers receive prompt data only when allow-hosted is true. Never use hosted mode with private, personal, credential-bearing or restricted records. Model results are untrusted and must pass application-level evidence gates.

## Catalog
- OpenRouter: discovers text models with :free IDs and zero advertised prices; selects by task-name heuristics, then openrouter/free; zero-price routing constraints on every request.
- Groq: GPT-OSS 120B/20B, Qwen 3.8 27B. Requires a confirmed Free-plan account.
- Gemini: Gemini 3.5 Flash-Lite candidate. Requires a confirmed non-billable free-tier project.
- Cloudflare Workers AI: GPT-OSS 120B/20B candidates. Requires a Workers Free account (no paid plan).
- Ollama: Qwen 3.5 4B, Qwen 3 4B, Qwen 2.5 1.5B, Qwen 2.5 Coder 3B, Gemma 3 1B/4B, Llama 3.2 1B/3B, Granite 3.3 2B.

Hosted availability and free quotas change. Never mark an account confirmed if billing or automatic overages are enabled. Confirmation is manual and must be revoked before changing plans; the gateway cannot independently verify provider billing settings. Free inference is not the same as free runner minutes. Use only included GitHub Actions runner capacity. Ollama uses a mutable upstream image; pin an audited digest before production. Local small models are not equivalent to frontier models.

## Usage

Checkout your repository, then add this step to a trusted workflow:

```yaml
- uses: ./.github/actions/free-model
  with:
    prompt-file: input.txt
    output: result.json
    profile: reasoning
```

For another repository, use jbmeadows26/Power-Atlas/.github/actions/free-model@<reviewed-commit-sha> after merge. For hosted public-data mode, set allow-hosted: 'true' and pass keys via step env from GitHub secrets. See free-model-gateway.yml for names. Add only accounts on free-only plans. OpenRouter key recommended with no credit and zero spending limit where supported. Never pass credentials to untrusted PR jobs.

On failure, exit 75 and JSON status deferred; no fake model content. Downstream jobs must check status before publishing. Task routing is heuristic, not benchmark validated. Weekly catalog artifact lists discovered and configured candidate models; live dispatch tests one actual route, not every catalog entry. Existing analyst workflows are unchanged until migrated deliberately. No image/audio/embedding inference in this action.
