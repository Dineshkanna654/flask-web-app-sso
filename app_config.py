import os


if (os.getenv('B2C_TENANT_NAME')
    and os.getenv('SIGNUPSIGNIN_USER_FLOW') and os.getenv('EDITPROFILE_USER_FLOW')):
    b2c_tenant = os.getenv('B2C_TENANT_NAME')
    authority_template = "https://{tenant}.b2clogin.com/{tenant}.onmicrosoft.com/{user_flow}"
    AUTHORITY = authority_template.format(
        tenant=b2c_tenant,
        user_flow=os.getenv('SIGNUPSIGNIN_USER_FLOW'))
    B2C_PROFILE_AUTHORITY = authority_template.format(
        tenant=b2c_tenant,
        user_flow=os.getenv('EDITPROFILE_USER_FLOW'))
    B2C_RESET_PASSWORD_AUTHORITY = authority_template.format(
        tenant=b2c_tenant,
        user_flow=os.getenv('RESETPASSWORD_USER_FLOW'))
else:  
    AUTHORITY = os.getenv("AUTHORITY") or "https://login.microsoftonline.com/common"

# Application (client) ID of app registration
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

REDIRECT_PATH = "/getAToken"  
ENDPOINT = 'https://graph.microsoft.com/v1.0/me' 

SCOPE = ["User.Read"]

SESSION_TYPE = "filesystem"