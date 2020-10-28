from flask import Flask, render_template, redirect, request
from flask_mysqldb import MySQL
import MySQLdb
import yaml

app = Flask(__name__)

# COnfigure db
db = yaml.load(open('db.yaml'), Loader=yaml.FullLoader)

app.config['MYSQL_HOST'] = db['mysql_host']
app.config['MYSQL_USER'] = db['mysql_user']
app.config['MYSQL_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DB'] = db['mysql_db']

mysql = MySQL(app)


@app.route("/")
def cultural():
    return render_template('home.html')


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