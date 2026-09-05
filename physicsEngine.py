"""
Module: physicsEngine.py
Purpose:
    Executes deterministic mechanical, thermal, and Life Cycle Assessment (LCA)
    calculations without heuristic fallbacks or AI dependencies.
    
Closed-Form Formulations:
    - Direct Nominal Stress: sigma_nom = F_applied / A_char
    - Yield Safety Factor: SF_yield = sigma_y / sigma_nom
    - Euler Critical Buckling: P_cr = (pi^2 * E * I_xx) / (K * L_char)^2
    - Linear Thermal Expansion: deltaL = L_char * alpha * deltaT
    - Constrained Thermal Stress: sigma_th = E * alpha * deltaT
    - Embodied Carbon: E_total = mass * carbonFactor
"""

import math
from materialDatabase import materialDatabase, getMaterialData, getAllMaterialsSummary


def calculateNominalStress(appliedForceN, crossSectionalAreaMm2):
    """
    Calculates direct uniaxial nominal stress in MPa (N/mm^2).
    """
    if crossSectionalAreaMm2 <= 0:
        return 0.0
    return appliedForceN / crossSectionalAreaMm2


def calculateSafetyFactor(yieldStrengthMpa, appliedStressMpa):
    """
    Calculates the structural factor of safety relative to material yield strength.
    """
    if appliedStressMpa <= 0:
        return float("inf")
    return yieldStrengthMpa / appliedStressMpa


def evaluateEulerBuckling(elasticModulusGpa, momentOfInertiaMm4, unsupportedLengthMm, appliedForceN, endConstraintFactorK=1.0):
    """
    Calculates Euler elastic column instability threshold under compressive loads.
    Returns critical buckling load (P_cr) in Newtons and the resulting safety factor.
    """
    if unsupportedLengthMm <= 0 or momentOfInertiaMm4 <= 0:
        return {
            "criticalLoadN": float("inf"),
            "bucklingSafetyFactor": float("inf"),
            "isBucklingRisk": False
        }

    elasticModulusMpa = elasticModulusGpa * 1000.0
    effectiveLengthMm = endConstraintFactorK * unsupportedLengthMm
    criticalLoadN = (math.pi**2 * elasticModulusMpa * momentOfInertiaMm4) / (effectiveLengthMm**2)
    bucklingSafetyFactor = criticalLoadN / appliedForceN if appliedForceN > 0 else float("inf")
    isBucklingRisk = bucklingSafetyFactor < 1.5

    return {
        "criticalLoadN": round(criticalLoadN, 1),
        "bucklingSafetyFactor": round(bucklingSafetyFactor, 2),
        "isBucklingRisk": isBucklingRisk
    }


def calculateThermalDeformation(characteristicLengthMm, thermalExpansionPpmK, tempDeltaC):
    """
    Calculates unconstrained linear thermal expansion (delta L) in millimeters.
    """
    alphaLinear = thermalExpansionPpmK * 1e-6
    return round(characteristicLengthMm * alphaLinear * tempDeltaC, 4)


def calculateConstrainedThermalStress(elasticModulusGpa, thermalExpansionPpmK, tempDeltaC):
    """
    Calculates internal compressive thermal stress in MPa generated when expansion
    is rigidly constrained between immutable boundary surfaces.
    """
    elasticModulusMpa = elasticModulusGpa * 1000.0
    alphaLinear = thermalExpansionPpmK * 1e-6
    return round(elasticModulusMpa * alphaLinear * abs(tempDeltaC), 2)


def computePhysicalInvariants(cadMetrics, operationalParams):
    """
    Aggregates geometric measurements from CAD parsing with user operational
    constraints, computing all nominal stress, buckling, thermal, and carbon invariants.
    """
    volumeCm3 = cadMetrics["volumeCm3"]
    characteristicLengthMm = cadMetrics["characteristicLengthMm"]
    momentOfInertiaMm4 = cadMetrics["momentOfInertiaMm4"]
    characteristicAreaMm2 = cadMetrics["characteristicAreaMm2"]
    minThicknessMm = cadMetrics["minThicknessMm"]

    baselineKey = operationalParams["baselineMaterialKey"]
    appliedForceN = operationalParams["appliedForceN"]
    tempDeltaC = operationalParams["tempDeltaC"]
    isConstrained = operationalParams["isConstrainedThermal"]

    baselineData = getMaterialData(baselineKey)
    if not baselineData:
        raise ValueError(f"Invalid baseline material key specified: {baselineKey}")

    appliedStressMpa = calculateNominalStress(appliedForceN, characteristicAreaMm2)
    safetyFactor = calculateSafetyFactor(baselineData["yieldStrengthMpa"], appliedStressMpa)

    bucklingAnalysis = evaluateEulerBuckling(
        baselineData["elasticModulusGpa"],
        momentOfInertiaMm4,
        characteristicLengthMm,
        appliedForceN
    )

    deltaLengthMm = calculateThermalDeformation(
        characteristicLengthMm,
        baselineData["thermalExpansionPpmK"],
        tempDeltaC
    )

    thermalStressMpa = 0.0
    if isConstrained:
        thermalStressMpa = calculateConstrainedThermalStress(
            baselineData["elasticModulusGpa"],
            baselineData["thermalExpansionPpmK"],
            tempDeltaC
        )

    baselineMassKg = (volumeCm3 * baselineData["densityGcm3"]) / 1000.0
    baselineEmbodiedCo2e = baselineMassKg * baselineData["carbonFactorKgCo2ePerKg"]
    baselineCostUsd = baselineMassKg * baselineData["costPerKgUsd"]

    baselineSummary = {
        "materialKey": baselineKey,
        "material": baselineData["displayName"],
        "cadFormat": cadMetrics.get("format", "CAD Solid"),
        "isBRep": cadMetrics.get("isBRep", False),
        "volumeCm3": round(volumeCm3, 2),
        "massKg": round(baselineMassKg, 3),
        "embodiedCo2eKg": round(baselineEmbodiedCo2e, 2),
        "materialCostUsd": round(baselineCostUsd, 2),
        "appliedStressMpa": round(appliedStressMpa, 2),
        "safetyFactor": round(safetyFactor, 2),
        "deltaLengthMm": deltaLengthMm,
        "constrainedThermalStressMpa": thermalStressMpa,
        "isBucklingRisk": bucklingAnalysis["isBucklingRisk"],
        "bucklingSafetyFactor": bucklingAnalysis["bucklingSafetyFactor"],
        "momentOfInertiaMm4": round(momentOfInertiaMm4, 1),
        "minThicknessMm": round(minThicknessMm, 2),
        "characteristicAreaMm2": round(characteristicAreaMm2, 2),
        "characteristicLengthMm": round(characteristicLengthMm, 2),
        "extentsMm": [round(extentValue, 1) for extentValue in cadMetrics["extentsMm"]]
    }

    return {
        "baselineSummary": baselineSummary,
        "materialsPool": getAllMaterialsSummary(),
        "operationalParams": operationalParams
    }