import os
import datetime
import calendar
import requests
from flask import Flask, session,render_template,request,redirect,flash
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from login import *
app = Flask(__name__)

#Check for environment variable
if not "postgres://qsfiaphzyrmsbm:d5fc6c9d9dcda8fa08e0b4fe70cd8546300b41a9a78f35263875407086c225ed@ec2-18-215-99-63.compute-1.amazonaws.com:5432/d59irftjbknjb0":
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine("postgres://qsfiaphzyrmsbm:d5fc6c9d9dcda8fa08e0b4fe70cd8546300b41a9a78f35263875407086c225ed@ec2-18-215-99-63.compute-1.amazonaws.com:5432/d59irftjbknjb0")
# engine=create_engine("postgres:///suhail1")
db = scoped_session(sessionmaker(bind=engine))

@app.route("/",methods=["GET","POST"])
def login():
	#login page
	session.clear()
	if request.method=='GET':
		return render_template("login.html")
	name=request.form.get("username")
	password=request.form.get("password")
	if not name or not password:
		flash("Enter all the credentials",'danger')
	#check for user 
	if db.execute("SELECT password FROM users WHERE username=:username",{"username":name}).rowcount==0:
		flash("Username not found")
		return render_template("login.html")
	passw=db.execute("SELECT password FROM users WHERE username=:uname",{"uname":name}).fetchone()
	if password==passw[0]:
		session["uname"]=name #login as user "name"
		flash(f"Successfully logged in as {name}",'success')
		return redirect("/search")
	else:
		flash("Incorrect password",'danger')
		return render_template("login.html")
@app.route("/register",methods=["POST","GET"])
def register():
	session.clear()
	if request.method=='GET':
		return render_template("register.html")
	name=request.form.get("username")
	password=request.form.get("password")
	rpassword=request.form.get("rpassword")
	if not name or not password:
		flash("Enter valid credentials",'warning')
		return render_template("register.html")
	if db.execute("SELECT password FROM users WHERE username=:username",{"username":name}).rowcount!=0:
		flash("Username aldready exists",'warning')
		return render_template("register.html")
	if password!=rpassword:
		flash("Passwords does not match",'warning')
		return render_template("register.html")
	db.execute("INSERT INTO users (username,password) VALUES(:name,:password)",{"name":name,"password":password})
	db.commit()
	return render_template("login.html")
@app.route("/search",methods=["GET","POST"])
@login_required
def search():
	if request.method=='POST':
		search=request.form.get("search").capitalize()
		query=str('%'+search+'%')
		books=db.execute("SELECT * FROM books WHERE isbn LIKE :query OR title LIKE :query OR author LIKE :query LIMIT 15",{"query":query}).fetchall()
		if not books:
			return render_template("error.html",message="Oops! We can't find books with that description")
		return render_template("index.html",books=books,user=session["uname"])
	return render_template("index.html",user=session["uname"])
@app.route("/book/<isbn>",methods=["GET","POST"])
@login_required
def book(isbn):
	book=db.execute("SELECT * FROM books WHERE isbn=:id",{"id":isbn}).fetchone()
	review=db.execute("SELECT * FROM reviews WHERE book_id=:id",{"id":book.id}).fetchall()
	print(review)
	key=os.getenv("GOOD_READS_KEY")
	res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": key, "isbns":isbn})
	if request.method=='POST':
		rating=int(request.form.get('rating'))
		review=request.form.get('review')
		id=db.execute("SELECT id from books WHERE isbn=:id",{"id":isbn}).fetchone()[0]
		if db.execute("SELECT * FROM reviews WHERE username=:uname AND book_id=:id",{"uname":session["uname"],"id":id}).rowcount!=0:
			flash("You have aldready submitted a review",'warning')
			return	redirect("/book/"+isbn)
		db.execute("INSERT INTO reviews(username,book_id,rating,review) VALUES(:uname,:id,:rtg,:rev)",{"uname":session["uname"],"id":id,"rtg":rating,"rev":review})
		db.commit()
		return redirect("/book/"+isbn)
	return render_template("book.html",book=book,res=res,reviews=review)
