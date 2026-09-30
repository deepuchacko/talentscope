"""Quick smoke test — run with: python examples/smoke_test.py"""
import os, sys
sys.path.insert(0, "src")

from talentscope.evaluator import validate_resume, evaluate

JD = """
Senior Python Engineer — Remote (US only)

Requirements (all required):
- 5+ years of Python development
- Experience with distributed systems or microservices
- Strong SQL skills
- Located in the United States

Nice to have:
- Kubernetes experience
- Prior startup experience
"""

GOOD_RESUME = """
Jane Smith
San Francisco, CA

Experience:
- Senior Software Engineer, Acme Corp (2018–2024): Led Python microservices
  architecture serving 10M requests/day. Built distributed data pipelines.
- Software Engineer, StartupCo (2016–2018): Python backend, Postgres SQL.

Skills: Python (7 years), PostgreSQL, Kafka, Docker, Kubernetes
Education: B.S. Computer Science, UC Berkeley
"""

BAD_RESUME = """
Carlos Mendez
Madrid, Spain

Experience:
- Junior JavaScript Developer, Web Studio (2022–2024)
- Intern, Digital Agency (2021–2022)

Skills: JavaScript, React, CSS
"""

if __name__ == "__main__":
    import json

    print("\n=== GOOD CANDIDATE ===")
    validate_resume(GOOD_RESUME)
    rec = evaluate(JD, GOOD_RESUME)
    print(json.dumps(rec.model_dump(), indent=2))

    print("\n=== BAD CANDIDATE (wrong location, wrong stack, junior) ===")
    validate_resume(BAD_RESUME)
    rec = evaluate(JD, BAD_RESUME)
    print(json.dumps(rec.model_dump(), indent=2))
