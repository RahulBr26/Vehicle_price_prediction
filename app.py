from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    flash
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

import sqlite3
import pandas as pd
import joblib
import os
from datetime import datetime


app = Flask(__name__)

app.secret_key = "vehicle_price_secret_key"



# ---------------- UPLOAD ----------------


UPLOAD_FOLDER = "uploads"


if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER





# ---------------- MODEL ----------------


model = joblib.load("model.pkl")

features = joblib.load("features.pkl")





# ---------------- DATABASE ----------------


DATABASE = "vehicle.db"



def get_db():

    conn = sqlite3.connect(DATABASE)

    conn.row_factory = sqlite3.Row

    return conn





def create_tables():

    conn = get_db()



    conn.execute("""
    CREATE TABLE IF NOT EXISTS users(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT NOT NULL,

        email TEXT UNIQUE NOT NULL,

        password TEXT NOT NULL,

        role TEXT DEFAULT 'user'

    )
    """)




    conn.execute("""
    CREATE TABLE IF NOT EXISTS predictions(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER,

        car_name TEXT,

        year INTEGER,

        kms INTEGER,

        fuel TEXT,

        seller TEXT,

        transmission TEXT,

        owner INTEGER,

        predicted_price REAL,

        image TEXT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )
    """)



    conn.commit()

    conn.close()





create_tables()





# ---------------- HOME ----------------



@app.route("/")

def home():

    if "user_id" in session:

        return redirect("/dashboard")


    return redirect("/login")







# ---------------- REGISTER ----------------



@app.route("/register", methods=["GET","POST"])

def register():


    if request.method=="POST":


        name=request.form["name"]

        email=request.form["email"]

        password=request.form["password"]

        confirm=request.form["confirm_password"]



        if password != confirm:

            flash("Password does not match")

            return redirect("/register")



        password_hash=generate_password_hash(password)



        conn=get_db()


        try:


            conn.execute(

            """
            INSERT INTO users
            (name,email,password)

            VALUES(?,?,?)

            """,

            (
                name,
                email,
                password_hash
            )

            )


            conn.commit()


            flash("Registration successful")


            return redirect("/login")



        except:


            flash("Email already exists")



        finally:

            conn.close()



    return render_template("register.html")









# ---------------- LOGIN ----------------



@app.route("/login", methods=["GET","POST"])

def login():



    if request.method=="POST":



        email=request.form["email"]

        password=request.form["password"]



        conn=get_db()



        user=conn.execute(

        """
        SELECT * FROM users
        WHERE email=?

        """,

        (email,)

        ).fetchone()



        conn.close()





        if user and check_password_hash(

            user["password"],

            password

        ):


            session["user_id"]=user["id"]

            session["name"]=user["name"]

            session["role"]=user["role"]



            return redirect("/dashboard")



        else:


            flash("Invalid email or password")




    return render_template("login.html")









# ---------------- LOGOUT ----------------



@app.route("/logout")

def logout():

    session.clear()

    return redirect("/login")









# ---------------- DASHBOARD ----------------



@app.route("/dashboard")

def dashboard():


    if "user_id" not in session:

        return redirect("/login")



    conn=get_db()



    total=conn.execute(

        """
        SELECT COUNT(*)
        FROM predictions

        WHERE user_id=?

        """,

        (session["user_id"],)

    ).fetchone()[0]





    avg=conn.execute(

        """
        SELECT AVG(predicted_price)
        FROM predictions

        WHERE user_id=?

        """,

        (session["user_id"],)

    ).fetchone()[0]





    recent=conn.execute(

        """
        SELECT *
        FROM predictions

        WHERE user_id=?

        ORDER BY id DESC
        LIMIT 5

        """,

        (session["user_id"],)

    ).fetchall()




    conn.close()



    return render_template(

        "dashboard.html",

        total_predictions=total,

        avg_price=round(avg or 0,2),

        recent_predictions=recent

    )









# ---------------- PREDICT ----------------



@app.route("/predict",methods=["GET","POST"])

def predict():



    if "user_id" not in session:

        return redirect("/login")



    prediction=None



    if request.method=="POST":



        car_name=request.form["car_name"]

        year=int(request.form["year"])

        present_price=float(request.form["present_price"])

        kms=int(request.form["kms"])

        fuel=request.form["fuel"]

        seller=request.form["seller"]

        transmission=request.form["transmission"]

        owner=int(request.form["owner"])





        filename=""



        if "image" in request.files:


            image=request.files["image"]


            if image.filename!="":


                filename=image.filename.replace(" ","_")


                image.save(

                    os.path.join(

                        UPLOAD_FOLDER,

                        filename

                    )

                )







        data=pd.DataFrame([{

            "Car_Name":car_name,

            "Year":year,

            "Present_Price":present_price,

            "Kms_Driven":kms,

            "Fuel_Type":fuel,

            "Seller_Type":seller,

            "Transmission":transmission,

            "Owner":owner

        }])





        data=pd.get_dummies(data)



        for col in features:

            if col not in data.columns:

                data[col]=0



        data=data[features]





        prediction=model.predict(data)[0]


        prediction=round(float(prediction),2)





        conn=get_db()



        conn.execute(

        """

        INSERT INTO predictions

        (

        user_id,

        car_name,

        year,

        kms,

        fuel,

        seller,

        transmission,

        owner,

        predicted_price,

        image

        )


        VALUES(?,?,?,?,?,?,?,?,?,?)

        """,

        (

        session["user_id"],

        car_name,

        year,

        kms,

        fuel,

        seller,

        transmission,

        owner,

        prediction,

        filename

        )

        )



        conn.commit()

        conn.close()





    return render_template(

        "predict.html",

        prediction=prediction

    )









# ---------------- HISTORY ----------------



@app.route("/history")

def history():


    if "user_id" not in session:

        return redirect("/login")



    conn=get_db()



    data=conn.execute(

    """

    SELECT *

    FROM predictions

    WHERE user_id=?

    ORDER BY id DESC

    """,

    (session["user_id"],)

    ).fetchall()



    conn.close()



    return render_template(

        "history.html",

        predictions=data

    )









# ---------------- ADMIN ----------------



@app.route("/admin")

def admin():



    if session.get("role")!="admin":

        return redirect("/dashboard")



    conn=get_db()



    users=conn.execute(

        "SELECT * FROM users"

    ).fetchall()



    predictions=conn.execute(

        "SELECT * FROM predictions"

    ).fetchall()



    conn.close()



    return render_template(

        "admin.html",

        users=users,

        predictions=predictions

    )









# ---------------- RUN ----------------



if __name__=="__main__":

    app.run(debug=True)