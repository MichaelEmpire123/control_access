class BaseService:
    model = None

    @classmethod
    def get_all(cls, filters=None):
        qs = cls.model.objects.all()
        if filters:
            qs = qs.filter(**filters)
        return qs

    @classmethod
    def get_by_id(cls, id):
        try:
            return cls.model.objects.get(id=id)
        except cls.model.DoesNotExist:
            return None

    @classmethod
    def create(cls, data):
        instance = cls.model(**data)
        instance.full_clean()
        instance.save()
        return instance

    @classmethod
    def update(cls, id, data):
        instance = cls.get_by_id(id)
        if not instance:
            return None
        for key, value in data.items():
            setattr(instance, key, value)
        instance.full_clean()
        instance.save()
        return instance

    @classmethod
    def delete(cls, id):
        instance = cls.get_by_id(id)
        if instance:
            instance.delete()
            return True
        return False