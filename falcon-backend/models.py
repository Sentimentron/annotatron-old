from sqlalchemy import Boolean, Column, Integer, String, DateTime, LargeBinary, Enum, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

import datetime

Base = declarative_base()


class InternalUser(Base):
    __tablename__ = "an_users"

    id = Column(Integer, primary_key=True)
    username = Column(String)
    created = Column(DateTime, server_default='now')
    email = Column(String)
    password = Column(LargeBinary)
    password_last_changed = Column(DateTime)
    role = Column(Enum("Administrator", "Staff", "Reviewer", "Annotator"))
    deactivated_on = Column(DateTime, nullable=True)
    random_seed = Column(String)

    password_reset_needed = Column(Boolean)

    tokens = relationship('InternalToken')
    uploaded_assets = relationship('InternalAsset')


class InternalToken(Base):
    __tablename__ = "an_user_tokens"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('an_users.id'))
    expires = Column(DateTime)
    token = Column(String, unique=True)
    user = relationship("InternalUser", back_populates="tokens")


class InternalCorpus(Base):
    __tablename__ = "an_corpora"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    description = Column(String, nullable=True)
    created = Column(DateTime, nullable=True, default=datetime.datetime.utcnow())
    copyright_usage_restrictions = Column(String)
    assets = relationship("InternalAsset")


class InternalAsset(Base):
    __tablename__ = "an_assets"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    content = Column(LargeBinary)
    user_metadata = Column(JSON)
    date_uploaded = Column(DateTime, nullable=True, default=datetime.datetime.utcnow())
    copyright_usage_restrictions = Column(String)
    checksum = Column(String)
    mime_type = Column(String)
    type_description = Column(String)
    corpus_id = Column(Integer, ForeignKey("an_corpora.id"))
    uploader_id = Column(Integer, ForeignKey("an_users.id"))

    corpus = relationship("InternalCorpus", back_populates="assets")
    uploader = relationship("InternalUser", back_populates="uploaded_assets")


class InternalAbstractQuestion(Base):

    __tablename__ = "an_questions"
    id = Column(Integer, primary_key=True)
    human_prompt = Column(String)
    kind = Column(String)
    summary_code = Column(String)
    created = Column(DateTime, default=datetime.datetime.now())
    annotation_instructions = Column(String)
    detailed_annotations_instructions = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': type,
    }


class InternalMultipleChoiceQuestion(InternalAbstractQuestion):

    choices = Column(JSON)
    __mapper_args__ = {
        'polymorphic_identity': 'MultipleChoiceQuestion'
    }


class Internal1DRangeQuestion(InternalAbstractQuestion):
    maximum_segments = Column(Integer)
    minimum_segments = Column(Integer)
    choices = Column(JSON)
    freeform_allowed = Column(Boolean)
    can_overlap = Column(Boolean)
    __mapper_args__ = {
        'polymorphic_identity': '1DRangeQuestion'
    }

class