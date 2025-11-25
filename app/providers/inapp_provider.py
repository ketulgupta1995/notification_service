from .base import Provider

class InAppProvider(Provider):
    name = 'inapp'

    async def send(self, user, subject, body, metadata=None):
        # In a real app, persist to DB and/or push via websocket. Here we simulate store.
        # metadata can carry notification_id for persistence by caller.
        return {'status': 'stored', 'provider_response': 'in-app stored'}