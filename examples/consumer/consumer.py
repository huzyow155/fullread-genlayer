# v0.2.16
# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

import json

from genlayer import *


class DocumentPolicyConsumer(gl.Contract):
    full_read_address: Address
    approved_documents: TreeMap[str, str]

    def __init__(self, full_read_address_str: str):
        self.full_read_address = Address(full_read_address_str)

    @gl.public.write
    def approve_if_passed(self, review_id: str) -> None:
        full_read = gl.get_contract_at(self.full_read_address)
        review_json_str = full_read.view().get_review(review_id)
        data = json.loads(review_json_str)

        outcome = str(data.get("outcome", "")).upper()
        coverage = int(data.get("coverage_bp", 0))

        if outcome != "PASS" or coverage != 10000:
            raise gl.vm.UserError(
                f"approval rejected: outcome={outcome}, coverage_bp={coverage} (requires PASS and 10000 bp)"
            )

        doc_url = str(data.get("doc_url", ""))
        self.approved_documents[doc_url] = review_id

    @gl.public.view
    def is_document_approved(self, doc_url: str) -> bool:
        return doc_url in self.approved_documents

    @gl.public.view
    def get_approval_review_id(self, doc_url: str) -> str:
        return self.approved_documents.get(doc_url, "")
