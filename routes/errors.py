from flask import Flask, render_template
from flask_wtf.csrf import CSRFError


def register_error_handlers(app: Flask) -> None:
    @app.route("/403.php", methods=["GET"])
    def legacy_forbidden():
        return render_template("errors/403.html"), 403

    @app.route("/404.php", methods=["GET"])
    def legacy_not_found():
        return render_template("errors/404.html"), 404

    @app.errorhandler(CSRFError)
    def csrf_error(_error):
        return "Your session token is invalid or expired. Please reload the page and try again.", 419

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(413)
    def payload_too_large(_error):
        return "The uploaded request is too large.", 413

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(_error):
        app.logger.exception("Unhandled application error")
        return render_template("errors/500.html"), 500
