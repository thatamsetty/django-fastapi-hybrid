from mongoengine import Document, StringField, BooleanField, DictField

class ProjectStatus(Document):
    project_id = StringField(required=True)
    active = BooleanField(default=True)
    running = BooleanField(default=False)
    completed = BooleanField(default=False)
    result = DictField()
