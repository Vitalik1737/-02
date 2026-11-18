import pytest
from app import app, get_db

@pytest.fixture()
def client(tmp_path):
    app.config.update(TESTING=True, DATABASE=str(tmp_path / "test.sqlite3"))
    with app.test_client() as client:
        yield client

def category_id(client, kind="expense"):
    data=client.get("/api/categories").get_json()
    return next(x["id"] for x in data if x["kind"]==kind)

def test_home_page(client):
    assert client.get("/").status_code == 200

def test_categories_endpoint(client):
    response=client.get("/api/categories")
    assert response.status_code == 200 and len(response.get_json()) >= 2

def test_create_transaction(client):
    response=client.post("/api/transactions",json={"amount":"1250.00","kind":"expense","category_id":category_id(client),"operation_date":"2026-06-09","comment":"Продукты"})
    assert response.status_code == 201
    assert response.get_json()["amount"] == "1250.00"

def test_reject_non_positive_amount(client):
    response=client.post("/api/transactions",json={"amount":"0","kind":"expense","category_id":category_id(client)})
    assert response.status_code == 400

def test_reject_wrong_category_kind(client):
    response=client.post("/api/transactions",json={"amount":"100","kind":"income","category_id":category_id(client,"expense")})
    assert response.status_code == 400

def test_summary(client):
    client.post("/api/transactions",json={"amount":"50000","kind":"income","category_id":category_id(client,"income"),"operation_date":"2026-06-01"})
    client.post("/api/transactions",json={"amount":"1250","kind":"expense","category_id":category_id(client,"expense"),"operation_date":"2026-06-02"})
    result=client.get("/api/reports/summary").get_json()
    assert result == {"income":50000.0,"expense":1250.0,"balance":48750.0}
