from flask import Flask, jsonify

# Modular blueprint imports will go here (e.g., from api.auth import auth_bp)

def create_app():
    app = Flask(__name__)

    # Register blueprints here
    from backend.api.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({'status': 'ok'}), 200

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(ssl_context='adhoc', port=5001)
