from flask import Flask
from app.config      import Config
from app.extensions  import db, login_manager


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates",
                static_folder="static")
    app.config.from_object(Config)

    # Extensions
    db.init_app(app)
    login_manager.init_app(app)

    # User loader
    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Blueprints
    from app.blueprints.auth         import auth_bp
    from app.blueprints.home         import home_bp
    from app.blueprints.dashboard    import dashboard_bp
    from app.blueprints.noshow       import noshow_bp
    from app.blueprints.operational  import operational_bp
    from app.blueprints.demographics import demographics_bp
    from app.blueprints.appointments import appointments_bp
    from app.blueprints.reminders    import reminders_bp
    from app.blueprints.patients     import patients_bp
    from app.blueprints.upload       import upload_bp
    from app.blueprints.reports      import reports_bp
    from app.blueprints.admin        import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(home_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(noshow_bp)
    app.register_blueprint(operational_bp)
    app.register_blueprint(demographics_bp)
    app.register_blueprint(appointments_bp)
    app.register_blueprint(reminders_bp)
    app.register_blueprint(patients_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(admin_bp)

    # Jinja2 custom filters
    @app.template_filter("format_number")
    def format_number(value):
        try:
            return f"{int(value):,}"
        except (TypeError, ValueError):
            return value

    @app.template_filter("min")
    def jinja_min(value):
        try:
            return min(value)
        except Exception:
            return value

    # Create tables + seed
    with app.app_context():
        db.create_all()
        from app.seed import run_seed
        run_seed(app)

    return app
