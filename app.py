from flask import Flask, render_template
from data import load_data

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/media-representation')
def media_representation():
    return render_template('media_representation.html')

@app.route('/media-desensitization')
def media_desensitization():
    return render_template('media_desensitization.html')

@app.route('/narratives-left-out')
def narratives_left_out():
    return render_template('narratives_left_out.html')

if __name__ == '__main__':
    app.run(debug=True)
