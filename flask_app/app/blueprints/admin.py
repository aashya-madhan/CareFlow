from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from app.extensions import db
from app.models.user import User

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_admin:
            flash("Admin access required.", "danger")
            return redirect(url_for("dashboard.index"))
        return f(*args, **kwargs)
    return decorated


@admin_bp.route("/users")
@login_required
@admin_required
def users():
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=all_users)


@admin_bp.route("/users/new", methods=["GET", "POST"])
@login_required
@admin_required
def new_user():
    if request.method == "POST":
        email     = request.form.get("email", "").strip().lower()
        full_name = request.form.get("full_name", "").strip()
        password  = request.form.get("password", "")
        role      = request.form.get("role", "staff")

        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "danger")
        elif len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
        else:
            user = User(email=email, full_name=full_name, role=role)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash(f"User {full_name} created.", "success")
            return redirect(url_for("admin.users"))

    return render_template("admin/user_form.html", action="new", user=None)


@admin_bp.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)

    if request.method == "POST":
        user.full_name = request.form.get("full_name", user.full_name).strip()
        user.email     = request.form.get("email",     user.email).strip().lower()
        user.role      = request.form.get("role",      user.role)
        user.is_active = "is_active" in request.form
        pw = request.form.get("password", "")
        if pw:
            user.set_password(pw)
        db.session.commit()
        flash("User updated.", "success")
        return redirect(url_for("admin.users"))

    return render_template("admin/user_form.html", action="edit", user=user)


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_user(user_id):
    if user_id == current_user.id:
        flash("You cannot delete your own account.", "warning")
        return redirect(url_for("admin.users"))
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash("User deleted.", "success")
    return redirect(url_for("admin.users"))
