import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

# Import general libraries
import uuid
import os
from typing import Dict

from nicegui import app, ui
import pandas as pd
pd.options.mode.chained_assignment = None

# Import fastapi-related libraries
from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth

oauth = OAuth()
oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
    authorize_state=os.getenv('SECRET_KEY')
)

app.add_middleware(SessionMiddleware, secret_key=os.getenv('NICEGUI_SECRET_KEY'))
session_info: Dict[str, Dict] = {}

@app.get("/login/google")
async def login_via_google(request: Request):
    # Build the redirect URI for OAuth callback.
    # (Ensure https is used in production)
    redirect_uri = str(request.url_for('auth_via_google')).replace('http://', 'https://')
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get("/auth/google")
async def auth_via_google(request: Request):
    token = await oauth.google.authorize_access_token(request)
    user_info = token['userinfo']

    # Replace this check with your actual authorization logic.
    if user_info['email'] not in os.getenv('GOOGLE_EMAIL'):
        return RedirectResponse('/not_authorized')
    
    # Mark the session as authenticated.
    request.session['id'] = str(uuid.uuid4())
    session_info[request.session['id']] = {'email': user_info['email'], 'authenticated': True}
    
    # Retrieve the originally requested page, default to '/' if not provided.
    next_page = request.session.pop('next', '/')
    return RedirectResponse(next_page)

def is_authenticated(request: Request) -> bool:
    return session_info.get(request.session.get('id'), {}).get('authenticated', False)

@ui.page('/login')
def login(request: Request) -> None:
    # Retrieve the 'next' parameter from the query parameters; default to root if missing.
    next_page = request.query_params.get('next', '/')
    
    if is_authenticated(request):
        # If already authenticated, send the user to the desired page.
        return RedirectResponse(next_page)
    
    # Store the target page in session for after login.
    request.session['next'] = next_page
    return RedirectResponse('/login/google')

@ui.page('/logout')
def logout(request: Request) -> None:
    if is_authenticated(request):
        session_info.pop(request.session['id'])
        request.session['id'] = None
        return RedirectResponse('/login')
    return RedirectResponse('/')

@ui.page('/not_authorized')
def not_authorized_page(request: Request) -> None:
    with ui.card().classes('absolute-center'):
        ui.label('You are not authorized to access this application. Please contact the administrator.')