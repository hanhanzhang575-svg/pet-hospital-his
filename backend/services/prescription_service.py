"""处方开具与库存冻结业务服务。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from backend.exceptions import ApiError
from backend.models.core import DrugInventory, Prescription, PrescriptionItem, User
from backend.schemas.prescription import PrescriptionCreate


def _generate_prescription_code(db: Session, now: datetime | None = None) -> str:
    """生成处方编码。"""
    current = now or datetime.now()
    prefix = f"RX{current.strftime('%Y%m%d')}"
    latest = (
        db.query(Prescription)
        .filter(Prescription.prescription_code.like(f"{prefix}%"))
        .order_by(Prescription.prescription_code.desc())
        .first()
    )
    if latest is None:
        seq = 1
    else:
        seq = int(latest.prescription_code[-4:]) + 1
    return f"{prefix}{seq:04d}"


def create_prescription(db: Session, payload: PrescriptionCreate) -> Prescription:
    """创建处方并冻结库存。"""
    doctor = db.query(User).filter(User.id == payload.doctor_id, User.is_active.is_(True)).first()
    if doctor is None:
        raise ApiError(code=404, message="医生不存在")
    if not doctor.is_licensed_vet:
        raise ApiError(code=403, message="仅执业兽医师可开具处方")
    if not payload.items:
        raise ApiError(code=400, message="处方明细不能为空")

    locked_inventory: dict[str, float] = {}
    inventory_cache: dict[int, DrugInventory] = {}
    for item in payload.items:
        inventory = (
            db.query(DrugInventory)
            .filter(DrugInventory.drug_id == item.drug_id, DrugInventory.branch_code == payload.clinic_id)
            .first()
        )
        if inventory is None:
            raise ApiError(code=404, message=f"药品{item.drug_id}无库存记录")
        if inventory.stock_qty < item.quantity:
            raise ApiError(code=409, message=f"药品{item.drug_id}库存不足")
        if inventory.stock_qty - item.quantity < inventory.safety_stock:
            raise ApiError(code=409, message=f"药品{item.drug_id}低于安全库存，禁止开方")
        inventory.stock_qty -= item.quantity
        inventory.frozen_for_prescription = True
        inventory_cache[item.drug_id] = inventory
        locked_inventory[str(item.drug_id)] = item.quantity

    prescription = Prescription(
        prescription_code=_generate_prescription_code(db),
        medical_record_id=payload.medical_record_id,
        doctor_id=payload.doctor_id,
        status="待缴费",
        locked_inventory=locked_inventory,
    )
    db.add(prescription)
    db.flush()

    for item in payload.items:
        db.add(
            PrescriptionItem(
                prescription_id=prescription.id,
                drug_id=item.drug_id,
                dosage=item.dosage,
                frequency=item.frequency,
                duration_days=item.duration_days,
                quantity=item.quantity,
            )
        )

    db.commit()
    db.refresh(prescription)
    return prescription


def list_prescriptions(db: Session, clinic_id: str | None = None) -> list[Prescription]:
    """查询处方列表。"""
    query = db.query(Prescription)
    if clinic_id:
        query = query.join(PrescriptionItem, PrescriptionItem.prescription_id == Prescription.id).join(
            DrugInventory, DrugInventory.drug_id == PrescriptionItem.drug_id
        ).filter(DrugInventory.branch_code == clinic_id)
    return query.order_by(Prescription.id.desc()).all()


def invalidate_prescription(db: Session, prescription_id: int) -> Prescription:
    """作废处方并释放冻结库存。"""
    prescription = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    if prescription is None:
        raise ApiError(code=404, message="处方不存在")
    if prescription.status in {"已发药", "已失效"}:
        raise ApiError(code=409, message="当前处方状态不可作废")

    for drug_id_text, qty in (prescription.locked_inventory or {}).items():
        try:
            drug_id = int(drug_id_text)
        except ValueError:
            continue
        inventory = db.query(DrugInventory).filter(DrugInventory.drug_id == drug_id).first()
        if inventory is None:
            continue
        inventory.stock_qty += float(qty or 0)
        inventory.frozen_for_prescription = False

    prescription.status = "已失效"
    db.commit()
    db.refresh(prescription)
    return prescription


def restore_prescription(db: Session, prescription_id: int) -> Prescription:
    """撤销作废处方（重新冻结库存）。"""
    prescription = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    if prescription is None:
        raise ApiError(code=404, message="处方不存在")
    if prescription.status != "已失效":
        raise ApiError(code=409, message="仅已失效处方可撤销作废")
    for drug_id_text, qty in (prescription.locked_inventory or {}).items():
        try:
            drug_id = int(drug_id_text)
        except ValueError:
            continue
        inventory = db.query(DrugInventory).filter(DrugInventory.drug_id == drug_id).first()
        if inventory is None:
            continue
        if inventory.stock_qty < float(qty or 0):
            raise ApiError(code=409, message=f"药品{drug_id}当前库存不足，无法撤销作废")
        inventory.stock_qty -= float(qty or 0)
        inventory.frozen_for_prescription = True
    prescription.status = "待缴费"
    db.commit()
    db.refresh(prescription)
    return prescription

