# from google_auth_oauthlib.flow import InstalledAppFlow
# import json

# SCOPES = ["https://www.googleapis.com/auth/drive.file"]

# flow = InstalledAppFlow.from_client_secrets_file(
#     "client_secret_900109888764-oqp6elf8uid129g9rc5tpn0a35i9a4uf.apps.googleusercontent.com.json", SCOPES
# )
# creds = flow.run_local_server(port=8000)  # opens a browser to sign in

# # save the credentials
# with open("token.json", "w") as token:
#     token.write(creds.to_json())

# print("Paste this into Django admin Creds json field:")
# print(creds.to_json())


# Run this file to create a refresh token, then use that refresh token in a .env file
# Refresh token lives for a long time, unused gets deleted after 6 months