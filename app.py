from flask import Flask, render_template, redirect

app = Flask(__name__)

@app.route("/")
def cultural():
    return render_template('culturals.html')


@app.route("/technicals")
def technical():
    return render_template('technicals.html')


@app.route("/others")
def others():
    return render_template('others.html')

@app.route("/clubs/<clubName>")
def club(clubName):
    print('clubs/'+ clubName + '/' + clubName + '.html')
    return render_template('clubs/'+ clubName + '/' + clubName + '.html')

    
    
@app.errorhandler(404)
def page_not_found(e):
    print("Redirecting to /")
    return redirect('/')

if __name__ == "__main__":
    app.run(debug=True)