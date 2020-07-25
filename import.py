import csv
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine("postgres://teyayfrbjlhjdi:7e93c8a63c0d398fe344649b19a7aa8d4e6530a2c618f24db13fdf38e8346846@ec2-35-173-94-156.compute-1.amazonaws.com:5432/d29dns5h3o57tg")
db=scoped_session(sessionmaker(bind=engine))
def main():
	f=open('books.csv')
	reader=csv.reader(f)
	header=next(reader)
	for isbn,title,author,year in reader:
		db.execute("INSERT INTO books (isbn,title,author,year) VALUES(:a,:b,:c,:d)",{"a":isbn,"b":title,"c":author,"d":year})
		db.commit()
	f.close()
if __name__=="__main__":
	main()
