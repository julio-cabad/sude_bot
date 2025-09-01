#!/usr/bin/env python3
"""
🔥⚔️ STRUCTURE FOLLOWER ENGINE - MOTOR SUPREMO ⚔️🔥
Motor que genera señales Structure Follower automáticamente
Created by TITANES DEL CÓDIGO - BESTIAS DEL TRADING
"""

import sys
import os
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import math

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.zone_alert import EcuadorTimeUtils


class StructureType(Enum):
    """🏛️ TIPOS DE ESTRUCTURA DE MERCADO 🏛️"""
    BULLISH_STRUCTURE = "BULLISH_STRUCTURE"
    BEARISH_STRUCTURE = "BEARISH_STRUCTURE"
    BULLISH_REVERSAL = "BULLISH_REVERSAL"
    BEARISH_REVERSAL = "BEARISH_REVERSAL"
    HIGHER_RESISTANCE = "HIGHER_RESISTANCE"
    LOWER_RESISTANCE = "LOWER_RESISTANCE"
    HIGHER_SUPPORT = "HIGHER_SUPPORT"
    LOWER_SUPPORT = "LOWER_SUPPORT"


class TradeAction(Enum):
    """⚔️ ACCIONES DE TRADING ⚔️"""
    BUY = "BUY"
    SELL = "SELL"
    WAIT = "WAIT"
    CAUTION = "CAUTION"


@dataclass
class TradingSignal:
    """🎯 SEÑAL DE TRADING ÉPICA 🎯"""
    symbol: str
    action: TradeAction
    structure_type: StructureType
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_amount: float
    reward_amount: float
    risk_reward_ratio: float
    confidence: int  # 0-100%
    reasoning: str
    zone_data: Dict
    timestamp: str
    
    def to_dict(self) -> Dict:
        """Convierte a diccionario"""
        return {
            'symbol': self.symbol,
            'action': self.action.value,
            'structure_type': self.structure_type.value,
            'entry': self.entry_price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'risk_amount': self.risk_amount,
            'reward_amount': self.reward_amount,
            'risk_reward_ratio': self.risk_reward_ratio,
            'confidence': self.confidence,
            'reasoning': self.reasoning,
            'zone_data': self.zone_data,
            'timestamp': self.timestamp
        }


class StructureFollowerEngine:
    """🏛️⚔️ STRUCTURE FOLLOWER ENGINE SUPREMO ⚔️🏛️"""
    
    def __init__(self):
        print("🔥⚔️ INITIALIZING STRUCTURE FOLLOWER ENGINE ⚔️🔥")
        print("🏛️ MOTOR QUE HARÍA LLORAR A WALL STREET 🏛️")
        
        # Configuración de trading
        self.config = {
            'min_risk_reward_ratio': 2.0,      # Mínimo R/R aceptable
            'max_risk_reward_ratio': 20.0,     # Máximo R/R (filtrar outliers)
            'min_confidence_threshold': 60,     # Mínima confianza para señal
            'reversal_confidence_penalty': 20,  # Penalización para reversiones
            'structure_confidence_bonus': 15,   # Bonus para estructuras claras
            'zone_strength_multiplier': 5,      # Multiplicador por fuerza de zona
        }
        
        print("✅ Structure Follower Engine initialized!")
        print(f"📊 Min R/R: {self.config['min_risk_reward_ratio']}:1")
        print(f"🎯 Min Confidence: {self.config['min_confidence_threshold']}%")
    
    def analyze_structure_and_generate_signal(self, zone_data: Dict, context: Dict, 
                                            current_price: float) -> Optional[TradingSignal]:
        """
        🎯 ANALIZA ESTRUCTURA Y GENERA SEÑAL DE TRADING
        
        Args:
            zone_data: Datos de la zona detectada
            context: Contexto de zona anterior
            current_price: Precio actual del mercado
            
        Returns:
            TradingSignal o None si no hay señal válida
        """
        try:
            print(f"\\n🏛️ ANALYZING STRUCTURE FOR TRADING SIGNAL...")
            print("-" * 60)
            
            if not context.get('has_previous'):
                print("ℹ️ No previous zone context - no signal generated")
                return None
            
            # Obtener tipo de estructura
            relationship = context.get('relationship')
            if not relationship:
                print("⚠️ No relationship detected - no signal generated")
                return None
            
            structure_type = StructureType(relationship)
            print(f"📊 Structure Type: {structure_type.value}")
            
            # Generar señal basada en estructura
            signal = self._generate_signal_for_structure(
                structure_type, zone_data, context, current_price
            )
            
            if signal:
                print(f"✅ SIGNAL GENERATED: {signal.action.value} {signal.symbol}")
                print(f"🎯 Entry: ${signal.entry_price:.3f}")
                print(f"🛡️ Stop: ${signal.stop_loss:.3f}")
                print(f"🏆 Target: ${signal.take_profit:.3f}")
                print(f"⚔️ R/R: {signal.risk_reward_ratio:.1f}:1")
                print(f"💪 Confidence: {signal.confidence}%")
            else:
                print("❌ No valid signal generated")
            
            return signal
            
        except Exception as e:
            print(f"❌ Error analyzing structure: {e}")
            return None
    
    def _generate_signal_for_structure(self, structure_type: StructureType, 
                                     zone_data: Dict, context: Dict, 
                                     current_price: float) -> Optional[TradingSignal]:
        """⚔️ GENERA SEÑAL ESPECÍFICA PARA TIPO DE ESTRUCTURA"""
        
        symbol = zone_data.get('symbol', 'UNKNOWN')
        zone_type = zone_data.get('type')
        poi = zone_data.get('poi', 0)
        zone_top = zone_data.get('top', 0)
        zone_bottom = zone_data.get('bottom', 0)
        
        # Determinar acción basada en estructura y tipo de zona
        action, reasoning = self._determine_action(structure_type, zone_type)
        
        if action == TradeAction.WAIT:
            return None
        
        # Calcular puntos de entrada, stop y target
        entry, stop_loss, take_profit = self._calculate_entry_exit_points(
            action, zone_data, context, current_price
        )
        
        if not entry or not stop_loss or not take_profit:
            return None
        
        # Calcular risk/reward
        risk_amount = abs(entry - stop_loss)
        reward_amount = abs(take_profit - entry)
        
        if risk_amount == 0:
            return None
        
        risk_reward_ratio = reward_amount / risk_amount
        
        # Filtrar por R/R mínimo
        if risk_reward_ratio < self.config['min_risk_reward_ratio']:
            print(f"⚠️ R/R too low: {risk_reward_ratio:.1f}:1 < {self.config['min_risk_reward_ratio']}:1")
            return None
        
        if risk_reward_ratio > self.config['max_risk_reward_ratio']:
            print(f"⚠️ R/R too high (suspicious): {risk_reward_ratio:.1f}:1")
            return None
        
        # Calcular confianza
        confidence = self._calculate_confidence(structure_type, zone_data, context, risk_reward_ratio)
        
        # Filtrar por confianza mínima
        if confidence < self.config['min_confidence_threshold']:
            print(f"⚠️ Confidence too low: {confidence}% < {self.config['min_confidence_threshold']}%")
            return None
        
        return TradingSignal(
            symbol=symbol,
            action=action,
            structure_type=structure_type,
            entry_price=entry,
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_amount=risk_amount,
            reward_amount=reward_amount,
            risk_reward_ratio=risk_reward_ratio,
            confidence=confidence,
            reasoning=reasoning,
            zone_data=zone_data,
            timestamp=EcuadorTimeUtils.now().isoformat()
        )
    
    def _determine_action(self, structure_type: StructureType, zone_type: str) -> Tuple[TradeAction, str]:
        """🎯 DETERMINA ACCIÓN BASADA EN ESTRUCTURA Y ZONA"""
        
        if structure_type == StructureType.BULLISH_STRUCTURE:
            if zone_type == 'DEMAND':
                return TradeAction.BUY, "Estructura alcista + nueva zona DEMAND = Oportunidad de compra"
            else:
                return TradeAction.WAIT, "Estructura alcista pero zona SUPPLY - esperar mejor oportunidad"
        
        elif structure_type == StructureType.BEARISH_STRUCTURE:
            if zone_type == 'SUPPLY':
                return TradeAction.SELL, "Estructura bajista + nueva zona SUPPLY = Oportunidad de venta"
            else:
                return TradeAction.WAIT, "Estructura bajista pero zona DEMAND - esperar mejor oportunidad"
        
        elif structure_type == StructureType.BULLISH_REVERSAL:
            if zone_type == 'DEMAND':
                return TradeAction.BUY, "Posible reversión alcista + zona DEMAND = Compra con precaución"
            else:
                return TradeAction.CAUTION, "Reversión alcista pero zona SUPPLY - señal mixta"
        
        elif structure_type == StructureType.BEARISH_REVERSAL:
            if zone_type == 'SUPPLY':
                return TradeAction.SELL, "Posible reversión bajista + zona SUPPLY = Venta con precaución"
            else:
                return TradeAction.CAUTION, "Reversión bajista pero zona DEMAND - señal mixta"
        
        elif structure_type == StructureType.HIGHER_SUPPORT:
            return TradeAction.BUY, "Soporte más alto - fortaleza alcista confirmada"
        
        elif structure_type == StructureType.LOWER_SUPPORT:
            return TradeAction.CAUTION, "Soporte más bajo - posible debilidad"
        
        elif structure_type == StructureType.HIGHER_RESISTANCE:
            return TradeAction.CAUTION, "Resistencia más alta - momentum alcista pero cuidado"
        
        elif structure_type == StructureType.LOWER_RESISTANCE:
            return TradeAction.SELL, "Resistencia más baja - debilidad alcista"
        
        return TradeAction.WAIT, "Estructura no clara - esperar mejor setup"
    
    def _calculate_entry_exit_points(self, action: TradeAction, zone_data: Dict, 
                                   context: Dict, current_price: float) -> Tuple[float, float, float]:
        """💰 CALCULA PUNTOS DE ENTRADA Y SALIDA PRECISOS"""
        
        poi = zone_data.get('poi', 0)
        zone_top = zone_data.get('top', 0)
        zone_bottom = zone_data.get('bottom', 0)
        atr = zone_data.get('atr_used', 0)
        
        previous_zone = context.get('previous_zone', {})
        prev_poi = previous_zone.get('poi', 0)
        
        if action == TradeAction.BUY:
            # COMPRA - entrar cerca del POI de zona DEMAND
            entry = poi + (zone_top - poi) * 0.2  # 20% hacia arriba del POI
            stop_loss = zone_bottom - (atr * 0.1)  # Debajo de la zona + buffer
            
            # Target: zona anterior o extensión basada en ATR
            if prev_poi > poi:
                take_profit = prev_poi - (atr * 0.2)  # Cerca de zona anterior
            else:
                take_profit = poi + (atr * 3)  # Extensión 3x ATR
            
        elif action == TradeAction.SELL:
            # VENTA - entrar cerca del POI de zona SUPPLY
            entry = poi - (poi - zone_bottom) * 0.2  # 20% hacia abajo del POI
            stop_loss = zone_top + (atr * 0.1)  # Encima de la zona + buffer
            
            # Target: zona anterior o extensión basada en ATR
            if prev_poi < poi:
                take_profit = prev_poi + (atr * 0.2)  # Cerca de zona anterior
            else:
                take_profit = poi - (atr * 3)  # Extensión 3x ATR
        
        else:
            return None, None, None
        
        # Validar que los puntos sean lógicos
        if action == TradeAction.BUY:
            if stop_loss >= entry or take_profit <= entry:
                return None, None, None
        else:  # SELL
            if stop_loss <= entry or take_profit >= entry:
                return None, None, None
        
        return entry, stop_loss, take_profit
    
    def _calculate_confidence(self, structure_type: StructureType, zone_data: Dict, 
                            context: Dict, risk_reward_ratio: float) -> int:
        """🎯 CALCULA CONFIANZA DE LA SEÑAL (0-100%)"""
        
        base_confidence = 50  # Confianza base
        
        # Bonus por tipo de estructura
        if structure_type in [StructureType.BULLISH_STRUCTURE, StructureType.BEARISH_STRUCTURE]:
            base_confidence += self.config['structure_confidence_bonus']
        
        # Penalización por reversiones
        if structure_type in [StructureType.BULLISH_REVERSAL, StructureType.BEARISH_REVERSAL]:
            base_confidence -= self.config['reversal_confidence_penalty']
        
        # Bonus por fuerza de zona
        zone_strength = zone_data.get('swing_strength', 5)
        strength_bonus = min(zone_strength * self.config['zone_strength_multiplier'], 25)
        base_confidence += strength_bonus
        
        # Bonus por R/R ratio
        if risk_reward_ratio >= 5.0:
            base_confidence += 15
        elif risk_reward_ratio >= 3.0:
            base_confidence += 10
        elif risk_reward_ratio >= 2.0:
            base_confidence += 5
        
        # Bonus por distancia entre zonas (mejor si hay buen rango)
        if context.get('has_previous'):
            prev_zone = context.get('previous_zone', {})
            distance_pct = abs(zone_data.get('poi', 0) - prev_zone.get('poi', 0)) / prev_zone.get('poi', 1) * 100
            
            if 2.0 <= distance_pct <= 8.0:  # Rango óptimo
                base_confidence += 10
            elif distance_pct > 10.0:  # Muy lejos
                base_confidence -= 5
        
        # Bonus por recencia de formación
        candles_ago = zone_data.get('formation_candles_ago', 100)
        if candles_ago <= 10:
            base_confidence += 10
        elif candles_ago <= 20:
            base_confidence += 5
        
        # Limitar entre 0 y 100
        return max(0, min(100, base_confidence))
    
    def get_structure_explanation(self, structure_type: StructureType) -> str:
        """📚 OBTIENE EXPLICACIÓN DE ESTRUCTURA"""
        
        explanations = {
            StructureType.BULLISH_STRUCTURE: "Mercado en tendencia alcista clara - Higher Highs y Higher Lows",
            StructureType.BEARISH_STRUCTURE: "Mercado en tendencia bajista clara - Lower Highs y Lower Lows", 
            StructureType.BULLISH_REVERSAL: "Posible cambio a tendencia alcista - Higher Low detectado",
            StructureType.BEARISH_REVERSAL: "Posible cambio a tendencia bajista - Lower High detectado",
            StructureType.HIGHER_SUPPORT: "Soporte más alto - fortaleza alcista",
            StructureType.LOWER_SUPPORT: "Soporte más bajo - posible debilidad",
            StructureType.HIGHER_RESISTANCE: "Resistencia más alta - momentum alcista",
            StructureType.LOWER_RESISTANCE: "Resistencia más baja - debilidad alcista"
        }
        
        return explanations.get(structure_type, "Estructura desconocida")


def main():
    """🔥 FUNCIÓN PRINCIPAL PARA TESTING 🔥"""
    print("🔥⚔️🏛️ TESTING STRUCTURE FOLLOWER ENGINE 🏛️⚔️🔥")
    
    # Crear engine
    engine = StructureFollowerEngine()
    
    # Test data - BULLISH_STRUCTURE
    zone_data = {
        'symbol': 'ETHUSDT',
        'type': 'DEMAND',
        'poi': 4367.590,
        'top': 4378.560,
        'bottom': 4356.610,
        'atr_used': 43.91,
        'swing_strength': 10,
        'formation_candles_ago': 14
    }
    
    context = {
        'has_previous': True,
        'relationship': 'BULLISH_STRUCTURE',
        'previous_zone': {
            'type': 'SUPPLY',
            'poi': 4487.020,
            'top': 4498.000,
            'bottom': 4476.050
        }
    }
    
    current_price = 4397.50
    
    # Generar señal
    signal = engine.analyze_structure_and_generate_signal(zone_data, context, current_price)
    
    if signal:
        print(f"\\n🏆 SIGNAL GENERATED SUCCESSFULLY! 🏆")
        print(f"📊 Signal Data: {signal.to_dict()}")
    else:
        print(f"\\n❌ No signal generated")
    
    print(f"\\n🔥 STRUCTURE FOLLOWER ENGINE TEST COMPLETE! 🔥")


if __name__ == "__main__":
    main()