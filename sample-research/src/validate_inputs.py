from .io_loader import load_raw_inputs

def validate_inputs():
    data = load_raw_inputs()
    # simple checks
    required = ["city","industry","compute","energy","base_inflow","city_cond"]
    for k in required:
        assert k in data, f"missing {k}"
    return True
