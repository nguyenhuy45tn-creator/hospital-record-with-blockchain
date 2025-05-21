# @version ^0.4.0
# @license MIT

log_db: public(DynArray[String[1000], 2**32])

@external
def add_log(log_mss: String[1000]):
    self.log_db.append(log_mss)

@view
@external
def get_length() -> uint256:
    return len(self.log_db)
    
