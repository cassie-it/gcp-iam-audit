from googleapiclient.discovery import build
from google.auth import default
import csv

def get_project_iam_members(project_id):
    """Récupère les comptes ayant accès à un projet GCP avec détails des comptes de service et leurs permissions"""
    creds, _ = default()
    crm_service = build('cloudresourcemanager', 'v1', credentials=creds)
    iam_service = build('iam', 'v1', credentials=creds)

    # Récupérer la politique IAM du projet
    policy_request = crm_service.projects().getIamPolicy(resource=project_id, body={})
    policy = policy_request.execute()

    accounts_permissions = []
    service_accounts = {}

    for binding in policy.get("bindings", []):
        role = binding.get("role", "Unknown Role")
        for member in binding.get("members", []):
            if member.startswith("serviceAccount:"):
                sa_email = member.replace("serviceAccount:", "")
                if sa_email not in service_accounts:
                    service_accounts[sa_email] = {
                        "description": "N/A", "disabled": False,
                        "client_id": "N/A", "name": "N/A", "has_key": False
                    }
                accounts_permissions.append((sa_email, role))
            elif member.startswith(("user:", "group:")):
                accounts_permissions.append((member, role))

    # Récupérer les détails des comptes de service
    service_accounts_details = []
    for sa_email in service_accounts.keys():
        try:
            sa_request = iam_service.projects().serviceAccounts().get(
                name=f"projects/{project_id}/serviceAccounts/{sa_email}"
            )
            sa_info = sa_request.execute()
            service_accounts[sa_email]["description"] = sa_info.get("description", "N/A")
            service_accounts[sa_email]["disabled"] = sa_info.get("disabled", False)
            service_accounts[sa_email]["client_id"] = sa_info.get("uniqueId", "N/A")
            service_accounts[sa_email]["name"] = sa_info.get("displayName", "N/A")
            
            # Vérifier l'existence d'une clé
            keys_request = iam_service.projects().serviceAccounts().keys().list(
                name=f"projects/{project_id}/serviceAccounts/{sa_email}"
            )
            keys_response = keys_request.execute()
            service_accounts[sa_email]["has_key"] = bool(keys_response.get("keys", []))
            
        except Exception as e:
            print(e)
            service_accounts[sa_email].update({
                "description": "Erreur de récupération", "disabled": "N/A",
                "client_id": "N/A", "name": "N/A", "has_key": "N/A"
            })
        service_accounts_details.append((
            sa_email, service_accounts[sa_email]["description"], service_accounts[sa_email]["disabled"],
            service_accounts[sa_email]["client_id"], service_accounts[sa_email]["name"],
            service_accounts[sa_email]["has_key"]
        ))

    return sorted(accounts_permissions), service_accounts_details

if __name__ == "__main__":
    PROJECT_ID = "apimonday-377411"
    accounts_permissions, service_accounts_details = get_project_iam_members(PROJECT_ID)
    
    # Exporter les permissions en format CSV
    with open("iam_accounts_permissions.csv", "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Account", "Role"])
        for account, role in accounts_permissions:
            writer.writerow([account, role])
        
    with open("service_accounts_details.csv", "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Service Account", "Description", "Disabled", "Client ID", "Name", "Has Key"])
        for sa, description, disabled, client_id, name, has_key in service_accounts_details:
            writer.writerow([sa, description, disabled, client_id, name, has_key])
    
    print("✅ Fichiers 'iam_accounts_permissions.csv' et 'service_accounts_details.csv' générés avec succès.")
