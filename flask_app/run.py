from app import create_app

app = create_app()

if __name__ == "__main__":
    # threaded=True allows long-running imports without blocking other requests.
    # Use a production WSGI server (gunicorn/waitress) in production.
    app.run(debug=True, port=5000, threaded=True)
