import requests
import os
import logging
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential
import time
from package.repoclient import GithubRepoClient
from .utils import get_headers

class GithubBackupClientAzure:
    """
    This class provides methods to backup GitHub repositories to Azure Blob Storage.

    Attributes:
        github_token (str): The GitHub token used for authentication.
        org_or_user (str): The name of the GitHub organization or user account.
        account_name (str): The name of the Azure storage account.
        container_name (str): The name of the Azure Blob Storage container.
        headers (dict): The headers used for GitHub API requests.
        github_client (GithubRepoClient): The client used for GitHub API requests.
    """

    def __init__(self, github_token, org_or_user, account_name, container_name):
        self.github_token = github_token
        self.org_or_user = org_or_user
        self.account_name = account_name
        self.container_name = container_name
        self.headers = self.get_headers()
        self.github_client = GithubRepoClient(github_token)
        """
        Initializes a new instance of the GithubBackupClientAzure class.

        Args:
            github_token (str): The GitHub token used for authentication.
            org_or_user (str): The name of the GitHub organization or user account.
            account_name (str): The name of the Azure storage account.
            container_name (str): The name of the Azure Blob Storage container.
        """
    def get_headers(self):
        """
        Returns the headers used for GitHub API requests.

        Returns:
            dict: A dictionary containing the headers.
        """
        return get_headers(self.github_token)

    def get_existing_repositories(self):
        """
        Returns a list of all existing repositories in the GitHub organization or user account.

        Returns:
            list: A list of repository names.
        """
        return self.github_client.get_existing_repositories(self.org_or_user)

    def download_migration_archive(self, migration_id):
        """
        Downloads the migration archive for a given migration ID.

        Args:
            migration_id (str): The ID of the migration.

        Returns:
            str: The file path of the downloaded migration archive. Returns None if the download failed.
        """
        base_url = f"https://api.github.com/orgs/{self.org_or_user}/migrations/{migration_id}/archive"
        headers = self.headers

        response = requests.get(base_url, headers=headers)
        if response.status_code == 200:
            file_path = f"migration_archive_{migration_id}.zip"
            with open(file_path, 'wb') as f:
                f.write(response.content)
            logging.info(f"Migration archive downloaded and saved to {file_path}")
            return file_path  # Return the file path
        else:
            logging.error(f"Failed to download migration archive. Status code: {response.status_code}")
            return None

    def upload_to_azure_blob_storage(self, file_path):
        """
        Uploads a file to Azure Blob Storage.

        Args:
            file_path (str): The path of the file to upload.
        """
        if not os.path.exists(file_path):
            logging.error(f"File '{file_path}' not found.")
            return

        credential = DefaultAzureCredential()

        # Create BlobServiceClient instance
        blob_service_client = BlobServiceClient(
            account_url=f"https://{self.account_name}.blob.core.windows.net",
            credential=credential
        )

        # Extract blob name from file path
        blob_name = file_path

        # Log container name and blob name for debugging
        logging.info(f"Container Name: {self.container_name}")
        logging.info(f"Blob Name: {blob_name}")

        # Get BlobClient instance
        blob_client = blob_service_client.get_blob_client(container=self.container_name, blob=blob_name)

        # Upload blob
        with open(file_path, "rb") as data:
            blob_client.upload_blob(data)

        logging.info("Migration archive uploaded to Azure Blob Storage.")

    def wait_and_upload(self, migration_id):
        """
        Waits for a migration to complete and then uploads the migration archive to Azure Blob Storage.

        Args:
            migration_id (str): The ID of the migration.
        """
        base_url = f"https://api.github.com/orgs/{self.org_or_user}/migrations/{migration_id}"
        headers = self.headers

        # Polling the migration status until it's completed
        while True:
            response = requests.get(base_url, headers=headers)
            if response.status_code == 200:
                status = response.json()["state"]
                if status == "exported":
                    file_path = self.download_migration_archive(migration_id)
                    if file_path:
                        self.upload_to_azure_blob_storage(file_path)
                    break
                elif status == "failed":
                    logging.error("Migration failed.")
                    break
                else:
                    logging.info(f"Migration status: {status}. Waiting...")
                    time.sleep(5) 
            else:
                logging.error(f"Failed to check migration status. Status code: {response.status_code}")
                break

    def create_gh_backup(self):
        """
        Triggers an Organization Migration job to backup all repositories in the GitHub organization and its configuration before uploading it to Azure Blob Storage.
        """
        existing_repositories = GithubRepoClient.get_existing_repositories(self, self.org_or_user)


        base_url = f"https://api.github.com/orgs/{self.org_or_user}/migrations"
        headers = self.headers
        payload = {
            "repositories": existing_repositories,
            "lock_repositories": False
        }

        # Make a POST request to start the migration
        response = requests.post(base_url, headers=headers, json=payload)

        if response.status_code == 201:
            logging.info("Migration started successfully.")
            migration_id = response.json()["id"]
            self.wait_and_upload(migration_id)
        else:
            logging.error("Failed to start migration. Response: %s", response.text)