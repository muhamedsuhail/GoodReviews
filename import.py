import csv
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine("postgres://qsfiaphzyrmsbm:d5fc6c9d9dcda8fa08e0b4fe70cd8546300b41a9a78f35263875407086c225ed@ec2-18-215-99-63.compute-1.amazonaws.com:5432/d59irftjbknjb0")
db=scoped_session(sessionmaker(bind=engine))
def main():
	f=open("books.csv")
	reader=csv.reader(f)
	for isbn,title,author,year in reader:
		db.execute("INSERT INTO books (isbn,title,author,year) VALUES(:a,:b,:c,:d)",{"a":isbn,"b":title,"c":author,"d":year})
		db.commit()
	#Remove duplicate books
	#SELECT title,COUNT(title) FROM books GROUP BY title HAVING COUNT(title)>1 ORDER BY title;
	#DELETE  FROM books a USING books b WHERE a.id<b.id AND a.title=b.title;

if __name__=="__main__":
	main()
