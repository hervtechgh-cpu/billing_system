from datetime import date

today = date.today()
due_date = date.fromisoformat("2026-09-17")

days_overdue = max(0, (today - due_date).days)

print(f"Days overdue: {days_overdue}")