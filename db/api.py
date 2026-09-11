from flask import Flask, jsonify, request
from flask_cors import CORS

from compliance.routes import compliance_bp
from compliance.access_routes import access_blueprint

app = Flask(__name__)
CORS(app)
app.register_blueprint(compliance_bp)
app.register_blueprint(access_blueprint)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
