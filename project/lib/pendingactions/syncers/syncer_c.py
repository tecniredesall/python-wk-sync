import random

from typing import List
from lib.pendingactions.syncer import Syncer, factory

class SyncerC(Syncer):
    
    def get_access(self):
        return None

    def do_sync(self) -> List:
        random.shuffle(self._request_payload['request_payload']['items'])
        self._response_payload = {
            "items": ",".join(self._request_payload['request_payload']['items'])
        }
        self.update_task()
        return self._response_payload['items']


factory.register_task('random-sorting', SyncerC)