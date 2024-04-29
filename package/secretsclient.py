import requests
import os
import json
from base64 import b64encode
from nacl import encoding, public
import logging
from .utils import get_headers

logging.basicConfig(level=logging.INFO)

class GithubSecretsClient:
    def __init__(self, github_token, org_or_user):
        """
        The constructor for the GithubSecretsClient class.

        Parameters:
        github_token (str): The GitHub token used for authentication.
        org_or_user (str): The name of the GitHub organization or user that owns the repositories.
        """
        self.github_token = github_token
        self.org_or_user = org_or_user
        self.headers = self.get_headers()

    def get_headers(self):
        return get_headers(self.github_token)


    def get_repository_details(self, repo_name):
        """
        Get the details of a repository. Used to retrieve the public key.

        Parameters:
        repo_name (str): The name of the repository.

        Returns:
        int: The ID of the repository.

        Raises:
        ValueError: If the repository details cannot be retrieved.
        """
        base_url = f"https://api.github.com/repos/{self.org_or_user}/{repo_name}"
        response = requests.get(base_url, headers=self.headers)
        if response.status_code == 200:
            repository_data = json.loads(response.content)
            return repository_data["id"]
        else:
            raise ValueError(f"Failed to get repository details for repository '{repo_name}'. Status code: {response.status_code}")

    def get_public_key(self, url):
        """
        Get the public key for a repository or environment to use for encryption.

        Parameters:
        url (str): The URL to get the public key from.

        Returns:
        dict: The public key data.

        Raises:
        ValueError: If the public key cannot be retrieved.
        """
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise ValueError(f"Failed to get public key from '{url}'. Status code: {response.status_code}")

    def encrypt(self, public_key: str, secret_value: str) -> str:
        """
        Encrypt a Unicode string using the public key.

        Parameters:
        public_key (str): The public key to use for encryption.
        secret_value (str): The secret value to encrypt.


        """
        public_key = public.PublicKey(public_key.encode("utf-8"), encoding.Base64Encoder())
        sealed_box = public.SealedBox(public_key)
        encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
        return b64encode(encrypted).decode("utf-8")

    def add_secrets(self, repo_name, secret_name, secret_value, environment_name=None):
        """
        Add a secret to a repository or environment.

        Parameters:
        repo_name (str): The name of the repository.
        secret_name (str): The name of the secret.
        secret_value (str): The value of the secret.
        environment_name (str, optional): The name of the environment. Defaults to None.
        """
        if environment_name:
            url = f"https://api.github.com/repos/{self.org_or_user}/{repo_name}/environments/{environment_name}/secrets/{secret_name}"
            public_key_data = self.get_public_key(f"https://api.github.com/repositories/{self.get_repository_details(repo_name)}/environments/{environment_name}/secrets/public-key")
        else:
            url = f"https://api.github.com/repos/{self.org_or_user}/{repo_name}/actions/secrets/{secret_name}"
            public_key_data = self.get_public_key(f"https://api.github.com/repos/{self.org_or_user}/{repo_name}/actions/secrets/public-key")
        
        public_key = public_key_data.get('key')
        public_key_id = public_key_data.get("key_id") 
        encrypted_value = self.encrypt(public_key, secret_value)
        encrypted_secret = {
            "encrypted_value": encrypted_value,
            "key_id": str(public_key_id),
        }
        
        response = requests.put(url, headers=self.headers, json=encrypted_secret)
        if response.status_code in [204, 201]:
            if environment_name:
                logging.info(f"Secret '{secret_name}' added to environment '{environment_name}' successfully.")
            else:
                logging.info(f"Secret '{secret_name}' added to repository '{repo_name}' successfully.")
        else:
            if environment_name:
                logging.error(f"Failed to add secret '{secret_name}' to environment '{environment_name}'. Status code: {response.status_code}")
            else:
                logging.error(f"Failed to add secret '{secret_name}' to repository '{repo_name}'. Status code: {response.status_code}")
            logging.error(response.text)


    def add_secrets_to_repos(self, repositories):
        """
        Add secrets to repositories.

        Parameters:
        repositories (list): A list of dictionaries, where each dictionary represents a repository and contains the keys "repo_name" and "repo_secrets". The value of "repo_secrets" is a list of dictionaries, where each dictionary represents a secret and contains the keys "secret_name" and "secret_value".
        """
        for repo in repositories:
            repo_name = repo.get("repo_name")
            repo_secrets = repo.get("repo_secrets", [])
            for secret in repo_secrets:
                secret_name = secret.get("secret_name")
                secret_value = secret.get("secret_value")
                self.add_secrets(repo_name, secret_name, secret_value)

    def add_secrets_to_envs(self, repositories):
        """
        Add secrets to the environments of repositories.

        Parameters:
        repositories (list): A list of dictionaries, where each dictionary represents a repository and contains the keys "repo_name" and "environments". The value of "environments" is a list of dictionaries, where each dictionary represents an environment and contains the keys "environment_name" and "secrets". The value of "secrets" is a list of dictionaries, where each dictionary represents a secret and contains the keys "secret_name" and "secret_value".
        """
        for repo in repositories:
            repo_name = repo.get("repo_name")
            repository_id = self.get_repository_details(repo_name)
            environments = repo.get("environments", [])
            
            for environment in environments:
                environment_name = environment["environment_name"]
                secrets = environment.get("secrets", [])
                for secret in secrets:
                    secret_name = secret.get("secret_name")
                    secret_value = secret.get("secret_value")
                    self.add_secrets(repo_name,  secret_name, secret_value, environment_name)