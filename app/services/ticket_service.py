from datetime import datetime

from sqlalchemy import func

from app.ai import analyze_email_text
from app.ai.reply_generator import generate_auto_reply, generate_support_reply
from app.config import Config
from app.extensions import db
from app.models import Admin, Analytics, Reply, Ticket


AUTO_RESOLVED = "AUTO_RESOLVED"
NEEDS_ADMIN_REVIEW = "NEEDS_ADMIN_REVIEW"
IN_PROGRESS = "IN_PROGRESS"
RESOLVED = "RESOLVED"
SPAM = "SPAM"


def create_ticket(user_id: int, subject: str, message: str) -> Ticket:
    analysis = analyze_email_text(subject, message)
    repeated = is_repeated_ticket(user_id, subject, message)
    ticket = Ticket(
        user_id=user_id,
        subject=subject.strip(),
        message=message.strip(),
        status=resolve_initial_status(analysis, repeated),
        sentiment=analysis.sentiment,
        intent=analysis.category,
        priority=analysis.priority,
    )
    db.session.add(ticket)
    db.session.flush()

    if ticket.status == AUTO_RESOLVED:
        db.session.add(
            Reply(
                ticket_id=ticket.id,
                admin_id=default_admin_id(),
                body=generate_auto_reply(customer_name=ticket.user.name, analysis=analysis),
            )
        )

    db.session.commit()
    record_metric("ticket_created", 1)
    return ticket


def generate_reply_draft(ticket: Ticket) -> str:
    analysis = analyze_email_text(ticket.subject, ticket.message)
    ticket.sentiment = analysis.sentiment
    ticket.intent = analysis.category
    ticket.priority = analysis.priority
    ticket.status = IN_PROGRESS
    db.session.commit()
    return generate_support_reply(
        customer_name=ticket.user.name,
        subject=ticket.subject,
        message=ticket.message,
        analysis=analysis,
    )


def send_reply(ticket: Ticket, admin_id: int, body: str) -> Reply:
    reply = Reply(ticket_id=ticket.id, admin_id=admin_id, body=body.strip())
    ticket.status = RESOLVED
    ticket.resolved_at = datetime.utcnow()
    db.session.add(reply)
    db.session.commit()
    record_metric("ticket_resolved", 1)
    return reply


def record_metric(name: str, value: float) -> None:
    db.session.add(Analytics(metric_name=name, metric_value=value))
    db.session.commit()


def admin_stats() -> dict[str, int]:
    total = db.session.scalar(db.select(func.count(Ticket.id))) or 0
    resolved = db.session.scalar(db.select(func.count(Ticket.id)).where(Ticket.status.in_((RESOLVED, AUTO_RESOLVED)))) or 0
    pending = db.session.scalar(db.select(func.count(Ticket.id)).where(Ticket.status == NEEDS_ADMIN_REVIEW)) or 0
    in_progress = db.session.scalar(db.select(func.count(Ticket.id)).where(Ticket.status == IN_PROGRESS)) or 0
    auto_resolved = db.session.scalar(db.select(func.count(Ticket.id)).where(Ticket.status == AUTO_RESOLVED)) or 0
    spam = db.session.scalar(db.select(func.count(Ticket.id)).where(Ticket.status == SPAM)) or 0
    positive = db.session.scalar(db.select(func.count(Ticket.id)).where(Ticket.sentiment == "Positive")) or 0
    neutral = db.session.scalar(db.select(func.count(Ticket.id)).where(Ticket.sentiment == "Neutral")) or 0
    negative = db.session.scalar(db.select(func.count(Ticket.id)).where(Ticket.sentiment == "Negative")) or 0
    return {
        "total": total,
        "resolved": resolved,
        "pending": pending,
        "in_progress": in_progress,
        "auto_resolved": auto_resolved,
        "spam": spam,
        "positive": positive,
        "neutral": neutral,
        "negative": negative,
    }


def resolve_initial_status(analysis, repeated: bool) -> str:
    if analysis.is_spam or repeated:
        return SPAM
    if analysis.auto_reply_eligible:
        return AUTO_RESOLVED
    return NEEDS_ADMIN_REVIEW


def is_repeated_ticket(user_id: int, subject: str, message: str) -> bool:
    normalized_subject = subject.strip().lower()
    normalized_message = message.strip().lower()
    if not normalized_subject or not normalized_message:
        return False
    duplicate_count = (
        Ticket.query.filter(Ticket.user_id == user_id)
        .filter(func.lower(Ticket.subject) == normalized_subject)
        .filter(func.lower(Ticket.message) == normalized_message)
        .count()
    )
    return duplicate_count >= 1


def default_admin_id() -> int:
    admin = Admin.query.filter_by(username=Config.DEFAULT_ADMIN_USERNAME).first()
    if admin is None:
        raise RuntimeError("Default admin account is missing.")
    return admin.id


def status_label(status: str) -> str:
    return {
        AUTO_RESOLVED: "Auto Resolved",
        NEEDS_ADMIN_REVIEW: "Needs Admin Review",
        IN_PROGRESS: "In Progress",
        RESOLVED: "Resolved",
        SPAM: "Spam",
        "Pending": "Pending",
        "In Progress": "In Progress",
        "Resolved": "Resolved",
    }.get(status, status.replace("_", " ").title())


def is_solved(status: str) -> bool:
    return status in {RESOLVED, AUTO_RESOLVED, "Resolved"}
