import os, json, requests

from flask import Flask, session, render_template,flash, request,redirect,jsonify, url_for
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    return render_template("homepage.html")


@app.route("/login", methods=["POST", "GET"])
def login():
        return render_template("login.html")

@app.route("/register", methods = ["POST", "GET"])
def register():
    if request.method == "POST":
        usernames = db.execute("select username,password from users").fetchall()
        newuser = request.form['username']
        newpass = request.form['password']

        for users in usernames:
            if newuser == users.username:
                return render_template("login.html",alert = "Username has been used!")
        
        if len(newpass)<8:
            return render_template("login.html", alert = "Password needs to be longer than 8!")
    
        
        db.execute("insert into users(username,password) values(:newuser,:newpass)",{"newuser":newuser,"newpass":newpass})
        db.commit()
        return render_template("login.html",alert = "Successfully Registered!")
    else:
        return render_template("Error.html")


@app.route("/searchome", methods = ["POST", "GET"])
def searchome():
        session.clear()
        if request.method == "POST":
            currentuser = request.form['username']
            currentpass = request.form['password']
            searchuser = db.execute("select * from users where username=:currentuser",{"currentuser":currentuser}).fetchone()
            if searchuser is None:
                return render_template("login.html",alert="Invalid Username!")
            
            if currentpass != searchuser.password:
                return render_template("login.html",alert= "Wrong Password!")
            session["sessionid"]=searchuser.user_id 
            return render_template("searchome.html")
        else:
            return render_template("Error.html")

@app.route("/logout",methods = ["POST","GET"])
def logout():
    if 'sessionid' in session:
        session.pop('sessionid',None)
        return render_template("homepage.html")
    
    else:
        return render_template("homepage.html")

@app.route("/search", methods = ["POST","GET"])
def search():
    if request.method == "POST":
        keyword = request.form['search']
        if keyword is None:
            return render_template("searchome.html",alert = "Nothing was searched!")
        keyword = keyword.lower()
        books1 = db.execute("select * from books").fetchall()

        book = []
        isbn = []

        for a in books1:
            if keyword in (a.title).lower() or keyword == '%'+a.isbn+'%':
                book.append(f"{a.title} - {a.author} - {a.isbn}")
                isbn.append(a.isbn)
            
            
            if keyword in (a.author).lower() or keyword == '%'+a.isbn+'%':
                book.append(f"{a.title} - {a.author} - {a.isbn}")
                isbn.append(a.isbn)
            
            
            if keyword in a.isbn or keyword == '%'+a.isbn+'%':
                book.append(f"{a.title} - {a.author} - {a.isbn}")
                isbn.append(a.isbn)    
        
        if not book:
            return render_template("searchome.html", alert = "No matches found!")
        
        else:       
            book = zip(book,isbn)

            return render_template("search.html",results = book)

    else:
        return  render_template("Error.html")


@app.route("/book/<string:isbn>",methods=["POST","GET"])
def book(isbn):
    if book in session:
        session.pop(book,None)
    
    session["booksession"]=isbn
    dbinfo = db.execute("select * from books where isbn= :isbn",{"isbn":isbn}).fetchone()
    try:
        retrieve = requests.get("https://www.goodreads.com/book/review_counts.json",params={"key":"z1PQoAwp0KAHaC7kkFglg","isbns":isbn})
        data = retrieve.json()
        totrating=data['books'][0]['work_ratings_count']
        goodrating=data['books'][0]['average_rating']
    
    except json.decoder.JSONDecodeError:
        totrating= "N/A"
        goodrating = "N/A"

    title=dbinfo.title
    author=dbinfo.author
    year=dbinfo.year
    revusername=[]
    revlist=[]
    ratecounter = 0
    allreviews = db.execute("select * from reviews where isbn= :isbn",{"isbn":isbn}).fetchall()
    if not allreviews:
        return render_template("book.html",isbn=isbn,title=title,author=author,year=year,ratingcount=totrating,rating=goodrating)
    
    for per in range(len(allreviews)):
        userdb=db.execute("select username from users where user_id=:id",{"id":allreviews[per].user_id}).fetchone()
        revusername.append(userdb.username)
        revlist.append(allreviews[per].reviews)
        ratecounter += allreviews[per].rating
    revfinal = zip(revusername,revlist)

    ownrating = ratecounter/len(allreviews)
    return render_template("book.html",isbn=isbn,title=title,author=author,year=year,ratingcount=totrating,rating=goodrating,bookreviews =revfinal,project1rating=ownrating)


@app.route("/review",methods = ["POST","GET"])
def addreview():
    if request.method == "POST":
        tempid = session["sessionid"]
        tempbook = session["booksession"]

        userdb = db.execute("select from reviews where user_id = :tempid and isbn = :tempbook",{"tempid":tempid,"tempbook":tempbook}).fetchone()

        if userdb is not None:
            return redirect(url_for("book",isbn=tempbook))

        
        userrating = request.form['rate']
        userreview = request.form['userreview']
        db.execute("insert into reviews (isbn,user_id,reviews,rating)values (:tempbook,:tempid,:userreview,:userrating)",{"tempbook":tempbook,"tempid":tempid,"userreview":userreview,"userrating":userrating})
        db.commit()

        return redirect(url_for("book",isbn=tempbook))

    else:
        return render_template("book.html")


@app.route("/api/<string:isbn>", methods = ["GET"])
def api(isbn):
    book = db.execute("select * from books where isbn = :isbn",{"isbn":isbn}).fetchone()
    if book is None:
        return render_template("Error.html")

    try:
        retrieve2 = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "z1PQoAwp0KAHaC7kkFglg", "isbns": isbn})
        data = retrieve2.json()
        totrating2 = data["books"][0]["work_ratings_count"]
        goodrating2 = data["books"][0]["average_rating"]
    
    except json.decoder.JSONDecodeError:
        totrating2 = "N/A"
        goodrating2 = "N/A"
    isbn = book.isbn
    title = book.title
    author = book.author
    year = book.year

    return jsonify({
        "title":title,
        "author":author,
        "year":year,
        "isbn":isbn,
        "Review_count": totrating2,
        "average_score":goodrating2
    })
    




    