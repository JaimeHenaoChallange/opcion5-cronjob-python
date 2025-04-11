from flask import Flask, render_template, request
import logging
import os

# Configura Flask para buscar plantillas en el directorio correcto
template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'template')
app = Flask(__name__, template_folder=template_dir)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

@app.route('/', methods=['GET', 'POST'])
def index():
    shape = None
    size = 100
    color = '#3498db'
    error = None  # Variable to store error messages

    if request.method == 'POST':
        try:
            shape = request.form.get('shape')
            size = int(request.form.get('size'))
            color = request.form.get('color')

            # Validate inputs
            if shape not in ['circle', 'square', 'triangle']:
                raise ValueError("Invalid shape selected.")
            if size <= 0:
                raise ValueError("Size must be a positive integer.")
            if not color.startswith('#') or len(color) != 7:
                raise ValueError("Invalid color format.")
        except Exception as e:
            error = str(e)
            app.logger.error(f"Error processing form: {error}")
            shape, size, color = None, 100, '#3498db'  # Reset values on error

    return render_template('index.html', shape=shape, size=size, color=color, error=error)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
