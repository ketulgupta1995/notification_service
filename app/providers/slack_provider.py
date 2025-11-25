from .base import Provider
import aiohttp

class SlackProvider(Provider):
    name = 'slack'

    async def send(self,user, subject, body, metadata=None):
        webhook = user.get('slack_webhook')
        if not webhook:
            return {'status': 'skipped', 'reason': 'no slack webhook'}
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(webhook, json={'text': body}) as resp:
                    text = await resp.text()
                    return {'status': 'sent' if resp.status == 200 else 'error', 'provider_response': f'{resp.status}: {text}'}
            except Exception as e:
                return {'status': 'error', 'provider_response': str(e)}