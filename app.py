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

    signedIn = dict(session).get("signedIn", None)
    msg = ""
    msg_alert = "danger"
    print(signedIn)

    if signedIn:
        email = dict(session).get("email", None)
        msg = "Successfully signed in as : " + email
        msg_alert = "success"
        # Check if student info is available
        cur = mysql.connection.cursor()
        cur.execute("select Full_Name from students where Mail_id='{}'".format(email))

        present = cur.fetchone()
        
        mysql.connection.commit()
        cur.close()
        
        if(present):
            print("Already Submitted")
        else:
            return render_template("newStudent.html", msg="Please verify your details", msg_alert="warning")

    elif signedIn == None:
        msg = "Please signin into CLUBSIITI"
        msg_alert = "warning"

    else:
        print("clearing sessiong info")
        for key in list(session.keys()):
            session.pop(key)
        msg = "Please use IITI email id"
    
    print(msg)
    
    name = dict(session).get("name", None)
    print("current user:", name)
    return render_template('home.html', name=name, msg=msg, msg_alert=msg_alert)



@app.route("/clubs/<clubName>")
def club(clubName):

    cur = mysql.connection.cursor()
    cur.execute("select * from clubs WHERE Title=\'{}\'".format(clubName))
    club = cur.fetchone()

    # print(club)
    try:
        title = club[1]
        info = club[2]
        achievements = club[3]
    except:
        return render_template("error.html")
    verified = False
    imageUrl = clubName + ".jpg"

    
    try:
        cur.execute("SELECT Club_Title FROM clubheads WHERE Club_Head_Mail_Id = '{}'".format(session["email"]))
        club = cur.fetchall()
        # print(club)

        for i in club:
            # print(i[0])
            if ( i[0] == clubName):
                verified = True
        
    except:
        verified=False
    
    print("verified:", verified)
    return render_template("clubtemplate.html",
                           title=title,
                           info=info,
                           achievements=achievements,
                           clubName=clubName,
                           imageUrl=imageUrl,
                           verified=verified)


@app.route("/clubs/<clubName>/edit", methods=['GET', 'POST'])
def edit(clubName):
    if request.method == 'GET':
        cur = mysql.connection.cursor()
        email = dict(session).get("email", None)
        if(email == None):
            return "Please sign in"
        
        verified = False
        print("Running query: ", "SELECT Club_Title FROM clubheads WHERE Club_Head_Mail_Id = '{}'".format(session["email"]))
        cur.execute("SELECT Club_Title FROM clubheads WHERE Club_Head_Mail_Id = '{}'".format(session["email"]))
        club = cur.fetchall()

        for i in club:
            if ( i[0] == clubName):
                verified = True

        if(verified):
            print("Running query:" , "select Info, Achievements FROM clubs WHERE Title='{}'".format(clubName))
            cur.execute("select Info, Achievements FROM clubs WHERE Title='{}'".format(clubName))
            information = cur.fetchone()
            return render_template("editor.html", info=information[0], achievements=information[1], clubName=clubName)

        else:
            return render_template("error.html")

    else:
        data = request.form
        print("Fetched form data")
        info = data['info']
        # replace ' with " so that these string does not interfere with our sql queries
        info = info.replace("'",'"')
        achievements = data['achievements']
        achievements = achievements.replace("'",'"')
        cur = mysql.connection.cursor()
        print("Running query:","UPDATE clubs SET Info = '{}', Achievements = '{}' WHERE Title = '{}'".format(info, achievements, clubName) )
        cur.execute("UPDATE clubs SET Info = '{}', Achievements = '{}' WHERE Title = '{}'".format(info, achievements, clubName))

        mysql.connection.commit()
        cur.close()

        return redirect("/clubs/{}".format(clubName))


@app.route("/new/student", methods=['GET', 'POST'])
def student():
    if request.method == 'POST':
        # Get DATA from the form
        student = request.form
        try:
            Mail_Id = student['mail_id']
            Full_Name = student['full_name']
            LinkedIn = student['linkedin']
            Branch = student['branch']
            Roll_No = int(student['roll_no'])
            Phone_No = int(student['phone_no'])
            Current_Year = int(student['year'])


            cur = mysql.connection.cursor()
            cur.execute(
                "INSERT INTO students VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (Mail_Id, Full_Name, LinkedIn, Branch, Roll_No, Phone_No,
                 Current_Year))
            
            mysql.connection.commit()
            cur.close()

            return render_template("success.html")


        except (MySQLdb.Error, MySQLdb.Warning) as e:
            return str(e)


    else:
        return render_template('newStudent.html')

    return "DONE"



# _______________________ AUTH ROUTES ___________________________________________

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
    # print(user_info)
    session["email"] = user_info["email"]
    email = session["email"] 

    session["name"] = user_info["name"]
    session["signedIn"] = True

    
    if email[:3]==("cse") and email[-11:]=="@iiti.ac.in":
        session["roll_no"] = email[3:12]
        session["branch"] = email[:3].upper()
        return redirect("/")
    elif email[:2]==("ee" or "me" or "ce") and email[-11:]=="@iiti.ac.in":
        session["roll_no"] = email[2:11]
        session["branch"] = email[:2].upper()
        return redirect("/")
    elif email[:4]==("mems") and email[-11:]=="@iiti.ac.in":
        session["roll_no"] = email[4:13]
        session["branch"] = email[:4].upper()

        return redirect("/")
    else:
        logout()
        session["signedIn"] = False 
        return redirect("/")



@app.route("/logout")
def logout():
    for key in list(session.keys()):
        session.pop(key)
    return redirect("/")

#___________________________________________________________________________________




@app.errorhandler(404)
def page_not_found(e):
    print("Page Not Found")
    return render_template('error.html')


if __name__ == "__main__":
    app.run(debug=True)