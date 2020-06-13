def diff(sm_out, sm_err, v8_out, v8_err):
    for err in [b"EvalError", b"RangeError", b"ReferenceError",
                b"SyntaxError", b"TypeError", b"URIError"]:
        if sm_err.find(err) != -1:
            sm_err = err
        if v8_err.find(err) != -1:
            v8_err = err

    if sm_err != "" or v8_err != "":
        if sm_err != v8_err:
            if sm_err != "" and v8_err != "":
                return ("Err", sm_err, "Err", v8_err)
            elif sm_err == "":
                return ("Run", sm_out, "Err", v8_err)
            elif v8_err == "":
                return ("Err", sm_err, "Run", v8_out)
            else:
                # Not reach
                return None
        else:
            return None
    elif sm_out != v8_out:
        return ("Run", sm_out, "Run", v8_out)
    else:
        return None
