import os
import uuid
import time
from datetime import datetime
from dateutil import parser
from flask import request, current_app, abort
from flask_restplus import Api, Resource, Namespace, fields
from flask_jwt import _jwt_required, JWTError, current_identity

from .. import db
from ..model import Post


api = Namespace('blog', description='Blog service')


post_model = api.model('Post', {
        'id': fields.Integer(description='Post id'),
        'username': fields.String(description='Username'),
        'trip_id': fields.Integer(description='Trip id'),
        'created_at': fields.DateTime(description='Time of creation'),
        'lon': fields.Float(description='Longitude'),
        'lat': fields.Float(description='Latitude'),
        'location': fields.String(description='Geocoded location'),
        'title': fields.String(description='Post title'),
        'content': fields.String(description='Post content'),
    })


paginated = api.model('Response', {
        'posts': fields.List(fields.Nested(post_model)),
        'total': fields.Integer(description='number of results')
    })


def belongs_to(username):
    try:
        _jwt_required(None)
        if not current_identity['username'] == username:
            return {'status': 403, 'message': 'not allowed'}, 403
    except JWTError as e:
        return {'status': 403, 'message': 'not allowed'}, 403

    return True


@api.route('/status')
class Status(Resource):
    def get(self, **kwargs):
        return {'status': 200,
                'version': '1.0'}, 200


@api.route('/<string:username>')
@api.doc(params={'username': 'username'})
class PostsByUser(Resource):
    @api.doc(responses={200: 'found posts', 404: 'no posts found'})
    @api.marshal_with(paginated)
    def get(self, username):
        """
        List posts for a given user
        """
        now = datetime.utcnow().isoformat()
        before = request.args.get('before', now, type=str)
        before_dt = parser.parse(before)
        size = min(request.args.get('size', 10, type=int), 1000)

        q = (Post.query.filter_by(username=username)
                       .filter(Post.created_at < before_dt)
                       .order_by(Post.created_at.desc()))
        total = q.count()
        if total == 0:
            abort(404, 'no posts found for this user')
        posts = q.limit(size)
        return {'posts': posts, 'total': total}, 200


@api.route('/<string:username>/<int:trip_id>')
@api.doc(params={'username': 'username', 'trip_id': 'numeric trip id'})
class PostByTrip(Resource):
    @api.doc(responses={400: 'missing fields', 201: 'post created'})
    def post(self, username, trip_id):
        """
        Create a post
        """
        # check the trip belongs to the authenticated user
        allowed = belongs_to(username)
        if allowed is not True:
            return allowed

        # check for required fields
        missing = []
        fields = {}
        for v in ['title', 'content']:
            fields[v] = request.json.get(v)
            if fields[v] is None:
                missing.append(v)
        if missing:
            return{'missing': missing, 'message': 'missing fields'}, 400
        post = Post(username=username,
                    trip_id=trip_id,
                    title=fields['title'],
                    content=fields['content'])
        db.session.add(post)
        db.session.commit()

        return {'post': post.to_json()}, 201

    @api.doc(responses={200: 'found posts', 404: 'no posts found'})
    @api.marshal_with(paginated)
    def get(self, username, trip_id):
        """
        List posts for a given trip
        """
        now = datetime.utcnow().isoformat()
        before = request.args.get('before', now, type=str)
        before_dt = parser.parse(before)
        size = min(request.args.get('size', 10, type=int), 1000)

        q = (Post.query.filter_by(username=username)
                       .filter_by(trip_id=trip_id)
                       .filter(Post.created_at < before_dt)
                       .order_by(Post.created_at.desc()))
        total = q.count()
        if total == 0:
            abort(404, 'no posts found for this user and trip')
        posts = q.limit(size)
        return {'posts': posts, 'total': total}, 200


@api.route('/<string:username>/<int:trip_id>/<int:id>')
@api.doc(params={'username': 'username',
                 'trip_id': 'numeric trip id',
                 'id': 'the post id'})
class PostById(Resource):

    @api.doc(responses={403: 'not allowed', 200: 'post deleted'})
    def delete(self, username, trip_id, id):
        """
        Delete a post
        """
        # check the trip belongs to the authenticated user
        allowed = belongs_to(username)
        if allowed is not True:
            return allowed
        post = Post.query.get(id)
        db.session.delete(post)
        db.session.commit()
