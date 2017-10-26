import os
# peer -> (localhost, peer_port_number)
class RFCs:
    def __init__(self, rfcnumber, title, peer):
        self.rfcnumber = rfcnumber
        self.title = title
        self.present_list = [peer]

    def add_peer(self, peer):
        self.present_list.append(peer)

    def del_peer(self, peer):
        self.present_list.remove(peer)