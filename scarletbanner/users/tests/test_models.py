from scarletbanner.users.models import User


def test_user_get_absolute_url(user: User):
    assert user.get_absolute_url() == f"/users/{user.username}/"


def test_to_dict(user: User):
    actual = user.get_dict()
    assert actual["username"] == user.username
    assert actual["email"] == user.email
    assert actual["name"] == user.name
