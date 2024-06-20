from typing import List

from lib.pendingactions.syncer import Syncer
from lib.pendingactions.syncer import factory

class SyncerA(Syncer):
    
    def get_access(self):
        return None

    def do_sync(self) -> List:
        self._response_payload = {
            "items": ",".join(sorted(self._request_payload['request_payload']['items']))
        }
        self.update_task()
        return self._response_payload['items']


factory.register_task('normal-sorting', SyncerA)