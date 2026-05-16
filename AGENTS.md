# AI Product Listing Generator — Agent Instructions

## Project Overview

This project is an AI-powered SaaS platform that generates SEO-optimized product listings from uploaded product images.

The system follows:
- Spec-Driven Development
- SOLID principles
- Clean Architecture
- API-first design

All implementation must align with the `/docs` specifications.

---

# Important Documentation

Before implementing features, ALWAYS read:

- /docs/vision.md
- /docs/product-spec.md
- /docs/mvp-scope.md
- /docs/architecture.md
- /docs/engineering-principles.md
- /docs/code-standards.md
- /docs/system-boundaries.md

---

# Engineering Rules

## Architecture

- Keep controllers thin
- Business logic belongs in services
- Use dependency injection
- Follow feature-based architecture
- Avoid tightly coupled modules

---

# SOLID Principles

All implementations must follow SOLID principles.

- Single Responsibility
- Open/Closed
- Liskov Substitution
- Interface Segregation
- Dependency Inversion

---

# Frontend Standards

## Stack
- Next.js 15
- TypeScript
- Tailwind CSS
- Shadcn UI

## Rules
- Keep components small
- Separate UI and business logic
- Prefer reusable components
- Avoid prop drilling
- Use typed APIs

---

# Backend Standards

## Stack
- FastAPI
- PostgreSQL
- Redis
- OpenAI APIs

## Rules
- Use service-layer architecture
- Validate all inputs
- Use typed schemas
- Keep APIs RESTful
- Queue long-running tasks

---

# AI Engineering Rules

- Prompts must be reusable
- Use structured JSON outputs
- Track token usage
- Implement retries for AI failures
- Validate AI outputs before persistence

---

# Folder Structure

/apps
/packages
/docs
/infra

Do not introduce unapproved architecture changes.

---

# Coding Standards

- Use descriptive naming
- Avoid duplicated logic
- Write maintainable code
- Prefer composition over inheritance
- Keep files focused and modular

---

# MVP Scope Constraints

Only implement features defined in:
- /docs/mvp-scope.md

Do NOT implement:
- billing
- multi-agent systems
- RAG pipelines
- advanced analytics
- marketplace optimization

unless explicitly requested.

---

# Testing Requirements

- Critical services require tests
- APIs require integration tests
- Validate AI response structures

---

# Output Expectations

When implementing features:
1. Explain architecture decisions
2. Follow existing project structure
3. Keep implementations modular
4. Avoid unnecessary complexity
5. Prefer production-grade patterns