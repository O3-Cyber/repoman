import requests
import json
import os
import logging
from .utils import get_headers

logging.basicConfig(level=logging.INFO)

class GithubTeamClient:
    def __init__(self, github_token):
        """
        Initialize the GithubTeamClient with a GitHub token.
        
        Parameters:
        github_token (str): The GitHub token used for authentication.
        """
        self.github_token = github_token

    def create_team(self, org_or_user, team_data):
        """
        Create a team for a specified organization or user.
        
        Parameters:
        org_or_user (str): The name of the organization or user.
        team_data (dict): The data for the team to be created.
        """
        url = f"https://api.github.com/orgs/{org_or_user}/teams"
        headers = get_headers(self.github_token)

        # Function to check if a team already exists
        def team_exists(team_name):
            """
            Check if a team already exists.
            
            Parameters:
            team_name (str): The name of the team.
            
            Returns:
            bool: True if the team exists, False otherwise.
            """
            response = requests.get(f"{url}/{team_name}", headers=headers)
            return response.status_code == 200

        team_name = team_data['team_name']
        team_description = team_data['description']
        team_permission = team_data['permission']

        if team_exists(team_name):
            logging.info(f"Team '{team_name}' already exists. Skipping creation.")
        else:
            team_payload = {
                "name": team_name,
                "description": team_description,
                "privacy": "closed",
                "permission": team_permission,
            }

            response = requests.post(url, headers=headers, json=team_payload)

            if response.status_code == 201:
                logging.info(f"Team '{team_name}' created successfully.")
            else:
                logging.error(f"Failed to create Team '{team_name}'. Status code: {response.status_code}")
                logging.error(response.text)

    def create_teams(self, org_or_user, teams_data):
        """
        Create multiple teams for a specified organization or user.
        
        Parameters:
        org_or_user (str): The name of the organization or user.
        teams_data (dict): The data containing the teams to be created.
        """
        for team_data in teams_data.get('teams', []):
            self.create_team(org_or_user, team_data)

    def associate_teams_idp(self, org_or_user, teams_data):
        """
        Associate teams with Identity Provider (IDP) groups.
        
        Parameters:
        org_or_user (str): The name of the organization or user.
        teams_data (dict): The data containing the teams and their associated IDP groups.
        """
        headers = get_headers(self.github_token)
        teams = teams_data.get('teams', [])

        # Iterate through teams object
        for team_info in teams:
            team_name = team_info.get('team_name')
            team_description = team_info.get('description', '')

            # Check if the team has associated groups for IDP connections
            groups = team_info.get('groups', [])
            for group in groups:
                group_id = group.get('group_id')
                group_name = group.get('group_name')
                group_description = group.get('group_description')

                # Define the URL for creating teams and IDP connections
                idp_connections_url = f"https://api.github.com/orgs/{org_or_user}/teams/{team_name}/team-sync/group-mappings"
                logging.info(idp_connections_url)

                # Create a dictionary with the IDP connection details
                idp_connection_payload = {
                    "groups": [
                        {
                        "group_id": group_id,
                        "group_name": group_name,
                        "group_description": group_description,
                        }
                    ]
                }

                # Send a POST request to create the IDP connection
                response = requests.patch(idp_connections_url, headers=headers, json=idp_connection_payload)
                if response.status_code == 200:
                    logging.info(f"IDP connection for group '{group_name}' created successfully for team '{team_name}'.")
                else:
                    logging.error(f"Failed to create IDP connection for group '{group_name}' for team '{team_name}'. Status code: {response.status_code}")
                    logging.error(response.text)

    def add_repos_to_teams(self, org_or_user, teams_assoc_data):
        """
        Add repositories to teams.
        
        Parameters:
        org_or_user (str): The name of the organization or user.
        teams_assoc_data (dict): The data containing the teams and the repositories to be added.
        """
        headers = get_headers(self.github_token)
        teams = teams_assoc_data.get("teams", [])

        for team_assoc_data in teams:
            team_name = team_assoc_data.get("team_name")
            permission = team_assoc_data.get("permission")
            repo_names = team_assoc_data.get("repo_names", [])

            # Check if repo_names is not empty before making the API request
            if repo_names:
                for repo_name in repo_names:
                    url = f'https://api.github.com/orgs/{org_or_user}/teams/{team_name}/repos/{org_or_user}/{repo_name}'
                    logging.info(f"Trying to add '{repo_name}' to team '{team_name}' with URL: {url}")
                    data = {
                        'permission': permission
                    }
                    response = requests.put(url, headers=headers, json=data)
                    response.raise_for_status()  # Raise an exception for HTTP errors
            
            if response.status_code == 204:
                logging.info(f"Repository added to team '{team_name}' with permission '{permission}'")
                if repo_names:
                    logging.info(f"Repository: '{repo_names}' associated with the team.")
            else:
                logging.error(f"Error: Failed to add repository to team '{team_name}'")