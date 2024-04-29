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
    """
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
    """
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

    try:
        logging.info("Starting repository creation process...")
        github_client = GithubRepoClient(env_vars['GITHUB_TOKEN'])
        github_client.create_repos(
            env_vars['ORG_OR_USER'],
            repositories,
            branch_protection_payload
        )
        logging.info("Repository creation process completed.")
    except Exception as e:
        logging.error(f"An error occurred while creating repositories: {e}")
        return

    try:
        logging.info("Starting environment creation process...")
        github_client.create_envs(
            env_vars['ORG_OR_USER'], 
            repositories
        )
        logging.info("Environment creation process completed.")
    except Exception as e:
        logging.error(f"An error occurred while creating environments: {e}")
        return

    try:
        logging.info("Starting secrets creation process...")
        secrets_client = GithubSecretsClient(env_vars['GITHUB_TOKEN'], env_vars['ORG_OR_USER'])
        secrets_client.add_secrets_to_repos(repositories)
        secrets_client.add_secrets_to_envs(repositories)
        logging.info("Secrets creation process completed.")
    except Exception as e:
        logging.error(f"An error occurred while creating secrets: {e}")
        return
    
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

    team_client = GithubTeamClient(env_vars['GITHUB_TOKEN'])
    try:
        logging.info("Starting team creation process...")
        team_client.create_teams(env_vars['ORG_OR_USER'], teams_data)
        logging.info("Team creation process completed.")
    except Exception as e:
        logging.error(f"An error occurred while creating teams: {e}")
        return

    # Requires Team-Synchronization to be configured.
    try:
        logging.info("Starting team association process...")
        team_client.associate_teams_idp(env_vars['ORG_OR_USER'], teams_data)
        logging.info("Team association process completed.")
    except Exception as e:
        logging.error(f"An error occurred while associating teams: {e}")

    try:
        logging.info("Starting repository to team addition process...")
        team_client.add_repos_to_teams(env_vars['ORG_OR_USER'], teams_data)
        logging.info("Repository to team addition process completed.")
    except Exception as e:
        logging.error(f"An error occurred while adding repositories to teams: {e}")
        return

if __name__ == "__main__":
    main()