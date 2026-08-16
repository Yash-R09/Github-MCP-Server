from app.github.client import GitHubClient


client = GitHubClient()

try:
    repository = client.get_repository("microsoft", "vscode")

    print("Repository:", repository["full_name"])
    print("Description:", repository["description"])
    print("Language:", repository["language"])
    print("Stars:", repository["stargazers_count"])
    print("Forks:", repository["forks_count"])

finally:
    client.close()