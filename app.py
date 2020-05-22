import os
import razorpay
import json
from flask import Flask, render_template, request
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


app = Flask(__name__,static_folder = "static")

engine = create_engine(os.environ.get("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

razorpay_client = razorpay.Client(auth=("rzp_test_cdJnNzG9Ar1H1T",os.environ.get("RAZORPAY_SECRET_KEY")))

@app.route("/")
def index():
    flights = db.execute("SELECT * FROM flights").fetchall()
    return render_template("index.html", flights=flights)

@app.route("/book", methods=["POST"])
def book():
    name = request.form.get("name")
    date= request.form.get("date")

    try:
        flight_id = int(request.form.get("flight_id"))
    except ValueError:
        return render_template("error.html", message="Payment failed or Invalid flight number.")

    if db.execute("SELECT * FROM flights WHERE id = :id", {"id": flight_id}).rowcount == 0:
        return render_template("error.html", message="No such flight with that id.")

    try:
      amount = 1000000
      payment_id = request.form['razorpay_payment_id']
      razorpay_client.payment.capture(payment_id, amount)
      db.execute("INSERT INTO passengers (name, flight_id, date) VALUES (:name, :flight_id, :date)",{"name": name, "flight_id": flight_id, "date":date})
      db.commit()
      return render_template("success.html",info=json.dumps(razorpay_client.payment.fetch(payment_id)))

    except:
      return render_template("error.html", message="Payment failed")


@app.route("/flights")
def flights():
    """Lists all flights."""
    flights = db.execute("SELECT * FROM flights").fetchall()
    return render_template("flights.html", flights=flights)

@app.route("/flights/<int:flight_id>")
def flight(flight_id):
    """Lists details about a single flight."""


    flight = db.execute("SELECT * FROM flights WHERE id = :id", {"id": flight_id}).fetchone()
    if flight is None:
        return render_template("error.html", message="No such flight.")


    passengers = db.execute("SELECT name,date,id FROM passengers WHERE flight_id = :flight_id",
                            {"flight_id": flight_id}).fetchall()
    return render_template("flight.html", flight=flight, passengers=passengers)
