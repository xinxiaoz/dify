# -*- coding:utf-8 -*-
import uuid
from controllers.web import api
from flask_restful import Resource
from flask import current_app, request
from werkzeug.exceptions import Unauthorized, NotFound
from models.model import Site, EndUser, App
from extensions.ext_database import db
from libs.passport import PassportService

class PassportResource(Resource):
    """Base resource for passport."""
    def get(self):
        app_id = request.headers.get('X-Site-Code')
        if app_id is None:
            raise Unauthorized('X-Site-Code header is missing.')

        sk = current_app.config.get('SECRET_KEY')
        # get site from db and check if it is normal
        site = db.session.query(Site).filter(
            Site.code == app_id,
            Site.status == 'normal'
        ).first()
        if not site:
            raise NotFound()
        # get app from db and check if it is normal and enable_site
        app_model = db.session.query(App).filter(App.id == site.app_id).first()
        if not app_model or app_model.status != 'normal' or not app_model.enable_site:
            raise NotFound()
        
        end_user = EndUser(
            tenant_id=app_model.tenant_id,
            app_id=app_model.id,
            type='browser',
            is_anonymous=True,
            session_id=generate_session_id(),
        )
        db.session.add(end_user)
        db.session.commit()

        payload = {
            "iss": site.app_id,
            'sub': 'Web API Passport',
            "aud": end_user.id,
            'app_id': site.app_id,
            'end_user_id': end_user.id,
        }

        tk = PassportService(sk, payload).get_token()
        
        return {
            'access_token': tk,
        }

api.add_resource(PassportResource, '/passport')

def generate_session_id():
    """
    Generate a unique session ID.
    """
    while True:
        session_id = str(uuid.uuid4())
        existing_count = db.session.query(EndUser) \
            .filter(EndUser.session_id == session_id).count()
        if existing_count == 0:
            return session_id
