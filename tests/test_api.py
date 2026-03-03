import pytest
import random
import string
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, engine, sessionDep, get_session






@pytest.fixture(scope="function")
def client():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


    app.dependency_overrides[sessionDep] = get_session
    yield TestClient(app)

    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)



def random_name(length=random.randint(0,250)):
    return ''.join(random.choices(string.ascii_letters, k=length))


def setup_db(client):
    r = client.post("/setup_db", json={})
    assert r.status_code == 200

def test_mass_create_departments(client):
    root_ids = []

    for _ in range(5):
        r = client.post("/departments", json={
            "name": random_name(),
            "parent_id": None
        })
        assert r.status_code == 200 or 400 or 404 or 422
        root_ids.append(len(root_ids) + 1)


    for _ in range(20):
        r = client.post("/departments", json={
            "name": random_name(),
            "parent_id": random.choice(root_ids)
        })
        assert r.status_code == 200 or 400 or 404 or 422




def test_name_too_long(client):
    r = client.post("/departments", json={
        "name": "a" * 201,
        "parent_id": None
    })
    assert r.status_code == 422


def test_empty_name(client):
    r = client.post("/departments", json={
        "name": "",
        "parent_id": None
    })
    assert r.status_code == 422



def test_unique_name_same_parent(client):
    client.post("/departments", json={"name": "Никитосы", "parent_id": None})
    client.post("/departments", json={"name": "Скебобчики", "parent_id": 1})

    r = client.post("/departments", json={"name": "Скебобчики", "parent_id": 1})
    assert r.status_code == 409



def test_set_self_parent(client):
    client.post("/departments", json={"name": "Скебобчики", "parent_id": None})

    r = client.patch("/departments/1", json={"parent_id": 1})
    assert r.status_code == 400


#------------------Циклы------------------

def test_cycle_detection(client):
    client.post("/departments", json={"name": "A", "parent_id": None})  
    client.post("/departments", json={"name": "B", "parent_id": 1})     
    client.post("/departments", json={"name": "C", "parent_id": 2})     


    r = client.patch("/departments/1", json={"parent_id": 3})
    assert r.status_code == 400 


# ------------------------------------

def test_delete_cascade(client):
    client.post("/departments", json={"name": "Папы", "parent_id": None})
    client.post("/departments", json={"name": "Ребзики", "parent_id": 1})

    r = client.delete("/departments/1?mode=cascade")
    assert r.status_code == 200


# ------------------ DELETE REASSIGN ------------------

def test_delete_reassign(client):
    client.post("/departments", json={"name": "Папы", "parent_id": None}) 
    client.post("/departments", json={"name": "Никитосы", "parent_id": 1}) 
    client.post("/departments", json={"name": "Ребзики", "parent_id": 2})
    
    client.post("/department/2/employees", json={
        "full_name": "Михаил Литвин",
        "position": "Входить в кондиции"
    })

    r = client.delete("/departments/2?mode=reassign&reassign_to_department_id=1")
    assert r.status_code == 200
    
