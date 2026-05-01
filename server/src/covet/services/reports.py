"""Report generation service."""

from __future__ import annotations

import csv
import io
import json
import zipfile
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

from covet.models import Collection, Item, Photo


class CollectionReport:
    """Generate various reports for a collection."""

    def __init__(self, db: DBSession, collection: Collection):
        self.db = db
        self.collection = collection

    def _get_items(self, include_archived: bool = False) -> list[Item]:
        """Get items in the collection."""
        stmt = select(Item).where(Item.collection_id == self.collection.id)
        if not include_archived:
            stmt = stmt.where(Item.archived_at.is_(None))
        return self.db.scalars(stmt.order_by(Item.title)).all()

    def generate_totals(self, include_archived: bool = False) -> dict:
        """Generate collection totals (count, value)."""
        items = self._get_items(include_archived)
        total_value = sum(
            (item.value or Decimal(0)) for item in items
        )
        total_count = len(items)

        return {
            "collection_id": self.collection.id,
            "collection_name": self.collection.name,
            "total_items": total_count,
            "total_value": float(total_value),
            "average_item_value": float(total_value / total_count) if total_count > 0 else 0,
            "generated_at": datetime.utcnow().isoformat(),
        }

    def generate_csv_export(self, include_archived: bool = False) -> str:
        """Generate CSV export of all items."""
        items = self._get_items(include_archived)

        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=[
                "ID",
                "Title",
                "Subtitle",
                "Category",
                "Value",
                "Quantity",
                "Notes",
                "Archived",
                "Created Date",
            ],
        )
        writer.writeheader()

        for item in items:
            writer.writerow(
                {
                    "ID": item.id,
                    "Title": item.title or "",
                    "Subtitle": item.subtitle or "",
                    "Category": item.category.slug if item.category else "",
                    "Value": item.value or 0,
                    "Quantity": item.quantity or 1,
                    "Notes": item.notes or "",
                    "Archived": "Yes" if item.archived_at else "No",
                    "Created Date": item.created_at.isoformat() if item.created_at else "",
                }
            )

        return output.getvalue()

    def generate_insurance_export(self) -> bytes:
        """Generate insurance-friendly export bundle (ZIP with CSV, photos, documents)."""
        items = self._get_items(include_archived=False)

        # Create ZIP file in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # Add CSV with item data
            csv_content = self.generate_csv_export(include_archived=False)
            zip_file.writestr("items.csv", csv_content)

            # Add manifest with collection info
            manifest = {
                "collection": self.collection.name,
                "exported_at": datetime.utcnow().isoformat(),
                "total_items": len(items),
                "total_value": float(sum(item.value or Decimal(0) for item in items)),
            }
            zip_file.writestr("manifest.json", json.dumps(manifest, indent=2))

            # Add photos
            for item in items:
                photos = self.db.scalars(
                    select(Photo).where(Photo.item_id == item.id)
                ).all()
                for photo in photos:
                    if photo.photo_path:
                        try:
                            with open(photo.photo_path, "rb") as f:
                                photo_data = f.read()
                                # Store with a readable path structure
                                zip_path = f"photos/{item.id}/{photo.id}.jpg"
                                zip_file.writestr(zip_path, photo_data)
                        except (IOError, OSError):
                            # Skip photos that can't be read
                            pass

        zip_buffer.seek(0)
        return zip_buffer.getvalue()

    def generate_bom_text(self) -> str:
        """Generate Bill of Materials as text."""
        items = self._get_items(include_archived=False)

        lines = [
            f"BILL OF MATERIALS - {self.collection.name}",
            f"Generated: {datetime.utcnow().isoformat()}",
            "",
            f"Total Items: {len(items)}",
            f"Total Value: ${sum(item.value or Decimal(0) for item in items)}",
            "",
            "=" * 80,
            "",
        ]

        # Group by category
        by_category: dict[str, list[Item]] = {}
        for item in items:
            cat = item.category.slug if item.category else "Uncategorized"
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(item)

        for category in sorted(by_category.keys()):
            lines.append(f"\n{category.upper()}")
            lines.append("-" * 80)
            for item in sorted(by_category[category], key=lambda i: i.title or ""):
                value_str = f"${item.value}" if item.value else "N/A"
                qty_str = f"x{item.quantity}" if item.quantity and item.quantity > 1 else ""
                lines.append(
                    f"  {item.title or 'Untitled':<40} {value_str:>10} {qty_str:>8}"
                )
                if item.subtitle:
                    lines.append(f"    > {item.subtitle}")

        return "\n".join(lines)
