from datetime import datetime

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app.extensions import db
from app.config import Config
from app.models import Admin, Ticket, User
from app.security import (
    clear_auth_session,
    current_admin,
    current_user,
    hash_password,
    login_required,
    validate_email,
    validate_password,
    verify_password,
)
from app.services.ticket_service import (
    SPAM,
    admin_stats,
    create_ticket,
    generate_reply_draft,
    send_reply,
)


main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def index():
    return render_template("index.html")


@main_bp.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        admin = Admin.query.filter_by(username=username).first()

        if (
            not admin
            or username != Config.DEFAULT_ADMIN_USERNAME
            or not verify_password(admin.password_hash, password)
        ):
            flash("Invalid admin credentials.", "danger")
            return render_template("admin_login.html"), 401

        clear_auth_session()
        session.permanent = True
        session["admin_id"] = admin.id
        session["role"] = "admin"
        return redirect(url_for("main.admin_dashboard"))

    return render_template("admin_login.html")


@main_bp.route("/user-login", methods=["GET", "POST"])
def user_login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email, role="user").first()

        if not user or not user.is_active or not verify_password(user.password_hash, password):
            flash("Invalid email or password.", "danger")
            return render_template("user_login.html"), 401

        user.last_login_at = datetime.utcnow()
        db.session.commit()
        clear_auth_session()
        session.permanent = True
        session["user_id"] = user.id
        session["role"] = "user"
        return redirect(url_for("main.user_dashboard"))

    return render_template("user_login.html")


@main_bp.route("/user-signup", methods=["GET", "POST"])
def user_signup():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not full_name or len(full_name) < 2:
            flash("Full name is required.", "danger")
        elif error := validate_email(email):
            flash(error, "danger")
        elif User.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "danger")
        elif password != confirm_password:
            flash("Passwords do not match.", "danger")
        elif error := validate_password(password):
            flash(error, "danger")
        else:
            user = User(
                name=full_name,
                email=email,
                password_hash=hash_password(password),
                role="user",
                is_active=True,
            )
            db.session.add(user)
            db.session.commit()
            flash("Account created. Please log in.", "success")
            return redirect(url_for("main.user_login"))

    return render_template("user_signup.html")


@main_bp.post("/logout")
def logout():
    clear_auth_session()
    flash("You have been logged out.", "success")
    return redirect(url_for("main.index"))


@main_bp.route("/user-dashboard", methods=["GET", "POST"])
@login_required("user")
def user_dashboard():
    user = current_user()
    if request.method == "POST":
        subject = request.form.get("subject", "").strip()
        message = request.form.get("message", "").strip()
        if len(subject) < 5:
            flash("Subject must be at least 5 characters.", "danger")
        elif len(message) < 10:
            flash("Message must be at least 10 characters.", "danger")
        else:
            create_ticket(user.id, subject, message)
            flash("Support query submitted successfully.", "success")
            return redirect(url_for("main.user_dashboard"))

    tickets = Ticket.query.filter_by(user_id=user.id).order_by(Ticket.created_at.desc()).all()
    return render_template("user_dashboard.html", user=user, tickets=tickets)


@main_bp.get("/dashboard")
def legacy_dashboard_redirect():
    if session.get("role") == "admin":
        return redirect(url_for("main.admin_dashboard"))
    if session.get("role") == "user":
        return redirect(url_for("main.user_dashboard"))
    return redirect(url_for("main.index"))


@main_bp.get("/admin-dashboard")
@login_required("admin")
def admin_dashboard():
    view = request.args.get("view", "queue")
    query = Ticket.query.join(User)
    if view == "spam":
        query = query.filter(Ticket.status == SPAM)
    else:
        query = query.filter(Ticket.status != SPAM)
    tickets = query.order_by(Ticket.created_at.desc()).all()
    return render_template(
        "admin_dashboard.html",
        admin=current_admin(),
        tickets=tickets,
        stats=admin_stats(),
        view=view,
    )


@main_bp.route("/ticket/<int:ticket_id>", methods=["GET", "POST"])
def ticket_details(ticket_id: int):
    ticket = db.session.get(Ticket, ticket_id)
    if ticket is None:
        return render_template("access_denied.html", message="Ticket not found."), 404

    if session.get("role") == "user":
        user = current_user()
        if not user or ticket.user_id != user.id:
            return render_template("access_denied.html"), 403
        return render_template("ticket_details.html", ticket=ticket, user=user)

    if session.get("role") != "admin" or not current_admin():
        return render_template("access_denied.html"), 403

    draft = None
    if request.method == "POST" and request.form.get("action") == "generate":
        draft = generate_reply_draft(ticket)
        flash("AI reply draft generated. Review and edit before sending.", "success")

    return render_template("ticket_details.html", ticket=ticket, admin=current_admin(), draft=draft)


@main_bp.post("/ticket/<int:ticket_id>/reply")
@login_required("admin")
def send_ticket_reply(ticket_id: int):
    ticket = db.session.get(Ticket, ticket_id)
    if ticket is None:
        return render_template("access_denied.html", message="Ticket not found."), 404

    body = request.form.get("reply_body", "").strip()
    if len(body) < 10:
        flash("Reply must be at least 10 characters.", "danger")
        return redirect(url_for("main.ticket_details", ticket_id=ticket.id))

    send_reply(ticket, current_admin().id, body)
    flash("Reply sent. Ticket marked as resolved.", "success")
    return redirect(url_for("main.ticket_details", ticket_id=ticket.id))


@main_bp.get("/analytics")
@login_required("admin")
def analytics():
    return render_template("analytics.html", stats=admin_stats())
