# This file requires a Celery instance. Let's create a placeholder for now.
# In a real app, you'd have a central celery_app.py file.
# For simplicity, we'll define a dummy task.

# NOTE: For this to work, you need a celery instance.
# We will create a simple one in main.py for now.

def send_signing_request_email(recipient_email: str, signing_link: str):
    """
    Simulates sending a signing request email.
    In a real application, this would use a library like smtplib or a service like SendGrid.
    """
    print("---- SENDING EMAIL ----")
    print(f"TO: {recipient_email}")
    print("SUBJECT: Document Signing Request")
    print("\nBODY:")
    print("You have been requested to sign a document.")
    print(f"Please click the following link to proceed: {signing_link}")
    print("-----------------------")
    # In a real Celery task, you would not return anything significant.
    # The work is done in the background.