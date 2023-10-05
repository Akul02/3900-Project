from flask import Flask
from flask_session import Session
from flask_cors import CORS
from prisma import Prisma
import os

from blueprints.example import example
from blueprints.auth import auth
from blueprints.search import search_tutor
from helpers.my_request import MyRequest

prisma = Prisma(auto_register=True)
prisma.connect()

Flask.request_class = MyRequest
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", default="not very secret")
# ? Consider moving to redis in the future?
app.config["SESSION_TYPE"] = "filesystem"
server_session = Session(app)
# todo: figure cors
cors = CORS(app)

# blueprints
app.register_blueprint(example, url_prefix="/example")
app.register_blueprint(auth, url_prefix="/")
app.register_blueprint(search_tutor, url_prefix="/")


# default route
@app.route("/")
def hello_world():
    return "Hello world!", 200


if __name__ == "__main__":
    app.run(debug=True, port=os.getenv("PORT", default=5000), host="0.0.0.0")
    prisma.disconnect()
