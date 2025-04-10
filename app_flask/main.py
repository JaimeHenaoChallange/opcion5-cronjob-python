from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    shape = None
    size = 100
    color = '#3498db'

    if request.method == 'POST':
        shape = request.form.get('shape')
        size = int(request.form.get('size'))
        color = request.form.get('color')

    return render_template('index.html', shape=shape, size=size, color=color)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
