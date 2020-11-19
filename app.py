from flask import Flask, render_template, redirect, request, session, url_for
from flask_mysqldb import MySQL
import smtplib, ssl, re
import MySQLdb
import yaml
from authlib.integrations.flask_client import OAuth
import os
from functions.dbConfig import database_config


from environment import env



app = Flask(__name__)

# env = "dev"
DATABASE_URL = ""
if env == "dev":
    dev = yaml.load(open('db.yaml'), Loader=yaml.FullLoader)
    DATABASE_URL  = dev['CLEARDB_DATABASE_URL']

else:
    DATABASE_URL  = os.environ.get("CLEARDB_DATABASE_URL")

user, password, host, db = database_config(DATABASE_URL)

app.config['MYSQL_HOST'] = host
app.config['MYSQL_USER'] = user
app.config['MYSQL_PASSWORD'] = password
app.config['MYSQL_DB'] = db

mysql = MySQL(app)

# LOADING IMAGES
img= yaml.load(open('images.yaml'), Loader=yaml.FullLoader)

# --------------------------------------


# --------- MAIL CONFIG
port = 465  # For SSL
smtp_server = "smtp.gmail.com"
sender_email = os.environ.get("mail_id") if (env != 'dev') else dev['mail_id']  
password = os.environ.get("mail_password") if (env != 'dev') else dev['mail_password']  

# --------------------------------


# OAuth Config
if env == 'dev':
    app.secret_key = dev['secret_key']
else:
    app.secret_key = os.environ.get("secret_key")
oauth = OAuth(app)
# value_when_true if condition else value_when_false
clientSecret = os.environ.get("client_secret") if (env != 'dev') else dev['client_secret']
clientId = os.environ.get("client_id") if (env != 'dev') else dev['client_id']

google = oauth.register(
    name="google",
    client_id=clientId,
    client_secret= clientSecret,
    access_token_url="https://accounts.google.com/o/oauth2/token",
    access_token_params=None,
    authorize_url="https://accounts.google.com/o/oauth2/auth",
    authorize_params=None,
    api_base_url="https://www.googleapis.com/oauth2/v1/",
    userinfo_endpoint=
    "https://openidconnect.googleapis.com/v1/userinfo",  # This is only needed if using openId to fetch user info
    client_kwargs={"scope": "openid email profile"},
)

def send_mail(receiver_email, message):
    print("Sending mail to " + receiver_email)
    print(message)
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message)

def check(email):
    regex = '(cse|ce|me|ee|mems)(\d{9})(@iiti.ac.in)'
    if(re.search(regex,email)):  
        return True
          
    else:  
        return False

@app.route("/")
def index():
    
    signedIn = dict(session).get("signedIn", None)
    msg = ""
    msg_alert = "danger"
    print(signedIn)
    admin = False

    if signedIn:
        email = dict(session).get("email", None)
        msg = "Successfully signed in as : " + email
        msg_alert = "success"

        # Check if is admin 
        if(email == "garvitgalgat@gmail.com"):
            print("Admin is here!!")
            admin = True

        else:        
            # Check if student info is available
            cur = mysql.connection.cursor()
            cur.execute("select Full_Name from students where Mail_id='{}'".format(email))

            present = cur.fetchone()
            
            mysql.connection.commit()
            cur.close()
            
            
            if(present):
                print("Already Submitted")
            else:
                return render_template("newStudent.html", msg="Please verify your details", msg_alert="warning", name=session['name'])

    elif signedIn == None:
        msg = "Please signin into CLUBSIITI"
        msg_alert = "warning"

    else:
        print("clearing session info")
        for key in list(session.keys()):
            session.pop(key)
        msg = "Please use IITI email id"
    
    

    cur = mysql.connection.cursor()
    print("Running query: ", "select * from events ORDER BY dated DESC;")
    cur.execute(f"select * from events ORDER BY dated DESC;")
    events = cur.fetchall()
    
    # print(events)
    name = dict(session).get("name", None)
    print("current user:", name)
    # print(img)
    return render_template('home.html', name=name, msg=msg, msg_alert=msg_alert,img=img, events=events, admin=admin)



@app.route("/details")
def myDetails():
    email = dict(session).get("email", None)
    if(email == None):
        msg = "Please signin into CLUBSIITI"
        msg_alert = "warning"
        return render_template('home.html', msg=msg, msg_alert=msg_alert,img=img)

    # Check if is admin 
    if(email == "garvitgalgat@gmail.com"):
        return render_template("error.html")
    
    else:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM students WHERE Mail_id='{}'".format(email))
        student = cur.fetchone()
        # for i in range(len(student)):
        #     print(i, student[i])

        return render_template("editStudent.html", student=student)

@app.route("/details/<clubName>/<email>")
def detailsOfStudent(clubName, email):
    #check if session['email'] is head of clubName 
    user = dict(session).get("email", None)
    if(user == None):
        return render_template("signIn.html")
    
    verified = False
    cur = mysql.connection.cursor()
    print("Running query: ", "SELECT Club_Title FROM clubheads WHERE Club_Head_Mail_Id = '{}'".format(session["email"]))
    cur.execute(f"SELECT Club_Title FROM clubheads WHERE Club_Head_Mail_Id ='{user}'")
    club = cur.fetchall()
    cur.execute(f"SELECT * FROM students WHERE Mail_id ='{email}'")
    member=cur.fetchone()
    print("member: ", member)
    for i in club:
        if ( i[0] == clubName):
            verified = True
        
    if(not verified):
        # Check if is admin 
        if(email == "garvitgalgat@gmail.com"):
            verified = True

    if(verified):
        return render_template("details.html",
                              email=member[0],
                              name=member[1],
                              link=member[2],
                              branch=member[3],
                              roll=member[4],
                              phone=member[5],
                              yr=member[6],Bio=member[7])
    else:
        return render_template("notAuthorized.html")



# Club Routes ----------------------------------------------------------
import clubs
app.register_blueprint(clubs.clubs)
# =========


@app.route("/student", methods=['GET', 'POST'])
def student():

    user = dict(session).get("email", None)
    if(user == None):
        return render_template("signIn.html")

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
            Bio=student['Bio']
            # send_mail(Mail_Id, "Thanks for trusting clubsIITI here are your submitted details: \nYour Mail Id : {}\n Full Name: {}\n LinkedIn: {}\n Branch: {}\n Roll No.: {}\n Phone No.: {}\n Current Year: {}\n Bio: {}\n".format(Mail_Id, Full_Name, LinkedIn, Branch, Roll_No, Phone_No, Current_Year,Bio))

            if(Mail_Id == user):
                cur = mysql.connection.cursor()
                cur.execute(
                    "INSERT INTO students VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE Mail_Id=%s, Full_Name=%s, LinkedIn=%s, Branch=%s, Roll_No=%s, Phone_No=%s, Current_Year=%s, Bio=%s",
                    (Mail_Id, Full_Name, LinkedIn, Branch, Roll_No, Phone_No,
                    Current_Year,Bio, Mail_Id, Full_Name, LinkedIn, Branch, Roll_No, Phone_No,
                    Current_Year,Bio))
                
                mysql.connection.commit()
                cur.close()

                return redirect("/")
            
            else:
                return render_template("notAuthorized.html")


        except (MySQLdb.Error, MySQLdb.Warning) as e:
            return str(e)

    else:
        # print("Redirect")
        return redirect("/login")



@app.route("/remove", methods=['POST'])
def bye():
    user = dict(session).get("email", None)
    if(user == None):
        return render_template("signIn.html")
    
    if request.method == 'POST':
        cur = mysql.connection.cursor()
        
        print("Executing Query: " + "DELETE FROM students WHERE Mail_Id='{}';".format(user))
        cur.execute("DELETE FROM students WHERE Mail_Id='{}';".format(user))
        mysql.connection.commit()
        cur.close()
        return render_template("goodbye.html")

    else:
        return render_template("error.html")

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

    
    # Find admin mail in database (assuming garvitgalgat@gmail.com is admin)
    if(email == "garvitgalgat@gmail.com"):
        session["name"] = "ADMIN"
        return redirect("/admin")

    
    if email[:3] in ("cse") and email[-11:] == "@iiti.ac.in":
        session["roll_no"] = email[3:12]
        session["branch"] = email[:3].upper()
        return redirect("/")
    elif email[:2] in ("ee", "me", "ce") and email[-11:] == "@iiti.ac.in":
        session["roll_no"] = email[2:11]
        session["branch"] = email[:2].upper()
        return redirect("/")
    elif email[:4] in ("mems") and email[-11:] == "@iiti.ac.in":
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

@app.route("/admin")
def admin():
    if(session['email'] == "garvitgalgat@gmail.com"):
        return "Hello USER"
    else:
        return render_template("error.html")



@app.errorhandler(404)
def page_not_found(e):
    print("Page Not Found")
    return render_template('error.html')


if __name__ == "__main__":
    if(env == 'dev'):
        app.run(debug=True)
    else:
        app.run()