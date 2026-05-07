import uuid
from datetime import date, datetime
from sqlalchemy import String, Text, Date, DateTime, ForeignKey, Index, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    source: Mapped[str] = mapped_column(String(32), index=True)
    nafdac_number: Mapped[str | None] = mapped_column(String(64), index=True)
    product_name: Mapped[str] = mapped_column(Text)
    applicant_name: Mapped[str | None] = mapped_column(Text)
    manufacturer: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(Text)
    issue_date: Mapped[date | None] = mapped_column(Date)
    expiry_date: Mapped[date | None] = mapped_column(Date)
    
    raw: Mapped[dict] = mapped_column(JSONB) # Assumed NOT NULL. Add | None if it can be null.
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now() # NOTE: Only triggers on ORM updates, not raw SQL
    )

    # Added lazy="selectin" to prevent N+1 queries when accessing product.chunks
    chunks: Mapped[list["Chunk"]] = relationship(
        back_populates="product", 
        cascade="all, delete-orphan",
        lazy="selectin" 
    )

    __table_args__ = (
        Index("ix_products_source_nafdac", "source", "nafdac_number"),
    )

    def __repr__(self) -> str:
        return f"<Product id={self.id} name='{self.product_name}'>"


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), 
        index=True 
    )
    text: Mapped[str] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    embedded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    qdrant_point_id: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )

    product: Mapped["Product"] = relationship(back_populates="chunks")

    def __repr__(self) -> str:
        return f"<Chunk id={self.id} product_id={self.product_id}>"