from flask_restplus import Api
from .post import api as post_ns

api = Api(
    title='Blog',
    version='1.0',
    description='Blog service',
    contact='Dan Kolbman',
    cantact_url='dankolbman.com',
    contact_email='dan@kolbman.com'
)

api.add_namespace(post_ns)
