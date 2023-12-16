from flask import Flask, render_template, request, session
from myModule import process_input, extract_keywords, beautify

app = Flask(__name__)
app.config['STATIC_FOLDER'] = 'static'
app.secret_key = '89f093aef2f4bd1ea042bf47335fa5df8fcda06ceb77a93cbacfa558cc2bd07f'

@app.route("/", methods=["GET", "POST"])
def index():

    if request.method == "POST":
        try:
            if request.form.get('action') == 'Generate Keywords':

                session['error_message'] = ''
                session['url'] = request.form['url'].strip()
                session['blog'] = request.form['blog'].strip()
                session['input_keywords'] = request.form['input_keywords'].strip()

                if session['url'] != '':
                    if session['input_keywords'] != '':
                        session['blog_keywords'] = extract_keywords(session['url'], 'URL_with_Keywords', session['input_keywords'])
                    else:
                        session['blog_keywords'] = extract_keywords(session['url'], 'URL_without_Keywords')
                elif session['blog'] != '':
                    if session['input_keywords'] != '':
                        session['blog_keywords'] = extract_keywords(session['blog'], 'Blog_with_Keywords', session['input_keywords'])
                    else:
                        session['blog_keywords'] = extract_keywords(session['blog'], 'Blog_without_Keywords')
                
                session['generated_keywords'] = process_input(session['blog_keywords'])
                session['beautified_keywords'] = beautify(session['generated_keywords'])
        except Exception as e:
            session['error_message'] = f"An error occurred: {str(e)}"  # Capture the error message

            
    return render_template("index.html",
                           blog=session.get('blog', ''),
                           url=session.get('url', ''),
                           input_keywords=session.get('input_keywords', ''),
                           beautified_keywords=session.get('beautified_keywords', ''),
                           error_message=session.get('error_message', ''))

if __name__ == "__main__":
    app.run(host='127.0.0.3', port=5002)