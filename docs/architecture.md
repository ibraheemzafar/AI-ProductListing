# System Architecture

## High-Level Architecture

Frontend (Next.js)
    |
API Gateway
    |
------------------------------------------------
|               |              |               |
AI Service   SEO Service   Export Service   Image Service
    |
Queue System (BullMQ)
    |
Redis
    |
PostgreSQL
    |
AWS S3

## Frontend Stack
- Next.js 15
- TypeScript
- Tailwind CSS
- Shadcn UI

## Backend Stack
- FastAPI
- PostgreSQL
- Redis
- BullMQ

## Infrastructure
- AWS S3
- CloudFront
- Docker
- GitHub Actions
