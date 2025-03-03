from google.cloud import logging

def get_service_account_creator(sa_email):
    client = logging.Client()
    filter_str = (
        f'resource.type="service_account" '
        f'resource.labels.email_id="{sa_email}" '
        f'timestamp>="2023-01-01T00:00:00Z"'
    )
    entries = client.list_entries(filter_=filter_str, order_by=logging.DESCENDING)

    for entry in entries:
        print(entry)
    return None
if __name__ == "__main__":
    sa_email = "crm-158@apimonday-377411.iam.gserviceaccount.com"
    get_service_account_creator(sa_email)