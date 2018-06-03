from sqlalchemy import Boolean, Column, Integer, String, DateTime, LargeBinary, Enum, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

import datetime

Base = declarative_base()


class AssignmentAction(Enum):
    SUBMIT_FOR_REVIEW="submit"
    REJECT="reject"
    APPROVE="approve"


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
    questions = relationship("InternalQuestion")


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
    assignment_refs = relationship("InternalAssignmentAssetXRef")


class InternalAssignmentAssetXRef(Base):

    __tablename__ = "an_assignments_assets_xref"
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("an_assets.id"))
    assignment_id = Column(Integer, ForeignKey("an_assignments.id"))

    assignment = relationship("InternalAssignment", back_populates="asset_refs")
    asset = relationship("InternalAsset", back_populates="assignment_refs")


class InternalAssignment(Base):

    __tablename__ = "an_assignments"
    id = Column(Integer, primary_key=True)
    summary_code=Column(String, nullable=False)
    assigned_user_id = Column(Integer, ForeignKey("an_users.id"), nullable=True)
    reviewer_id = Column(Integer, ForeignKey("an_users.id"), nullable=True)
    annotator_id = Column(Integer, ForeignKey("an_users.id"), nullable=True)
    corpus_id = Column(Integer, ForeignKey("an_corpora.id"))
    created = Column(DateTime, default=datetime.datetime.utcnow())
    question = Column(JSON, nullable=False)
    response = Column(JSON)
    state = Column(String)

    asset_refs = relationship("InternalAssignmentAssetXRef")
    assigned_user = relationship("InternalUser", foreign_keys=[assigned_user_id])
    assigned_reviewer = relationship("InternalUser", foreign_keys=[reviewer_id])
    corpus = relationship("InternalCorpus")


class InternalAssignmentHistory(Base):

    __tablename__ = "an_assignment_history"
    id = Column(Integer, primary_key=True)
    assignment_id = Column(Integer, ForeignKey("an_assigments.id"))
    updated_on = Column(DateTime, default=datetime.datetime.utcnow())
    state = Column(String)
    notes = Column(String)
    response = Column(JSON)


class InternalQuestion(Base):

    __tablename__ = "an_questions"
    id = Column(Integer, primary_key=True)
    content = Column(JSON, nullable=False)
    created = Column(DateTime, nullable=True, default=datetime.datetime.utcnow())
    creator_id = Column(Integer, ForeignKey("an_users.id"))
    corpus_id = Column(Integer, ForeignKey("an_corpora.id"))
    summary_code = Column(String)
    kind = Column(String)

    corpus = relationship("InternalCorpus", back_populates="questions")
    creator = relationship("InternalUser")


