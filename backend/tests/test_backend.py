import pytest

import database
import app as app_module


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_file = tmp_path / "test_stocks.db"
    monkeypatch.setattr(database, "DB_PATH", db_file)
    database.init_db()

    app_module.app.config.update(TESTING=True)
    with app_module.app.test_client() as test_client:
        yield test_client


def make_stock(**overrides):
    payload = {
        "name": "Widget A",
        "quantity": 10,
        "price": 19.99,
        "purchase_date": "2026-01-15",
        "category": "Hardware",
    }
    payload.update(overrides)
    return payload


def create_stock(client, **overrides):
    resp = client.post("/api/stocks", json=make_stock(**overrides))
    return resp

def test_health_check(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}

def test_get_stocks_empty(client):
    resp = client.get("/api/stocks")
    assert resp.status_code == 200
    assert resp.get_json() == []
    
def test_get_stocks_returns_created_items_desc_by_id(client):
    create_stock(client, name="First")
    create_stock(client, name="Second")

    resp = client.get("/api/stocks")
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data) == 2
    # ORDER BY id DESC -> most recently created first
    assert data[0]["name"] == "Second"
    assert data[1]["name"] == "First"

def test_create_stock_success(client):
    resp = create_stock(client)
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["name"] == "Widget A"
    assert body["quantity"] == 10
    assert body["price"] == 19.99
    assert body["purchase_date"] == "2026-01-15"
    assert body["category"] == "Hardware"
    assert "id" in body
    assert "created_at" in body


def test_create_stock_without_category_defaults_to_none(client):
    payload = make_stock()
    del payload["category"]
    resp = client.post("/api/stocks", json=payload)
    assert resp.status_code == 201
    assert resp.get_json()["category"] is None


def test_create_stock_non_json_body_returns_400(client):
    resp = client.post("/api/stocks", data="not json", content_type="text/plain")
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "Request body must be JSON"


def test_create_stock_empty_json_body_returns_400(client):
    resp = client.post("/api/stocks", json={})
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "Request body must be JSON"


def test_create_stock_missing_all_fields_but_nonempty_body_returns_field_errors(client):
    resp = client.post("/api/stocks", json={"unrelated_key": "x"})
    assert resp.status_code == 400
    body = resp.get_json()
    assert "fields" in body
    assert set(body["fields"]) == {"name", "quantity", "price", "purchase_date"}


@pytest.mark.parametrize("field", ["name", "quantity", "price", "purchase_date"])
def test_create_stock_missing_required_field(client, field):
    payload = make_stock()
    del payload[field]
    resp = client.post("/api/stocks", json=payload)
    assert resp.status_code == 400
    assert field in resp.get_json()["fields"]


def test_create_stock_blank_name_rejected(client):
    resp = create_stock(client, name="   ")
    assert resp.status_code == 400
    assert "name" in resp.get_json()["fields"]


def test_create_stock_name_is_trimmed(client):
    resp = create_stock(client, name="  Widget B  ")
    assert resp.status_code == 201
    assert resp.get_json()["name"] == "Widget B"


@pytest.mark.parametrize("bad_quantity", [-1, "abc", None])
def test_create_stock_invalid_quantity_rejected(client, bad_quantity):
    resp = create_stock(client, quantity=bad_quantity)
    assert resp.status_code == 400
    assert "quantity" in resp.get_json()["fields"]


def test_create_stock_quantity_as_numeric_string_is_coerced(client):
    resp = create_stock(client, quantity="25")
    assert resp.status_code == 201
    assert resp.get_json()["quantity"] == 25


@pytest.mark.parametrize("bad_price", [-5.0, "expensive", None])
def test_create_stock_invalid_price_rejected(client, bad_price):
    resp = create_stock(client, price=bad_price)
    assert resp.status_code == 400
    assert "price" in resp.get_json()["fields"]


def test_create_stock_price_as_numeric_string_is_coerced(client):
    resp = create_stock(client, price="42.5")
    assert resp.status_code == 201
    assert resp.get_json()["price"] == 42.5


def test_create_stock_zero_quantity_and_price_allowed(client):
    resp = create_stock(client, quantity=0, price=0)
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["quantity"] == 0
    assert body["price"] == 0

def test_get_stock_by_id_found(client):
    created = create_stock(client).get_json()
    resp = client.get(f"/api/stocks/{created['id']}")
    assert resp.status_code == 200
    assert resp.get_json() == created


def test_get_stock_by_id_not_found(client):
    resp = client.get("/api/stocks/9999")
    assert resp.status_code == 404
    assert resp.get_json()["error"] == "Stock not found"

def test_update_stock_full_replacement(client):
    created = create_stock(client).get_json()
    resp = client.put(
        f"/api/stocks/{created['id']}",
        json=make_stock(name="Updated Widget", quantity=5, price=9.5,
                         purchase_date="2026-02-01", category="Software"),
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["name"] == "Updated Widget"
    assert body["quantity"] == 5
    assert body["price"] == 9.5
    assert body["purchase_date"] == "2026-02-01"
    assert body["category"] == "Software"


def test_update_stock_partial_field_only(client):
    created = create_stock(client).get_json()
    resp = client.put(f"/api/stocks/{created['id']}", json={"quantity": 100})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["quantity"] == 100
    # untouched fields remain the same as originally created
    assert body["name"] == created["name"]
    assert body["price"] == created["price"]
    assert body["purchase_date"] == created["purchase_date"]
    assert body["category"] == created["category"]


def test_update_stock_not_found(client):
    resp = client.put("/api/stocks/9999", json={"quantity": 1})
    assert resp.status_code == 404
    assert resp.get_json()["error"] == "Stock not found"


def test_update_stock_non_json_body_returns_400(client):
    created = create_stock(client).get_json()
    resp = client.put(
        f"/api/stocks/{created['id']}", data="oops", content_type="text/plain"
    )
    assert resp.status_code == 400


def test_update_stock_invalid_field_value_rejected(client):
    created = create_stock(client).get_json()
    resp = client.put(f"/api/stocks/{created['id']}", json={"quantity": -50})
    assert resp.status_code == 400
    assert "quantity" in resp.get_json()["fields"]


def test_update_stock_blank_name_rejected(client):
    created = create_stock(client).get_json()
    resp = client.put(f"/api/stocks/{created['id']}", json={"name": "   "})
    assert resp.status_code == 400
    assert "name" in resp.get_json()["fields"]


def test_update_stock_category_can_be_cleared_to_none(client):
    created = create_stock(client, category="Hardware").get_json()
    resp = client.put(f"/api/stocks/{created['id']}", json={"category": None})
    assert resp.status_code == 200
    assert resp.get_json()["category"] is None

def test_delete_stock_success(client):
    created = create_stock(client).get_json()
    resp = client.delete(f"/api/stocks/{created['id']}")
    assert resp.status_code == 200
    assert resp.get_json() == {"message": f"Stock {created['id']} deleted"}

    # confirm it's actually gone
    follow_up = client.get(f"/api/stocks/{created['id']}")
    assert follow_up.status_code == 404


def test_delete_stock_not_found(client):
    resp = client.delete("/api/stocks/9999")
    assert resp.status_code == 404
    assert resp.get_json()["error"] == "Stock not found"

def test_unknown_route_returns_404_json(client):
    resp = client.get("/api/does-not-exist")
    assert resp.status_code == 404
    assert resp.get_json()["error"] == "Not found"


def test_get_stock_with_non_integer_id_returns_404(client):
    # Flask's <int:stock_id> converter rejects non-integer path segments
    resp = client.get("/api/stocks/not-an-id")
    assert resp.status_code == 404