import os

def load_env_vars():
    """
    Load required environment variables into a dictionary.
    """
    env_vars = ['GITHUB_TOKEN', 'ORG_OR_USER', 'AZURE_STORAGE_ACCOUNT_NAME', 'AZURE_STORAGE_CONTAINER_NAME', 'AZURE_TENANT_ID', 'AZURE_CLIENT_ID', 'AZURE_CLIENT_SECRET']
    return {var: os.environ.get(var) for var in env_vars}

def get_headers(github_token):
    github_token = os.environ.get('GITHUB_TOKEN')
    return {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }