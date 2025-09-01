#!/usr/bin/env python3
"""
🔥 MULTI-SYMBOL SMC SCANNER - ARMA DEFINITIVA 🔥
Escáner masivo de zonas SMC para todos los símbolos configurados
Created by KRATOS - DOMINADOR DEL MERCADO CRIPTO
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import logging
import json
import concurrent.futures
from typing import List, Dict, Any, Optional, Tuple
from threading import Lock

# Our EPIC SMC Components
from demo.implacable_zones_detector import ImplacableZonesDetector
from config.config_manager import get_config

# Setup minimal logging for mass scanning
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


class MultiSymbolSMCScanner:
    """
    🏛️ MULTI-SYMBOL SMC SCANNER - ARMA DEFINITIVA
    Escáner masivo que analiza todos los símbolos configurados
    """
    
    def __init__(self, timeframe: str = "1h", max_workers: int = 5):
        self.timeframe = timeframe
        self.max_workers = max_workers
        
        print(f"🔥⚔️ MULTI-SYMBOL SMC SCANNER INITIALIZED ⚔️🔥")
        print("🏛️ ARMA DEFINITIVA - DOMINADOR DEL MERCADO CRIPTO 🏛️")
        print("=" * 80)
        
        # Load configuration
        self.config = get_config()
        self.symbols = self.config.symbols
        
        # Results storage
        self.scan_results: Dict[str, Dict] = {}
        self.scan_stats: Dict[str, Any] = {
            'total_symbols': len(self.symbols),
            'successful_scans': 0,
            'failed_scans': 0,
            'total_zones_detected': 0,
            'scan_start_time': None,
            'scan_end_time': None,
            'total_scan_time': 0.0
        }
        
        # Thread safety
        self._results_lock = Lock()
        
        print(f"✅ Scanner initialized for {len(self.symbols)} symbols")
        print(f"📊 Symbols to scan: {', '.join(self.symbols)}")
        print(f"⚡ Max workers: {self.max_workers}")
        print(f"⏰ Timeframe: {self.timeframe}")
    
    def scan_single_symbol(self, symbol: str) -> Tuple[str, Dict]:
        """
        Scan a single symbol with our IMPLACABLE weapon
        
        Args:
            symbol: Symbol to scan
            
        Returns:
            Tuple of (symbol, results_dict)
        """
        try:
            print(f"🎯 Scanning {symbol}...")
            
            # Deploy IMPLACABLE weapon
            detector = ImplacableZonesDetector(symbol, self.timeframe)
            
            # Suppress output for mass scanning
            import io
            import contextlib
            
            # Capture output to reduce noise
            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                success = detector.run_implacable_detection()
            
            if success:
                # Export results
                results = detector.export_implacable_json()
                
                if results:
                    # Add scan metadata
                    results['scan_timestamp'] = datetime.now().isoformat()
                    results['scan_success'] = True
                    results['scan_error'] = None
                    
                    # Calculate summary stats
                    supply_count = len(results.get('supply_zones', []))
                    demand_count = len(results.get('demand_zones', []))
                    total_zones = supply_count + demand_count
                    precision_score = results.get('tradingview_precision', {}).get('score', 0)
                    
                    results['summary'] = {
                        'supply_zones_count': supply_count,
                        'demand_zones_count': demand_count,
                        'total_zones': total_zones,
                        'precision_score': precision_score,
                        'has_zones': total_zones > 0
                    }
                    
                    print(f"✅ {symbol}: {total_zones} zones, {precision_score:.1f}% precision")
                    return symbol, results
                else:
                    print(f"⚠️ {symbol}: No results exported")
                    return symbol, {'scan_success': False, 'scan_error': 'No results exported'}
            else:
                print(f"❌ {symbol}: Detection failed")
                return symbol, {'scan_success': False, 'scan_error': 'Detection failed'}
                
        except Exception as e:
            print(f"❌ {symbol}: Error - {str(e)[:50]}...")
            return symbol, {
                'scan_success': False, 
                'scan_error': str(e),
                'scan_timestamp': datetime.now().isoformat()
            } 
   
    def scan_all_symbols_parallel(self) -> Dict[str, Dict]:
        """
        Scan all symbols in parallel using ThreadPoolExecutor
        
        Returns:
            Dictionary with all scan results
        """
        try:
            print(f"\n🔥⚔️ STARTING MASS SMC SCAN ⚔️🔥")
            print(f"🏛️ DEPLOYING IMPLACABLE WEAPONS ON {len(self.symbols)} TARGETS 🏛️")
            print("=" * 80)
            
            self.scan_stats['scan_start_time'] = datetime.now()
            start_time = time.time()
            
            # Parallel scanning with ThreadPoolExecutor
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all scanning tasks
                future_to_symbol = {
                    executor.submit(self.scan_single_symbol, symbol): symbol 
                    for symbol in self.symbols
                }
                
                # Collect results as they complete
                for future in concurrent.futures.as_completed(future_to_symbol):
                    symbol = future_to_symbol[future]
                    try:
                        symbol_result, results = future.result()
                        
                        with self._results_lock:
                            self.scan_results[symbol_result] = results
                            
                            if results.get('scan_success', False):
                                self.scan_stats['successful_scans'] += 1
                                zones_count = results.get('summary', {}).get('total_zones', 0)
                                self.scan_stats['total_zones_detected'] += zones_count
                            else:
                                self.scan_stats['failed_scans'] += 1
                                
                    except Exception as e:
                        print(f"❌ {symbol}: Future error - {e}")
                        with self._results_lock:
                            self.scan_results[symbol] = {
                                'scan_success': False,
                                'scan_error': f'Future error: {e}'
                            }
                            self.scan_stats['failed_scans'] += 1
            
            # Calculate final stats
            end_time = time.time()
            self.scan_stats['scan_end_time'] = datetime.now()
            self.scan_stats['total_scan_time'] = end_time - start_time
            
            print(f"\n🏆 MASS SMC SCAN COMPLETE! 🏆")
            print("=" * 80)
            print(f"⏱️  Total scan time: {self.scan_stats['total_scan_time']:.2f}s")
            print(f"✅ Successful scans: {self.scan_stats['successful_scans']}/{self.scan_stats['total_symbols']}")
            print(f"❌ Failed scans: {self.scan_stats['failed_scans']}")
            print(f"🎯 Total zones detected: {self.scan_stats['total_zones_detected']}")
            print(f"⚡ Average time per symbol: {self.scan_stats['total_scan_time']/len(self.symbols):.2f}s")
            
            return self.scan_results
            
        except Exception as e:
            print(f"❌ EPIC FAIL in mass scanning: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def display_scan_summary(self) -> None:
        """
        Display comprehensive scan summary
        """
        try:
            print(f"\n🏛️ COMPREHENSIVE SCAN SUMMARY 🏛️")
            print("=" * 80)
            
            # Sort symbols by zones detected (descending)
            successful_scans = {
                symbol: data for symbol, data in self.scan_results.items() 
                if data.get('scan_success', False)
            }
            
            if successful_scans:
                sorted_symbols = sorted(
                    successful_scans.items(),
                    key=lambda x: x[1].get('summary', {}).get('total_zones', 0),
                    reverse=True
                )
                
                print(f"🎯 TOP PERFORMERS (by zones detected):")
                print("-" * 60)
                
                for i, (symbol, data) in enumerate(sorted_symbols[:10], 1):
                    summary = data.get('summary', {})
                    supply_zones = summary.get('supply_zones_count', 0)
                    demand_zones = summary.get('demand_zones_count', 0)
                    total_zones = summary.get('total_zones', 0)
                    precision = summary.get('precision_score', 0)
                    
                    print(f"{i:2d}. {symbol:10s} | {total_zones:2d} zones | "
                          f"S:{supply_zones} D:{demand_zones} | {precision:5.1f}% precision")
                
                # Zone type distribution
                total_supply = sum(
                    data.get('summary', {}).get('supply_zones_count', 0) 
                    for data in successful_scans.values()
                )
                total_demand = sum(
                    data.get('summary', {}).get('demand_zones_count', 0) 
                    for data in successful_scans.values()
                )
                
                print(f"\n📊 ZONE DISTRIBUTION:")
                print("-" * 40)
                print(f"🔴 Supply zones: {total_supply}")
                print(f"🟢 Demand zones: {total_demand}")
                print(f"📈 Supply/Demand ratio: {total_supply/max(total_demand,1):.2f}")
                
                # Precision statistics
                precisions = [
                    data.get('summary', {}).get('precision_score', 0)
                    for data in successful_scans.values()
                ]
                
                if precisions:
                    avg_precision = np.mean(precisions)
                    max_precision = max(precisions)
                    min_precision = min(precisions)
                    
                    print(f"\n🎯 PRECISION STATISTICS:")
                    print("-" * 40)
                    print(f"📊 Average precision: {avg_precision:.1f}%")
                    print(f"🏆 Best precision: {max_precision:.1f}%")
                    print(f"⚠️  Worst precision: {min_precision:.1f}%")
            
            # Failed scans
            failed_scans = {
                symbol: data for symbol, data in self.scan_results.items() 
                if not data.get('scan_success', False)
            }
            
            if failed_scans:
                print(f"\n❌ FAILED SCANS ({len(failed_scans)}):")
                print("-" * 40)
                for symbol, data in failed_scans.items():
                    error = data.get('scan_error', 'Unknown error')[:50]
                    print(f"• {symbol}: {error}...")
            
            print(f"\n🏛️ SCAN COMPLETED SUCCESSFULLY! 🏛️")
            
        except Exception as e:
            print(f"❌ Error displaying summary: {e}")
    
    def export_results_to_json(self, filename: Optional[str] = None) -> str:
        """
        Export all scan results to JSON file
        
        Args:
            filename: Optional custom filename
            
        Returns:
            Path to exported file
        """
        try:
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"multi_symbol_smc_scan_{timestamp}.json"
            
            # Prepare export data
            export_data = {
                'scan_metadata': {
                    'scan_timestamp': datetime.now().isoformat(),
                    'timeframe': self.timeframe,
                    'scanner_version': '1.0.0',
                    'total_symbols_scanned': len(self.symbols),
                    'symbols_list': self.symbols
                },
                'scan_statistics': self.scan_stats,
                'scan_results': self.scan_results
            }
            
            # Write to file
            filepath = os.path.join('demo', filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            print(f"📁 Results exported to: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"❌ Error exporting results: {e}")
            return ""


def main():
    """
    🔥 MAIN EXECUTION - DEPLOY THE IMPLACABLE ARMY! 🔥
    """
    try:
        print("🏛️" + "=" * 78 + "🏛️")
        print("🔥" + " " * 20 + "MULTI-SYMBOL SMC SCANNER" + " " * 20 + "🔥")
        print("⚔️" + " " * 15 + "ARMA DEFINITIVA DEL OLIMPO" + " " * 15 + "⚔️")
        print("🏛️" + "=" * 78 + "🏛️")
        
        # Initialize scanner
        scanner = MultiSymbolSMCScanner(
            timeframe="1h",  # Can be changed to 4h, 1d, etc.
            max_workers=3    # Adjust based on your system
        )
        
        # Execute mass scan
        results = scanner.scan_all_symbols_parallel()
        
        if results:
            # Display comprehensive summary
            scanner.display_scan_summary()
            
            # Export results
            export_path = scanner.export_results_to_json()
            
            print(f"\n🏆 MISSION ACCOMPLISHED! 🏆")
            print(f"📊 Scanned {len(results)} symbols")
            print(f"📁 Results saved to: {export_path}")
            
        else:
            print("❌ No results obtained from mass scan")
            
    except KeyboardInterrupt:
        print(f"\n⚠️ Scan interrupted by user")
    except Exception as e:
        print(f"❌ EPIC FAIL in main execution: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()