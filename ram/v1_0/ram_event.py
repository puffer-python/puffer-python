class RamEvent:

    def __init__(self, r):
        self.id = r['id']
        self.ref = r['ref']
        self.parent_key = r['parent_key']
        self.key = r['key']
        self.type = r['type']
        self.status = r['status']
        self.retry_count = r['retry_count']
        self.payload = r['payload']
        self.created_at = r['created_at']
        self.updated_at = r['updated_at']
        self.want_to_send_after = r['want_to_send_after']
