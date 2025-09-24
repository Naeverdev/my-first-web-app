from flask import Flask

# Create Flask application
app = Flask(__name__)

@app.route('/')
def hello_world():
    return '''
    <h1>🎉 Hello World!</h1>
    <p>My first web application is running!</p>
    <p>Built with Python Flask</p>
    <p>Time: ''' + str(__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + '''</p>
    <p><a href="/about">About</a> | <a href="/contact">Contact</a></p>
    '''

@app.route('/about')
def about():
    return '''
    <h1>About This App</h1>
    <p>This is my first Python web application!</p>
    <p>I built this using Flask framework.</p>
    <a href="/">← Back to Home</a>
    '''

@app.route('/contact')
def contact():
    return '''
    <h1>📧 Contact Me</h1>
    <p>This is my contact page!</p>
    <p>Email: your-email@example.com</p>
    <p>GitHub: github.com/YOUR-USERNAME</p>
    <a href="/">← Back to Home</a>
    '''



if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
