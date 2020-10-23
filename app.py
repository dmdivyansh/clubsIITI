from flask import Flask, render_template, redirect
from flask_mysqldb import MySQL
import yaml

app = Flask(__name__)


# COnfigure db
db = yaml.load(open('db.yaml'), Loader=yaml.FullLoader)

app.config['MYSQL_HOST'] = db['mysql_host']
app.config['MYSQL_USER'] = db['mysql_user']
app.config['MYSQL_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DB'] = db['mysql_db']



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