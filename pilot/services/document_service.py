from pilot.models import ComplianceDocument
from pilot.services.base_service import BaseService
from pilot.services.contractor_service import ContractorService


class DocumentService(BaseService):
    model = ComplianceDocument

    @classmethod
    def create_document(cls, data):
        document = cls.create(data)
        contractor_id = data.get('contractor_id')
        ContractorService.recheck_accreditation(contractor_id)
        return document

    @classmethod
    def delete_document(cls, doc_id):
        document = cls.get_by_id(doc_id)
        if not document:
            return False

        contractor_id = document.contractor_id
        document.delete()
        ContractorService.recheck_accreditation(contractor_id)
        return True