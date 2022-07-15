from __future__ import print_function
from googleapiclient.discovery import build
from google.oauth2 import credentials, service_account
import configparser
import os
import csv

config = configparser.ConfigParser()
config.read('config')

customer_id = config['google']['customer_id']
admin_account = config['google']['admin_account'] 
cred_file_path = config['google']['cred_file_path']
result_path = config['google']['result_path']

USER_SCOPES = ['https://www.googleapis.com/auth/admin.directory.user.readonly']
DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive.metadata.readonly"]
 
credentials = service_account.Credentials.from_service_account_file(cred_file_path, scopes=USER_SCOPES)
delegated_creds = credentials.with_subject(admin_account)

user_service = build('admin', 'directory_v1', credentials=delegated_creds)

user_results = user_service.users().list(customer=customer_id, maxResults=500, orderBy='email').execute()
users = user_results.get('users', [])
nextPageToken = user_results.get('nextPageToken')

user_list = []
while nextPageToken:
    user_results = user_service.users().list(customer=customer_id, maxResults=500, pageToken=nextPageToken, orderBy='email').execute()
    users.extend(user_results.get('users', []))
    nextPageToken = user_results.get('nextPageToken')

if not users:
    print('No users in the domain.')
else:
    print('Users:')

for user in users:
    user_list.append(user['primaryEmail'])

credentials = service_account.Credentials.from_service_account_file(cred_file_path, scopes=DRIVE_SCOPES)

csv_columns = ['delegated_email', 'name', 'id', 'mimeType', 'webViewLink', 'owners', 'createdTime', 'ownedByMe', 'teamDriveId', \
 'driveId', 'lastModifyingUser']
with open(result_path, 'a') as f:
            wr = csv.DictWriter(f, fieldnames=csv_columns)
            wr.writeheader()

#query = "visibility='anyoneWithLink' or visibility='anyoneCanFind'"
#query = "visibility='anyoneCanFind'"
query = "visibility='anyoneWithLink'"

for i in user_list:
    print(i)
    delegated_creds = credentials.with_subject(str(i))
    drive_service = build('drive', 'v3', credentials = delegated_creds)
    drive_results = drive_service.files().list(q=query, orderBy = 'name', \
     pageSize = 1000, supportsAllDrives=True, includeItemsFromAllDrives=True, corpora= 'allDrives').execute()
    drive_items = drive_results.get('files', [])
    nextPageToken = drive_results.get('nextPageToken')
    while nextPageToken:
        drive_results = drive_service.files().list(q=query, orderBy = 'name', pageSize = 1000, \
         pageToken=nextPageToken, supportsAllDrives=True, includeItemsFromAllDrives=True, corpora= 'allDrives').execute()        
        drive_items.extend(drive_results.get('files', []))
        nextPageToken = drive_results.get('nextPageToken')
    for file in drive_items:
        data = drive_service.files().get(fileId=str(file['id']), \
         fields='name,id,mimeType,webViewLink,owners,createdTime,ownedByMe,teamDriveId,driveId,lastModifyingUser', \
          supportsAllDrives=True, supportsTeamDrives=True).execute()
        data['delegated_email'] = i
        with open(result_path, 'a') as f:
            wr = csv.DictWriter(f, fieldnames=csv_columns)
            wr.writerow(data)
