# Repoman

Repoman is a tool designed to manage GitHub repositories. It provides functionalities such as creating repositories, enabling vulnerability alerts, automated fixes, branch protection, and creating environments.

It also offers a backup client that allows using the Organization Migrations API to backup a GitHub organization to an Azure Storage Container.

## Prerequisites

- Python3
- A GitHub token with the necessary permissions
- An Azure Storage Account for the backup client

## Usage

1. Clone the repository:
```bash
git clone https://github.com/O3-Cyber/Repoman.git
```
2. Navigate to the project directory:
```bash
cd repoman
```
3. Install the required dependencies:
```bash
pip install -r requirements.txt
```
4. Set the environment variables:
```bash
export GITHUB_TOKEN=your-github-token
export ORG_OR_USER=your-org-or-user
export AZURE_STORAGE_ACCOUNT_NAME=your-azure-storage-account-name
export AZURE_STORAGE_CONTAINER_NAME=your-azure-storage-container-name
```


## Examples
### Creating a Repository

```python
from package.repoclient import GithubRepoClient

# Instantiate the client
client = GithubRepoClient('your-github-token')

# Create a repository
client.create_repos('your-org-or-user', [{'repo_name': 'name-of-repository'}])
```

### Creating a Team
```python
from package.teamclient import GithubTeamClient

# Instantiate the client
client = GithubTeamClient('your-github-token')

team_data = {
    'team_name': 'example-team',
    'description': 'This is a description for example-team',
    'permission': 'push'
}
client.create_team('your-org', team_data)
```

### Assocating a Team with an IDP Group 

```python
teams_data = [
    {
        'team_name': 'team1',
        'idp_group_name': 'idp_group1'
    },
    {
        'team_name': 'team2',
        'idp_group_name': 'idp_group2'
    }
]

# Associate teams
client.associate_teams_idp(os.environ['ORG_OR_USER'], teams_data)
```

### Adding Secrets to a Repository

```python
from package.secretsclient import GithubSecretsClient

# Instantiate the client
client = GithubSecretsClient('your_github_token', 'org_or_user')

# Add a secret to a repository
client.add_secrets('repo_name', 'secret_name', 'secret_value')
```

### Backing up a GitHub Organization

```python
import os
import logging
from package.backupclient import GithubBackupClientAzure
from package.repoclient import GithubRepoClient
from package.secretsclient import GithubSecretsClient
from package.teamclient import GithubTeamClient
from package.utils import load_env_vars

# Configure logging
logging.basicConfig(level=logging.INFO)

def load_env_vars(var_names):
    return {var: os.getenv(var) for var in var_names}

def main():
    env_vars = load_env_vars([
        'GITHUB_TOKEN',
        'ORG_OR_USER',
        'AZURE_STORAGE_ACCOUNT_NAME',
        'AZURE_STORAGE_CONTAINER_NAME'
    ])
    missing_vars = [var for var, value in env_vars.items() if value is None]
    if missing_vars:
        error_message = f'Missing environment variables: {", ".join(missing_vars)}'
        logging.error(error_message)
        raise ValueError(error_message) 
    try:
        logging.info("Starting backup process...")
        backup = GithubBackupClientAzure(
            env_vars['GITHUB_TOKEN'], 
            env_vars['ORG_OR_USER'], 
            env_vars['AZURE_STORAGE_ACCOUNT_NAME'], 
            env_vars['AZURE_STORAGE_CONTAINER_NAME']
        )
        backup.create_gh_backup()
        logging.info("Backup process completed.")
    except Exception as e:
        logging.error(f"An error occurred while creating backups: {e}")
        return


if __name__ == "__main__":
    main()
```
### Creating a Repositories object

The first part of this section shows an array of objects, each representing a repository to be created. Each object can contain the following properties:

* `repo_name`: The name of the repository. (Required)
* `description`: A description of the repository.
* `environments`: An array of objects, each representing an environment to be created in the repository. Each environment object can contain the following properties:
* `environment_name`: The name of the environment.
* `protected_branches_only`: A boolean indicating whether the environment should only be available for protected branches.
* `branch_protection`: A boolean indicating whether branch protection should be enabled for the repository.
* `auto_init`: A boolean indicating whether the repository should be automatically initialized with a README.

```python
repositories = [
    {
        "repo_name": "company-project",
        "description": "This is a configuration repository",
        "repo_secrets": [
            {"secret_name": "SECRET1", "secret_value": "value1"},
            {"secret_name": "SECRET2", "secret_value": "value2"}
        ]
    },
    {
        "repo_name": "test-automation",
        "description": "This is a test automation repository",
        "environments": [
            {"environment_name": "production", "protected_branches_only": True}
        ]
    },
    {
        "repo_name": "no-init-no-branchprotection",
        "description": "This is a no init to branch protection repository",
        "branch_protection": False,
        "auto_init": False
    }
]
```

### Creating a Branch Protection Object

The second part of this section shows an example of a branch protection object. This object can contain the following properties:

* `required_status_checks`: An array of status checks that must pass before merging.
* `enforce_admins`: A boolean indicating whether the protection rules should also apply to admins.
* `required_pull_request_reviews`: An object containing rules for pull request reviews.
* `restrictions`: An object specifying who can push to the protected branch.
* `required_linear_history`: A boolean indicating whether the repository should only allow linear commit histories.
* `allow_force_pushes`: A boolean indicating whether force pushes should be allowed on the protected branch.
* `allow_deletions`: A boolean indicating whether deletions of the protected branch should be allowed.
* `block_creations`: A boolean indicating whether new branches should be blocked from being created.
* `required_conversation_resolution`: A boolean indicating whether all conversations in a pull request must be resolved before merging.
* `lock_branch`: A boolean indicating whether the branch should be locked to prevent changes.
* `allow_fork_syncing`: A boolean indicating whether forks of the repository should be allowed to sync with the original repository.

These objects are used as input when calling the methods to create repositories and branch protection rules.

```python
branch_protection_payload = {
    "required_status_checks": None,
    "enforce_admins": True,
    "required_pull_request_reviews": {
        "dismissal_restrictions": {},
        "dismiss_stale_reviews": True,
        "require_code_owner_reviews": False,
        "required_approving_review_count": 1,
        "require_last_push_approval": True,
        "bypass_pull_request_allowances": {
            "users": [],
            "teams": []
        }
    },
    "restrictions": None,
    "required_linear_history": True,
    "allow_force_pushes": False,
    "allow_deletions": False,
    "block_creations": True,
    "required_conversation_resolution": True,
    "lock_branch": False,
    "allow_fork_syncing": False
}
```

### Creating Teams object
```python
teams_data = {
    "teams": [
        {
            "team_name": "developers",
            "description": "Developers team responsible for coding",
            "permission": "push",
            "groups": [
                {
                    "group_id": "<IDP Object ID>",
                    "group_name": "Developers",
                    "group_description": "This group comprises developers"
                }
            ],
            "repo_names": ["company-project"]
        },
        {
            "team_name": "testers",
            "description": "Quality assurance team for testing",
            "permission": "pull",
            "groups": [
                {
                    "group_id": "qa",
                    "group_name": "QA Team",
                    "group_description": "This group is responsible for quality assurance"
                }
            ],
            "repo_names": ["company-project", "test-automation"]
        }
    ]
}
```

## Environment Variables

The script uses the following environment variables:

- `GITHUB_TOKEN`: Your GitHub token.
- `ORG_OR_USER`: The name of the GitHub organization or user for which the script should perform actions.
- `AZURE_STORAGE_ACCOUNT_NAME`: The name of the Azure storage account where backups should be stored.
- `AZURE_STORAGE_CONTAINER_NAME`: The name of the Azure storage container where backups should be stored.

## Contributing

We warmly welcome contributions that aim to enhance the functionality, performance, and usability of this project. Whether you're fixing bugs, adding new features, improving documentation, or suggesting updates, your efforts are greatly appreciated.

Before contributing, please ensure you have a clear understanding of the project's structure and goals. Feel free to open an issue to discuss any major changes or enhancements you have in mind.

Thank you for considering contributing to our project!
