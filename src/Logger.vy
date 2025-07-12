# @version 0.4.1
# @license MIT

log_db: public(DynArray[String[1000], 2**32])

event AppLog:
    sender: indexed(address)
    value: uint256

@external
def add_log(log_mss: String[1000]):
    self.log_db.append(log_mss)
    log AppLog(msg.sender, len(self.log_db) + 1)

@view
@external
def get_length() -> uint256:
    return len(self.log_db)
    
@view
@external
def get_value(i:uint256) -> String[1000]:
    if i < len(self.log_db):
        return self.log_db[i]
    else:
        return "{}"