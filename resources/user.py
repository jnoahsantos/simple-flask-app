from flask_restful import Resource, reqparse
from sqlalchemy import Identity
from models.user import UserModel
from blacklist import BLACKLIST
from hmac import compare_digest
from flask_jwt_extended import (
    create_access_token, 
    create_refresh_token, 
    jwt_refresh_token_required,
    get_jwt_identity,
    jwt_required,
    get_raw_jwt
    )

BLANK_ERROR = "'{}' cannot be left blank!"
NAME_ALREADY_EXISTS = "An item with name '{}' already exists."
ERROR_INSERTING = "An error occurred inserting the item."
USER_DELETED = "User deleted."
USER_NOT_FOUND = "User not found"
INVALID_CREDENTIALS = "Invalid credentials"
USER_LOGGED_OUT = "User <id={user_id}}> successfully logged out"

_user_parser = reqparse.RequestParser()
_user_parser.add_argument('username',
                            type=str,
                            required=True,
                            help=BLANK_ERROR.format("username")
                            )
_user_parser.add_argument('password',
                            type=str,
                            required=True,
                            help=BLANK_ERROR.format("password")
                            )



class UserRegister(Resource):
    @classmethod
    def post(cls):
        data = _user_parser.parser.parse_args()

        if UserModel.find_by_username(data['username']):
            return {"message": "A user with that username already exists"}, 400

        user = UserModel(**data)
        user.save_to_db()

        return {"message": "User created successfully."}, 201


class User(Resource):
    """
    This resource can be useful when testing our Flask app. We may not want to expose it to public users, but for the
    sake of demonstration in this course, it can be useful when we are manipulating data regarding the users.
    """
    @classmethod
    def get(cls, user_id: int):
        user = UserModel.find_by_id(user_id)
        if not user:
            return {'message': USER_NOT_FOUND}, 404
        return user.json(), 200

    @classmethod
    def delete(cls, user_id: int):
        user = UserModel.find_by_id(user_id)
        if not user:
            return {'message': USER_NOT_FOUND}, 404
        user.delete_from_db()
        return {'message': USER_DELETED}, 200

class UserLogin(Resource):
    @classmethod
    def post(cls):
        data = _user_parser.parser.parse_args()

        user = UserModel.find_by_username(data['username'])

        # This is what authenticate() function used to do
        if user and compare_digest(user.password, data['password']):
            # identity = is what identity() function used to do
            access_token = create_access_token(identity=user.id, fresh=True)
            refresh_token = create_refresh_token(user.id)
            return {
                'access_token': access_token,
                'refresh_token': refresh_token
            }, 200

        return {'message', INVALID_CREDENTIALS}, 401

class UserLogout(Resource):
    @classmethod
    @jwt_required
    def post(cls):
        jti = get_raw_jwt()['jti'] # jti is "JWT ID", a unique identifier for a JWT
        user_id = get_jwt_identity()
        BLACKLIST.add(jti)
        return {'message': USER_LOGGED_OUT.format(user_id)}, 200

class TokenRefresh(Resource):
    @classmethod
    @jwt_refresh_token_required
    def post(cls):
        current_user = get_jwt_identity()
        new_token = create_access_token(identity=current_user, freah=False)
        return {'access_token': new_token}, 200
