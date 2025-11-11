# Security Policy

## 🔒 Supported Versions

This project is currently in active development. Security updates are provided for the following:

| Version | Supported          | Notes |
| ------- | ------------------ | ----- |
| main (latest) | ✅ | Active development branch |
| < 1.0   | ⚠️ | Pre-release; use at your own risk |

**Note:** Since this is a local-first application designed to run on your own infrastructure, you are responsible for securing your deployment environment.

---

## 🛡️ Security Considerations

### Local Deployment
- This project is designed to run **locally** with no cloud dependencies
- All data (Islamic texts, embeddings, chat history) stays on your machine
- Ollama models run locally; no API keys or external calls required

### Known Security Boundaries
- **Input Validation:** User queries are passed to Ollama; ensure you trust your local LLM
- **File Ingestion:** Only ingest files from trusted sources; malicious PDFs or scripts could pose risks
- **API Exposure:** The FastAPI server is meant for local use; do not expose it to the public internet without proper authentication and rate limiting
- **CORS Configuration:** Default CORS allows `*`; restrict this in production deployments

---

## 🚨 Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly:

### 📧 Contact
**Do NOT open a public GitHub issue for security vulnerabilities.**

Instead, reach out privately via:
- **Email:** [usmangourworkid@gmail.com](mailto:usmangourworkid@gmail.com)
- **Telegram:** [@thechampusman](https://t.me/thechampusman)
- **GitHub:** [thechampusman](https://github.com/thechampusman) (private message or security advisory)

### 📋 What to Include
Please provide:
1. **Description** of the vulnerability
2. **Steps to reproduce** (proof of concept)
3. **Potential impact** (what could an attacker achieve?)
4. **Suggested fix** (if you have one)

### ⏱️ Response Timeline
- **Acknowledgment:** Within 48 hours of your report
- **Initial Assessment:** Within 7 days
- **Fix Timeline:** Depends on severity (critical issues prioritized)
- **Disclosure:** Coordinated disclosure after a fix is released

### ✅ What to Expect
- If accepted: We will work on a fix, credit you in the changelog (if you wish), and issue a security advisory
- If declined: We will explain why the issue is not considered a vulnerability
- Public disclosure will only happen after a patch is available

---

## 🔐 Best Practices for Users

1. **Keep dependencies updated:** Run `pip install --upgrade -r requirements.txt` regularly
2. **Restrict API access:** Use firewall rules or authentication middleware if exposing the API
3. **Validate sources:** Only ingest Islamic texts from authenticated, trusted publishers
4. **Review logs:** Monitor `backend/core/logging.py` output for suspicious activity
5. **Ollama security:** Keep Ollama updated and review model provenance

---

## 📚 Related Documentation
- [CONTRIBUTING.md](./CONTRIBUTING.md) - Contribution guidelines
- [LICENSE](./LICENSE) - Source-available license terms
- [README.md](./README.md) - Setup and usage instructions

---

**Jazakum Allahu khayran** for helping keep this project secure and trustworthy for the Muslim community.
