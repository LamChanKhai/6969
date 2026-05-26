# Handoff to Backend — Slide Deck Complete

## Status: COMPLETE

## Deliverables

All three deck artifacts generated in `slides/cscv2025-proposal/`:

| File | Size | Description |
|------|------|-------------|
| `deck.html` | 78 KB | Self-contained interactive HTML deck (keyboard nav, thumbnail sidebar, dark/light theme) |
| `deck.pdf` | 3.9 MB | Print-ready PDF (1920×1080, vector text, 60 pages) |
| `deck.pptx` | 21 MB | Editable PowerPoint (native text shapes, 60 slides) |

## Deck Summary

- **Topic**: CSCV2025 セキュリティ評価およびプラットフォーム刷新プロジェクト — FPT Software提案
- **Language**: Japanese
- **Style**: Formal consulting (RFP/proposal)
- **Total Slides**: 60
- **Brand**: FPT logo on every slide (cover + top-right corner)

### Slide Structure (60 slides across 12 chapters)

| Chapter | Slides | Content |
|---------|--------|---------|
| Cover + Agenda | 1-3 | Title slide, 2-page agenda |
| Ch 1: Executive Summary | 4-7 | Background, challenges, recommended approach |
| Ch 2: Current State Analysis | 8-11 | Existing architecture, App1/App2 analysis |
| Ch 3: Security Evaluation | 12-18 | Vulnerability assessment, STRIDE threat model, attack scenarios, risk matrix |
| Ch 4: Proposed Solution | 19-24 | Refreshed architecture, security hardening, container security, DevSecOps, monitoring |
| Ch 5: Technical Approach | 25-30 | Implementation phases, tech stack selection, migration strategy, upload protection, testing |
| Ch 6: Demo Plan | 31-35 | Demo scope, user journey, wow moments, success criteria |
| Ch 7: Project Plan | 36-42 | Gantt timeline, milestones, team structure, RACI, risk register, communication plan |
| Ch 8: Quality & Compliance | 43-46 | QA framework, compliance (ISO 27001, GDPR, OWASP, SOC 2), SLA |
| Ch 9: Pricing | 47-50 | Cost breakdown (2,700万円), ROI analysis, competitor comparison |
| Ch 10: Why FPT | 51-53 | Differentiators, case studies |
| Ch 11: Next Steps | 54-56 | Action items, FAQ |
| Ch 12: Appendix | 57-60 | Glossary, references, contact |

## Quality Checks

- **Overflow**: 0 slides exceed 1080px
- **Word-break**: 0 awkward word-breaks detected
- **Under-fill**: 1 borderline slide (636px, ~59% of 1080 — acceptable)
- **PPTX**: Valid ZIP archive (418 internal files)

## Key Decisions

1. Built deck from codebase context since no prior PM/SA/Cloud docs existed
2. Focused on CSCV2025 CTF security evaluation narrative
3. Used FPT brand styling (corporate gradient, Meiryo UI font, FPT logo)
4. Split agenda and STRIDE slides to avoid overflow (max 10 slides/file rule)
5. Applied `slide--sparse` / `slide--very-sparse` modifiers for density optimization

## Notes for Next Role (Backend)

- The demo backend (`demo/backend/`) is empty — the next role should implement the demo API
- The deck describes a refreshed architecture with: Django REST + FastAPI API gateway, Go microservice for storage, Keycloak auth, mTLS communication, Kubernetes orchestration
- The demo should showcase: secure file upload, sandboxed archive extraction, JWT auth with RBAC, DevSecOps pipeline visualization, real-time monitoring dashboard
