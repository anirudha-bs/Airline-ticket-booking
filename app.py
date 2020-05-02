import os
import stripe
from flask import Flask, render_template, request
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


app = Flask(__name__)

engine = create_engine(os.environ.get("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

pub_key='pk_test_LzADRLfG3h8oxkH86qCszlhb00pt7VeSDB'
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
stripe.api_key = STRIPE_SECRET_KEY

@app.route("/")
def index():
    flights = db.execute("SELECT * FROM flights").fetchall()
    return render_template("index.html", flights=flights, pub_key=pub_key)

@app.route("/book", methods=["POST"])
def book():
    """Book a flight."""


    name = request.form.get("name")
    date= request.form.get("date")
    if date=='':
        return render_template("error.html", message="Enter valid date")
    try:
        flight_id = int(request.form.get("flight_id"))
    except ValueError:
        return render_template("error.html", message="Payment failed or Invalid flight number.")


    if db.execute("SELECT * FROM flights WHERE id = :id", {"id": flight_id}).rowcount == 0:
        return render_template("error.html", message="No such flight with that id.")

    try:
      customer = stripe.Customer.create(email=request.form['stripeEmail'], source=request.form['stripeToken'])

      amount=19900

      stripe.Charge.create(
      customer=customer.id,
      amount=amount,
      currency='usd',
      description='Flight ticket'
      )

    except:
        return render_template("error.html", message="Payment failed")


    db.execute("INSERT INTO passengers (name, flight_id, date) VALUES (:name, :flight_id, :date)",
            {"name": name, "flight_id": flight_id, "date":date})
    db.commit()
    return render_template("success.html")


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
