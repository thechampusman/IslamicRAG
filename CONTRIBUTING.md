# Contributing to Islamic RAG

Thank you for your interest in contributing! This is a **source-available, contribute-only** project under a custom license (see `LICENSE`). Please read the guidelines below before opening issues or pull requests.

## 🤝 Code of Conduct

This project adheres to a [Code of Conduct](./CODE_OF_CONDUCT.md) that integrates Islamic values (adab, amānah, ikhlās) with professional community standards. By participating, you agree to uphold these principles. Please read it before contributing.

## 📜 License Acceptance
By submitting a pull request you **affirm** that:
1. You have read and agree to the `LICENSE` terms.
2. You grant the project a perpetual, irrevocable, royalty-free license to include your contribution.
3. You are not submitting copyrighted third-party content without permission.
4. Any Islamic texts you add are authentic and properly attributed.

## ✅ What to Contribute
- Bug fixes and performance improvements
- Retrieval quality enhancements (ranking, hybrid search)
- Structured metadata extraction (verse numbers, hadith grading)
- Tests (unit + integration)
- Documentation improvements

## 🚫 What NOT to Contribute
- Non-authenticated or speculative religious content
- Attempts to bypass the licensing restrictions
- Proprietary code you do not own

## 🧪 Development Workflow
1. Clone repo and set up environment per `README.md`.
2. Create a feature branch: `feat/your-feature`.
3. Run ingestion only on test data (avoid adding heavy corpora directly).
4. Add tests if logic changes (`pytest -q`).
5. Ensure style is consistent; keep imports minimal.
6. Open a PR using the template.

## 🧩 Testing Suggestions
- Mock embedding calls for faster unit tests.
- Provide small fixture texts for retrieval tests.
- Test fallback logic (`mode: fallback`) when no passages returned.

## 🔎 Islamic Source Guidelines
- Prefer widely accepted translations and authenticated collections.
- Clearly name files (e.g., `quran_en_clear_translation.txt`, `sahih_bukhari_book1.pdf`).
- Do not mix commentary with primary text unless labeled.

## 🛡 Security & Authenticity
- Avoid code that executes arbitrary user input.
- Validate file types during ingestion if extending.
- Maintain disclaimers; do not remove guardrails.

## 🗂 Issue Labels
- `bug`: Incorrect behavior or tracebacks
- `enhancement`: New capability or optimization
- `docs`: README / usage improvements
- `question`: Need clarification

## 💬 Communication
Be respectful and professional. This project centers on preserving authenticity and scholarly integrity. Review our [Code of Conduct](./CODE_OF_CONDUCT.md) for detailed community standards.

## 📧 Contact
Maintainer: usman gour (thechampusman)

For license questions or sensitive submissions, reach out via:

**Email:** [usmangourworkid@gmail.com](mailto:usmangourworkid@gmail.com)

<p>
	<a href="https://t.me/thechampusman"><img src="https://img.shields.io/badge/Telegram-@thechampusman-229ED9?logo=telegram" alt="Telegram" /></a>
	<a href="https://instagram.com/thechampusman"><img src="https://img.shields.io/badge/Instagram-@thechampusman-E4405F?logo=instagram&logoColor=white" alt="Instagram" /></a>
	<a href="https://www.linkedin.com/in/thechampusman/"><img src="https://img.shields.io/badge/LinkedIn-/in/thechampusman-0A66C2?logo=linkedin" alt="LinkedIn" /></a>
	<a href="https://github.com/thechampusman"><img src="https://img.shields.io/badge/GitHub-thechampusman-181717?logo=github" alt="GitHub" /></a>
</p>

Jazakum Allahu khayran for your contribution!
