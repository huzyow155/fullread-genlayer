# v0.2.16
# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

import json

from genlayer import *


def _run_custom_consensus(leader_fn, validator_fn):
    vm = gl.vm
    fn = (
        getattr(vm, "run_nondet_default", None)
        or getattr(vm, "run_nondet", None)
        or getattr(vm, "run_nondet_unsafe", None)
    )
    if fn is not None:
        return fn(leader_fn, validator_fn)
    return None


def _leader_payload(leader_res):
    if leader_res is None:
        return None
    if hasattr(leader_res, "calldata"):
        cd = leader_res.calldata
        if isinstance(cd, dict):
            return cd
        if isinstance(cd, str):
            try:
                return json.loads(cd)
            except Exception:
                return None
    if isinstance(leader_res, dict):
        return leader_res
    if isinstance(leader_res, str):
        try:
            return json.loads(leader_res)
        except Exception:
            return None
    return None


class RuntimeProbe(gl.Contract):
    probe_data: TreeMap[str, str]

    def __init__(self):
        pass

    @gl.public.view
    def probe_runtime(self) -> str:
        import hashlib
        import json

        vm = gl.vm
        nondet = gl.nondet
        storage = gl.storage

        vm_attrs = [
            "run_nondet_default",
            "run_nondet",
            "run_nondet_unsafe",
            "Return",
            "UserError",
        ]
        available_vm = [attr for attr in vm_attrs if hasattr(vm, attr)]

        has_copy_to_memory = hasattr(storage, "copy_to_memory")

        nondet_attrs = dir(nondet) if hasattr(gl, "nondet") else []
        web_attrs = []
        if hasattr(nondet, "web"):
            web_attrs = dir(nondet.web)

        has_eq_principle = hasattr(gl, "eq_principle")
        eq_attrs = dir(gl.eq_principle) if has_eq_principle else []

        test_sha = hashlib.sha256(b"probe").hexdigest()

        res = {
            "available_vm_nondet": available_vm,
            "has_copy_to_memory": has_copy_to_memory,
            "hashlib_working": test_sha
            == "a7a4dc6f8f5eef12574e4be2c4876b4a530eb7b9b1be3855a4fb797e5564fe06",
            "json_working": True,
            "nondet_attrs": nondet_attrs,
            "web_attrs": web_attrs,
            "eq_principle_attrs": eq_attrs,
        }
        return json.dumps(res)

    @gl.public.write
    def probe_web_and_consensus(self, test_url: str) -> None:
        import json

        def leader():
            info = {}
            if hasattr(gl.nondet, "web") and hasattr(gl.nondet.web, "get"):
                try:
                    res = gl.nondet.web.get(test_url)
                    info["web_get_type"] = str(type(res))
                    info["web_get_dir"] = dir(res)
                    if hasattr(res, "status"):
                        info["status"] = getattr(res, "status")
                    if hasattr(res, "body"):
                        b = getattr(res, "body")
                        info["body_type"] = str(type(b))
                        info["body_preview"] = str(b)[:100]
                except Exception as e:
                    info["web_get_error"] = str(e)
            else:
                info["web_get"] = "absent"
            return json.dumps(info)

        def validator(leader_res):
            p = _leader_payload(leader_res)
            return p is not None

        custom_fn = (
            getattr(gl.vm, "run_nondet_default", None)
            or getattr(gl.vm, "run_nondet", None)
            or getattr(gl.vm, "run_nondet_unsafe", None)
        )

        if custom_fn is not None:
            raw = _run_custom_consensus(leader, validator)
            self.probe_data["consensus_used"] = "custom"
            self.probe_data["web_result"] = str(raw)
        else:
            raw = gl.eq_principle.strict_eq(leader)
            self.probe_data["consensus_used"] = "strict_eq"
            self.probe_data["web_result"] = str(raw)

    @gl.public.view
    def get_probe_data(self, key: str) -> str:
        return self.probe_data.get(key, "")
