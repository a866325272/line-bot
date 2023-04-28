from google.cloud import firestore
#db = firestore.Client()

def get_firestore_field(collection: str,document: str,field):
    doc_ref = db.collection(collection).document(document)
    doc = doc_ref.get()
    if doc.exists:
        try:
            value = doc.get(field)
            return value
        except:
            return None
    else:
        return None

def update_firestore_field(collection: str,document: str,field: str,value):
    doc_ref = db.collection(collection).document(document)
    try:
        try:
            doc_ref.update({
                field: value
            })
        except:
            # If the document does not exist, create a new one
            doc_ref.set({
                field: value
            })
        #print(f'{collection}/{document}/{field}/{value} updated success')
    except:
        #print(f'{collection}/{document}/{field}/{value} updated failed')
        pass

def append_firestore_array_field(collection: str,document: str,field: str,value):
    doc_ref = db.collection(collection).document(document)
    try:
        doc_ref.update({
            field: firestore.ArrayUnion(value)
        })
        #print(f'{collection}/{document}/{field}/{value} updated success')
    except:
        #print(f'{collection}/{document}/{field}/{value} updated failed')
        pass

def delete_firestore_field(collection: str,document: str,field):
    doc_ref = db.collection(collection).document(document)
    doc_ref.update({
        field: firestore.DELETE_FIELD
    })
    #rint(f'{collection}/{document}/{field} deleted success')