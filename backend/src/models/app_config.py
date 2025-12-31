from ..extensions import db

class AppConfig(db.Model):
    """
    Application configuration key-value storage.
    """
    __tablename__ = 'app_config'

    key = db.Column(db.Text, primary_key=True)
    value = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), onupdate=db.func.now())

    def __repr__(self):
        return f"<AppConfig {self.key}>"
