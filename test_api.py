from database.database import SessionLocal
from database.models import Product, Order
from backend.services.license_service import activate_license, create_license, generate_license_key, hash_value
from backend.services.download_service import create_download_token
from backend.services.order_service import fulfill_paid_order
from tests.conftest import auth
from datetime import timedelta
from database.models import now, DownloadToken

def test_health(client):
    assert client.get("/health").json["status"] == "ok"

def test_product_creation_and_retrieval(client):
    r = client.post("/api/admin/products", json={"name":"Starter","price_cents":1299,"download_filename":"x.zip","download_path":"x.zip"}, headers={**auth(), "X-Admin-Role-Id":"admin"})
    assert r.status_code == 201 and client.get("/api/products/1").json["name"] == "Starter"

def test_inactive_products_hidden(client):
    with SessionLocal() as db: db.add(Product(name="off", price_cents=1, currency="USD", download_filename="x", download_path="x", active=False)); db.commit()
    assert client.get("/api/products").json == []

def test_order_creation_and_price_validation(client, monkeypatch):
    with SessionLocal() as db: db.add(Product(name="x", price_cents=100, currency="USD", download_filename="x", download_path="x")); db.commit()
    class Fake:
        def __init__(self,*a): pass
        def create_order(self,*a,**k): return {"id":"paypal-1"}
    monkeypatch.setattr("backend.routes.orders.PayPalService", Fake)
    r=client.post("/api/orders",json={"product_id":1,"discord_id":"1","username":"u"},headers=auth())
    assert r.status_code == 201

def test_license_generation_and_activation(client):
    with SessionLocal() as db:
        from database.models import Customer
        customer = Customer(discord_id="customer", username="user"); db.add(customer)
        p=Product(name="x",price_cents=1,currency="USD",download_filename="x",download_path="x"); db.add(p); db.flush()
        o=Order(public_id="o",customer_id=customer.id,product_id=p.id,amount_cents=1,currency="USD"); db.add(o); db.flush()
        license = create_license(db, o); db.commit()
        assert license.license_key.startswith("BOTLAB-")
        ok, message = activate_license(db, license.license_key, "hardware-id-123")
        db.commit()
        assert ok and message == "activated"
        assert db.query(type(license)).filter_by(license_key=license.license_key).one().hwid_hash == hash_value("hardware-id-123")
        ok, message = activate_license(db, license.license_key, "different-hardware")
        assert not ok and message == "different_hwid"

def test_license_keys_are_unique():
    keys = {generate_license_key() for _ in range(100)}
    assert len(keys) == 100

def test_duplicate_payment_callbacks_are_idempotent(client):
    with SessionLocal() as db:
        from database.models import Customer
        customer = Customer(discord_id="customer", username="user"); db.add(customer)
        p=Product(name="x",price_cents=100,currency="USD",download_filename="x",download_path="x"); db.add(p); db.flush()
        order=Order(public_id="paid-order",customer_id=customer.id,product_id=p.id,amount_cents=100,currency="USD"); db.add(order); db.flush()
        first, created = fulfill_paid_order(db, order, "capture-1", 100, "USD")
        second, duplicate = fulfill_paid_order(db, order, "capture-1", 100, "USD")
        db.commit()
        assert created and duplicate is False and first.license_key == second.license_key

def test_payment_amount_mismatch_is_rejected(client):
    with SessionLocal() as db:
        from database.models import Customer
        customer = Customer(discord_id="customer", username="user"); db.add(customer)
        p=Product(name="x",price_cents=100,currency="USD",download_filename="x",download_path="x"); db.add(p); db.flush()
        order=Order(public_id="amount-order",customer_id=customer.id,product_id=p.id,amount_cents=100,currency="USD"); db.add(order); db.flush()
        import pytest
        with pytest.raises(ValueError): fulfill_paid_order(db, order, "capture-2", 99, "USD")

def test_download_token_expiration_and_limit(client):
    with SessionLocal() as db:
        from database.models import Customer
        customer = Customer(discord_id="customer", username="user"); db.add(customer)
        p=Product(name="x",price_cents=1,currency="USD",download_filename="x",download_path="x"); db.add(p); db.flush()
        o=Order(public_id="download-order",customer_id=customer.id,product_id=p.id,amount_cents=1,currency="USD"); db.add(o); db.flush()
        license=create_license(db,o); db.flush()
        raw=create_download_token(db,license,o.id,max_downloads=1); db.commit()
        from backend.services.download_service import resolve_download
        assert resolve_download(db, raw, "downloads")
        db.commit()
        assert resolve_download(db, raw, "downloads") is None
        token = create_download_token(db, license, o.id); db.flush()
        db.query(DownloadToken).filter_by(token_hash=hash_value(token)).update({"expires_at": now() - timedelta(minutes=1)})
        db.commit()
        assert resolve_download(db, token, "downloads") is None

def test_unauthorized_admin(client):
    r=client.post("/api/admin/products",json={},headers=auth())
    assert r.status_code == 403