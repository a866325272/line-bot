from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, Docker!'

if __name__ == "__main__":
    app.run(ssl_context='adhoc',host='0.0.0.0')
