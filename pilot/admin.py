from django.contrib import admin


from pilot.models import ComplianceDocument, User, Contractor, ContractorEmployee, AccessPass, Blacklist

# Register your models here.

admin.site.register(User)
admin.site.register(Contractor)
admin.site.register(ComplianceDocument)
admin.site.register(ContractorEmployee)
admin.site.register(AccessPass)
admin.site.register(Blacklist)

