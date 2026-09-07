from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.models.user import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    error = None
    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user     = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            error = "Invalid email or password."
        elif not user.is_active:
            error = "Account is disabled. Contact your administrator."
        else:
            login_user(user, remember=request.form.get("remember") == "on")
            next_page = request.args.get("next")
            flash(f"Welcome back, {user.full_name}!", "success")
            return redirect(next_page or url_for("dashboard.index"))

    return render_template("auth/login.html", error=error)


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    errors = {}
    form   = {}
    if request.method == "POST":
        form["full_name"] = request.form.get("full_name", "").strip()
        form["email"]     = request.form.get("email", "").strip().lower()
        password          = request.form.get("password", "")
        confirm           = request.form.get("confirm_password", "")

        if not form["full_name"]:
            errors["full_name"] = "Full name is required."
        if not form["email"] or "@" not in form["email"]:
            errors["email"] = "A valid email is required."
        elif User.query.filter_by(email=form["email"]).first():
            errors["email"] = "An account with this email already exists."
        if len(password) < 6:
            errors["password"] = "Password must be at least 6 characters."
        elif password != confirm:
            errors["confirm_password"] = "Passwords do not match."

        if not errors:
            user = User(
                email=form["email"],
                full_name=form["full_name"],
                role="staff",
                is_active=True,
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash(f"Account created! Welcome, {user.full_name}.", "success")
            return redirect(url_for("dashboard.index"))

    return render_template("auth/signup.html", errors=errors, form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been signed out.", "info")
    return redirect(url_for("auth.login"))
