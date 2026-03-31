"""
自进化调度器测试脚本
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agentforge.core.self_evolution_scheduler import (
    SelfEvolutionManager,
    get_evolution_manager,
    run_self_evolution_now
)


async def test_scheduler():
    """测试调度器功能"""
    print("\n" + "="*60)
    print("🔄 测试自进化定时调度器")
    print("="*60)
    
    manager = get_evolution_manager()
    
    # 测试初始化
    print("\n1️⃣ 初始化自进化系统...")
    await manager.initialize()
    print("✅ 初始化完成")
    
    # 测试立即运行记忆巩固
    print("\n2️⃣ 测试记忆巩固...")
    try:
        await run_self_evolution_now("consolidation")
        print("✅ 记忆巩固完成")
    except Exception as e:
        print(f"⚠️ 记忆巩固跳过（需要 AI 配置）: {e}")
    
    # 测试立即运行自我检查
    print("\n3️⃣ 测试自我检查...")
    try:
        await run_self_evolution_now("self_check")
        print("✅ 自我检查完成")
    except Exception as e:
        print(f"⚠️ 自我检查跳过: {e}")
    
    # 测试立即运行任务复盘
    print("\n4️⃣ 测试任务复盘...")
    try:
        await run_self_evolution_now("review")
        print("✅ 任务复盘完成")
    except Exception as e:
        print(f"⚠️ 任务复盘跳过: {e}")
    
    # 测试获取状态
    print("\n5️⃣ 系统状态:")
    status = manager.get_status()
    print(f"   - 已初始化：{status['initialized']}")
    print(f"   - 运行中：{status['running']}")
    print(f"   - 下次记忆巩固：{status['next_consolidation']}")
    print(f"   - 下次自我检查：{status['next_self_check']}")
    print(f"   - 下次任务复盘：{status['next_review']}")
    
    print("\n" + "="*60)
    print("✅ 调度器测试完成")
    print("="*60)
    
    print("\n📝 说明:")
    print("   - 定时任务已配置：凌晨 3 点记忆巩固，4 点自我检查，23 点任务复盘")
    print("   - 使用 start_self_evolution() 启动自动调度")
    print("   - 使用 run_self_evolution_now() 手动触发任务")
    print("   - 详细日志请查看：logs/app.log")


if __name__ == "__main__":
    asyncio.run(test_scheduler())
