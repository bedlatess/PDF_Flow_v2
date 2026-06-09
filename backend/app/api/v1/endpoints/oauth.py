"""
OAuth authentication endpoints for Google and GitHub
Implements social login with account linking
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from authlib.integrations.starlette_client import OAuth
from datetime import datetime
import secrets

from app.core.database import get_db
from app.core.security import create_access_token, create_refresh_token, get_password_hash
from app.core.config import settings
from app.models.user import User, UserRole
from app.schemas.user import Token
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter()

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


def get_or_create_oauth_user(
    db: Session,
    provider: str,
    oauth_id: str,
    email: str,
    full_name: str = None
) -> User:
    """
    Get existing user by OAuth provider/id or create new one
    If email exists but not linked to OAuth, link it
    """
    # Try to find user by OAuth provider and ID
    user = db.query(User).filter(
        User.oauth_provider == provider,
        User.oauth_id == oauth_id
    ).first()

    if user:
        # Update last login
        user.last_login_at = datetime.utcnow()
        db.commit()
        return user

    # Check if email exists (user registered with email/password)
    user = db.query(User).filter(User.email == email).first()

    if user:
        # Link OAuth to existing account
        user.oauth_provider = provider
        user.oauth_id = oauth_id
        user.is_verified = True  # OAuth emails are pre-verified
        user.last_login_at = datetime.utcnow()
        db.commit()
        return user

    # Create new user with OAuth
    # Generate random password for OAuth users (they won't use it)
    random_password = secrets.token_urlsafe(32)

    new_user = User(
        email=email,
        hashed_password=get_password_hash(random_password),
        full_name=full_name,
        oauth_provider=provider,
        oauth_id=oauth_id,
        role=UserRole.FREE,
        is_active=True,
        is_verified=True,  # OAuth emails are pre-verified
        last_login_at=datetime.utcnow()
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


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

        # Create JWT tokens
        access_token = create_access_token(data={"sub": user.id})
        refresh_token = create_refresh_token(data={"sub": user.id})

        # Redirect to frontend with tokens
        # Frontend will extract tokens from URL and store them
        frontend_url = settings.ALLOWED_ORIGINS[0]  # Primary frontend URL
        redirect_url = f"{frontend_url}/auth/oauth-callback?access_token={access_token}&refresh_token={refresh_token}&token_type=bearer"

        return RedirectResponse(url=redirect_url)

    except Exception as e:
        # Log error and redirect to frontend with error
        print(f"OAuth error: {str(e)}")
        frontend_url = settings.ALLOWED_ORIGINS[0]
        error_url = f"{frontend_url}/auth/login?error=oauth_failed&provider={provider}"
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

        # Check if OAuth ID is already used by another user
        existing_oauth_user = db.query(User).filter(
            User.oauth_provider == provider,
            User.oauth_id == oauth_id,
            User.id != current_user.id
        ).first()

        if existing_oauth_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"This {provider} account is already linked to another user"
            )

        # Link to current user
        current_user.oauth_provider = provider
        current_user.oauth_id = oauth_id
        db.commit()

        # Redirect to profile page with success
        frontend_url = settings.ALLOWED_ORIGINS[0]
        return RedirectResponse(url=f"{frontend_url}/profile?oauth_linked=success")

    except HTTPException:
        raise
    except Exception as e:
        print(f"OAuth link error: {str(e)}")
        frontend_url = settings.ALLOWED_ORIGINS[0]
        return RedirectResponse(url=f"{frontend_url}/profile?oauth_linked=error")
