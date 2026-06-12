"""
OAuth authentication endpoints for Google and GitHub
Implements social login with account linking
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from authlib.integrations.starlette_client import OAuth
import logging

from app.core.database import get_db
from app.core.config import settings
from app.models.user import User
from app.domains.auth.service import (
    get_or_create_oauth_user,
    link_oauth_identity,
    oauth_callback_redirect_url,
    oauth_error_redirect_url,
    oauth_link_result_redirect_url,
    token_pair_for_user,
)
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize OAuth client
oauth = OAuth()

# Register Google OAuth
if settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET:
    oauth.register(
        name='google',
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile'
        }
    )

# Register GitHub OAuth
if settings.GITHUB_CLIENT_ID and settings.GITHUB_CLIENT_SECRET:
    oauth.register(
        name='github',
        client_id=settings.GITHUB_CLIENT_ID,
        client_secret=settings.GITHUB_CLIENT_SECRET,
        access_token_url='https://github.com/login/oauth/access_token',
        access_token_params=None,
        authorize_url='https://github.com/login/oauth/authorize',
        authorize_params=None,
        api_base_url='https://api.github.com/',
        client_kwargs={'scope': 'user:email'},
    )


@router.get("/oauth/{provider}")
async def oauth_login(provider: str, request: Request):
    """
    Initiate OAuth flow - redirects user to provider's login page

    Supported providers: google, github
    """
    if provider not in ['google', 'github']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported OAuth provider: {provider}"
        )

    # Check if provider is configured
    if provider == 'google' and not (settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth is not configured"
        )

    if provider == 'github' and not (settings.GITHUB_CLIENT_ID and settings.GITHUB_CLIENT_SECRET):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub OAuth is not configured"
        )

    # Build callback URL
    redirect_uri = request.url_for('oauth_callback', provider=provider)

    # Redirect to OAuth provider
    return await oauth.create_client(provider).authorize_redirect(request, redirect_uri)


@router.get("/oauth/{provider}/callback")
async def oauth_callback(
    provider: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    OAuth callback - handles the redirect from provider

    Returns: Redirects to frontend with tokens in URL
    """
    if provider not in ['google', 'github']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported OAuth provider: {provider}"
        )

    try:
        # Get access token from provider
        client = oauth.create_client(provider)
        token = await client.authorize_access_token(request)

        # Get user info from provider
        if provider == 'google':
            user_info = token.get('userinfo')
            if not user_info:
                # Fallback: fetch userinfo
                resp = await client.get('https://www.googleapis.com/oauth2/v1/userinfo')
                user_info = resp.json()

            oauth_id = user_info.get('sub') or user_info.get('id')
            email = user_info.get('email')
            full_name = user_info.get('name')

        elif provider == 'github':
            # GitHub requires separate API call for user info
            resp = await client.get('user')
            user_info = resp.json()

            oauth_id = str(user_info.get('id'))
            email = user_info.get('email')

            # If email is private, fetch from emails endpoint
            if not email:
                emails_resp = await client.get('user/emails')
                emails = emails_resp.json()
                # Get primary verified email
                for email_data in emails:
                    if email_data.get('primary') and email_data.get('verified'):
                        email = email_data.get('email')
                        break

            full_name = user_info.get('name') or user_info.get('login')

        # Validate required fields
        if not oauth_id or not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not retrieve user information from OAuth provider"
            )

        # Get or create user
        user = get_or_create_oauth_user(
            db=db,
            provider=provider,
            oauth_id=oauth_id,
            email=email,
            full_name=full_name
        )

        # Redirect to frontend with tokens
        # Frontend will extract tokens from URL and store them
        frontend_url = settings.ALLOWED_ORIGINS[0]  # Primary frontend URL
        redirect_url = oauth_callback_redirect_url(
            frontend_url=frontend_url,
            token_pair=token_pair_for_user(user),
        )

        return RedirectResponse(url=redirect_url)

    except Exception as e:
        # Log error and redirect to frontend with error
        logger.warning("OAuth callback failed for provider %s: %s", provider, e)
        frontend_url = settings.ALLOWED_ORIGINS[0]
        error_url = oauth_error_redirect_url(frontend_url=frontend_url, provider=provider)
        return RedirectResponse(url=error_url)


@router.post("/oauth/link/{provider}")
async def link_oauth_account(
    provider: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Link OAuth provider to existing authenticated account
    Requires user to be logged in
    """
    if provider not in ['google', 'github']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported OAuth provider: {provider}"
        )

    # Check if already linked
    if current_user.oauth_provider == provider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Account already linked to {provider}"
        )

    # Similar OAuth flow but for linking
    redirect_uri = request.url_for('link_oauth_callback', provider=provider)
    return await oauth.create_client(provider).authorize_redirect(request, redirect_uri)


@router.get("/oauth/link/{provider}/callback")
async def link_oauth_callback(
    provider: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Callback for linking OAuth account to existing user
    """
    # Similar to oauth_callback but updates existing user
    try:
        client = oauth.create_client(provider)
        token = await client.authorize_access_token(request)

        # Get OAuth ID
        if provider == 'google':
            user_info = token.get('userinfo') or (await client.get('https://www.googleapis.com/oauth2/v1/userinfo')).json()
            oauth_id = user_info.get('sub') or user_info.get('id')
        elif provider == 'github':
            user_info = (await client.get('user')).json()
            oauth_id = str(user_info.get('id'))

        link_oauth_identity(
            db,
            user=current_user,
            provider=provider,
            oauth_id=oauth_id,
        )

        # Redirect to profile page with success
        frontend_url = settings.ALLOWED_ORIGINS[0]
        return RedirectResponse(url=oauth_link_result_redirect_url(
            frontend_url=frontend_url,
            success=True,
        ))

    except HTTPException:
        raise
    except Exception as e:
        logger.warning("OAuth link failed for provider %s: %s", provider, e)
        frontend_url = settings.ALLOWED_ORIGINS[0]
        return RedirectResponse(url=oauth_link_result_redirect_url(
            frontend_url=frontend_url,
            success=False,
        ))
