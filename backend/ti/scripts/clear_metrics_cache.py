"""
Script to clear metrics cache.
This ensures that metrics are recalculated using the new SLA start date filter (01.01.2026).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def clear_metrics_cache():
    """Clear all metrics-related caches"""
    
    try:
        print("\n[CACHE] 🧹 Starting metrics cache cleanup...")
        
        # Try to clear SLA cache if it exists
        try:
            from ti.services.sla_cache import clear_all_caches
            clear_all_caches()
            print("[CACHE] ✓ SLA cache cleared")
        except Exception as e:
            print(f"[CACHE] ℹ️ SLA cache not available or already clean: {e}")
        
        # Try to clear cache manager if it exists
        try:
            from ti.services.cache_manager_incremental import ChamadosTodayCounter
            # Reset the counter
            ChamadosTodayCounter._reset_cache()
            print("[CACHE] ✓ Daily counter cache cleared")
        except Exception as e:
            print(f"[CACHE] ℹ️ Daily counter not available or already clean: {e}")
        
        # Try to clear cache debouncer
        try:
            from ti.services.cache_debouncer import CacheDebouncer
            CacheDebouncer.clear_all()
            print("[CACHE] ✓ Debouncer cache cleared")
        except Exception as e:
            print(f"[CACHE] ℹ️ Debouncer not available or already clean: {e}")
        
        print("[CACHE] ✅ Metrics cache cleanup completed!\n")
        
    except Exception as e:
        print(f"[CACHE] ⚠️  Error during cache cleanup: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    clear_metrics_cache()
