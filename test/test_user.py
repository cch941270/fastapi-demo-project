import pytest

def new_user_data():
    return {"username": "user1", "password": "user1pw", "confirm_password": "user1pw"}

def user_data():
    return {"username": "testuser", "password": "testuserpw", "confirm_password": "testuserpw"}

@pytest.mark.asyncio
async def test_create_user(async_client):
    data = new_user_data()
    response = await async_client.post("/user/create/", data=data)
    assert response.status_code == 200
    assert response.json() == {"message": "New user created"}

@pytest.mark.asyncio
async def test_create_user_wrong_password(async_client):
    data = new_user_data()
    data.update({"confirm_password": "user2pw"})
    response = await async_client.post("/user/create/", data=data)
    assert response.status_code == 422
    assert response.json() == {"detail": "Two passwords are not the same"}

@pytest.mark.asyncio
async def test_create_user_duplicate_username(async_client):
    data = user_data()
    response = await async_client.post("/user/create/", data=data)
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_login_for_access_token(async_client):
    data = user_data()
    del data["confirm_password"]
    response = await async_client.post("/token/", data=data)
    token = response.json().get("access_token")
    assert response.status_code == 200
    assert token is not None
