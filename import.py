import os
import csv
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session,sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


def main():
    file=open("books.csv")
    read=csv.reader(file)
    id = 0
    next(read)
    for isbn,title,author,year in read:
        temp = int(year)
        db.execute("insert into books(isbn,title,author,year) values (:isbn,:title,:author,:temp)", {"isbn":isbn,"title":title,"author":author,"temp":temp})
        id+1
        print(id)
    

    db.commit()



if __name__ == "__main__":
    main()