class PendingAction:
    def __init__(self, data):
        self.id = data['_id']
        self.request_payload = data['request_payload']
        self.received = data['received']

    def sync(self, syncer):
        syncer.start_object('id', self.id)
        syncer.add_property('request_payload', self.request_payload)
        syncer.add_property('received', self.received)
        
