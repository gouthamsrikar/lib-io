from flask import Flask, Response, request, jsonify
from datetime import datetime
import pymongo
import json
from bson.json_util import dumps

app = Flask(__name__)



try:
    mongo = pymongo.MongoClient(
        "")
    db = mongo.library
    mongo.server_info()

except Exception as ex:
    #print(ex)
    print("ERROR-cannot connect to mongodb")

###############################################################################


@app.route('/book', methods=["POST"])
def create_book():
    try:
        book=json.loads(request.data)
        
        dbResponse = db.books.insert_one(book)

        cursor = db.books.find_one({
            "_id": dbResponse.inserted_id
        }, {"_id": 0})

        return dumps(cursor)

    except Exception as ex:
        #print(ex)
        return Response(status=400)


@app.route('/book', methods=["GET"])
def get_all_books():
    try:
        bookName = request.args.get
        dbResponse = db.books.find({}, {"_id": 0}).limit(100)

        return dumps(dbResponse)

    except Exception as ex:
        #print(ex)
        return Response(status=500)


###############################################################################


@app.route('/search/books', methods=["GET"])
def search_book():
    try:
        bookName = request.args.get('book_name_or_term')
        category = request.args.get('category')
        from_rent = request.args.get('from_rent')
        to_rent = request.args.get('to_rent')

        query = {}

        if (bookName != None):
            query["book_name"] = {"$regex":  bookName}

        if (category != None):
            query["category"] = category

        if (from_rent != None and to_rent != None):
            query["rent"] = {"$gte": from_rent, "$lte": to_rent}

        dbResponse = db.books.find(query, {"_id": 0})

        return dumps(dbResponse)

    except Exception as ex:
        #print(ex)
        return Response(status=400)


###############################################################################


@app.route('/issue', methods=["POST"])
def issue_book():
    try:
        issue = {
            "book_name": request.form["book_name"],
            "person_name": request.form["person_name"],
            "issue_date": datetime.strptime(request.form["issue_date"], '%Y/%m/%d').timestamp(),
        }

        if (request.form["book_name"] == None or request.form["person_name"] == None or request.form["issue_date"] == None):
            return Response(status=400)
        else:
            bookCursor=db.books.find_one({"book_name":request.form["book_name"]})
            #print(bookCursor)
            if(bookCursor==None):
                return Response(status=400)
            else:
                dbresponse = db.transactions.insert_one(issue)

                cursor = db.transactions.find_one(
                    {"_id": dbresponse.inserted_id}, {"_id": 0})

                return dumps(cursor)



        

    except Exception as ex:
        #print(ex)
        return Response(status=500)


@app.route('/return', methods=["POST"])
def return_book():
    try:
        if (request.form["book_name"] == None or request.form["person_name"] == None or request.form["return_date"] == None):
            Response(status=400)

        map = {
            "book_name": request.form["book_name"],
            "person_name": request.form["person_name"],
            "return_date": None
        }

        updateMap = {
            "$set": {"return_date": datetime.strptime(request.form["return_date"], '%Y/%m/%d').timestamp()}
        }

        updateTransactionResult = db.transactions.update_one(map, updateMap)
        transactionCursor = db.transactions.find_one(
            {"_id": updateTransactionResult.upserted_id})
        bookCursor = db.books.find_one(
            {"book_name": request.form["book_name"]})

        days=datetime.fromtimestamp(transactionCursor.get("return_date"))-datetime.fromtimestamp(transactionCursor.get("issue_date"))
        

        total_rent = bookCursor.get("rent")*days 

        return dumps({"total_rent":total_rent})

    except Exception as ex:
        #print(ex)
        return Response(status=400)


###############################################################################


@app.route('/transactions/filter/bydate', methods=["GET"])
def transactions_filterbydate():
    try:
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')
        #print(from_date)
        #print(to_date)
        query = {}

        if (from_date != None and to_date != None):
            query["issue_date"] = {"$gte": datetime.strptime(request.form["from_date"], '%Y/%m/%d').timestamp(
            ), "$lte": datetime.strptime(request.form["to_date"], '%Y/%m/%d').timestamp()}

            # dbResponse = db.transactions.find(
            # query, {"_id": 0,})

            return dumps(query)

        else:
            return Response(status=400)

    except Exception as ex:
        #print(ex)
        return Response(status=400)


@app.route('/transactions/filter/bypersonname', methods=["GET"])
def transactions_filterbypersonname():
    try:
        person_name = request.args.get('person_name')

        query = {}

        if (person_name != None):
            query["person_name"] = person_name

            dbResponse = db.transactions.find(
                query, {"_id": 0, "issue_date": 0, "return_date": 0})

            return dumps(dbResponse)

        else:
            return Response(status=400)

    except Exception as ex:
        #print(ex)
        return Response(status=400)


@app.route('/transactions/filter/bybookname', methods=["GET"])
def transactions_filterbybookname():
    try:
        book_name = request.args.get('book_name')

        query1 = {}
        query2 = {}

        if (book_name != None):
            query1["book_name"] = book_name
            query2["book_name"] = book_name

            dbResponseAll = db.transactions.find(
                query1, {"_id": 0, "issue_date": 0, "return_date": 0})

            query2["return_date"] = None

            dbResponseCurrent = db.transactions.find(
                query2, {"_id": 0, "issue_date": 0, "return_date": 0})

            return jsonify({
                "total issues": dumps(dbResponseAll),
                "current issues": dumps(dbResponseCurrent)
            })

        else:
            return Response(status=400)

    except Exception as ex:
        #print(ex)
        return Response(status=500)


@app.route('/transactions/filter/rentbybook', methods=["GET"])
def transactions_rentbybook():
    try:
        book_name = request.args.get('book_name')

        query = {}

        if (book_name != None):
            query["book_name"] = book_name
            query["return_date"]={"$exists":True}
            total_days=0
            
            dbResponse = db.transactions.find(
                query, {"_id": 0,})

            for document in dbResponse:
                days=datetime.fromtimestamp(document.get("return_date"))-datetime.fromtimestamp(document.get("issue_date"))
                total_days=total_days + days.days 

            bookCursor=db.books.find_one({"book_name":book_name},{"rent":1}) 

            total_rent=total_days*bookCursor.get("rent")

            return jsonify({"total_rent":total_rent})

        else:
            return Response(status=400)

    except Exception as ex:
        #print(ex)
        return Response(status=400)


###############################################################################

if __name__ == "__main__":
    app.run(port=5000, debug=True)
