from .base import Provider


class EmailProvider(Provider):
    name = 'email'

    async def send(self, user, subject, body, metadata=None):
        email = user.get('email')
        if not email:
            return {'status': 'skipped', 'reason': 'no email address'}
        # Simulate sending email
        print(f"Sending email to {email} with subject '{subject}' and body '{body}'")
        return {'status': 'sent', 'provider_response': 'Email sent successfully'}   