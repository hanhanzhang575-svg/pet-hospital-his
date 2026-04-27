#!/usr/bin/env python
"""RFM调试脚本 - 直接测试数据库RFM计算"""

import sys
sys.path.insert(0, 'C:\\Users\\zhangmohan\\Desktop\\信息系统')

from backend.database import SessionLocal
from backend.services.rfm_analyzer import analyze_owner_rfm

db = SessionLocal()
try:
    result = analyze_owner_rfm(db)
    print(f"✓ RFM分析成功，返回 {len(result)} 条客户记录")
    for i, item in enumerate(result[:3]):
        print(f"  {i+1}. {item.owner_name}")
        print(f"     R:{item.recency_days} F:{item.frequency} M:{item.monetary}")
        print(f"     Score:{item.rfm_score} Risk:{item.risk_level}")
    
    # 检查是否所有必需字段都有值
    if result:
        sample = result[0]
        print(f"\n首条记录完整性检查:")
        print(f"  owner_id: {sample.owner_id} ({type(sample.owner_id).__name__})")
        print(f"  owner_name: {sample.owner_name} ({type(sample.owner_name).__name__})")
        print(f"  recency_days: {sample.recency_days} ({type(sample.recency_days).__name__})")
        print(f"  frequency: {sample.frequency} ({type(sample.frequency).__name__})")
        print(f"  monetary: {sample.monetary} ({type(sample.monetary).__name__})")
        print(f"  rfm_score: {sample.rfm_score} ({type(sample.rfm_score).__name__})")
        print(f"  risk_level: {sample.risk_level} ({type(sample.risk_level).__name__})")
    else:
        print("⚠ 无RFM数据（可能没有客户或发票记录）")
finally:
    db.close()
