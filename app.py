from flask import Flask, render_template, redirect, request, session, url_for
from flask_mysqldb import MySQL
import MySQLdb
import yaml
from authlib.integrations.flask_client import OAuth

app = Flask(__name__)

# Configure db
db = yaml.load(open('db.yaml'), Loader=yaml.FullLoader)

app.config['MYSQL_HOST'] = db['mysql_host']
app.config['MYSQL_USER'] = db['mysql_user']
app.config['MYSQL_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DB'] = db['mysql_db']

mysql = MySQL(app)

# OAuth Config
app.secret_key = db['secret_key']
oauth = OAuth(app)
google = oauth.register(
    name="google",
    client_id=db['client_id'],
    client_secret=db['client_secret'],
    access_token_url="https://accounts.google.com/o/oauth2/token",
    access_token_params=None,
    authorize_url="https://accounts.google.com/o/oauth2/auth",
    authorize_params=None,
    api_base_url="https://www.googleapis.com/oauth2/v1/",
    userinfo_endpoint=
    "https://openidconnect.googleapis.com/v1/userinfo",  # This is only needed if using openId to fetch user info
    client_kwargs={"scope": "openid email profile"},
)


@app.route("/")
def cultural():
    email = dict(session).get("email", None)
    print("current user:", email)
    return render_template('home.html')


@app.route("/login")
def login():
    google = oauth.create_client("google")
    redirect_uri = url_for("authorize", _external=True)
    return google.authorize_redirect(redirect_uri)


@app.route("/authorize")
def authorize():
    google = oauth.create_client("google")
    token = google.authorize_access_token()
    resp = google.get("userinfo", token=token)
    user_info = resp.json()
    # do something with the token and profile
    session["email"] = user_info["email"]
    print(user_info)
    return redirect("/")


@app.route("/logout")
def logout():
    for key in list(session.keys()):
        session.pop(key)
    return redirect("/")


@app.route("/clubs/<clubName>")
def club(clubName):

    cur = mysql.connection.cursor()
    cur.execute("select * from clubs WHERE Title=\'{}\'".format(clubName))
    club = cur.fetchone()

    print(club)
    try:
        title = club[1]
        info = club[2]
        achievements = club[3]
    except:
        return "404 Club Not FOUND"  # ADD NOT FOUND PAGE

    imageUrl = clubName + ".jpg"

    return render_template("clubtemplate.html",
                           title=title,
                           info=info,
                           achievements=achievements,
                           clubName=clubName,
                           imageUrl=imageUrl)


@app.route("/new/student", methods=['GET', 'POST'])
def student():
    if request.method == 'POST':
        # Get DATA from the form
        student = request.form
        try:
            Github_Profile = student['github_profile']
            Branch = student['branch']
            LinkedIn = student['linkedin']
            Full_Name = student['full_name']
            Mail_Id = student['mail_id']
            Roll_No = int(student['roll_no'])
            Phone_No = int(student['phone_no'])
            Semester = int(student['semester'])
            print(Github_Profile, Branch, LinkedIn, Full_Name, Mail_Id,
                  Roll_No, Phone_No, Semester)
            print(type(Github_Profile), type(Branch), type(LinkedIn),
                  type(Full_Name), type(Mail_Id), type(Roll_No),
                  type(Phone_No), type(Semester))

            cur = mysql.connection.cursor()
            cur.execute(
                "INSERT INTO students VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (Github_Profile, Branch, LinkedIn, Full_Name, Mail_Id, Roll_No,
                 Phone_No, Semester))

            mysql.connection.commit()
            cur.close()

        except (MySQLdb.Error, MySQLdb.Warning) as e:
            return str(e)

        return render_template("success.html")

    else:
        return render_template('newStudent.html')

    return "DONE"


@app.errorhandler(404)
def page_not_found(e):
    print("Redirecting to /")
    return redirect('/')


if __name__ == "__main__":
    app.run(debug=True)