from flask import Flask, render_template, redirect, request, session, url_for
from flask_mysqldb import MySQL
import smtplib, ssl, re
import MySQLdb
import yaml
from authlib.integrations.flask_client import OAuth
import os
from functions.dbConfig import database_config


app = Flask(__name__)

env = "dev"
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

@app.route("/clubs/<clubName>")
def club(clubName):

    cur = mysql.connection.cursor()
    cur.execute("select * from clubs WHERE Title=\'{}\'".format(clubName))
    club = cur.fetchone()

    # Check if club exists ----------------
    try:
        title = club[1]
        info = club[2]
        achievements = club[3]
        website = club[6]
        events = club[-1]

    except:
        return render_template("error.html")
    member = False
    verified = False
    notexist = True
    imageUrl = img[clubName]
    # print('-----------------')
    # print(imageUrl)
    # -----------------------------------------

    # verifying the current email id ---------------
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
    # ----------------------------------------------

    # verifying the current email id with current members ---------------
    try:
        cur.execute("SELECT Club_Name FROM clubmembers WHERE Mail_Id = '{}'".format(session["email"]))
        club = cur.fetchall()
        # print(club)

        for i in club:
            # print(i[0])
            if i[0] == title:
                notexist = False

        if notexist:
            cur.execute("SELECT Club_Name FROM approvals WHERE Mail_Id = '{}'".format(session["email"]))
            clb = cur.fetchall()
            for i in clb:
            # print(i[0])
                if i[0] == title:
                    notexist = False
        
    except:
        notexist=True
    # ----------------------------------------------

    # verifying iiti student ---------------
    try:
        email = session["email"] 
        if email[-11:]=="@iiti.ac.in":
            member = True
    except:
        member = False


    # ----------------------------------------------

    # Get new recruits from database
    cur.execute("select Club_Name FROM clubs WHERE Title='{}'".format(clubName))
    club=cur.fetchone()
    # print(club)
    

    cur.execute("SELECT Full_Name, Mail_Id, CurrentStatus FROM approvals INNER JOIN students USING(Mail_Id) WHERE Club_Name = '{}'".format(club[0]))
    newRecruits=cur.fetchall()
    print("newRecruits: ", newRecruits)
    cur.execute("SELECT FUll_Name, Mail_Id FROM students WHERE Mail_id IN (SELECT Mail_id FROM clubmembers WHERE Club_Name='{}');".format(club[0]))
    currentMembers=cur.fetchall()
    print("currentMembers: ", currentMembers)
    # print(clubName)

    
    if(not verified):
        # Check if is admin 
        email = session["email"]
        if(email == "garvitgalgat@gmail.com"):
            verified = True
    print("verified:", verified)
    
    return render_template("clubtemplate.html",
                           title=title,
                           info=info,
                           achievements=achievements,
                           website=website,
                           clubName=clubName,
                           imageUrl=imageUrl,
                           verified=verified,notexist=notexist,member=member,
                           currentMembers=currentMembers,newRecruits=newRecruits, events=events)


@app.route("/clubs/<clubName>/apply")
def apply(clubName):
    cur = mysql.connection.cursor()
    user = dict(session).get("email", None)

    if(user == None):
        return render_template("signIn.html")
    else:
        cur = mysql.connection.cursor()
        cur.execute("select Club_Name FROM clubs WHERE Title='{}'".format(clubName))
        club=cur.fetchone()
        cur.execute("INSERT INTO approvals VALUES('{}', '{}', 'U');".format(user, club[0]))
        mysql.connection.commit()
        cur.execute("select * from clubs WHERE Title=\'{}\'".format(clubName))
        club_title = cur.fetchone()
        cur.close()
        title = club_title[1]
        send_mail(user, "Subject: Thanks for applying\n\nThank you for applying to {}. \n You will soon recieve a mail regarding the interview from the club head".format(title))
        return render_template("applied.html", title=title)





@app.route("/clubs/<clubName>/<manage>/<email>")
def manage(clubName, manage, email):

    # print(manage + " " + email + " in " + clubName)
    cur = mysql.connection.cursor()
    user = dict(session).get("email", None)
    if(user == None):
        return render_template("signIn.html")
    
    verified = False
    # Check if is admin 
    if(email == "garvitgalgat@gmail.com"):
        verified = True
    else:
        print("Running query: ", "SELECT Club_Title FROM clubheads WHERE Club_Head_Mail_Id = '{}'".format(session["email"]))
        cur.execute(f"SELECT Club_Title FROM clubheads WHERE Club_Head_Mail_Id ='{user}'")
        club = cur.fetchall()

        for i in club:
            if ( i[0] == clubName):
                verified = True

    if(verified):
        
        # Remove student from the club
        if(manage == "remove"):
            # print("Remove {} from {}".format(email, clubName))
            cur = mysql.connection.cursor()
            cur.execute("select Club_Name FROM clubs WHERE Title='{}'".format(clubName))
            club=cur.fetchone()
            print("Executing Query: " + "DELETE FROM clubMembers WHERE Mail_Id='{}' AND Club_Name='{}';".format(email, club[0]))
            cur.execute("DELETE FROM clubMembers WHERE Mail_Id='{}' AND Club_Name='{}';".format(email, club[0]))
            mysql.connection.commit()
            cur.close()
            return redirect("/clubs/{}".format(clubName))

        elif(manage == "approve"):
            cur = mysql.connection.cursor()
            cur.execute("select Club_Name FROM clubs WHERE Title='{}'".format(clubName))
            club=cur.fetchone()
            cur.execute("INSERT INTO clubmembers VALUES ('{}','{}');".format(email, club[0]))
            cur.execute("DELETE FROM approvals WHERE Mail_Id='{}' AND Club_Name='{}';".format(email, club[0]))
            cur.execute("DELETE FROM meetings WHERE student_mail_id = '{}' AND host_mail_id = '{}'".format(email, user))
            send_mail(email, "Subject:Welcome Welcome!!\n\nCongrats from {}\n You have been accepted into the club!!".format(club[0]))
            mysql.connection.commit()
            cur.close()
            return redirect("/clubs/{}".format(clubName))
            
        elif(manage == "reject"):
            cur = mysql.connection.cursor()
            cur.execute("select Club_Name FROM clubs WHERE Title='{}'".format(clubName))
            club=cur.fetchone()
            cur.execute("DELETE FROM approvals WHERE Mail_Id='{}' AND Club_Name='{}';".format(email, club[0]))
            mysql.connection.commit()
            cur.close()
            return redirect("/clubs/{}".format(clubName))     

        elif(manage == "schedule"):
            if(check(email)):
                # print("Sending mail to " +  email)
                # msg = "Scheduling Interview with clubhead of " + clubName
                # send_mail(user, "Interview scheduled with student")
                return render_template("interview.html", host=user, student = email, clubName=clubName, meeting_details=["", "", ""]) 

            else:
                return render_template("error.html")


        else:
            return render_template("error.html")
        
    else:
        return render_template("error.html")



@app.route("/clubs/<clubName>/edit", methods=['GET', 'POST'])
def edit(clubName):
    if request.method == 'GET':
        cur = mysql.connection.cursor()
        email = dict(session).get("email", None)
        if(email == None):
            return render_template("signIn.html")
        
        verified = False

        print("Running query: ", "SELECT Club_Title FROM clubheads WHERE Club_Head_Mail_Id = '{}'".format(session["email"]))
        cur.execute(f"SELECT Club_Title FROM clubheads WHERE Club_Head_Mail_Id ='{email}'")
        club = cur.fetchall()

        for i in club:
            if ( i[0] == clubName):
                verified = True

        if(not verified):
            # Check if is admin 
            if(email == "garvitgalgat@gmail.com"):
                verified = True

        if(verified):
            print("Running query:" , "select Info, Achievements, Events FROM clubs WHERE Title='{}'".format(clubName))
            cur.execute("select Info, Achievements, Events FROM clubs WHERE Title='{}'".format(clubName))
            information = cur.fetchone()
            return render_template("editor.html", info=information[0], achievements=information[1], clubName=clubName, events=information[2])

        else:
            return render_template("error.html")

    else:
        data = request.form
        # print("Fetched form data")
        info = data['info']
        # replace ' with " so that these string does not interfere with our sql queries
        info = info.replace("'",'"')
        achievements = data['achievements']
        achievements = achievements.replace("'",'"')
        events = data['events']
        events = events.replace("'",'"')
        cur = mysql.connection.cursor()
        print("Running query:","UPDATE clubs SET Info = '{}', Achievements = '{}', Events = '{}' WHERE Title = '{}'".format(info, achievements, events, clubName) )
        cur.execute("UPDATE clubs SET Info = '{}', Achievements = '{}', Events = '{}' WHERE Title = '{}'".format(info, achievements, events, clubName) )
        cur.execute("INSERT INTO events VALUES ('{}','{}', NOW());".format(clubName, events))

        mysql.connection.commit()
        cur.close()

        return redirect("/clubs/{}".format(clubName))



@app.route("/clubs/<clubName>/meeting/<student>" , methods=["GET", "POST"])
def schedule(clubName, student):

    user = dict(session).get("email", None)
    if(user == None):
        return render_template("signIn.html")
    
    details = request.form
    
    verified = False
    cur = mysql.connection.cursor()
    cur.execute(f"SELECT Club_Title FROM clubheads WHERE Club_Head_Mail_Id ='{user}'")
    club = cur.fetchall()
    
    for i in club:
        if ( i[0] == clubName):
            verified = True

    if(not verified):
        # Check if is admin 
        if(email == "garvitgalgat@gmail.com"):
            verified = True

    if(verified):
        
        if request.method == "POST":
            

            details = request.form
            time = details['time']
            time = time[:-3]

            date = details['date']
            date = date.split("/")
            date = date[2]+"-"+date[0]+"-"+date[1]

            link = details['link']
            host = details['host']
            

            # print(host, student, time, date, link)

            #Insert into db 

            send_mail(user, "Subject: Meeting Details\n\nMeeting scheduled with {}\nDetails: \nTime: {}\n Date: {}\n Link: {}".format(student, time, date, link))
            send_mail(student, "Subject: Meeting Details\n\nHere are the scheduled meeting details:\nTime: {}\n Date: {}\n Link: {}".format(time, date, link))

            cur = mysql.connection.cursor()
            # print("INSERT INTO meetings VALUES (%s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE host_mail_id=%s, student_mail_id=%s, meeting_time=%s, meeting_date=%s, link=%s",
            #     (host, student, time, date, link, 
            #         host, student, time, date, link ))
            cur.execute("INSERT INTO meetings VALUES (%s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE host_mail_id=%s, student_mail_id=%s, meeting_time=%s, meeting_date=%s, link=%s",
                (host, student, time, date, link, 
                    host, student, time, date, link ))
            cur.execute("UPDATE approvals SET CurrentStatus='A' WHERE Mail_Id='{}'".format(student))
            mysql.connection.commit()
            cur.close()
            # send mails
            return render_template("scheduled.html", student=student, link=link)

        else:
            if(check(student)):
                cur = mysql.connection.cursor()
                cur.execute("SELECT meeting_time, meeting_date, link FROM meetings WHERE host_mail_id = '{}' AND student_mail_id = '{}'".format(user, student))
                meeting_details = cur.fetchone()
                date = str(meeting_details[1])
                # print(date, type(date))
                date = date.split("-")
                date = date[1]+'/'+date[2]+'/'+date[0]
                date = date
                send_mail(user, "Subject: Meeting Updated\n\nMeeting updated with {}\nDetails:\nTime: {}\n Date: {}\n Link: {}".format(student, meeting_details[0], date, meeting_details[2]))
                # print(meeting_details)
                return render_template("interview.html", host=user, student = student, clubName=clubName, meeting_details=meeting_details, date=date) 
            else:
                return render_template("error.html")


    else:
        return render_template("error.html")




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