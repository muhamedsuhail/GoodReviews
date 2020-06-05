import os
import datetime
import arrow
from passlib.hash import sha256_crypt
import requests
from flask import Flask, session,render_template,request,redirect,flash,jsonify
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
db = scoped_session(sessionmaker(bind=engine))

@app.route("/",methods=["GET","POST"])
def login():

	#Login page
	#Clears all active sessions
	session.clear()

	if request.method=='GET':
		return render_template("login.html")

	#Login Credentials
	name=request.form.get("username")
	password=request.form.get("password")

	#Check if all credentials are entered
	if not name or not password:
		flash("Enter all the credentials",'danger')

	#Check for user in database 
	if db.execute("SELECT password FROM users WHERE username=:username",{"username":name}).rowcount==0:
		flash("Invalid credentials",'danger')
		return render_template("login.html")
	hpassw=db.execute("SELECT password FROM users WHERE username=:uname",{"uname":name}).fetchone()[0]

	#Verify the password user entered with the hashed password in database
	if sha256_crypt.verify(password,hpassw):
		session["uname"]=name #login as user "name"
		flash(f"Successfully logged in as {name}",'success')
		return redirect("/search")
	else:
		flash("Incorrect password",'danger')
		return render_template("login.html")

@app.route("/register",methods=["POST","GET"])
def register():

	#Registration page
	session.clear()

	if request.method=='GET':
		return render_template("register.html")

	#User credentials
	name=request.form.get("username")
	password=request.form.get("password")
	rpassword=request.form.get("rpassword")

	#Check for all credentials
	if not name or not password:
		flash("Enter valid credentials",'warning')
		return render_template("register.html")

	#Check for existing user with the same name
	if db.execute("SELECT password FROM users WHERE username=:username",{"username":name}).rowcount!=0:
		flash("Username aldready exists",'warning')
		return render_template("register.html")

	if password!=rpassword:
		flash("Passwords does not match",'warning')
		return render_template("register.html")


	#Hash password with sha256 and store the hash in database
	hpass=sha256_crypt.encrypt(password)
	db.execute("INSERT INTO users (username,password) VALUES(:name,:password)",{"name":name,"password":hpass})
	db.commit()

	flash("Successfully Registered!",'success')
	return redirect("/")

@app.route("/search",methods=["GET","POST"])
@login_required
def search():

	#Search page

	if request.method=='POST':
		search=request.form.get("search").capitalize()
		#Append % for LIKE operation- sql
		query=str('%'+search+'%')

		books=db.execute("SELECT * FROM books WHERE isbn LIKE :query OR title LIKE :query OR author LIKE :query LIMIT 15",{"query":query}).fetchall()

		if not books:
			return render_template("error.html",message="Oops! We can't find books with that description")
		return render_template("index.html",books=books,user=session["uname"])
	return render_template("index.html",user=session["uname"])

@app.route("/book/<isbn>",methods=["GET","POST"])
@login_required
def book(isbn):

	#Book page

	book=db.execute("SELECT * FROM books WHERE isbn=:id",{"id":isbn}).fetchone()
	review=db.execute("SELECT username,rating,review,to_char(time, 'DD Mon YYYY - HH24:MI:SS') as time FROM reviews WHERE book_id=:id",{"id":book.id}).fetchall()
	
	#Goodreads API key
	key=os.getenv("GOOD_READS_KEY")

	#Get review count from goodreads api
	res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": key, "isbns":isbn})


	if request.method=='POST':

		#Get rating and review from current user
		rating=int(request.form.get('rating'))
		review=request.form.get('review')

		#Get book id
		id=db.execute("SELECT id from books WHERE isbn=:id",{"id":isbn}).fetchone()[0]

		# 1 review per user
		if db.execute("SELECT * FROM reviews WHERE username=:uname AND book_id=:id",{"uname":session["uname"],"id":id}).rowcount!=0:
			flash("You have aldready submitted a review",'warning')
			return	redirect("/book/"+isbn)

		db.execute("INSERT INTO reviews(username,book_id,rating,review) VALUES(:uname,:id,:rtg,:rev)",{"uname":session["uname"],"id":id,"rtg":rating,"rev":review})
		db.commit()

		return redirect("/book/"+isbn)

	return render_template("book.html",book=book,res=res,reviews=review,user=session["uname"])

@app.route("/api/<isbn>")
def api_req(isbn):

	#Api access

	#Get book details from database...Get the average and Count of ratings and reviews
	book=db.execute("SELECT id,title,author,year,isbn FROM books WHERE isbn=:id ",{"id":isbn}).fetchone()

	#Wrong ISBN- 404 Error

	if book is None:
		return jsonify({"Error": "Invalid ISBN"}),404


	review=db.execute("SELECT COUNT(id) as review_count,AVG(rating) as average_score FROM reviews WHERE book_id=:id",{"id":book.id}).fetchone()	

	#Converting book items to json format
	bk=dict(book.items())
	rv=dict(review.items())
	bk.update(rv)

	#Rounding of the average score to 2 decimal places
	if bk['average_score']!=None:
		bk['average_score']=float('%.2f'%(bk['average_score']))
	
	return jsonify(bk)

	